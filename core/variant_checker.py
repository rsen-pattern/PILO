"""Variant group detection and attribute consistency checks."""


def find_variant_groups(enriched_df) -> dict:
    """Group SKUs by parent ASIN.

    Checks for 'parent_asin' or 'parentage' columns first, then falls back
    to the first 9 characters of the ASIN column.
    Returns {parent_id: [sku1, sku2, ...]} — only groups with 2+ members.
    """
    if enriched_df is None or "sku" not in enriched_df.columns:
        return {}

    cols = {c.lower(): c for c in enriched_df.columns}
    groups = {}

    parent_col = cols.get("parent_asin") or cols.get("parentage")
    if parent_col:
        for _, row in enriched_df.iterrows():
            parent = str(row[parent_col]).strip()
            sku = str(row[cols["sku"]])
            if parent and parent.lower() not in ("nan", "none", ""):
                groups.setdefault(parent, []).append(sku)
    elif "asin" in cols:
        asin_col = cols["asin"]
        for _, row in enriched_df.iterrows():
            asin = str(row[asin_col]).strip()
            sku = str(row[cols["sku"]])
            if asin and asin.lower() not in ("nan", "none", "") and len(asin) >= 9:
                prefix = asin[:9]
                groups.setdefault(prefix, []).append(sku)

    return {k: v for k, v in groups.items() if len(v) >= 2}


def check_variant_consistency(
    variant_group: list,
    generated_results: dict,
    marketplace_key: str,
    check_fields: list = None,
) -> list:
    """Check that core attributes match across a variant group.

    Returns list of inconsistency dicts:
    {"field": str, "values": {sku: value}, "severity": "warning"}
    """
    if check_fields is None:
        check_fields = ["material", "brand", "item_type"]

    def _get_field(result, field):
        # item_type lives at top level; others may be in attributes
        if field in result:
            return str(result[field]).strip()
        attrs = result.get("attributes", {})
        if isinstance(attrs, dict) and field in attrs:
            return str(attrs[field]).strip()
        return ""

    inconsistencies = []
    for field in check_fields:
        values = {}
        for sku in variant_group:
            res = generated_results.get((sku, marketplace_key))
            if res:
                val = _get_field(res, field)
                if val and val.lower() not in ("nan", "none", ""):
                    values[sku] = val
        unique = set(values.values())
        if len(unique) > 1:
            inconsistencies.append({
                "field": field,
                "values": values,
                "severity": "warning",
            })

    return inconsistencies
