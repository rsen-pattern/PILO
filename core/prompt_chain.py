"""
7-step prompt chain engine for multi-marketplace content generation.

Steps:
  0. Deep Research (optional — if research_method includes AI)
  1. Keyword Generation (optional — if keyword_enhancement is ON)
  2. Title Generation
  3. Bullet Points (skipped for eBay/Google)
  4. Description
  5. Attributes
  6. Special Features (Amazon only)
  7. Item Type Classification
"""

import json
import time

from config.default_prompts import (
    KEYWORDS_PROMPT, TITLE_PROMPT, BULLETS_PROMPT,
    DESCRIPTION_PROMPT, ATTRIBUTES_PROMPT, SPECIAL_FEATURES_PROMPT,
    ITEM_TYPE_PROMPT, SYSTEM_PROMPT_TEMPLATE,
)
from config.marketplace_configs import (
    get_config, get_title_limit, get_bullet_count, get_bullet_limit,
    get_description_limit, marketplace_supports_bullets,
    marketplace_supports_special_features,
)


def build_system_prompt(marketplace_key: str) -> str:
    """Build the system prompt for a given marketplace."""
    cfg = get_config(marketplace_key)
    return SYSTEM_PROMPT_TEMPLATE.format(
        marketplace_name=cfg.get("name", marketplace_key),
        language=cfg.get("language", "English"),
        title_limit=get_title_limit(marketplace_key),
        bullet_limit=get_bullet_limit(marketplace_key),
        desc_limit=get_description_limit(marketplace_key),
    )


def run_chain(client, model: str, product: dict, marketplace_key: str,
              settings: dict, research_data: dict = None,
              predict_keywords: list = None,
              scraped_data: dict = None,
              document_context: str = None,
              crossretail_data: dict = None,
              progress_callback=None) -> dict:
    """Run the full prompt chain for one SKU × one marketplace.

    Args:
        client: OpenAI-compatible client (Bifrost)
        model: model ID string
        product: dict with product data fields
        marketplace_key: e.g. 'amazon_au'
        settings: user settings dict
        research_data: optional pre-computed research for this product
        predict_keywords: optional list of Predict keyword dicts
        scraped_data: optional dict of scraped product data for this SKU
        document_context: optional string of relevant document text for this SKU
        crossretail_data: optional dict of cross-retail data for this SKU
        progress_callback: optional callable(step_name, step_num, total_steps)

    Returns:
        dict with all generated content + metadata
    """
    cfg = get_config(marketplace_key)
    system_prompt = build_system_prompt(marketplace_key)
    temperature = settings.get("temperature", 0.1)
    api_delay = settings.get("api_rate_delay", 0.3)
    keyword_enhancement = settings.get("keyword_enhancement", True)

    # Selective generation toggles
    generate_titles = settings.get("generate_titles", True)
    generate_bullets = settings.get("generate_bullets", True)
    generate_descriptions = settings.get("generate_descriptions", True)
    generate_attributes = settings.get("generate_attributes", True)

    result = {
        "marketplace": marketplace_key,
        "marketplace_name": cfg["name"],
        "sku": product.get("sku", ""),
        "steps_completed": [],
        "errors": [],
    }

    product_data_str = "\n".join(f"  {k}: {v}" for k, v in product.items() if v)
    research_str = ""
    if research_data and research_data.get("research"):
        research_str = json.dumps(research_data["research"], indent=2)

    # Build supplementary context from all data sources
    supplementary_context = _build_supplementary_context(
        scraped_data=scraped_data,
        document_context=document_context,
        crossretail_data=crossretail_data,
        brand_tov=settings.get("brand_tov", ""),
        brand_limitations=settings.get("brand_limitations", ""),
        category_guidelines_override=settings.get("category_guidelines_override", ""),
    )

    # Determine which steps to run (respecting selective generation toggles)
    steps = []
    if keyword_enhancement:
        steps.append("keywords")
    if generate_titles:
        steps.append("title")
    if generate_bullets and marketplace_supports_bullets(marketplace_key):
        steps.append("bullets")
    if generate_descriptions:
        steps.append("description")
    if generate_attributes:
        steps.append("attributes")
    if marketplace_supports_special_features(marketplace_key):
        steps.append("special_features")
    steps.append("item_type")

    total_steps = len(steps)
    keywords_context = ""

    for step_idx, step_name in enumerate(steps):
        if progress_callback:
            progress_callback(step_name, step_idx + 1, total_steps)

        try:
            if step_name == "keywords":
                keywords_result = _run_keywords(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str, predict_keywords,
                    supplementary_context,
                )
                result["keywords"] = keywords_result
                result["steps_completed"].append("keywords")
                # Build context string for subsequent steps
                kw = keywords_result
                primary = kw.get("primary_keywords", [])
                secondary = kw.get("secondary_keywords", [])
                keywords_context = f"\nKEYWORDS TO INCORPORATE:\nPrimary: {', '.join(primary)}\nSecondary: {', '.join(secondary)}"
                if kw.get("search_terms"):
                    result["search_terms"] = kw["search_terms"]

            elif step_name == "title":
                title_result = _run_title(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str, keywords_context, settings,
                    supplementary_context,
                )
                result["title"] = title_result.get("title", "")
                result["title_char_count"] = title_result.get("char_count", len(result["title"]))
                result["steps_completed"].append("title")

            elif step_name == "bullets":
                bullets_result = _run_bullets(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str, keywords_context,
                    result.get("title", ""), settings, supplementary_context,
                )
                result["bullets"] = bullets_result.get("bullets", [])
                result["steps_completed"].append("bullets")

            elif step_name == "description":
                desc_result = _run_description(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str, keywords_context,
                    result.get("title", ""), result.get("bullets", []), settings,
                    supplementary_context,
                )
                result["description"] = desc_result.get("description", "")
                result["desc_char_count"] = desc_result.get("char_count", len(result["description"]))
                result["steps_completed"].append("description")

            elif step_name == "attributes":
                attr_result = _run_attributes(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str, research_str,
                    supplementary_context,
                )
                result["attributes"] = attr_result
                result["steps_completed"].append("attributes")

            elif step_name == "special_features":
                sf_result = _run_special_features(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str, supplementary_context,
                )
                result["special_features"] = sf_result.get("special_features", [])
                result["steps_completed"].append("special_features")

            elif step_name == "item_type":
                it_result = _run_item_type(
                    client, model, system_prompt, temperature,
                    product, cfg, product_data_str,
                )
                result["item_type"] = it_result.get("item_type", "")
                result["category_path"] = it_result.get("category_path", "")
                result["steps_completed"].append("item_type")

        except Exception as e:
            result["errors"].append({"step": step_name, "error": str(e)})

        # Rate-limited delay between API calls
        time.sleep(api_delay)

    return result


