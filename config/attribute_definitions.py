"""
Per-marketplace attribute schemas — defines required/optional attributes,
their types, accepted values, and display labels for each marketplace.
"""

# Standard PILO internal attribute fields used across the app
STANDARD_FIELDS = [
    "sku", "asin", "ean_gtin", "upc", "brand", "product_type",
    "title", "bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5",
    "description", "price", "image_url",
    "color", "material", "size", "weight", "gender", "age_group",
    "country_of_origin", "model_number",
]

# Attribute definitions keyed by marketplace → field name
ATTRIBUTE_SCHEMAS = {
    "amazon_au": {
        "item_type": {"label": "Item Type Keyword", "required": True, "type": "text"},
        "color_name": {"label": "Colour Name", "required": False, "type": "text"},
        "material_type1": {"label": "Material", "required": False, "type": "text"},
        "size_name": {"label": "Size", "required": False, "type": "text"},
        "target_audience_keywords": {
            "label": "Target Gender",
            "required": False,
            "type": "enum",
            "accepted": ["Male", "Female", "Unisex"],
        },
        "age_range_description": {
            "label": "Age Range",
            "required": False,
            "type": "enum",
            "accepted": ["newborn", "infant", "toddler", "kids", "adult"],
        },
        "special_feature1": {"label": "Special Feature 1", "required": False, "type": "text"},
        "special_feature2": {"label": "Special Feature 2", "required": False, "type": "text"},
        "special_feature3": {"label": "Special Feature 3", "required": False, "type": "text"},
        "special_feature4": {"label": "Special Feature 4", "required": False, "type": "text"},
        "special_feature5": {"label": "Special Feature 5", "required": False, "type": "text"},
        "generic_keywords": {"label": "Search Terms", "required": False, "type": "text", "max_bytes": 250},
    },
    "amazon_us": {
        "item_type": {"label": "Item Type Keyword", "required": True, "type": "text"},
        "color_name": {"label": "Color Name", "required": False, "type": "text"},
        "material_type1": {"label": "Material", "required": False, "type": "text"},
        "size_name": {"label": "Size", "required": False, "type": "text"},
        "target_audience_keywords": {
            "label": "Target Gender",
            "required": False,
            "type": "enum",
            "accepted": ["Male", "Female", "Unisex"],
        },
        "age_range_description": {
            "label": "Age Range",
            "required": False,
            "type": "enum",
            "accepted": ["newborn", "infant", "toddler", "kids", "adult"],
        },
        "special_feature1": {"label": "Special Feature 1", "required": False, "type": "text"},
        "special_feature2": {"label": "Special Feature 2", "required": False, "type": "text"},
        "special_feature3": {"label": "Special Feature 3", "required": False, "type": "text"},
        "special_feature4": {"label": "Special Feature 4", "required": False, "type": "text"},
        "special_feature5": {"label": "Special Feature 5", "required": False, "type": "text"},
        "generic_keywords": {"label": "Search Terms", "required": False, "type": "text", "max_bytes": 250},
    },
    "amazon_uk": {
        "item_type": {"label": "Item Type Keyword", "required": True, "type": "text"},
        "color_name": {"label": "Colour Name", "required": False, "type": "text"},
        "material_type1": {"label": "Material", "required": False, "type": "text"},
        "size_name": {"label": "Size", "required": False, "type": "text"},
        "target_audience_keywords": {
            "label": "Target Gender",
            "required": False,
            "type": "enum",
            "accepted": ["Male", "Female", "Unisex"],
        },
        "age_range_description": {
            "label": "Age Range",
            "required": False,
            "type": "enum",
            "accepted": ["newborn", "infant", "toddler", "kids", "adult"],
        },
        "special_feature1": {"label": "Special Feature 1", "required": False, "type": "text"},
        "special_feature2": {"label": "Special Feature 2", "required": False, "type": "text"},
        "special_feature3": {"label": "Special Feature 3", "required": False, "type": "text"},
        "special_feature4": {"label": "Special Feature 4", "required": False, "type": "text"},
        "special_feature5": {"label": "Special Feature 5", "required": False, "type": "text"},
        "generic_keywords": {"label": "Search Terms", "required": False, "type": "text", "max_bytes": 250},
    },
    "walmart_us": {
        "color": {"label": "Color", "required": False, "type": "text"},
        "material": {"label": "Material", "required": False, "type": "text"},
        "size": {"label": "Size", "required": False, "type": "text"},
        "gender": {
            "label": "Gender",
            "required": False,
            "type": "enum",
            "accepted": ["Male", "Female", "Gender Neutral"],
        },
        "ageGroup": {
            "label": "Age Group",
            "required": False,
            "type": "enum",
            "accepted": ["Newborn", "Infant", "Toddler", "Child", "Teen", "Adult"],
        },
        "brand": {"label": "Brand", "required": True, "type": "text"},
        "shortDescription": {"label": "Short Description", "required": False, "type": "text"},
        "shelfDescription": {"label": "Shelf Description", "required": False, "type": "text"},
    },
    "woolworths_au": {
        "gtin": {"label": "GTIN/Barcode", "required": True, "type": "text"},
        "brand": {"label": "Brand", "required": True, "type": "text"},
        "npc_category": {"label": "NPC Category", "required": False, "type": "text"},
        "country_of_origin": {"label": "Country of Origin", "required": False, "type": "text"},
        "weight_net": {"label": "Net Weight", "required": False, "type": "text"},
    },
    "ebay_au": {
        "Brand": {"label": "Brand", "required": True, "type": "text"},
        "MPN": {"label": "MPN", "required": False, "type": "text"},
        "Type": {"label": "Type", "required": False, "type": "text"},
        "Material": {"label": "Material", "required": False, "type": "text"},
        "Colour": {"label": "Colour", "required": False, "type": "text"},
        "Size": {"label": "Size", "required": False, "type": "text"},
        "Condition": {
            "label": "Condition",
            "required": True,
            "type": "enum",
            "accepted": ["New", "New with tags", "New without tags", "Refurbished", "Used"],
        },
    },
    "google_shopping": {
        "google_product_category": {"label": "Google Product Category", "required": True, "type": "taxonomy"},
        "product_type": {"label": "Product Type", "required": False, "type": "text"},
        "brand": {"label": "Brand", "required": True, "type": "text"},
        "condition": {
            "label": "Condition",
            "required": True,
            "type": "enum",
            "accepted": ["new", "refurbished", "used"],
        },
        "material": {"label": "Material", "required": False, "type": "text"},
        "color": {"label": "Color", "required": False, "type": "text"},
        "size": {"label": "Size", "required": False, "type": "text"},
        "age_group": {
            "label": "Age Group",
            "required": False,
            "type": "enum",
            "accepted": ["newborn", "infant", "toddler", "kids", "adult"],
        },
        "gender": {
            "label": "Gender",
            "required": False,
            "type": "enum",
            "accepted": ["male", "female", "unisex"],
        },
    },
}


def get_required_attributes(marketplace_key: str) -> list:
    """Return list of field names that are required for the marketplace."""
    schema = ATTRIBUTE_SCHEMAS.get(marketplace_key, {})
    return [k for k, v in schema.items() if v.get("required")]


def get_attribute_labels(marketplace_key: str) -> dict:
    """Return {field: label} mapping for a marketplace."""
    schema = ATTRIBUTE_SCHEMAS.get(marketplace_key, {})
    return {k: v["label"] for k, v in schema.items()}
