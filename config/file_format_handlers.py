"""
Parsers and exporters for each marketplace file format.
Handles Amazon 3-row headers, Walmart Item Spec, GS1/NPC, eBay CSV, Google Merchant.
"""

import pandas as pd
import io


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_file_format(df_raw: pd.DataFrame, filename: str = "") -> str:
    """Detect the marketplace file format from raw DataFrame contents.

    Returns one of:
        'amazon_flat_file', 'walmart_item_spec', 'gs1_npc',
        'ebay_file_exchange', 'google_merchant_center', 'standard'
    """
    if df_raw.shape[0] < 1:
        return "standard"

    first_row = df_raw.iloc[0].astype(str).str.lower().tolist()
    cols_lower = [str(c).lower() for c in df_raw.columns]
    all_text = " ".join(first_row + cols_lower)

    # Amazon flat file: Row 1 often contains 'TemplateType=' or 'template_type'
    if any("templatetype" in v.replace(" ", "").replace("=", "") for v in first_row):
        return "amazon_flat_file"
    if any("item_sku" in c for c in cols_lower) and any("item_name" in c for c in cols_lower):
        return "amazon_flat_file"

    # Walmart Item Spec
    if any("product name" in c for c in cols_lower) and any("shelf description" in c for c in cols_lower):
        return "walmart_item_spec"
    if any("walmart" in v for v in first_row):
        return "walmart_item_spec"

    # GS1 / Woolworths NPC
    if any("gtin" in c for c in cols_lower) and any("npc" in all_text or "gs1" in all_text for _ in [1]):
        return "gs1_npc"

    # eBay File Exchange
    if any("*action" in c for c in cols_lower) or any("paypal" in all_text for _ in [1]):
        return "ebay_file_exchange"
    if filename.lower().endswith(".csv") and any("ebay" in all_text for _ in [1]):
        return "ebay_file_exchange"

    # Google Merchant Center
    if any("google_product_category" in c for c in cols_lower):
        return "google_merchant_center"
    if any("g:id" in c or "g:title" in c for c in cols_lower):
        return "google_merchant_center"

    return "standard"


# ---------------------------------------------------------------------------
# Amazon flat file (3-row header)
# ---------------------------------------------------------------------------

def parse_amazon_flat_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse Amazon flat file with 3-row header. Row 3 = actual field names."""
    if filename.endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(file_bytes), header=None)
    else:
        raw = pd.read_excel(io.BytesIO(file_bytes), header=None)

    if raw.shape[0] < 4:
        # Fewer than 4 rows — treat as standard
        raw.columns = raw.iloc[0]
        return raw.iloc[1:].reset_index(drop=True)

    # Row 3 (index 2) = field names
    field_names = raw.iloc[2].astype(str).tolist()
    data = raw.iloc[3:].reset_index(drop=True)
    data.columns = field_names
    return data


def export_amazon_flat_file(df: pd.DataFrame, metadata_row: list = None,
                            display_row: list = None) -> bytes:
    """Export DataFrame in Amazon flat file format with 3-row header."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Build 3-row header + data
        cols = list(df.columns)
        if metadata_row is None:
            metadata_row = [""] * len(cols)
        if display_row is None:
            display_row = cols  # Use field names as display names

        header_df = pd.DataFrame([metadata_row, display_row, cols])
        header_df.to_excel(writer, sheet_name="Template", index=False, header=False, startrow=0)
        df.to_excel(writer, sheet_name="Template", index=False, header=False, startrow=3)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Walmart Item Spec
# ---------------------------------------------------------------------------

def parse_walmart_spec(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def export_walmart_spec(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Item Spec", index=False)
    return output.getvalue()


# ---------------------------------------------------------------------------
# GS1 / Woolworths NPC
# ---------------------------------------------------------------------------

def parse_gs1_npc(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def export_gs1_npc(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="NPC", index=False)
    return output.getvalue()


# ---------------------------------------------------------------------------
# eBay File Exchange
# ---------------------------------------------------------------------------

def parse_ebay_file_exchange(file_bytes: bytes, filename: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))


def export_ebay_csv(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Google Merchant Center
# ---------------------------------------------------------------------------

def parse_google_merchant(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def export_google_merchant(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()


# ---------------------------------------------------------------------------
# Unified parser dispatcher
# ---------------------------------------------------------------------------

PARSER_MAP = {
    "amazon_flat_file": parse_amazon_flat_file,
    "walmart_item_spec": parse_walmart_spec,
    "gs1_npc": parse_gs1_npc,
    "ebay_file_exchange": parse_ebay_file_exchange,
    "google_merchant_center": parse_google_merchant,
}

EXPORTER_MAP = {
    "amazon_flat_file": export_amazon_flat_file,
    "walmart_item_spec": export_walmart_spec,
    "gs1_npc": export_gs1_npc,
    "ebay_file_exchange": export_ebay_csv,
    "google_merchant_center": export_google_merchant,
}


def parse_file(file_bytes: bytes, filename: str, detected_format: str = None) -> pd.DataFrame:
    """Parse a file using the appropriate handler. Auto-detects if format not specified."""
    if detected_format is None:
        # Quick detection from raw load
        if filename.endswith(".csv"):
            raw = pd.read_csv(io.BytesIO(file_bytes), nrows=5, header=None)
        else:
            raw = pd.read_excel(io.BytesIO(file_bytes), nrows=5, header=None)
        detected_format = detect_file_format(raw, filename)

    parser = PARSER_MAP.get(detected_format)
    if parser:
        return parser(file_bytes, filename)

    # Standard format
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def export_file(df: pd.DataFrame, format_type: str, **kwargs) -> bytes:
    """Export DataFrame using the appropriate handler."""
    exporter = EXPORTER_MAP.get(format_type)
    if exporter:
        return exporter(df, **kwargs)
    # Fallback: standard XLSX
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()
