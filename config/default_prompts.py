"""
Default prompt templates for the 7-step content generation chain.
Each template uses Python format strings with named placeholders.
"""

# ---------------------------------------------------------------------------
# Step 0 — Deep Research
# ---------------------------------------------------------------------------
RESEARCH_PROMPT = """You are a product research specialist. Research the following product thoroughly.

PRODUCT: {product_name}
BRAND: {brand_name}
CATEGORY: {category}
EXISTING DATA: {existing_data}

Research and provide:
1. Detailed product description (materials, dimensions, features)
2. Key selling points and unique features
3. Target audience and use cases
4. Competitor comparisons (what makes this product different)
5. Common customer questions and concerns
6. Relevant certifications, awards, or endorsements

{additional_context}

Return your research as a structured JSON:
{{
    "product_summary": "...",
    "key_features": ["..."],
    "materials": "...",
    "dimensions": "...",
    "target_audience": "...",
    "use_cases": ["..."],
    "differentiators": ["..."],
    "certifications": ["..."],
    "confidence_notes": "Brief note on what you're most/least confident about"
}}"""

# ---------------------------------------------------------------------------
# Step 0b — Confidence Self-Assessment
# ---------------------------------------------------------------------------
CONFIDENCE_PROMPT = """Rate your confidence in the research above on a scale of 0.0 to 1.0:
- 1.0 = All facts verified from known sources, specific numbers confirmed
- 0.7 = Most information is reliable, some details inferred
- 0.4 = Mix of known and uncertain information
- 0.1 = Mostly inferred, low certainty

Return ONLY the number."""

# ---------------------------------------------------------------------------
# Step 1 — Keyword Generation
# ---------------------------------------------------------------------------
KEYWORDS_PROMPT = """You are an SEO keyword specialist for {marketplace_name}.

PRODUCT: {product_name}
BRAND: {brand_name}
CATEGORY: {category}
PRODUCT DATA: {product_data}
{predict_keywords}

Generate a comprehensive keyword list for this product optimised for {marketplace_name}.

Rules:
- {search_terms_rules}
- Focus on high-intent, product-relevant search terms
- Include long-tail variations
- No competitor brand names
- No subjective/promotional terms

Return JSON:
{{
    "primary_keywords": ["top 5 highest-volume terms"],
    "secondary_keywords": ["10-15 supporting terms"],
    "long_tail_keywords": ["5-10 long-tail phrases"],
    "search_terms": "single string of all terms for search field (if applicable)"
}}"""

# ---------------------------------------------------------------------------
# Step 2 — Title Generation
# ---------------------------------------------------------------------------
TITLE_PROMPT = """You are a product title specialist for {marketplace_name}.

BRAND: {brand_name}
PRODUCT: {product_name}
CATEGORY: {category}
PRODUCT DATA: {product_data}
{keywords_context}

TITLE STRUCTURE: {title_structure}
CHARACTER LIMIT: {title_char_limit}

RULES:
{title_rules}

BRAND TONE: {brand_tone}
BRAND RULES: {brand_rules}
LANGUAGE: {language}

Generate an optimised product title following the exact structure and rules above.

Return JSON:
{{
    "title": "the optimised title",
    "char_count": 123,
    "keywords_used": ["list of keywords incorporated"]
}}"""

# ---------------------------------------------------------------------------
# Step 3 — Bullet Points
# ---------------------------------------------------------------------------
BULLETS_PROMPT = """You are a product copywriter specialising in bullet points for {marketplace_name}.

BRAND: {brand_name}
PRODUCT: {product_name}
TITLE: {generated_title}
PRODUCT DATA: {product_data}
{keywords_context}

Generate exactly {bullet_count} bullet points.
CHARACTER LIMIT PER BULLET: {bullet_char_limit}

BULLET GUIDES:
{bullet_guides}

RULES:
- Each bullet must start with a CAPITALISED key benefit phrase
- Include relevant keywords naturally
- No promotional/subjective claims
- {language} spelling and conventions
- BRAND TONE: {brand_tone}

Return JSON:
{{
    "bullets": [
        "BULLET 1 TEXT",
        "BULLET 2 TEXT",
        ...
    ]
}}"""

# ---------------------------------------------------------------------------
# Step 4 — Description
# ---------------------------------------------------------------------------
DESCRIPTION_PROMPT = """You are a product description writer for {marketplace_name}.

BRAND: {brand_name}
PRODUCT: {product_name}
TITLE: {generated_title}
BULLETS: {generated_bullets}
PRODUCT DATA: {product_data}
{keywords_context}

CHARACTER LIMIT: {desc_char_limit}

RULES:
{desc_rules}

BRAND TONE: {brand_tone}
LANGUAGE: {language}

Write a compelling product description that tells the product story:
use case → key features → trust signals.

Return JSON:
{{
    "description": "the full description text",
    "char_count": 456
}}"""

# ---------------------------------------------------------------------------
# Step 5 — Attributes
# ---------------------------------------------------------------------------
ATTRIBUTES_PROMPT = """You are a product data specialist for {marketplace_name}.

PRODUCT: {product_name}
BRAND: {brand_name}
PRODUCT DATA: {product_data}
RESEARCH DATA: {research_data}

Generate values for the following marketplace attributes:
{attribute_definitions}

RULES:
- Use accepted values where specified (enum fields)
- Be factual and specific — no guessing if data is unavailable
- Return empty string for attributes you cannot determine
- {language} spelling

Return JSON with field names as keys:
{{
    "field_name_1": "value",
    "field_name_2": "value",
    ...
}}"""

# ---------------------------------------------------------------------------
# Step 6 — Special Features (Amazon only)
# ---------------------------------------------------------------------------
SPECIAL_FEATURES_PROMPT = """You are a product feature specialist for {marketplace_name}.

PRODUCT: {product_name}
BRAND: {brand_name}
PRODUCT DATA: {product_data}

Generate exactly {feature_count} special features. Each should be a concise,
specific product feature (2-5 words).

Examples: "Dishwasher Safe", "BPA Free", "Ergonomic Grip", "UV Resistant"

Return JSON:
{{
    "special_features": ["Feature 1", "Feature 2", ...]
}}"""

# ---------------------------------------------------------------------------
# Step 7 — Item Type Classification
# ---------------------------------------------------------------------------
ITEM_TYPE_PROMPT = """You are a product categorisation specialist for {marketplace_name}.

PRODUCT: {product_name}
BRAND: {brand_name}
CATEGORY: {category}
PRODUCT DATA: {product_data}

Determine the most specific and accurate item type keyword for this product
on {marketplace_name}.

Return JSON:
{{
    "item_type": "the item type keyword",
    "category_path": "Top Level > Sub Category > Specific Type"
}}"""

# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """You are PILO — Pattern Intelligence Listing Optimisation — an expert product content engine.
You generate optimised product listings for online marketplaces.

TARGET MARKETPLACE: {marketplace_name}
LANGUAGE: {language}
CHARACTER LIMITS: Title={title_limit}, Bullets={bullet_limit}, Description={desc_limit}

You MUST:
- Follow all marketplace rules exactly
- Stay within character limits
- Use the specified language variant
- Return valid JSON only — no markdown, no explanations outside JSON
- Be factual — never fabricate specifications or certifications
"""