def _build_supplementary_context(scraped_data=None, document_context=None,
                                  crossretail_data=None, brand_tov="",
                                  brand_limitations="",
                                  category_guidelines_override="") -> str:
    """Build a supplementary context block from all additional data sources."""
    parts = []

    if scraped_data:
        scraped_str = "\n".join(f"  {k}: {v}" for k, v in scraped_data.items() if v)
        if scraped_str:
            parts.append(f"SCRAPED PRODUCT DATA (from live marketplace listing):\n{scraped_str}")

    if document_context:
        parts.append(f"CLIENT DOCUMENT CONTEXT:\n{document_context}")

    if crossretail_data:
        cr_str = "\n".join(f"  {k}: {v}" for k, v in crossretail_data.items() if v)
        if cr_str:
            parts.append(f"CROSS-RETAIL REFERENCE DATA:\n{cr_str}")

    if brand_tov:
        parts.append(f"BRAND TONE OF VOICE DETAIL:\n{brand_tov}")

    if brand_limitations:
        parts.append(f"BRAND LIMITATIONS / RESTRICTIONS:\n{brand_limitations}")

    if category_guidelines_override:
        parts.append(f"CATEGORY GUIDELINES (CUSTOM):\n{category_guidelines_override}")

    return "\n\n".join(parts)


def _call_api(client, model, system_prompt, temperature, user_prompt):
    """Make a single Bifrost API call and return parsed JSON."""
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=4096,
    )
    raw = response.choices[0].message.content
    return _parse_json(raw), raw


