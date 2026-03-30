"""Column mappings and schemas for each target marketplace export."""

MARKETPLACE_OPTIONS = [
    "Amazon AU",
    "Amazon US",
    "Amazon UK",
    "Walmart US",
    "Woolworths AU",
    "Google Shopping",
]

AMAZON_FLAT_FILE_COLUMNS = [
    "sku",
    "asin",
    "product_type",
    "brand",
    "item_name",  # title
    "bullet_point_1",
    "bullet_point_2",
    "bullet_point_3",
    "bullet_point_4",
    "bullet_point_5",
    "product_description",
    "material",
    "colour",
    "size",
    "weight",
    "breed_size",
    "age_range",
    "is_dishwasher_safe",
    "chew_strength",
    "item_shape",
    "special_feature",
    "included_components",
    "sport",
    "target_species",
    "care_instructions",
    "country_of_origin",
    "price",
]

WALMART_COLUMNS = [
    "sku",
    "product_id_type",
    "product_id",
    "product_name",  # title
    "brand",
    "short_description",  # bullets combined
    "long_description",  # description
    "shelf_description",
    "main_image_url",
    "price",
    "category",
    "subcategory",
    "material",
    "colour",
    "size",
    "weight",
    "country_of_origin",
]

WOOLWORTHS_COLUMNS = [
    "gtin",
    "sku",
    "brand",
    "product_name",
    "product_description",
    "category",
    "subcategory",
    "size",
    "weight",
    "material",
    "colour",
    "country_of_origin",
    "price",
]

GOOGLE_SHOPPING_COLUMNS = [
    "id",  # sku
    "title",
    "description",
    "link",
    "image_link",
    "price",
    "brand",
    "gtin",
    "product_type",
    "google_product_category",
    "condition",
    "availability",
    "material",
    "color",
    "size",
]


def map_to_amazon(row, generated):
    """Map enriched row + generated content to Amazon flat file format."""
    out = {}
    out["sku"] = row.get("sku", "")
    out["asin"] = row.get("asin", "")
    out["product_type"] = row.get("product_type", "")
    out["brand"] = row.get("brand", "")
    out["item_name"] = generated.get("title", row.get("title", ""))
    bullets = generated.get("bullets", [])
    for i in range(5):
        out[f"bullet_point_{i+1}"] = bullets[i] if i < len(bullets) else row.get(f"bullet_{i+1}", "")
    out["product_description"] = generated.get("description", row.get("description", ""))

    attrs = generated.get("attributes", {})
    for col in AMAZON_FLAT_FILE_COLUMNS:
        if col not in out:
            out[col] = attrs.get(col, row.get(col, ""))
    return out


def map_to_walmart(row, generated):
    """Map enriched row + generated content to Walmart format."""
    bullets = generated.get("bullets", [])
    short_desc = " | ".join(b for b in bullets if b)
    return {
        "sku": row.get("sku", ""),
        "product_id_type": "ASIN",
        "product_id": row.get("asin", ""),
        "product_name": generated.get("title", row.get("title", "")),
        "brand": row.get("brand", ""),
        "short_description": short_desc,
        "long_description": generated.get("description", row.get("description", "")),
        "shelf_description": generated.get("title", row.get("title", "")),
        "main_image_url": row.get("image_url", ""),
        "price": row.get("price", ""),
        "category": row.get("product_type", ""),
        "subcategory": "",
        "material": row.get("material", ""),
        "colour": row.get("colour", ""),
        "size": row.get("size", ""),
        "weight": row.get("weight", ""),
        "country_of_origin": row.get("country_of_origin", ""),
    }


def map_to_woolworths(row, generated):
    """Map enriched row + generated content to Woolworths AU format."""
    return {
        "gtin": "",
        "sku": row.get("sku", ""),
        "brand": row.get("brand", ""),
        "product_name": generated.get("title", row.get("title", "")),
        "product_description": generated.get("description", row.get("description", "")),
        "category": row.get("product_type", ""),
        "subcategory": "",
        "size": row.get("size", ""),
        "weight": row.get("weight", ""),
        "material": row.get("material", ""),
        "colour": row.get("colour", ""),
        "country_of_origin": row.get("country_of_origin", ""),
        "price": row.get("price", ""),
    }


def map_to_google_shopping(row, generated):
    """Map enriched row + generated content to Google Shopping format."""
    return {
        "id": row.get("sku", ""),
        "title": generated.get("title", row.get("title", "")),
        "description": generated.get("description", row.get("description", "")),
        "link": "",
        "image_link": row.get("image_url", ""),
        "price": row.get("price", ""),
        "brand": row.get("brand", ""),
        "gtin": "",
        "product_type": row.get("product_type", ""),
        "google_product_category": row.get("product_type", ""),
        "condition": "new",
        "availability": "in stock",
        "material": row.get("material", ""),
        "color": row.get("colour", ""),
        "size": row.get("size", ""),
    }
