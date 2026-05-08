"""
Content generation orchestrator — wraps prompt_chain.py for multi-marketplace runs.
Maintains backward-compatible helpers for scraping/doc context.
"""

import json
import time
import logging

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


def run_generation(enriched_df, settings, selected_skus=None, generate_options=None,
                   research_results=None, predict_keywords=None, ingested_docs=None,
                   scraped_df=None, crossretail_df=None, deep_enrichment_results=None,
                   progress_callback=None, status_callback=None):
    """Run multi-marketplace content generation via the prompt chain.

    Returns (results_dict, errors_list, cost_tracker).
    results_dict is keyed by (sku, marketplace).
    """
    try:
        client, model_id = _create_client(settings)
    except ValueError as e:
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

    research_data = research_results or {}
    predict_keywords_data = predict_keywords or {}
    ingested_docs = ingested_docs or []
    cost_tracker = CostTracker()

    if selected_skus is None:
        selected_skus = enriched_df["sku"].tolist() if "sku" in enriched_df.columns else []

    results = {}
    errors = []
    total = len(selected_skus) * len(marketplace_keys)
    current = 0

    if progress_callback:
        progress_callback(0, f"Starting generation via Bifrost ({model_id})...")

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
        sku_predict = predict_keywords_data.get(sku, [])

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
            if progress_callback:
                progress_callback(
                    min(current / total, 0.99),
                    f"Generating {sku} for {mp_key} ({current}/{total})",
                )

            def step_callback(step_name, step_num, total_steps):
                if progress_callback:
                    progress_callback(
                        min(current / total, 0.99),
                        f"{sku} / {mp_key}: Step {step_num}/{total_steps} — {step_name}",
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
                    scraped_data=sku_scraped,
                    document_context=sku_doc_context,
                    crossretail_data=sku_crossretail,
                    deep_enrichment_results=deep_enrichment_results,
                    progress_callback=step_callback,
                )
                results[(sku, mp_key)] = chain_result

                if status_callback:
                    title_preview = chain_result.get("title", "")[:60]
                    steps_done = len(chain_result.get("steps_completed", []))
                    status_callback(f"**{sku}** [{mp_key}]: {title_preview}... ({steps_done} steps)")

                if chain_result.get("errors"):
                    for err in chain_result["errors"]:
                        errors.append(f"{sku}/{mp_key}/{err['step']}: {err['error']}")

            except Exception as e:
                errors.append(f"{sku}/{mp_key}: {str(e)}")
                if status_callback:
                    status_callback(f"**{sku}** [{mp_key}]: Error - {str(e)[:80]}")

    if progress_callback:
        progress_callback(1.0, "Generation complete!")
    return results, errors, cost_tracker