def _run_keywords(client, model, system_prompt, temperature,
                  product, cfg, product_data_str, predict_keywords,
                  supplementary_context=""):
    predict_str = ""
    if predict_keywords:
        terms = [kw.get("search_term", "") for kw in predict_keywords[:20]]
        predict_str = f"\nPATTERN PREDICT KEYWORDS (incorporate these):\n{', '.join(terms)}"

    search_rules = ""
    if cfg.get("search_terms_field"):
        limit = cfg.get("search_terms_limit", 250)
        search_rules = f"Search terms field: {cfg['search_terms_field']}, limit: {limit} bytes"
    else:
        search_rules = "This marketplace does not have a dedicated search terms field"

    prompt = KEYWORDS_PROMPT.format(
        marketplace_name=cfg["name"],
        product_name=product.get("title", product.get("sku", "")),
        brand_name=product.get("brand", ""),
        category=product.get("product_type", ""),
        product_data=product_data_str,
        predict_keywords=predict_str,
        search_terms_rules=search_rules,
    )
    if supplementary_context:
        prompt += f"\n\n{supplementary_context}"
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _run_title(client, model, system_prompt, temperature,
               product, cfg, product_data_str, keywords_context, settings,
               supplementary_context=""):
    prompt = TITLE_PROMPT.format(
        marketplace_name=cfg["name"],
        brand_name=product.get("brand", ""),
        product_name=product.get("title", product.get("sku", "")),
        category=product.get("product_type", ""),
        product_data=product_data_str,
        keywords_context=keywords_context,
        title_structure=cfg["title"]["structure"],
        title_char_limit=cfg["title"]["char_limit"],
        title_rules=cfg["title"]["rules"],
        brand_tone=settings.get("brand_tone", "Professional"),
        brand_rules=settings.get("brand_rules", ""),
        language=cfg["language"],
    )
    if supplementary_context:
        prompt += f"\n\n{supplementary_context}"
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _run_bullets(client, model, system_prompt, temperature,
                 product, cfg, product_data_str, keywords_context,
                 generated_title, settings, supplementary_context=""):
    bullet_guides = "\n".join(
        f"  Bullet {n}: {guide}" for n, guide in cfg["bullets"]["guides"].items()
    )
    prompt = BULLETS_PROMPT.format(
        marketplace_name=cfg["name"],
        brand_name=product.get("brand", ""),
        product_name=product.get("title", product.get("sku", "")),
        generated_title=generated_title,
        product_data=product_data_str,
        keywords_context=keywords_context,
        bullet_count=cfg["bullets"]["count"],
        bullet_char_limit=cfg["bullets"]["char_limit"],
        bullet_guides=bullet_guides,
        language=cfg["language"],
        brand_tone=settings.get("brand_tone", "Professional"),
    )
    if supplementary_context:
        prompt += f"\n\n{supplementary_context}"
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _run_description(client, model, system_prompt, temperature,
                     product, cfg, product_data_str, keywords_context,
                     generated_title, generated_bullets, settings,
                     supplementary_context=""):
    bullets_str = "\n".join(f"  - {b}" for b in generated_bullets) if generated_bullets else "(none)"
    prompt = DESCRIPTION_PROMPT.format(
        marketplace_name=cfg["name"],
        brand_name=product.get("brand", ""),
        product_name=product.get("title", product.get("sku", "")),
        generated_title=generated_title,
        generated_bullets=bullets_str,
        product_data=product_data_str,
        keywords_context=keywords_context,
        desc_char_limit=cfg["description"]["char_limit"],
        desc_rules=cfg["description"]["rules"],
        brand_tone=settings.get("brand_tone", "Professional"),
        language=cfg["language"],
    )
    if supplementary_context:
        prompt += f"\n\n{supplementary_context}"
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _run_attributes(client, model, system_prompt, temperature,
                    product, cfg, product_data_str, research_str,
                    supplementary_context=""):
    attr_defs = "\n".join(
        f"  {a['field']} ({a['label']}): type={a['type']}"
        + (f", accepted={a['accepted']}" if a.get("accepted") else "")
        + (", REQUIRED" if a.get("required") else "")
        for a in cfg.get("attributes", [])
    )
    prompt = ATTRIBUTES_PROMPT.format(
        marketplace_name=cfg["name"],
        product_name=product.get("title", product.get("sku", "")),
        brand_name=product.get("brand", ""),
        product_data=product_data_str,
        research_data=research_str or "(none)",
        attribute_definitions=attr_defs,
        language=cfg["language"],
    )
    if supplementary_context:
        prompt += f"\n\n{supplementary_context}"
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _run_special_features(client, model, system_prompt, temperature,
                          product, cfg, product_data_str,
                          supplementary_context=""):
    prompt = SPECIAL_FEATURES_PROMPT.format(
        marketplace_name=cfg["name"],
        product_name=product.get("title", product.get("sku", "")),
        brand_name=product.get("brand", ""),
        product_data=product_data_str,
        feature_count=cfg.get("special_features_count", 5),
    )
    if supplementary_context:
        prompt += f"\n\n{supplementary_context}"
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _run_item_type(client, model, system_prompt, temperature,
                   product, cfg, product_data_str):
    prompt = ITEM_TYPE_PROMPT.format(
        marketplace_name=cfg["name"],
        product_name=product.get("title", product.get("sku", "")),
        brand_name=product.get("brand", ""),
        category=product.get("product_type", ""),
        product_data=product_data_str,
    )
    result, _ = _call_api(client, model, system_prompt, temperature, prompt)
    return result


def _parse_json(text: str) -> dict:
    """Parse JSON from response text, handling markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}
