"""
Content generation orchestrator — wraps prompt_chain.py for multi-marketplace runs.
Maintains backward-compatible helpers for scraping/doc context.
"""

import json
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
    """Get relevant document context for a SKU."""
    if not ingested_docs:
        return None
    relevant_texts = []
    for doc in ingested_docs:
        applicable = doc.get("applicable_skus", [])
        if applicable == ["All"] or sku in applicable:
            relevant_texts.append(
                f"[{doc['type']} - {doc['filename']}]:\n{doc['text'][:3000]}"
            )
    return "\n\n".join(relevant_texts) if relevant_texts else None


def run_generation(enriched_df, settings, selected_skus=None, generate_options=None):
    """Run multi-marketplace content generation via the prompt chain.

    Returns (results_dict, errors_list, cost_tracker).
    results_dict is keyed by (sku, marketplace).
    """
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
        sku_predict = predict_keywords.get(sku, [])

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
                chain_result = run_chain(
                    client=client,
                    model=model_id,
                    product=product,
                    marketplace_key=mp_key,
                    settings=settings,
                    research_data=sku_research,
                    predict_keywords=sku_predict if isinstance(sku_predict, list) else [],
                    progress_callback=step_callback,
                )
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
