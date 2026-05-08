"""
Amazon Composite Data Quality (CDQ) Validator.
Checks generated content against category-specific requirements.
"""

import json
import os

def load_category_config():
    config_path = os.path.join("config", "category_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

_CONTENT_FIELDS = ["title", "brand", "description",
                   "bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5",
                   "material", "colour", "size"]
_IDENTIFIER_FIELDS = ["asin", "ean_gtin", "sku"]


def validate_feed_preflight(df, marketplace_keys: list) -> dict:
    """Validate the enriched feed before generation runs.

    Returns {"passed": bool, "errors": [...], "warnings": [...]}
    """
    errors = []
    warnings = []
    cols = [c.lower() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}

    # 1. SKU column
    if "sku" not in cols:
        errors.append("Feed is missing a 'sku' column.")
    else:
        sku_col = col_map["sku"]
        dupes = df[sku_col][df[sku_col].duplicated()].tolist()
        if dupes:
            errors.append(f"Duplicate SKUs found: {', '.join(str(s) for s in dupes[:10])}"
                          + (" (and more)" if len(dupes) > 10 else ""))

    # 2. Title / product name column
    if not any(f in cols for f in ("title", "product_name")):
        errors.append("Feed is missing a 'title' or 'product_name' column.")

    # 3. Rows where ALL content fields are empty
    present_content = [col_map[f] for f in _CONTENT_FIELDS if f in cols]
    if present_content:
        def _all_empty(row):
            return all(str(row[c]).strip().lower() in ("", "nan", "none", "null")
                       for c in present_content)
        empty_mask = df.apply(_all_empty, axis=1)
        if empty_mask.any():
            sku_col = col_map.get("sku")
            bad = df[empty_mask][sku_col].tolist() if sku_col else list(df[empty_mask].index)
            warnings.append(f"{len(bad)} row(s) have all content fields empty: "
                            + ", ".join(str(s) for s in bad[:10])
                            + (" (and more)" if len(bad) > 10 else ""))

    # 4. At least one identifier per row
    present_ids = [col_map[f] for f in _IDENTIFIER_FIELDS if f in cols]
    if present_ids:
        def _no_id(row):
            return all(str(row[c]).strip().lower() in ("", "nan", "none", "null")
                       for c in present_ids)
        no_id_mask = df.apply(_no_id, axis=1)
        if no_id_mask.any():
            sku_col = col_map.get("sku")
            bad = df[no_id_mask][sku_col].tolist() if sku_col else list(df[no_id_mask].index)
            warnings.append(f"{len(bad)} row(s) have no identifier (asin/ean_gtin/sku): "
                            + ", ".join(str(s) for s in bad[:10])
                            + (" (and more)" if len(bad) > 10 else ""))

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


def validate_sku_content(sku_result, category, settings):
    """Validate generated content for a SKU.

    Returns a list of flags/errors.
    """
    flags = []
    cat_config = load_category_config().get(category, {})

    # 1. Title Validation
    title = sku_result.get("title", "")
    if title:
        # Length check
        if len(title) > 200:
            flags.append({"level": "error", "field": "title", "message": "Title exceeds 200 character limit."})
        elif len(title) < 80:
            flags.append({"level": "warning", "field": "title", "message": "Title is under 80 characters (wasted space)."})

        # Special character check
        banned_chars = ["!", "$", "?", "_", "{", "}", "^", "¬", "¦"]
        for char in banned_chars:
            if char in title:
                flags.append({"level": "error", "field": "title", "message": f"Banned character '{char}' found in title."})
                break

        # Repetition check (simple)
        words = title.lower().split()
        for word in set(words):
            if words.count(word) > 2:
                flags.append({"level": "error", "field": "title", "message": f"Word '{word}' repeated more than twice."})
                break

    # 2. Attribute Validation (Discovery-Critical)
    discovery_critical = cat_config.get("discovery_critical", [])
    generated_attrs = sku_result.get("attributes", {})

    for attr in discovery_critical:
        val = generated_attrs.get(attr)
        if not val or str(val).lower() in ("nan", "none", "null", ""):
            flags.append({
                "level": "error" if attr in ("material_type", "ingredients") else "warning",
                "field": f"attr_{attr}",
                "message": f"Discovery-Critical attribute '{attr}' is missing."
            })

    # 3. Bullets Validation
    bullets = sku_result.get("bullets", [])
    if bullets:
        if len(bullets) != 5:
            flags.append({"level": "warning", "field": "bullets", "message": f"Generated {len(bullets)} bullets instead of 5."})

        for i, b in enumerate(bullets):
            if len(b) < 100 or len(b) > 250:
                flags.append({"level": "warning", "field": f"bullet_{i+1}", "message": f"Bullet {i+1} length ({len(b)}) outside 100-250 char range."})
            if " – " not in b and " - " not in b:
                flags.append({"level": "warning", "field": f"bullet_{i+1}", "message": f"Bullet {i+1} missing Feature-Benefit Bridge separator."})

    return flags

def calculate_cdq_score(flags):
    """Calculate a simple CDQ score (0-100) based on flags."""
    if not flags:
        return 100

    deductions = 0
    for f in flags:
        if f["level"] == "error":
            deductions += 20
        else:
            deductions += 5

    return max(0, 100 - deductions)
