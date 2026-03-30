"""
Marketplace-driven dynamic configuration — single source of truth.

When a user selects a marketplace, ALL configuration (title rules, bullet structure,
description limits, attribute definitions, accepted values, output format) auto-populate
from this file. Adding a new marketplace means adding one dict entry.
"""

MARKETPLACE_CONFIGS = {
    "amazon_au": {
        "name": "Amazon AU",
        "language": "Australian English",
        "title": {
            "structure": "[Brand], [Style/Product Line], [Material/Key Feature], [Product Type], [Colour], [Size/Pack Count], [Model]",
            "char_limit": 200,
            "rules": (
                "Length: ≤200 chars. "
                "No promotional/subjective or pricing terms (e.g., best, free, sale, guarantee, % off). "
                "No merchant/seller-specific language. "
                "No ALL CAPS except brand name if brand guidelines require it. "
                "Front-load the most important search terms. "
                "Include colour and size variant for variant products."
            ),
        },
        "bullets": {
            "count": 5,
            "char_limit": 500,
            "guides": {
                1: "Primary benefit — lead with what the product does for the user",
                2: "Supporting features — key specs and materials",
                3: "Key Feature/USP — what makes this different",
                4: "Customer benefit — convenience, safety, or lifestyle fit",
                5: "Directions for use & care — how to use, clean, maintain",
            },
        },
        "description": {
            "char_limit": 2000,
            "rules": (
                "Length: ≤2,000 characters. "
                "No HTML/JS/CSS; only simple line breaks allowed. "
                "No keyword stuffing or promotional/pricing claims. "
                "Tell the product story: use case → key features → trust signals."
            ),
        },
        "attributes": [
            {"field": "color_name", "label": "Colour", "type": "text", "accepted": None},
            {"field": "material_type1", "label": "Material", "type": "text", "accepted": None},
            {"field": "size_name", "label": "Size", "type": "text", "accepted": None},
            {"field": "target_audience_keywords", "label": "Gender", "type": "enum",
             "accepted": ["Male", "Female", "Unisex"]},
            {"field": "age_range_description", "label": "Age Group", "type": "enum",
             "accepted": ["newborn", "infant", "toddler", "kids", "adult"]},
        ],
        "special_features_count": 5,
        "file_format": {
            "type": "amazon_flat_file",
            "header_rows": 3,
            "data_start_row": 4,
            "description": "Amazon Seller Central flat file (.xlsx) with 3-row header structure",
        },
        "search_terms_field": "generic_keywords",
        "search_terms_limit": 250,
    },

    "amazon_us": {
        "name": "Amazon US",
        "language": "US English",
        "title": {
            "structure": "[Brand] [Product Line] [Material] [Product Type] [Colour] [Size] [Packaging]",
            "char_limit": 200,
            "rules": (
                "Length: ≤200 chars. Title case (capitalise first letter of each word). "
                "No promotional language. Include key differentiators. "
                "Front-load brand + primary product type."
            ),
        },
        "bullets": {
            "count": 5,
            "char_limit": 500,
            "guides": {
                1: "Primary benefit and use case",
                2: "Key features and specifications",
                3: "Materials and build quality",
                4: "Compatibility and sizing",
                5: "What's included and care instructions",
            },
        },
        "description": {
            "char_limit": 2000,
            "rules": "Length: ≤2,000 characters. Same core rules as AU. Use US English spelling.",
        },
        "attributes": [
            {"field": "color_name", "label": "Color", "type": "text", "accepted": None},
            {"field": "material_type1", "label": "Material", "type": "text", "accepted": None},
            {"field": "size_name", "label": "Size", "type": "text", "accepted": None},
            {"field": "target_audience_keywords", "label": "Gender", "type": "enum",
             "accepted": ["Male", "Female", "Unisex"]},
            {"field": "age_range_description", "label": "Age Group", "type": "enum",
             "accepted": ["newborn", "infant", "toddler", "kids", "adult"]},
        ],
        "special_features_count": 5,
        "file_format": {
            "type": "amazon_flat_file",
            "header_rows": 3,
            "data_start_row": 4,
            "description": "Amazon Seller Central flat file (.xlsx)",
        },
        "search_terms_field": "generic_keywords",
        "search_terms_limit": 250,
    },

    "amazon_uk": {
        "name": "Amazon UK",
        "language": "UK English",
        "title": {
            "structure": "[Brand] [Product Line] [Material] [Product Type] [Colour] [Size] [Packaging]",
            "char_limit": 200,
            "rules": (
                "Length: ≤200 chars. Title case. "
                "No promotional language. Use UK English spelling. "
                "Front-load brand + primary product type."
            ),
        },
        "bullets": {
            "count": 5,
            "char_limit": 500,
            "guides": {
                1: "Primary benefit and use case",
                2: "Key features and specifications",
                3: "Materials and build quality",
                4: "Compatibility and sizing",
                5: "What's included and care instructions",
            },
        },
        "description": {
            "char_limit": 2000,
            "rules": "Length: ≤2,000 characters. Same core rules as AU. Use UK English spelling (colour, behaviour, etc.).",
        },
        "attributes": [
            {"field": "color_name", "label": "Colour", "type": "text", "accepted": None},
            {"field": "material_type1", "label": "Material", "type": "text", "accepted": None},
            {"field": "size_name", "label": "Size", "type": "text", "accepted": None},
            {"field": "target_audience_keywords", "label": "Gender", "type": "enum",
             "accepted": ["Male", "Female", "Unisex"]},
            {"field": "age_range_description", "label": "Age Group", "type": "enum",
             "accepted": ["newborn", "infant", "toddler", "kids", "adult"]},
        ],
        "special_features_count": 5,
        "file_format": {
            "type": "amazon_flat_file",
            "header_rows": 3,
            "data_start_row": 4,
            "description": "Amazon Seller Central flat file (.xlsx)",
        },
        "search_terms_field": "generic_keywords",
        "search_terms_limit": 250,
    },

    "walmart_us": {
        "name": "Walmart US",
        "language": "US English",
        "title": {
            "structure": "[Brand] + [Product Name] + [Key Attribute 1] + [Key Attribute 2] + [Count/Size]",
            "char_limit": 75,
            "rules": (
                "Length: ≤75 chars (Walmart is stricter than Amazon). "
                "No special characters except hyphens, commas, periods. "
                "No ALL CAPS. No subjective claims. "
                "Include the most critical search terms."
            ),
        },
        "bullets": {
            "count": 5,
            "char_limit": 500,
            "guides": {
                1: "Primary product benefit",
                2: "Key specifications",
                3: "Material and quality",
                4: "Use case and compatibility",
                5: "Care and warranty",
            },
        },
        "description": {
            "char_limit": 4000,
            "rules": (
                "Length: ≤4,000 characters. No HTML. "
                "Include use cases, features, and specifications. "
                "Walmart rewards completeness — be thorough."
            ),
        },
        "attributes": [
            {"field": "color", "label": "Color", "type": "text", "accepted": None},
            {"field": "material", "label": "Material", "type": "text", "accepted": None},
            {"field": "size", "label": "Size", "type": "text", "accepted": None},
            {"field": "gender", "label": "Gender", "type": "enum",
             "accepted": ["Male", "Female", "Gender Neutral"]},
            {"field": "ageGroup", "label": "Age Group", "type": "enum",
             "accepted": ["Newborn", "Infant", "Toddler", "Child", "Teen", "Adult"]},
        ],
        "special_features_count": 0,
        "file_format": {
            "type": "walmart_item_spec",
            "header_rows": 1,
            "data_start_row": 2,
            "description": "Walmart Item Spec 5.0 template (.xlsx)",
        },
        "search_terms_field": None,
        "search_terms_limit": None,
    },

    "woolworths_au": {
        "name": "Woolworths AU",
        "language": "Australian English",
        "title": {
            "structure": "[Brand] [Product Name] [Size/Weight] [Variant]",
            "char_limit": 150,
            "rules": (
                "Length: ≤150 chars. "
                "Must include GTIN-identifiable product name. "
                "Include weight/volume in metric units. "
                "No promotional language."
            ),
        },
        "bullets": {
            "count": 3,
            "char_limit": 300,
            "guides": {
                1: "Primary product description and use",
                2: "Key ingredients/materials and certifications",
                3: "Storage/care instructions and allergen info",
            },
        },
        "description": {
            "char_limit": 1500,
            "rules": "Concise, factual. Include nutritional/safety information where applicable.",
        },
        "attributes": [
            {"field": "gtin", "label": "GTIN/Barcode", "type": "text", "accepted": None, "required": True},
            {"field": "brand", "label": "Brand", "type": "text", "accepted": None, "required": True},
            {"field": "npc_category", "label": "NPC Category", "type": "text", "accepted": None},
            {"field": "country_of_origin", "label": "Country of Origin", "type": "text", "accepted": None},
            {"field": "weight_net", "label": "Net Weight", "type": "text", "accepted": None},
        ],
        "special_features_count": 0,
        "file_format": {
            "type": "gs1_npc",
            "header_rows": 1,
            "data_start_row": 2,
            "description": "GS1 National Product Catalogue format (.xlsx)",
        },
        "search_terms_field": None,
        "search_terms_limit": None,
    },

    "ebay_au": {
        "name": "eBay AU",
        "language": "Australian English",
        "title": {
            "structure": "[Brand] [Product Name] [Key Feature] [Colour] [Size] [Condition]",
            "char_limit": 80,
            "rules": (
                "Length: ≤80 chars. eBay titles are very short. "
                "Front-load the most searched terms. "
                "Include condition (New, Refurbished) if applicable. "
                "No promotional language or special characters."
            ),
        },
        "bullets": {
            "count": 0,
            "char_limit": 0,
            "guides": {},
        },
        "description": {
            "char_limit": 4000,
            "rules": (
                "eBay allows HTML in descriptions but keep it simple. "
                "Focus on specs, condition, compatibility, shipping info. "
                "Include keywords naturally."
            ),
        },
        "attributes": [
            {"field": "Brand", "label": "Brand", "type": "text", "accepted": None, "required": True},
            {"field": "MPN", "label": "MPN", "type": "text", "accepted": None},
            {"field": "Type", "label": "Type", "type": "text", "accepted": None},
            {"field": "Material", "label": "Material", "type": "text", "accepted": None},
            {"field": "Colour", "label": "Colour", "type": "text", "accepted": None},
            {"field": "Size", "label": "Size", "type": "text", "accepted": None},
        ],
        "special_features_count": 0,
        "file_format": {
            "type": "ebay_file_exchange",
            "header_rows": 1,
            "data_start_row": 2,
            "description": "eBay File Exchange / Seller Hub CSV format",
        },
        "search_terms_field": None,
        "search_terms_limit": None,
    },

    "google_shopping": {
        "name": "Google Shopping / UCP",
        "language": "configurable",
        "title": {
            "structure": "[Brand] [Product Type] [Key Attributes] [Size] [Colour]",
            "char_limit": 150,
            "rules": (
                "Length: ≤150 chars (Google truncates at ~70 in search results). "
                "Front-load the product type for Google's matching algorithm. "
                "Include variant-specific attributes. "
                "No promotional text."
            ),
        },
        "bullets": {
            "count": 0,
            "char_limit": 0,
            "guides": {},
        },
        "description": {
            "char_limit": 5000,
            "rules": (
                "Length: ≤5,000 chars. No HTML tags. "
                "Include product features, specs, materials. "
                "Google rewards rich, keyword-natural descriptions."
            ),
        },
        "attributes": [
            {"field": "google_product_category", "label": "Google Product Category",
             "type": "taxonomy", "accepted": None, "required": True},
            {"field": "product_type", "label": "Product Type", "type": "text", "accepted": None},
            {"field": "brand", "label": "Brand", "type": "text", "accepted": None, "required": True},
            {"field": "condition", "label": "Condition", "type": "enum",
             "accepted": ["new", "refurbished", "used"]},
            {"field": "material", "label": "Material", "type": "text", "accepted": None},
            {"field": "color", "label": "Color", "type": "text", "accepted": None},
            {"field": "size", "label": "Size", "type": "text", "accepted": None},
            {"field": "age_group", "label": "Age Group", "type": "enum",
             "accepted": ["newborn", "infant", "toddler", "kids", "adult"]},
            {"field": "gender", "label": "Gender", "type": "enum",
             "accepted": ["male", "female", "unisex"]},
        ],
        "special_features_count": 0,
        "file_format": {
            "type": "google_merchant_center",
            "header_rows": 1,
            "data_start_row": 2,
            "description": "Google Merchant Center feed (.csv or .xlsx)",
        },
        "search_terms_field": None,
        "search_terms_limit": None,
    },
}

