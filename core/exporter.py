"""
Multi-format export engine.
Supports: match-input-format, marketplace templates, PXM JSON, comparison output.
"""

import io
import json
import zipfile

import pandas as pd

from config.marketplace_configs import get_config, MARKETPLACE_CONFIGS
from config.file_format_handlers import export_file
from core.pxm_connector import generate_pxm_export, export_pxm_json
from .utils import row_to_dict


# ---------------------------------------------------------------------------
# Marketplace-specific column mappers
# ---------------------------------------------------------------------------

def _map_to_amazon(row: dict, generated: dict, marketplace_key: str = "amazon_au") -> dict:
    bullets = generated.get("bullets", [])
    attrs = generated.get("attributes", {})
    return {
        "item_sku": row.get("sku", ""),
        "external_product_id": row.get("asin", ""),
        "item_name": generated.get("title", row.get("title", "")),
        "brand_name": row.get("brand", ""),
        "bullet_point1": bullets[0] if len(bullets) > 0 else "",
        "bullet_point2": bullets[1] if len(bullets) > 1 else "",
        "bullet_point3": bullets[2] if len(bullets) > 2 else "",
        "bullet_point4": bullets[3] if len(bullets) > 3 else "",
        "bullet_point5": bullets[4] if len(bullets) > 4 else "",
        "product_description": generated.get("description", ""),
        "generic_keywords": generated.get("search_terms", ""),
        "item_type_keyword": generated.get("item_type", ""),
        "color_name": attrs.get("color_name", row.get("color", "")),
        "material_type1": attrs.get("material_type1", row.get("material", "")),
        "size_name": attrs.get("size_name", row.get("size", "")),
        "target_audience_keywords": attrs.get("target_audience_keywords", ""),
        "age_range_description": attrs.get("age_range_description", ""),
        **{f"special_feature{i+1}": (generated.get("special_features", []) + [""] * 5)[i]
           for i in range(5)},
    }


def _map_to_walmart(row: dict, generated: dict) -> dict:
    bullets = generated.get("bullets", [])
    attrs = generated.get("attributes", {})
    return {
        "sku": row.get("sku", ""),
        "productName": generated.get("title", row.get("title", "")),
        "brand": row.get("brand", ""),
        "keyFeature1": bullets[0] if len(bullets) > 0 else "",
        "keyFeature2": bullets[1] if len(bullets) > 1 else "",
        "keyFeature3": bullets[2] if len(bullets) > 2 else "",
        "keyFeature4": bullets[3] if len(bullets) > 3 else "",
        "keyFeature5": bullets[4] if len(bullets) > 4 else "",
        "longDescription": generated.get("description", ""),
        "shortDescription": attrs.get("shortDescription", ""),
        "shelfDescription": attrs.get("shelfDescription", ""),
        "color": attrs.get("color", row.get("color", "")),
        "material": attrs.get("material", row.get("material", "")),
        "size": attrs.get("size", row.get("size", "")),
        "gender": attrs.get("gender", ""),
        "ageGroup": attrs.get("ageGroup", ""),
    }


def _map_to_woolworths(row: dict, generated: dict) -> dict:
    bullets = generated.get("bullets", [])
    attrs = generated.get("attributes", {})
    return {
        "gtin": row.get("ean_gtin", ""),
        "brand": row.get("brand", ""),
        "productName": generated.get("title", row.get("title", "")),
        "description": generated.get("description", ""),
        "feature1": bullets[0] if len(bullets) > 0 else "",
        "feature2": bullets[1] if len(bullets) > 1 else "",
        "feature3": bullets[2] if len(bullets) > 2 else "",
        "npc_category": attrs.get("npc_category", ""),
        "country_of_origin": attrs.get("country_of_origin", row.get("country_of_origin", "")),
        "weight_net": attrs.get("weight_net", row.get("weight", "")),
    }


def _map_to_ebay(row: dict, generated: dict) -> dict:
    attrs = generated.get("attributes", {})
    return {
        "*Action": "Revise",
        "CustomLabel": row.get("sku", ""),
        "*Title": generated.get("title", row.get("title", "")),
        "*Description": generated.get("description", ""),
        "Brand": attrs.get("Brand", row.get("brand", "")),
        "MPN": attrs.get("MPN", ""),
        "Type": attrs.get("Type", ""),
        "Material": attrs.get("Material", row.get("material", "")),
        "Colour": attrs.get("Colour", row.get("color", "")),
        "Size": attrs.get("Size", row.get("size", "")),
    }


