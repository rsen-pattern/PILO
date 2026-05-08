"""
Content generation orchestrator — wraps prompt_chain.py for multi-marketplace runs.
Maintains backward-compatible helpers for scraping/doc context.
"""

import json
import os
import time

import streamlit as st

from .utils import get_missing_attributes, parse_json_response, row_to_dict
from .cost_tracker import CostTracker
from core.prompt_chain import run_chain, build_system_prompt


def _create_client(settings):
    """Create the Bifrost API client. Returns (client, model_id)."""
    from openai import OpenAI

    api_key = settings.get("bifrost_api_key", "")
    base_url = settings.get("bifrost_base_url", "https://bifrost.pattern.com")

    if not api_key:
        raise ValueError("Bifrost API key is not configured. Please set it in Control Centre.")

    client = OpenAI(base_url=base_url, api_key=api_key)
    model_id = settings.get("model", "anthropic/claude-sonnet-4-6")
    return client, model_id


def get_doc_context_for_sku(sku, ingested_docs):
    """Get relevant document context for a SKU, capped at 8000 chars total."""
    if not ingested_docs:
        return None
    relevant_texts = []
    total_cap = 8000
    total_len = 0
    for doc in ingested_docs:
        applicable = doc.get("applicable_skus", [])
        if applicable == ["All"] or sku in applicable:
            remaining = total_cap - total_len
            if remaining <= 0:
                break
            text_chunk = doc["text"][:min(3000, remaining)]
            relevant_texts.append(f"[{doc['type']} - {doc['filename']}]:\n{text_chunk}")
            total_len += len(text_chunk)
    return "\n\n".join(relevant_texts) if relevant_texts else None


def _sanitize_for_json(obj):
    """Recursively convert non-serializable types to strings."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


def load_cached_run(cache_file: str) -> dict:
    """Load a previous run from a .jsonl cache file.

    Returns {(sku, mp_key): chain_result}
    """
    results = {}
    try:
        with open(cache_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                results[(entry["sku"], entry["marketplace"])] = entry["result"]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return results


def run_generation(enriched_df, settings, selected_skus=None, generate_options=None):
    """Run multi-marketplace content generation via the prompt chain.

    Returns (results_dict, errors_list, cost_tracker).
    results_dict is keyed by (sku, marketplace).
    """
    run_id = f"pilo_run_{int(time.time())}"
    cache_dir = ".pilo_cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = f"{cache_dir}/{run_id}.jsonl"
    st.session_state["last_run_cache_file"] = cache_file

    try:
        client, model_id = _create_client(settings)
    except ValueError as e:
        st.error(str(e))
        return {}, [str(e)], CostTracker()

    marketplaces = settings.get("target_marketplace", ["amazon_au"])
    if isinstance(marketplaces, str):
        marketplaces = [marketplaces]

    # Convert display names to keys if needed
    from config.marketplace_configs import MARKETPLACE_KEY_BY_NAME
    marketplace_keys = []
    for mp in marketplaces:
        key = MARKETPLACE_KEY_BY_NAME.get(mp, mp)
        marketplace_keys.append(key)

    research_data = st.session_state.get("research_results", {})
    predict_keywords = st.session_state.get("predict_keywords", {})
    ingested_docs = st.session_state.get("ingested_docs", [])
    scraped_df = st.session_state.get("scraped_df")
    crossretail_df = st.session_state.get("crossretail_df")
    cost_tracker = CostTracker()

    if selected_skus is None:
        selected_skus = enriched_df["sku"].tolist() if "sku" in enriched_df.columns else []

    results = {}
    errors = []
    total = len(selected_skus) * len(marketplace_keys)
    current = 0

    progress_bar = st.progress(0, text=f"Starting generation via Bifrost ({model_id})...")
    status_container = st.container()

    for sku in selected_skus:
        if "sku" in enriched_df.columns:
            row_mask = enriched_df["sku"] == sku
        else:
            continue

        if not row_mask.any():
            errors.append(f"SKU {sku} not found in enriched data")
            current += len(marketplace_keys)
            continue

        row = enriched_df[row_mask].iloc[0]
        product = row_to_dict(row)
        sku_research = research_data.get(sku, None)
        conf_threshold = settings.get("confidence_threshold", 0.7)
        if sku_research and sku_research.get("confidence", 0) < conf_threshold:
            sku_research = {**sku_research, "_below_threshold": True}
        sku_predict = predict_keywords.get(sku, [])

        # Gather scraped data for this SKU
        sku_scraped = None
        if scraped_df is not None and "sku" in scraped_df.columns:
            scraped_mask = scraped_df["sku"] == sku
            if scraped_mask.any():
                sku_scraped = row_to_dict(scraped_df[scraped_mask].iloc[0])

        # Gather crossretail data for this SKU
        sku_crossretail = None
        if crossretail_df is not None and "sku" in crossretail_df.columns:
            cr_mask = crossretail_df["sku"] == sku
            if cr_mask.any():
                sku_crossretail = row_to_dict(crossretail_df[cr_mask].iloc[0])

        # Gather document context for this SKU
        sku_doc_context = get_doc_context_for_sku(sku, ingested_docs)

        for mp_key in marketplace_keys:
            current += 1
            progress_bar.progress(
                min(current / total, 0.99),
                text=f"Generating {sku} for {mp_key} ({current}/{total})",
            )

            def step_callback(step_name, step_num, total_steps):
                progress_bar.progress(
                    min(current / total, 0.99),
                    text=f"{sku} / {mp_key}: Step {step_num}/{total_steps} — {step_name}",
                )

            try:
                if (sku, mp_key) in results:
                    chain_result = results[(sku, mp_key)]
                else:
                    chain_result = run_chain(
                        client=client,
                        model=model_id,
                        product=product,
                        marketplace_key=mp_key,
                        settings=settings,
                        research_data=sku_research,
                        predict_keywords=sku_predict if isinstance(sku_predict, list) else [],
                        scraped_data=sku_scraped,
                        document_context=sku_doc_context,
                        crossretail_data=sku_crossretail,
                        progress_callback=step_callback,
                    )
                    try:
                        safe_result = _sanitize_for_json(chain_result)
                        with open(cache_file, "a") as _cf:
                            _cf.write(json.dumps({"sku": sku, "marketplace": mp_key, "result": safe_result}) + "\n")
                            _cf.flush()
                    except Exception as _cache_err:
                        st.caption(f"Cache write warning: {_cache_err}")
                results[(sku, mp_key)] = chain_result

                with status_container:
                    title_preview = chain_result.get("title", "")[:60]
                    steps_done = len(chain_result.get("steps_completed", []))
                    st.caption(f"**{sku}** [{mp_key}]: {title_preview}... ({steps_done} steps)")

                if chain_result.get("errors"):
                    for err in chain_result["errors"]:
                        errors.append(f"{sku}/{mp_key}/{err['step']}: {err['error']}")

            except Exception as e:
                errors.append(f"{sku}/{mp_key}: {str(e)}")
                with status_container:
                    st.caption(f"**{sku}** [{mp_key}]: Error - {str(e)[:80]}")

    progress_bar.progress(1.0, text="Generation complete!")
    return results, errors, cost_tracker
