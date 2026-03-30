"""
Pattern internal tool field mappings — PXM, Predict, Shelf.
For MVP, these are import/export schemas only (no live API calls).
"""

# ---------------------------------------------------------------------------
# PXM (Product Experience Management) — JSON export schema
# ---------------------------------------------------------------------------

PXM_FIELD_MAP = {
    # PILO field → PXM API field
    "sku": "product_sku",
    "asin": "marketplace_id",
    "title": "product_title",
    "description": "product_description",
    "bullet_1": "feature_bullet_1",
    "bullet_2": "feature_bullet_2",
    "bullet_3": "feature_bullet_3",
    "bullet_4": "feature_bullet_4",
    "bullet_5": "feature_bullet_5",
    "brand": "brand_name",
    "color": "attribute_color",
    "material": "attribute_material",
    "size": "attribute_size",
    "weight": "attribute_weight",
    "product_type": "category_name",
    "image_url": "primary_image_url",
    "price": "list_price",
}


def to_pxm_product(row: dict, marketplace: str, generated: dict) -> dict:
    """Convert a PILO row + generated content into PXM-compatible JSON."""
    product = {}
    for pilo_field, pxm_field in PXM_FIELD_MAP.items():
        val = generated.get(pilo_field) or row.get(pilo_field, "")
        if val:
            product[pxm_field] = val

    # Add marketplace-specific content
    product["marketplace"] = marketplace
    if "title" in generated:
        product["product_title"] = generated["title"]
    if "description" in generated:
        product["product_description"] = generated["description"]
    bullets = []
    for i in range(1, 11):
        b = generated.get(f"bullet_{i}") or generated.get("bullets", [None] * i)
        if isinstance(b, list) and len(b) >= i:
            bullets.append(b[i - 1])
        elif isinstance(b, str):
            bullets.append(b)
    for idx, bullet in enumerate(bullets[:5], 1):
        if bullet:
            product[f"feature_bullet_{idx}"] = bullet

    if "attributes" in generated:
        for k, v in generated["attributes"].items():
            product[f"attribute_{k}"] = v

    return product


def build_pxm_export(products: list) -> dict:
    """Build full PXM export JSON structure."""
    return {
        "version": "1.0",
        "source": "PILO",
        "products": products,
    }


# ---------------------------------------------------------------------------
# Predict — keyword data import schema
# ---------------------------------------------------------------------------

PREDICT_IMPORT_FIELDS = {
    "keyword": "search_term",
    "search_volume": "monthly_volume",
    "relevance_score": "relevance",
    "competition": "competition_level",
    "trend": "trend_direction",
    "category": "product_category",
    "asin": "asin",
    "sku": "sku",
}


def parse_predict_export(df) -> list:
    """Parse a Predict keyword export into a list of keyword dicts."""
    keywords = []
    for _, row in df.iterrows():
        kw = {}
        for predict_col, internal_key in PREDICT_IMPORT_FIELDS.items():
            for col in df.columns:
                if predict_col.lower() in col.lower():
                    kw[internal_key] = row[col]
                    break
        if kw.get("search_term"):
            keywords.append(kw)
    return keywords


# ---------------------------------------------------------------------------
# Shelf — compliance score import schema
# ---------------------------------------------------------------------------

SHELF_IMPORT_FIELDS = {
    "asin": "asin",
    "sku": "sku",
    "title_score": "title_compliance",
    "bullet_score": "bullet_compliance",
    "image_score": "image_compliance",
    "content_score": "overall_content_score",
    "search_rank": "organic_rank",
    "category_rank": "category_rank",
}


def parse_shelf_export(df) -> dict:
    """Parse a Shelf compliance export into {sku: scores} dict."""
    scores = {}
    for _, row in df.iterrows():
        sku = None
        score_data = {}
        for shelf_col, internal_key in SHELF_IMPORT_FIELDS.items():
            for col in df.columns:
                if shelf_col.lower() in col.lower():
                    val = row[col]
                    if internal_key in ("asin", "sku"):
                        sku = sku or str(val)
                    else:
                        score_data[internal_key] = val
                    break
        if sku:
            scores[sku] = score_data
    return scores