def _map_to_google(row: dict, generated: dict) -> dict:
    attrs = generated.get("attributes", {})
    return {
        "id": row.get("sku", ""),
        "title": generated.get("title", row.get("title", "")),
        "description": generated.get("description", ""),
        "brand": row.get("brand", ""),
        "gtin": row.get("ean_gtin", ""),
        "condition": attrs.get("condition", "new"),
        "google_product_category": attrs.get("google_product_category", ""),
        "product_type": attrs.get("product_type", row.get("product_type", "")),
        "color": attrs.get("color", row.get("color", "")),
        "material": attrs.get("material", row.get("material", "")),
        "size": attrs.get("size", row.get("size", "")),
        "age_group": attrs.get("age_group", ""),
        "gender": attrs.get("gender", ""),
        "image_link": row.get("image_url", ""),
        "link": "",
        "price": row.get("price", ""),
    }


MARKETPLACE_MAPPERS = {
    "amazon_au": _map_to_amazon,
    "amazon_us": _map_to_amazon,
    "amazon_uk": _map_to_amazon,
    "walmart_us": _map_to_walmart,
    "woolworths_au": _map_to_woolworths,
    "ebay_au": _map_to_ebay,
    "google_shopping": _map_to_google,
}


# ---------------------------------------------------------------------------
# Export builders
# ---------------------------------------------------------------------------

def build_marketplace_export(enriched_df, generated_results, qa_decisions,
                             marketplace_key):
    """Build export DataFrame for a specific marketplace.

    generated_results is keyed by (sku, marketplace_key).
    """
    mapper = MARKETPLACE_MAPPERS.get(marketplace_key, _map_to_amazon)
    rows = []

    for _, row in enriched_df.iterrows():
        sku = row.get("sku", "")
        decision = qa_decisions.get(sku, {}).get(marketplace_key, qa_decisions.get(sku, {}))
        status = decision.get("status", "pending")

        if status not in ("approved", "approved_with_edits"):
            continue

        key = (sku, marketplace_key)
        generated = generated_results.get(key, {})

        if status == "approved_with_edits" and "edited" in decision:
            generated = {**generated, **decision["edited"]}

        mapped = mapper(row_to_dict(row), generated)
        rows.append(mapped)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def build_match_input_export(original_df, enriched_df, generated_results,
                             qa_decisions, marketplace_key, format_metadata=None):
    """Export preserving the original file structure — only overwrite generated columns."""
    output = original_df.copy() if original_df is not None else enriched_df.copy()

    for idx, row in output.iterrows():
        sku = row.get("sku", row.get("item_sku", ""))
        if not sku:
            continue

        decision = qa_decisions.get(sku, {}).get(marketplace_key, qa_decisions.get(sku, {}))
        status = decision.get("status", "pending")
        if status not in ("approved", "approved_with_edits"):
            continue

        key = (sku, marketplace_key)
        generated = generated_results.get(key, {})
        if status == "approved_with_edits" and "edited" in decision:
            generated = {**generated, **decision["edited"]}

        # Map generated fields back to original column names
        if generated.get("title"):
            for col in ["title", "item_name", "product_name", "productName", "*Title"]:
                if col in output.columns:
                    output.at[idx, col] = generated["title"]
                    break

        if generated.get("description"):
            for col in ["description", "product_description", "longDescription", "*Description"]:
                if col in output.columns:
                    output.at[idx, col] = generated["description"]
                    break

        bullets = generated.get("bullets", [])
        for i, bullet in enumerate(bullets):
            for col in [f"bullet_{i+1}", f"bullet_point{i+1}", f"keyFeature{i+1}", f"feature{i+1}"]:
                if col in output.columns:
                    output.at[idx, col] = bullet
                    break

    return output