# Marketplace display names for UI dropdowns
MARKETPLACE_CHOICES = {k: v["name"] for k, v in MARKETPLACE_CONFIGS.items()}

# Reverse lookup: display name → key
MARKETPLACE_KEY_BY_NAME = {v: k for k, v in MARKETPLACE_CHOICES.items()}


def get_config(marketplace_key: str) -> dict:
    """Return the full config dict for a marketplace key, or empty dict."""
    return MARKETPLACE_CONFIGS.get(marketplace_key, {})


def get_title_limit(marketplace_key: str) -> int:
    cfg = MARKETPLACE_CONFIGS.get(marketplace_key, {})
    return cfg.get("title", {}).get("char_limit", 200)


def get_bullet_count(marketplace_key: str) -> int:
    cfg = MARKETPLACE_CONFIGS.get(marketplace_key, {})
    return cfg.get("bullets", {}).get("count", 5)


def get_bullet_limit(marketplace_key: str) -> int:
    cfg = MARKETPLACE_CONFIGS.get(marketplace_key, {})
    return cfg.get("bullets", {}).get("char_limit", 500)


def get_description_limit(marketplace_key: str) -> int:
    cfg = MARKETPLACE_CONFIGS.get(marketplace_key, {})
    return cfg.get("description", {}).get("char_limit", 2000)


def marketplace_supports_bullets(marketplace_key: str) -> bool:
    return get_bullet_count(marketplace_key) > 0


def marketplace_supports_special_features(marketplace_key: str) -> bool:
    cfg = MARKETPLACE_CONFIGS.get(marketplace_key, {})
    return cfg.get("special_features_count", 0) > 0
