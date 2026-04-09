"""Feed upload, parsing, smart format detection, and column mapping utilities."""

import io
import pandas as pd
import streamlit as st

from config.file_format_handlers import detect_file_format, parse_file
from core.product_matcher import check_identifiers, find_identifier_columns

STANDARD_FIELDS = [
    # Core identifiers
    "sku", "asin", "ean_gtin", "upc", "product_id", "product_id_type",
    # Core content
    "title", "brand", "manufacturer",
    "bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5",
    "description", "product_type", "item_type",
    # Search & discovery
    "search_terms", "recommended_browse_nodes",
    # Target audience
    "target_audience_1", "target_audience_2", "target_audience_3",
    "target_audience_4", "target_audience_5",
    # Pricing & images
    "price", "quantity", "image_url",
    # Physical attributes
    "color", "color_map", "material", "material_type", "size", "weight",
    "scent", "style_name", "pattern_name", "item_form",
    # Skin / hair (beauty & personal care)
    "skin_type", "hair_type",
    # Special features
    "special_feature_1", "special_feature_2", "special_feature_3",
    "special_feature_4", "special_feature_5",
    # Product details
    "ingredients", "directions", "product_benefits", "indications",
    "unit_count", "unit_count_type", "number_of_items",
    # Dimensions & weight
    "item_length", "item_width", "package_length", "volume",
    # Demographics
    "gender", "department", "age_group", "age_range",
    "country_of_origin", "parentage",
    # Compliance
    "is_expirable", "is_heat_sensitive", "specification_met",
    # Amazon-specific
    "update_delete", "flavor", "seasons", "sport_type",
]


