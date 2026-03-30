"""Merge logic across the four data layers."""

import pandas as pd


def merge_layers(feed_df, scraped_df=None, crossretail_df=None, overwrite=False):
    """Merge primary feed with scraped and cross-retail data.

    Args:
        feed_df: Primary product feed DataFrame (must have 'sku' or 'asin' column).
        scraped_df: Optional DataFrame from web scraping.
        crossretail_df: Optional DataFrame from cross-retail sources.
        overwrite: If True, scraped/cross-retail data overwrites existing values.

    Returns:
        Tuple of (enriched_df, source_map) where source_map tracks data origins.
    """
    enriched = feed_df.copy()

    # Track which source each cell value came from
    # 'feed' = primary feed, 'scraped' = web scraping, 'crossretail' = cross-retail
    source_map = pd.DataFrame("feed", index=enriched.index, columns=enriched.columns)

    # Mark empty cells in original feed
    for col in enriched.columns:
        mask = enriched[col].astype(str).str.strip().isin(["", "nan", "None", "NaN"])
        source_map.loc[mask, col] = ""

    # Layer scraped data
    if scraped_df is not None and not scraped_df.empty:
        enriched, source_map = _merge_layer(
            enriched, scraped_df, source_map, "scraped", overwrite
        )

    # Layer cross-retail data
    if crossretail_df is not None and not crossretail_df.empty:
        enriched, source_map = _merge_layer(
            enriched, crossretail_df, source_map, "crossretail", overwrite
        )

    return enriched, source_map


def _merge_layer(enriched, layer_df, source_map, source_name, overwrite):
    """Merge a single data layer into the enriched dataframe."""
    # Determine join key
    join_key = "sku" if "sku" in enriched.columns and "sku" in layer_df.columns else None
    if join_key is None and "asin" in enriched.columns and "asin" in layer_df.columns:
        join_key = "asin"
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

            # Add column if it doesn't exist
            if col not in enriched.columns:
                enriched[col] = ""
                source_map[col] = ""

            existing_val = str(enriched.at[idx, col]).strip()
            is_empty = existing_val in ("", "nan", "None", "NaN")

            if is_empty or overwrite:
                enriched.at[idx, col] = layer_val
                source_map.at[idx, col] = source_name

    return enriched, source_map


def get_enrichment_stats(feed_df, enriched_df, source_map):
    """Calculate enrichment statistics."""
    from .utils import calculate_completeness

    before = calculate_completeness(feed_df)
    after = calculate_completeness(enriched_df)

    scraped_cells = (source_map == "scraped").sum().sum()
    crossretail_cells = (source_map == "crossretail").sum().sum()

    return {
        "completeness_before": before,
        "completeness_after": after,
        "improvement": round(after - before, 1),
        "scraped_cells_filled": int(scraped_cells),
        "crossretail_cells_filled": int(crossretail_cells),
    }
