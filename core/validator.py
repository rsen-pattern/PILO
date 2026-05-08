"""
Amazon Composite Data Quality (CDQ) Validator.
Checks generated content against category-specific requirements.
"""

from core.utils import load_category_config

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
