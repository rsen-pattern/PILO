"""Marketplace-specific file formatting and export."""

import io
import zipfile

import pandas as pd

from config.marketplace_schemas import (
    map_to_amazon,
    map_to_google_shopping,
    map_to_walmart,
    map_to_woolworths,
)
from .utils import row_to_dict


def build_export_df(enriched_df, generated_results, qa_decisions, mapper_fn):
    """Build an export DataFrame using a marketplace mapper function.

    Only includes SKUs that were approved in QA.
    """
    rows = []
    for _, row in enriched_df.iterrows():
        sku = row.get("sku", "")
        decision = qa_decisions.get(sku, {})
        status = decision.get("status", "pending")

        if status not in ("approved", "approved_with_edits"):
            continue

        generated = generated_results.get(sku, {})

        # If approved with edits, use edited content
        if status == "approved_with_edits" and "edited" in decision:
            generated = decision["edited"]

        mapped = mapper_fn(row_to_dict(row), generated)
        rows.append(mapped)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def export_amazon(enriched_df, generated_results, qa_decisions):
    """Export Amazon flat file format."""
    return build_export_df(enriched_df, generated_results, qa_decisions, map_to_amazon)


def export_walmart(enriched_df, generated_results, qa_decisions):
    """Export Walmart format."""
    return build_export_df(enriched_df, generated_results, qa_decisions, map_to_walmart)


def export_woolworths(enriched_df, generated_results, qa_decisions):
    """Export Woolworths AU format."""
    return build_export_df(enriched_df, generated_results, qa_decisions, map_to_woolworths)


def export_google_shopping(enriched_df, generated_results, qa_decisions):
    """Export Google Shopping format."""
    return build_export_df(enriched_df, generated_results, qa_decisions, map_to_google_shopping)


def export_universal(enriched_df, generated_results, qa_decisions):
    """Export universal format with all data and QA status."""
    rows = []
    for _, row in enriched_df.iterrows():
        sku = row.get("sku", "")
        generated = generated_results.get(sku, {})
        decision = qa_decisions.get(sku, {})
        status = decision.get("status", "pending")

        if status == "approved_with_edits" and "edited" in decision:
            generated = decision["edited"]

        out = row_to_dict(row)
        out["generated_title"] = generated.get("title", "")
        bullets = generated.get("bullets", [])
        for i in range(5):
            out[f"generated_bullet_{i+1}"] = bullets[i] if i < len(bullets) else ""
        out["generated_description"] = generated.get("description", "")
        out["qa_status"] = status

        for attr_name, attr_val in generated.get("attributes", {}).items():
            out[f"generated_{attr_name}"] = attr_val

        rows.append(out)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def df_to_excel_bytes(df):
    """Convert a DataFrame to Excel bytes for download."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buf.getvalue()


def build_universal_excel(enriched_df, generated_results, qa_decisions):
    """Build a multi-tab universal Excel export."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        # Summary tab
        summary_data = {
            "Metric": [
                "Total SKUs",
                "Approved SKUs",
                "Rejected SKUs",
                "Pending SKUs",
                "Titles Generated",
                "Attributes Filled",
            ],
            "Value": [
                len(enriched_df),
                sum(1 for d in qa_decisions.values() if d.get("status") in ("approved", "approved_with_edits")),
                sum(1 for d in qa_decisions.values() if d.get("status") == "rejected"),
                sum(1 for d in qa_decisions.values() if d.get("status") == "pending"),
                sum(1 for r in generated_results.values() if r.get("title")),
                sum(len(r.get("attributes", {})) for r in generated_results.values()),
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, index=False, sheet_name="Summary")

        # Generated content tab
        universal_df = export_universal(enriched_df, generated_results, qa_decisions)
        if not universal_df.empty:
            universal_df.to_excel(writer, index=False, sheet_name="Generated Content")

        # QA log tab
        qa_rows = []
        for sku, decision in qa_decisions.items():
            qa_rows.append({
                "sku": sku,
                "status": decision.get("status", "pending"),
                "notes": decision.get("notes", ""),
            })
        if qa_rows:
            pd.DataFrame(qa_rows).to_excel(writer, index=False, sheet_name="QA Log")

    return buf.getvalue()


def build_zip_export(exports_dict):
    """Build a ZIP file containing multiple export files.

    Args:
        exports_dict: Dict of {filename: excel_bytes}

    Returns:
        ZIP file bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, data in exports_dict.items():
            zf.writestr(filename, data)
    return buf.getvalue()
