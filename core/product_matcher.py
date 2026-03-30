"""
Product matching across data sources.
Matches products via ASIN (exact) → EAN/GTIN (exact) → SKU (fuzzy).
"""

import pandas as pd
from difflib import SequenceMatcher


def find_identifier_columns(df: pd.DataFrame) -> dict:
    """Detect identifier columns in a DataFrame.

    Returns dict of {identifier_type: column_name} for found identifiers.
    """
    cols_lower = {c.lower().strip(): c for c in df.columns}
    found = {}

    # ASIN patterns
    for pattern in ["asin", "amazon_id", "amazon_asin"]:
        if pattern in cols_lower:
            found["asin"] = cols_lower[pattern]
            break

    # EAN/GTIN/UPC patterns
    for pattern in ["ean_gtin", "ean", "gtin", "barcode", "upc", "ean13", "gtin13", "gtin14"]:
        if pattern in cols_lower:
            found["ean_gtin"] = cols_lower[pattern]
            break

    # SKU patterns
    for pattern in ["sku", "item_sku", "seller_sku", "product_sku", "internal_sku"]:
        if pattern in cols_lower:
            found["sku"] = cols_lower[pattern]
            break

    return found


def check_identifiers(df: pd.DataFrame) -> dict:
    """Check what product identifiers are available in the data.

    Returns:
        {
            "found": {"asin": "ASIN", "sku": "item_sku", ...},
            "missing": ["ean_gtin"],
            "has_any": True/False,
            "warning": str or None
        }
    """
    found = find_identifier_columns(df)
    all_types = {"asin", "ean_gtin", "sku"}
    missing = list(all_types - set(found.keys()))

    warning = None
    if not found:
        warning = (
            "No product identifier detected. PILO requires at least one of: "
            "Barcode (EAN/GTIN/UPC), ASIN, or SKU for accurate product matching "
            "across data sources."
        )

    return {
        "found": found,
        "missing": missing,
        "has_any": bool(found),
        "warning": warning,
    }


def match_products(primary_df: pd.DataFrame, secondary_df: pd.DataFrame,
                   primary_ids: dict = None, secondary_ids: dict = None,
                   fuzzy_threshold: float = 0.85) -> pd.DataFrame:
    """Match products between two DataFrames using available identifiers.

    Strategy: ASIN (exact) → EAN/GTIN (exact) → SKU (fuzzy with threshold).

    Returns the secondary_df with an added '_matched_to' column containing
    the primary DataFrame's index for matched rows. Unmatched rows get NaN.
    """
    if primary_ids is None:
        primary_ids = find_identifier_columns(primary_df)
    if secondary_ids is None:
        secondary_ids = find_identifier_columns(secondary_df)

    matched = pd.Series([None] * len(secondary_df), index=secondary_df.index, name="_matched_to")

    # Phase 1: ASIN exact match
    if "asin" in primary_ids and "asin" in secondary_ids:
        p_col, s_col = primary_ids["asin"], secondary_ids["asin"]
        p_asins = primary_df[p_col].astype(str).str.strip().str.upper()
        for idx, row in secondary_df.iterrows():
            if matched[idx] is not None:
                continue
            val = str(row[s_col]).strip().upper()
            if val and val != "NAN":
                hits = p_asins[p_asins == val]
                if len(hits) > 0:
                    matched[idx] = hits.index[0]

    # Phase 2: EAN/GTIN exact match
    if "ean_gtin" in primary_ids and "ean_gtin" in secondary_ids:
        p_col, s_col = primary_ids["ean_gtin"], secondary_ids["ean_gtin"]
        p_gtins = primary_df[p_col].astype(str).str.strip()
        for idx, row in secondary_df.iterrows():
            if matched[idx] is not None:
                continue
            val = str(row[s_col]).strip()
            if val and val != "nan":
                hits = p_gtins[p_gtins == val]
                if len(hits) > 0:
                    matched[idx] = hits.index[0]

    # Phase 3: SKU fuzzy match
    if "sku" in primary_ids and "sku" in secondary_ids:
        p_col, s_col = primary_ids["sku"], secondary_ids["sku"]
        p_skus = primary_df[p_col].astype(str).str.strip()
        for idx, row in secondary_df.iterrows():
            if matched[idx] is not None:
                continue
            val = str(row[s_col]).strip()
            if val and val != "nan":
                best_score, best_idx = 0, None
                for p_idx, p_sku in p_skus.items():
                    score = SequenceMatcher(None, val.lower(), p_sku.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_idx = p_idx
                if best_score >= fuzzy_threshold:
                    matched[idx] = best_idx

    secondary_df = secondary_df.copy()
    secondary_df["_matched_to"] = matched
    return secondary_df


def merge_matched_data(primary_df: pd.DataFrame, matched_secondary: pd.DataFrame,
                       source_label: str = "secondary") -> tuple:
    """Merge matched secondary data into primary DataFrame.

    Returns (merged_df, source_tracking_dict).
    source_tracking_dict maps (row_idx, col_name) → source_label for cells filled from secondary.
    """
    merged = primary_df.copy()
    source_tracking = {}

    for sec_idx, row in matched_secondary.iterrows():
        primary_idx = row.get("_matched_to")
        if primary_idx is None or pd.isna(primary_idx):
            continue
        primary_idx = int(primary_idx)

        for col in matched_secondary.columns:
            if col == "_matched_to":
                continue
            if col not in merged.columns:
                continue
            sec_val = row[col]
            if pd.isna(sec_val) or str(sec_val).strip() == "":
                continue
            current_val = merged.at[primary_idx, col]
            if pd.isna(current_val) or str(current_val).strip() == "":
                merged.at[primary_idx, col] = sec_val
                source_tracking[(primary_idx, col)] = source_label

    return merged, source_tracking
