"""
6-source enrichment merge with provenance tracking.

Sources (by trust level):
  1. feed       (green)  — Primary product feed
  2. document   (blue)   — Client documents
  3. crossretail (orange) — Cross-retail / Pattern tools
  4. scraped    (purple) — Web scraping (client sites)
  5. ai_research (yellow) — AI model research (confidence-rated)
  6. external   (red)    — External website scraping (non-client)
"""

import pandas as pd


SOURCE_COLOURS = {
    "feed":        {"bg": "#14532d", "fg": "#bbf7d0", "label": "Primary Feed",   "trust": "highest"},
    "document":    {"bg": "#1e3a5f", "fg": "#93c5fd", "label": "Client Docs",    "trust": "high"},
    "crossretail": {"bg": "#78350f", "fg": "#fde68a", "label": "Cross-Retail",   "trust": "medium"},
    "scraped":     {"bg": "#4c1d95", "fg": "#c4b5fd", "label": "Web Scraped",    "trust": "medium"},
    "ai_research": {"bg": "#713f12", "fg": "#fef08a", "label": "AI Research",    "trust": "variable"},
    "external":    {"bg": "#3f1219", "fg": "#fca5a5", "label": "External Scrape", "trust": "lowest"},
}


def merge_layers(feed_df, scraped_df=None, crossretail_df=None,
                 document_data=None, ai_research_data=None,
                 external_df=None, overwrite=False):
    """Merge primary feed with all enrichment layers.

    Args:
        feed_df: Primary product feed DataFrame.
        scraped_df: Optional DataFrame from client-site web scraping.
        crossretail_df: Optional DataFrame from cross-retail / Pattern tools.
        document_data: Optional dict {sku: {field: value}} from document extraction.
        ai_research_data: Optional dict {sku: {field: value}} from AI research.
        external_df: Optional DataFrame from external (non-client) scraping.
        overwrite: If True, later sources overwrite earlier non-empty values.

    Returns:
        (enriched_df, source_map) where source_map tracks data origins per cell.
    """
    enriched = feed_df.copy()

    # Initialize source map
    source_map = pd.DataFrame("feed", index=enriched.index, columns=enriched.columns)
    for col in enriched.columns:
        mask = enriched[col].astype(str).str.strip().isin(["", "nan", "None", "NaN"])
        source_map.loc[mask, col] = ""

    # Merge each layer in trust-priority order
    if scraped_df is not None and not scraped_df.empty:
        enriched, source_map = _merge_df_layer(
            enriched, scraped_df, source_map, "scraped", overwrite
        )

    if crossretail_df is not None and not crossretail_df.empty:
        enriched, source_map = _merge_df_layer(
            enriched, crossretail_df, source_map, "crossretail", overwrite
        )

    if document_data:
        enriched, source_map = _merge_dict_layer(
            enriched, document_data, source_map, "document", overwrite
        )

    if ai_research_data:
        enriched, source_map = _merge_dict_layer(
            enriched, ai_research_data, source_map, "ai_research", overwrite
        )

    if external_df is not None and not external_df.empty:
        enriched, source_map = _merge_df_layer(
            enriched, external_df, source_map, "external", overwrite
        )

    return enriched, source_map


def _merge_df_layer(enriched, layer_df, source_map, source_name, overwrite):
    """Merge a DataFrame layer into enriched data."""
    join_key = _find_join_key(enriched, layer_df)
    if join_key is None:
        return enriched, source_map

    for _, layer_row in layer_df.iterrows():
        key_val = layer_row.get(join_key)
        if pd.isna(key_val):
            continue

        match_mask = enriched[join_key] == key_val
        if not match_mask.any():
            continue

        idx = enriched.index[match_mask][0]

        for col in layer_df.columns:
            if col == join_key:
                continue

            layer_val = layer_row[col]
            if pd.isna(layer_val) or str(layer_val).strip() == "":
                continue

            if col not in enriched.columns:
                enriched[col] = ""
                source_map[col] = ""

            existing_val = str(enriched.at[idx, col]).strip()
            is_empty = existing_val in ("", "nan", "None", "NaN")

            if is_empty or overwrite:
                enriched.at[idx, col] = layer_val
                source_map.at[idx, col] = source_name

    return enriched, source_map


def _merge_dict_layer(enriched, data_dict, source_map, source_name, overwrite):
    """Merge a dict layer {sku: {field: value}} into enriched data."""
    sku_col = "sku" if "sku" in enriched.columns else None
    if sku_col is None:
        return enriched, source_map

    for sku, fields in data_dict.items():
        if not isinstance(fields, dict):
            continue
        match_mask = enriched[sku_col] == sku
        if not match_mask.any():
            continue
        idx = enriched.index[match_mask][0]

        for col, val in fields.items():
            if not val or str(val).strip() == "":
                continue

            if col not in enriched.columns:
                enriched[col] = ""
                source_map[col] = ""

            existing_val = str(enriched.at[idx, col]).strip()
            is_empty = existing_val in ("", "nan", "None", "NaN")

            if is_empty or overwrite:
                enriched.at[idx, col] = val
                source_map.at[idx, col] = source_name

    return enriched, source_map


def _find_join_key(enriched, layer_df):
    """Find the best join key between two DataFrames."""
    for key in ["sku", "asin", "ean_gtin", "upc"]:
        if key in enriched.columns and key in layer_df.columns:
            return key
    return None


def get_enrichment_stats(feed_df, enriched_df, source_map):
    """Calculate enrichment statistics across all sources."""
    from .utils import calculate_completeness

    before = calculate_completeness(feed_df)
    after = calculate_completeness(enriched_df)

    stats = {
        "completeness_before": before,
        "completeness_after": after,
        "improvement": round(after - before, 1),
    }

    for source in SOURCE_COLOURS:
        count = int((source_map == source).sum().sum())
        stats[f"{source}_cells"] = count

    empty_cells = int((source_map == "").sum().sum())
    stats["empty_cells"] = empty_cells

    return stats


def style_source_cell(source_val):
    """Return CSS style string for a source value (dark-theme optimised)."""
    info = SOURCE_COLOURS.get(source_val)
    if info:
        return f"background-color: {info['bg']}; color: {info['fg']}"
    return "background-color: #1a1a2e; color: #6b7280"