def build_universal_export(enriched_df, generated_results, qa_decisions, marketplace_keys):
    """Build universal export with all data, generated content, and QA status."""
    rows = []
    for _, row in enriched_df.iterrows():
        sku = row.get("sku", "")
        out = row_to_dict(row)

        for mp_key in marketplace_keys:
            key = (sku, mp_key)
            generated = generated_results.get(key, {})
            decision = qa_decisions.get(sku, {}).get(mp_key, qa_decisions.get(sku, {}))
            status = decision.get("status", "pending")

            if status == "approved_with_edits" and "edited" in decision:
                generated = {**generated, **decision["edited"]}

            prefix = f"{mp_key}_"
            out[f"{prefix}title"] = generated.get("title", "")
            bullets = generated.get("bullets", [])
            for i in range(5):
                out[f"{prefix}bullet_{i+1}"] = bullets[i] if i < len(bullets) else ""
            out[f"{prefix}description"] = generated.get("description", "")
            out[f"{prefix}qa_status"] = status

            for attr_name, attr_val in generated.get("attributes", {}).items():
                out[f"{prefix}{attr_name}"] = attr_val

        rows.append(out)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def build_comparison_output(enriched_df, generated_results, qa_decisions, marketplace_keys):
    """Build comparison table: SKU | Field | Original | Generated | Marketplace | Source | QA Status."""
    rows = []
    for _, row in enriched_df.iterrows():
        sku = row.get("sku", "")

        for mp_key in marketplace_keys:
            key = (sku, mp_key)
            generated = generated_results.get(key, {})
            decision = qa_decisions.get(sku, {}).get(mp_key, qa_decisions.get(sku, {}))
            status = decision.get("status", "pending")

            # Title
            if generated.get("title"):
                rows.append({
                    "SKU": sku, "Field": "Title",
                    "Original": row.get("title", ""),
                    "Generated": generated["title"],
                    "Marketplace": mp_key, "QA Status": status,
                })

            # Bullets
            for i, bullet in enumerate(generated.get("bullets", [])):
                rows.append({
                    "SKU": sku, "Field": f"Bullet {i+1}",
                    "Original": row.get(f"bullet_{i+1}", ""),
                    "Generated": bullet,
                    "Marketplace": mp_key, "QA Status": status,
                })

            # Description
            if generated.get("description"):
                rows.append({
                    "SKU": sku, "Field": "Description",
                    "Original": row.get("description", ""),
                    "Generated": generated["description"],
                    "Marketplace": mp_key, "QA Status": status,
                })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# File generation helpers
# ---------------------------------------------------------------------------

def df_to_excel_bytes(df):
    """Convert a DataFrame to Excel bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buf.getvalue()


def build_multi_tab_excel(enriched_df, generated_results, qa_decisions, marketplace_keys):
    """Build multi-tab Excel with Summary, per-marketplace, comparison, and QA log tabs."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        # Summary tab
        approved = sum(
            1 for d in qa_decisions.values()
            for v in (d.values() if isinstance(d, dict) and any(isinstance(x, dict) for x in d.values()) else [d])
            if isinstance(v, dict) and v.get("status") in ("approved", "approved_with_edits")
        )
        summary = pd.DataFrame({
            "Metric": [
                "Total SKUs", "Marketplaces", "Approved SKUs",
                "Total Titles Generated", "Total API Calls",
            ],
            "Value": [
                len(enriched_df), len(marketplace_keys), approved,
                sum(1 for r in generated_results.values() if r.get("title")),
                len(generated_results),
            ],
        })
        summary.to_excel(writer, index=False, sheet_name="Summary")

        # Per-marketplace tabs
        for mp_key in marketplace_keys:
            mp_df = build_marketplace_export(enriched_df, generated_results, qa_decisions, mp_key)
            if not mp_df.empty:
                sheet_name = mp_key[:31]  # Excel 31-char limit
                mp_df.to_excel(writer, index=False, sheet_name=sheet_name)

        # Comparison tab
        comp_df = build_comparison_output(enriched_df, generated_results, qa_decisions, marketplace_keys)
        if not comp_df.empty:
            comp_df.to_excel(writer, index=False, sheet_name="Comparison")

        # QA Log tab
        qa_rows = []
        for sku, decisions in qa_decisions.items():
            if isinstance(decisions, dict) and all(isinstance(v, dict) for v in decisions.values()):
                for mp, dec in decisions.items():
                    qa_rows.append({"sku": sku, "marketplace": mp,
                                    "status": dec.get("status", ""), "notes": dec.get("notes", "")})
            elif isinstance(decisions, dict):
                qa_rows.append({"sku": sku, "marketplace": "all",
                                "status": decisions.get("status", ""), "notes": decisions.get("notes", "")})
        if qa_rows:
            pd.DataFrame(qa_rows).to_excel(writer, index=False, sheet_name="QA Log")

    return buf.getvalue()


def build_pxm_export_json(generated_results, product_data, marketplace_keys):
    """Build PXM JSON export."""
    return export_pxm_json(
        generate_pxm_export(generated_results, product_data, marketplace_keys)
    )


def build_zip_export(exports_dict):
    """Build ZIP file from {filename: bytes} dict."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, data in exports_dict.items():
            if isinstance(data, str):
                data = data.encode("utf-8")
            zf.writestr(filename, data)
    return buf.getvalue()