def load_feed(uploaded_file, header_row=0, sheet_name=None):
    """Load a CSV or Excel file with smart format detection.

    Args:
        uploaded_file: Streamlit UploadedFile.
        header_row: Which row to use as the column header (0-indexed).
            Default 0 uses the first row. Set to e.g. 2 for Amazon flat files
            with 3-row headers.
        sheet_name: For xlsx files, which sheet to read. None = auto-detect.

    Returns (df, detected_format, format_metadata).
    """
    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    # Read raw for format detection — from specified sheet if given
    if name.endswith((".xlsx", ".xls")):
        try:
            xls = pd.ExcelFile(io.BytesIO(file_bytes))
            if sheet_name and sheet_name in xls.sheet_names:
                raw = pd.read_excel(xls, sheet_name=sheet_name, nrows=5, header=None)
            elif "Template" in xls.sheet_names:
                sheet_name = "Template"
                raw = pd.read_excel(xls, sheet_name="Template", nrows=5, header=None)
            else:
                raw = pd.read_excel(xls, nrows=5, header=None)
                if not sheet_name:
                    sheet_name = xls.sheet_names[0] if xls.sheet_names else None
        except Exception:
            raw = pd.read_excel(io.BytesIO(file_bytes), nrows=5, header=None)
    elif name.endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(file_bytes), nrows=5, header=None)
    else:
        raise ValueError(f"Unsupported file type: {name}")

    detected_format = detect_file_format(raw, name)

    # Parse with appropriate handler
    df = parse_file(file_bytes, name, detected_format,
                    header_row=header_row, sheet_name=sheet_name)

    format_metadata = {
        "format": detected_format,
        "filename": uploaded_file.name,
        "original_bytes": file_bytes,
        "rows": len(df),
        "columns": len(df.columns),
        "header_row": header_row,
        "sheet_name": sheet_name,
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
        # Core identifiers
        "sku": ["sku", "item_sku", "seller_sku", "product_sku", "seller sku"],
        "asin": ["asin", "amazon_asin", "product_id"],
        "ean_gtin": ["ean", "gtin", "barcode", "ean13", "gtin13"],
        "upc": ["upc", "upc_code"],
        "product_id": ["product_id", "product id"],
        "product_id_type": ["product_id_type", "product id type"],
        # Core content
        "title": ["title", "item_name", "product_name", "product_title", "product name"],
        "brand": ["brand", "brand_name", "brand name"],
        "manufacturer": ["manufacturer"],
        "bullet_1": ["bullet_1", "bullet_point_1", "key_product_features", "key product features"],
        "bullet_2": ["bullet_2", "bullet_point_2"],
        "bullet_3": ["bullet_3", "bullet_point_3"],
        "bullet_4": ["bullet_4", "bullet_point_4"],
        "bullet_5": ["bullet_5", "bullet_point_5"],
        "description": ["description", "product_description", "long_description", "product description"],
        "product_type": ["product_type", "category", "product type"],
        "item_type": ["item_type", "item_type_name", "item type name", "item_type_keyword"],
        # Search & discovery
        "search_terms": ["search_terms", "search terms", "generic_keywords", "generic keywords"],
        "recommended_browse_nodes": ["recommended_browse_nodes", "recommended browse nodes"],
        # Target audience
        "target_audience_1": ["target_audience", "target audience"],
        # Pricing & images
        "price": ["price", "list_price", "standard_price", "your_price", "your price"],
        "quantity": ["quantity", "qty"],
        "image_url": ["image_url", "main_image", "image", "main_image_url", "main image url"],
        # Physical attributes
        "color": ["color", "colour", "color_name"],
        "color_map": ["color_map", "colour_map", "colour map"],
        "material": ["material", "material_type"],
        "material_type": ["material_type_free", "material type free"],
        "size": ["size", "size_name"],
        "weight": ["weight", "item_weight", "item weight"],
        "scent": ["scent", "scent_name", "scent name"],
        "style_name": ["style_name", "style name"],
        "pattern_name": ["pattern_name", "pattern name"],
        "item_form": ["item_form", "item form"],
        # Skin / hair
        "skin_type": ["skin_type", "skin type"],
        "hair_type": ["hair_type", "hair type"],
        # Special features
        "special_feature_1": ["special_feature", "special_features", "special features"],
        # Product details
        "ingredients": ["ingredients"],
        "directions": ["directions"],
        "product_benefits": ["product_benefits", "product benefits"],
        "indications": ["indications"],
        "unit_count": ["unit_count", "unit count"],
        "unit_count_type": ["unit_count_type", "unit count type"],
        "number_of_items": ["number_of_items", "number of items"],
        "volume": ["volume"],
        "item_length": ["item_length", "item length longer edge", "item_length_longer_edge"],
        "item_width": ["item_width", "item width shorter edge", "item_width_shorter_edge"],
        "package_length": ["package_length", "package length"],
        # Demographics
        "gender": ["gender"],
        "department": ["department"],
        "age_group": ["age_group", "age_range", "age_range_description", "age range description"],
        "age_range": ["age_range", "age_range_description", "age range description"],
        "country_of_origin": ["country_of_origin"],
        "parentage": ["parentage", "parent_child"],
        # Compliance
        "is_expirable": ["is_product_expirable", "is product expirable"],
        "is_heat_sensitive": ["is_the_item_heat_sensitive", "is the item heat sensitive"],
        "specification_met": ["specification_met", "specification met"],
        # Amazon-specific
        "update_delete": ["update_delete", "update delete"],
        "flavor": ["flavor", "flavour"],
        "seasons": ["seasons"],
        "sport_type": ["sport_type", "sport type"],
    }

    check_names = aliases.get(field_lower, [field_lower])
    for j, src in enumerate(source_cols):
        src_lower = src.lower().replace(" ", "_")
        if src_lower in check_names:
            return j
        # Also check without underscores (raw "Seller SKU" → "seller_sku")
        src_clean = src.lower().strip()
        if src_clean in check_names:
            return j
        for name in check_names:
            if name in src_lower:
                return j
    return 0


def apply_column_mapping(df, mapping):
    """Rename columns in the dataframe according to the mapping."""
    reverse_map = {v: k for k, v in mapping.items()}
    return df.rename(columns=reverse_map)
