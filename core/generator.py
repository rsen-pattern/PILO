"""Claude API prompt construction and content generation."""

import json
import time

import anthropic
import streamlit as st

from .utils import get_missing_attributes, parse_json_response, row_to_dict


def build_system_prompt(settings):
    """Build the system prompt from settings."""
    marketplaces = ", ".join(settings.get("target_marketplace", ["Amazon AU"]))

    return f"""You are PILO, Pattern Intelligence Listing Optimisation — an AI content engine \
that generates optimised product listings for {marketplaces} marketplace.

BRAND CONTEXT:
Brand: {settings.get('brand_name', '')}
Tone of voice: {settings.get('brand_tone', '')}
Brand rules: {settings.get('brand_rules', '')}

CATEGORY CONTEXT:
Category: {settings.get('category', '')}
Category guidelines: {settings.get('category_guidelines', '')}

MARKETPLACE RULES:
Target: {marketplaces}
Language: {settings.get('language_variant', 'Australian English')}
Title character limit: {settings.get('title_char_limit', 200)}
Bullet point count: {settings.get('bullet_count', 5)}
Bullet point character limit: {settings.get('bullet_char_limit', 500)} per bullet
Description character limit: {settings.get('description_char_limit', 2000)}

INSTRUCTIONS:
You will receive product data from multiple verified sources. Generate optimised content \
based ONLY on the data provided. Never invent features, specifications, or claims.

For each output field:
- TITLE: Include brand, key product descriptor, main benefit, key differentiator, and \
relevant attributes (size, colour, variant). Front-load the most important search terms. \
Respect the character limit.
- BULLET POINTS: Each bullet should lead with a BENEFIT then support with a feature. \
Order thematically: primary use → key features → materials/quality → compatibility/sizing → care/safety. \
Respect the character limit per bullet.
- DESCRIPTION: Compelling paragraph(s) that tell the product story. Include use cases, \
key differentiators, and trust signals. Not a repeat of bullets.
- SUPPLEMENTARY ATTRIBUTES: For each missing attribute field provided, return an accurate \
value based on the source data. If you cannot determine a value with confidence, return "NEEDS_REVIEW" \
rather than guessing.

Respond in JSON format exactly matching this structure:
{{
  "title": "...",
  "bullets": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "description": "...",
  "attributes": {{
    "attribute_name_1": "value or NEEDS_REVIEW",
    "attribute_name_2": "value or NEEDS_REVIEW"
  }}
}}"""


def build_user_prompt(sku_data, missing_attrs, scraped_data=None, crossretail_data=None, doc_context=None):
    """Build the user prompt for a single SKU."""
    parts = [
        "Generate optimised content for this product.",
        "",
        "PRODUCT DATA (from verified feed):",
        json.dumps(sku_data, indent=2, default=str),
        "",
        "MISSING ATTRIBUTES TO FILL:",
        json.dumps(missing_attrs),
    ]

    if scraped_data:
        parts.append("")
        parts.append("SUPPLEMENTARY DATA (from cross-region scraping):")
        parts.append(json.dumps(scraped_data, indent=2, default=str))

    if crossretail_data:
        parts.append("")
        parts.append("SUPPLEMENTARY DATA (from cross-retail sources):")
        parts.append(json.dumps(crossretail_data, indent=2, default=str))

    if doc_context:
        parts.append("")
        parts.append("BRAND DOCUMENTATION CONTEXT:")
        parts.append(doc_context)

    return "\n".join(parts)


def generate_content_for_sku(client, model, temperature, system_prompt, user_prompt):
    """Call the Claude API for a single SKU and return parsed result."""
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text
    return parse_json_response(raw_text)


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


def get_scraped_data_for_sku(sku, asin, scraped_df):
    """Get scraped data for a specific SKU/ASIN."""
    if scraped_df is None or scraped_df.empty:
        return None

    if "asin" in scraped_df.columns:
        matches = scraped_df[scraped_df["asin"] == asin]
        if not matches.empty:
            return matches.iloc[0].to_dict()
    return None


def get_crossretail_data_for_sku(sku, crossretail_df):
    """Get cross-retail data for a specific SKU."""
    if crossretail_df is None or crossretail_df.empty:
        return None

    if "sku" in crossretail_df.columns:
        matches = crossretail_df[crossretail_df["sku"] == sku]
        if not matches.empty:
            return matches.iloc[0].to_dict()
    return None


def run_generation(enriched_df, settings, selected_skus=None, generate_options=None):
    """Run content generation for all selected SKUs.

    Args:
        enriched_df: The enriched product dataframe.
        settings: Dict of all settings from session state.
        selected_skus: List of SKUs to process, or None for all.
        generate_options: Dict of what to generate (title, bullets, description, attributes).

    Returns:
        Dict of results keyed by SKU, and a list of errors.
    """
    api_key = settings.get("anthropic_api_key", "")
    if not api_key:
        st.error("Anthropic API key is not configured. Please set it in Settings.")
        return {}, ["No API key"]

    client = anthropic.Anthropic(api_key=api_key)
    model = settings.get("model", "claude-sonnet-4-20250514")
    temperature = settings.get("temperature", 0.1)
    delay = settings.get("api_delay", 0.5)

    system_prompt = build_system_prompt(settings)

    scraped_df = st.session_state.get("scraped_df")
    crossretail_df = st.session_state.get("crossretail_df")
    ingested_docs = st.session_state.get("ingested_docs", [])

    if selected_skus is None:
        selected_skus = enriched_df["sku"].tolist() if "sku" in enriched_df.columns else []

    results = {}
    errors = []
    total = len(selected_skus)

    progress_bar = st.progress(0, text="Starting generation...")
    status_container = st.container()

    for i, sku in enumerate(selected_skus):
        progress_bar.progress((i) / total, text=f"Generating content for SKU {i+1} of {total}: {sku}")

        # Get row data
        if "sku" in enriched_df.columns:
            row_mask = enriched_df["sku"] == sku
        else:
            continue

        if not row_mask.any():
            errors.append(f"SKU {sku} not found in enriched data")
            continue

        row = enriched_df[row_mask].iloc[0]
        sku_data = row_to_dict(row)
        missing_attrs = get_missing_attributes(row)
        asin = sku_data.get("asin", "")

        scraped_data = get_scraped_data_for_sku(sku, asin, scraped_df)
        crossretail_data = get_crossretail_data_for_sku(sku, crossretail_df)
        doc_context = get_doc_context_for_sku(sku, ingested_docs)

        user_prompt = build_user_prompt(
            sku_data, missing_attrs, scraped_data, crossretail_data, doc_context
        )

        try:
            result = generate_content_for_sku(client, model, temperature, system_prompt, user_prompt)
            results[sku] = result

            with status_container:
                title_preview = result.get("title", "")[:80]
                attr_count = len([v for v in result.get("attributes", {}).values() if v != "NEEDS_REVIEW"])
                st.caption(f"**{sku}**: {title_preview}... | {attr_count} attributes filled")

        except Exception as e:
            errors.append(f"SKU {sku}: {str(e)}")
            with status_container:
                st.caption(f"**{sku}**: Error - {str(e)[:100]}")

        if i < total - 1:
            time.sleep(delay)

    progress_bar.progress(1.0, text="Generation complete!")
    return results, errors
