"""Feed upload, parsing, smart format detection, and column mapping utilities."""

import io
import pandas as pd
import streamlit as st

from config.file_format_handlers import detect_file_format, parse_file
from core.product_matcher import check_identifiers, find_identifier_columns

STANDARD_FIELDS = [
    "sku", "asin", "ean_gtin", "upc",
    "title", "brand",
    "bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5",
    "description", "product_type", "price", "image_url",
    "color", "material", "size", "weight",
    "gender", "age_group", "country_of_origin",
]


def load_feed(uploaded_file):
    """Load a CSV or Excel file with smart format detection.

    Returns (df, detected_format, format_metadata).
    """
    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    # Quick detection pass
    if name.endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(file_bytes), nrows=5, header=None)
    elif name.endswith((".xlsx", ".xls")):
        raw = pd.read_excel(io.BytesIO(file_bytes), nrows=5, header=None)
    else:
        raise ValueError(f"Unsupported file type: {name}")

    detected_format = detect_file_format(raw, name)

    # Parse with appropriate handler
    df = parse_file(file_bytes, name, detected_format)

    format_metadata = {
        "format": detected_format,
        "filename": uploaded_file.name,
        "original_bytes": file_bytes,
        "rows": len(df),
        "columns": len(df.columns),
    }

    return df, detected_format, format_metadata


def check_product_identifiers(df):
    """Check for product identifier columns and return status dict."""
    return check_identifiers(df)


def display_feed_preview(df, detected_format=None):
    """Display feed summary and preview."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        fmt_label = {
            "amazon_flat_file": "Amazon Flat File",
            "walmart_item_spec": "Walmart Item Spec",
            "gs1_npc": "GS1/NPC (Woolworths)",
            "ebay_file_exchange": "eBay File Exchange",
            "google_merchant_center": "Google Merchant",
            "standard": "Standard CSV/XLSX",
        }.get(detected_format, "Standard")
        st.metric("Format Detected", fmt_label)

    # Identifier check
    id_check = check_identifiers(df)
    if id_check["has_any"]:
        found_names = ", ".join(f"{k} ({v})" for k, v in id_check["found"].items())
        st.success(f"Product identifiers found: {found_names}")
    else:
        st.warning(id_check["warning"])

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)

    with st.expander("Column Details"):
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": [str(df[c].dtype) for c in df.columns],
            "Non-null": [df[c].notna().sum() for c in df.columns],
            "Fill %": [round(df[c].notna().sum() / len(df) * 100, 1) for c in df.columns],
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)


def build_column_mapping_ui(df):
    """Show selectboxes for mapping uploaded columns to standard fields.

    Returns a dict mapping standard field names to source column names.
    """
    st.subheader("Column Mapping")
    st.caption("Map your feed columns to PILO's standard fields.")

    source_cols = ["(not mapped)"] + list(df.columns)
    mapping = {}

    cols_per_row = 4
    for i in range(0, len(STANDARD_FIELDS), cols_per_row):
        row_fields = STANDARD_FIELDS[i : i + cols_per_row]
        cols = st.columns(len(row_fields))
        for col_ui, field in zip(cols, row_fields):
            with col_ui:
                default_idx = _auto_detect_column(field, source_cols)
                chosen = st.selectbox(
                    field, source_cols, index=default_idx, key=f"map_{field}",
                )
                if chosen != "(not mapped)":
                    mapping[field] = chosen

    return mapping


def _auto_detect_column(field, source_cols):
    """Try to auto-detect matching column for a standard field."""
    field_lower = field.lower()
    aliases = {
        "sku": ["sku", "item_sku", "seller_sku", "product_sku"],
        "asin": ["asin", "amazon_asin"],
        "ean_gtin": ["ean", "gtin", "barcode", "upc", "ean13", "gtin13"],
        "upc": ["upc", "upc_code"],
        "title": ["title", "item_name", "product_name", "product_title"],
        "brand": ["brand", "brand_name"],
        "description": ["description", "product_description", "long_description"],
        "product_type": ["product_type", "category", "item_type"],
        "price": ["price", "list_price", "standard_price"],
        "image_url": ["image_url", "main_image", "image", "main_image_url"],
        "color": ["color", "colour", "color_name"],
        "material": ["material", "material_type", "material_type1"],
        "size": ["size", "size_name"],
        "weight": ["weight", "item_weight"],
        "gender": ["gender", "target_audience_keywords"],
        "age_group": ["age_group", "age_range", "age_range_description"],
        "country_of_origin": ["country_of_origin"],
    }

    check_names = aliases.get(field_lower, [field_lower])
    for j, src in enumerate(source_cols):
        src_lower = src.lower().replace(" ", "_")
        if src_lower in check_names:
            return j
        for name in check_names:
            if name in src_lower:
                return j
    return 0


def apply_column_mapping(df, mapping):
    """Rename columns in the dataframe according to the mapping."""
    reverse_map = {v: k for k, v in mapping.items()}
    return df.rename(columns=reverse_map)
