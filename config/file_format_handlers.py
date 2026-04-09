"""
Parsers and exporters for each marketplace file format.
Handles Amazon 3-row headers, Walmart Item Spec, GS1/NPC, eBay CSV, Google Merchant.
"""

import pandas as pd
import io
import re
from urllib.parse import parse_qs


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

def _parse_amazon_settings_row(raw: pd.DataFrame) -> dict:
    """Extract attributeRow, dataRow, labelRow from the Amazon metadata/settings row.

    The first row often contains a cell like:
        settings=attributeRow=3&dataRow=4&labelRow=2&...
    These values are 1-indexed.  Returns 0-indexed equivalents.
    """
    defaults = {"attribute_row": 2, "data_row": 3, "label_row": 1}
    if raw.shape[0] < 1:
        return defaults

    for cell in raw.iloc[0]:
        cell_str = str(cell)
        if "attributeRow" not in cell_str:
            continue
        # The settings value may be inside a larger "settings=..." string
        m = re.search(r"(?:^|settings=)(.*)", cell_str)
        if not m:
            continue
        qs = m.group(1)
        try:
            params = parse_qs(qs)
            attr_row = int(params.get("attributeRow", [3])[0])
            data_row = int(params.get("dataRow", [4])[0])
            label_row = int(params.get("labelRow", [2])[0])
            return {
                "attribute_row": attr_row - 1,   # convert to 0-indexed
                "data_row": data_row - 1,
                "label_row": label_row - 1,
            }
        except (ValueError, IndexError):
            pass
    return defaults


def _read_xlsx_template_sheet(file_bytes: bytes) -> pd.DataFrame:
    """Try reading the 'Template' sheet from an xlsx file. Falls back to first sheet."""
    try:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        if "Template" in xls.sheet_names:
            return pd.read_excel(xls, sheet_name="Template", header=None)
        # Fall back to first sheet
        return pd.read_excel(xls, header=None)
    except Exception:
        return pd.read_excel(io.BytesIO(file_bytes), header=None)


def parse_amazon_flat_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse Amazon flat file with multi-row header.

    For xlsx files, reads from the 'Template' tab first.
    Auto-detects attributeRow and dataRow from the metadata/settings row,
    falling back to row 3 (0-indexed 2) for attributes and row 4 (0-indexed 3) for data.
    """
    if filename.endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(file_bytes), header=None)
    else:
        raw = _read_xlsx_template_sheet(file_bytes)

    if raw.shape[0] < 2:
        raw.columns = raw.iloc[0]
        return raw.iloc[1:].reset_index(drop=True)

    # Parse settings from metadata row to find attribute and data rows
    settings = _parse_amazon_settings_row(raw)
    attr_idx = settings["attribute_row"]
    data_idx = settings["data_row"]

    if attr_idx >= raw.shape[0]:
        attr_idx = min(2, raw.shape[0] - 1)
    if data_idx >= raw.shape[0]:
        data_idx = attr_idx + 1

    field_names = raw.iloc[attr_idx].astype(str).tolist()
    data = raw.iloc[data_idx:].reset_index(drop=True)
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


def parse_file(file_bytes: bytes, filename: str, detected_format: str = None,
               header_row: int = 0) -> pd.DataFrame:
    """Parse a file using the appropriate handler. Auto-detects if format not specified.

    Args:
        file_bytes: Raw file content.
        filename: Original filename (used for format hints).
        detected_format: Pre-detected format string (auto-detects if None).
        header_row: Which row to use as column header (0-indexed).
            When header_row > 0 and format is 'standard', the specified row
            is used as headers and earlier rows are skipped. For marketplace-
            specific formats (Amazon flat file etc.), their native parsers
            are used by default — set header_row > 0 to override.
    """
    if detected_format is None:
        if filename.endswith(".csv"):
            raw = pd.read_csv(io.BytesIO(file_bytes), nrows=5, header=None)
        else:
            raw = pd.read_excel(io.BytesIO(file_bytes), nrows=5, header=None)
        detected_format = detect_file_format(raw, filename)

    # If user explicitly set a custom header row, use generic parsing with that row
    if header_row > 0:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), header=None)
        else:
            # For xlsx, try "Template" sheet first (Amazon flat files)
            df = _read_xlsx_template_sheet(file_bytes)
        if header_row < len(df):
            df.columns = df.iloc[header_row].astype(str).tolist()
            df = df.iloc[header_row + 1:].reset_index(drop=True)
        return df

    parser = PARSER_MAP.get(detected_format)
    if parser:
        return parser(file_bytes, filename)

    # Standard format (header_row == 0)
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
