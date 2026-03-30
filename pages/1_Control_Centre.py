"""Page 1: Control Centre — marketplace-driven configuration hub."""

import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from config.marketplace_configs import (
    MARKETPLACE_CONFIGS, MARKETPLACE_CHOICES, MARKETPLACE_KEY_BY_NAME, get_config,
)
from config.model_registry import BIFROST_MODELS, RECOMMENDED_MODELS
from config.category_defaults import CATEGORY_GUIDELINES, CATEGORIES
import os

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Control Centre", "Marketplace-driven configuration — all settings in one place")

# ── Helper: auto-load secrets ──
def _load_secret(key):
    try:
        return st.secrets.get(key, "") or os.environ.get(key, "")
    except Exception:
        return os.environ.get(key, "")


# ═══════════════════════════════════════════════════════════════════════════
# 1A — Marketplace Selection (FIRST)
# ═══════════════════════════════════════════════════════════════════════════
st.header("1. Marketplace Selection")

marketplace_names = list(MARKETPLACE_CHOICES.values())
selected_names = st.multiselect(
    "Target Marketplaces",
    marketplace_names,
    default=st.session_state.get("target_marketplace_names", ["Amazon AU"]),
    key="mp_select",
)
st.session_state["target_marketplace_names"] = selected_names

# Convert names to keys
selected_keys = [MARKETPLACE_KEY_BY_NAME.get(n, n) for n in selected_names]
st.session_state["target_marketplace"] = selected_keys

primary_name = st.selectbox(
    "Primary Marketplace (drives default rules)",
    selected_names or ["Amazon AU"],
    index=0,
    key="primary_mp",
)
primary_key = MARKETPLACE_KEY_BY_NAME.get(primary_name, "amazon_au")
st.session_state["primary_marketplace"] = primary_key
primary_cfg = get_config(primary_key)

if primary_cfg:
    st.info(f"Guidelines auto-loaded for **{primary_cfg['name']}**. You can override any field below.")

# ═══════════════════════════════════════════════════════════════════════════
# 1B — Brand Configuration
# ═══════════════════════════════════════════════════════════════════════════
st.header("2. Brand Configuration")
col1, col2 = st.columns(2)
with col1:
    brand_name = st.text_input("Brand Name", value=st.session_state.get("brand_name", ""), key="brand_in")
    st.session_state["brand_name"] = brand_name
with col2:
    tone_options = ["Professional", "Friendly", "Premium", "Technical", "Playful", "Minimalist"]
    brand_tone = st.selectbox(
        "Brand Tone of Voice",
        tone_options,
        index=tone_options.index(st.session_state.get("brand_tone", "Professional")),
        key="tone_in",
    )
    st.session_state["brand_tone"] = brand_tone

brand_tov = st.text_area(
    "Brand Tone of Voice — Detail",
    value=st.session_state.get("brand_tov", ""),
    placeholder="Describe the brand voice in detail: e.g. 'Warm but authoritative. Use short, punchy sentences. "
                "Avoid jargon. Speak directly to pet owners as fellow animal lovers.'",
    key="tov_in",
    height=100,
)
st.session_state["brand_tov"] = brand_tov

brand_rules = st.text_area(
    "Brand Rules / Guidelines",
    value=st.session_state.get("brand_rules", ""),
    placeholder="e.g. Always capitalise BRAND NAME. Never use 'cheap'. Include trademark symbol.",
    key="rules_in",
)
st.session_state["brand_rules"] = brand_rules

brand_limitations = st.text_area(
    "Brand Limitations / Restrictions",
    value=st.session_state.get("brand_limitations", ""),
    placeholder="e.g. Do not mention competitors by name. Never claim 'best' or '#1'. "
                "Do not reference animal testing. Avoid words: cheap, budget, discount.",
    key="limitations_in",
    height=100,
)
st.session_state["brand_limitations"] = brand_limitations

# Category
categories = list(CATEGORY_GUIDELINES.keys())
category = st.selectbox(
    "Product Category",
    categories,
    index=categories.index(st.session_state.get("category", "Pet Supplies"))
    if st.session_state.get("category", "Pet Supplies") in categories else 0,
    key="cat_in",
)
st.session_state["category"] = category
st.session_state["category_guidelines"] = CATEGORY_GUIDELINES.get(category, "")

category_override = st.text_area(
    "Category Guidelines Override",
    value=st.session_state.get("category_guidelines_override", ""),
    placeholder="Override or supplement the default category guidelines with custom instructions.",
    key="cat_override_in",
    height=80,
)
st.session_state["category_guidelines_override"] = category_override

# ═══════════════════════════════════════════════════════════════════════════
# 1C — Title / Bullet / Description / Attribute Configuration
# ═══════════════════════════════════════════════════════════════════════════
st.header("3. Content Rules")
st.caption("Auto-populated from primary marketplace. Override any field.")

col1, col2, col3 = st.columns(3)
with col1:
    title_limit = st.number_input(
        "Title Character Limit",
        50, 500,
        value=primary_cfg.get("title", {}).get("char_limit", 200) if primary_cfg else 200,
        key="title_lim",
    )
    st.session_state["title_char_limit"] = title_limit
with col2:
    bullet_count = st.number_input(
        "Bullet Count",
        0, 10,
        value=primary_cfg.get("bullets", {}).get("count", 5) if primary_cfg else 5,
        key="bullet_cnt",
    )
    st.session_state["bullet_count"] = bullet_count
with col3:
    bullet_limit = st.number_input(
        "Bullet Char Limit",
        50, 1000,
        value=primary_cfg.get("bullets", {}).get("char_limit", 500) if primary_cfg else 500,
        key="bullet_lim",
    )
    st.session_state["bullet_char_limit"] = bullet_limit

desc_limit = st.number_input(
    "Description Character Limit",
    100, 10000,
    value=primary_cfg.get("description", {}).get("char_limit", 2000) if primary_cfg else 2000,
    key="desc_lim",
)
st.session_state["description_char_limit"] = desc_limit

with st.expander("Title Structure & Rules"):
    title_structure = st.text_input(
        "Title Structure",
        value=primary_cfg.get("title", {}).get("structure", "") if primary_cfg else "",
        key="w_title_struct",
    )
    st.session_state["title_structure"] = title_structure
    title_rules = st.text_area(
        "Title Rules",
        value=primary_cfg.get("title", {}).get("rules", "") if primary_cfg else "",
        key="w_title_rules",
    )
    st.session_state["title_rules"] = title_rules

with st.expander("Description Rules"):
    desc_rules = st.text_area(
        "Description Rules",
        value=primary_cfg.get("description", {}).get("rules", "") if primary_cfg else "",
        key="w_desc_rules",
    )
    st.session_state["description_rules"] = desc_rules

lang_options = ["Australian English", "US English", "UK English"]
language = st.selectbox(
    "Language Variant",
    lang_options,
    index=lang_options.index(primary_cfg.get("language", "Australian English"))
    if primary_cfg and primary_cfg.get("language") in lang_options else 0,
    key="lang_in",
)
st.session_state["language_variant"] = language

# ═══════════════════════════════════════════════════════════════════════════
# 1D — Data Generation Layer Configuration
# ═══════════════════════════════════════════════════════════════════════════
st.header("4. Data Generation Settings")

col1, col2 = st.columns(2)
with col1:
    keyword_enhancement = st.checkbox(
        "Keyword Enhancement",
        value=st.session_state.get("keyword_enhancement", True),
        help="Enhance content with keyword research step (Step 1 of chain)",
        key="kw_enh",
    )
    st.session_state["keyword_enhancement"] = keyword_enhancement

with col2:
    research_method = st.radio(
        "Research Method",
        ["AI Deep Research", "Web Scraping", "Both"],
        index=["AI Deep Research", "Web Scraping", "Both"].index(
            st.session_state.get("research_method", "AI Deep Research")
        ),
        key="research_method_in",
        horizontal=True,
    )
    st.session_state["research_method"] = research_method

confidence_threshold = st.slider(
    "Confidence Threshold",
    0.0, 1.0,
    value=st.session_state.get("confidence_threshold", 0.7),
    step=0.05,
    help="Flag AI research results below this confidence for human review",
    key="conf_thresh",
)
st.session_state["confidence_threshold"] = confidence_threshold

col1, col2 = st.columns(2)
with col1:
    api_delay = st.number_input(
        "API Rate Limit Delay (seconds)",
        0.0, 10.0,
        value=float(st.session_state.get("api_rate_delay", 0.3)),
        step=0.1,
        help="Delay between API calls to avoid rate limiting",
        key="api_delay_in",
    )
    st.session_state["api_rate_delay"] = api_delay
with col2:
    enrichment_overwrite = st.checkbox(
        "Enrichment Overwrites Feed Data",
        value=st.session_state.get("enrichment_overwrite", False),
        help="When ON, scraped/research data overwrites existing feed values. When OFF, only fills blanks.",
        key="overwrite_chk",
    )
    st.session_state["enrichment_overwrite"] = enrichment_overwrite

# Selective generation
st.subheader("Content Generation Toggles")
gen_cols = st.columns(4)
with gen_cols[0]:
    gen_title = st.checkbox("Generate Titles", value=st.session_state.get("generate_titles", True), key="gen_title_chk")
    st.session_state["generate_titles"] = gen_title
with gen_cols[1]:
    gen_bullets = st.checkbox("Generate Bullets", value=st.session_state.get("generate_bullets", True), key="gen_bullets_chk")
    st.session_state["generate_bullets"] = gen_bullets
with gen_cols[2]:
    gen_desc = st.checkbox("Generate Descriptions", value=st.session_state.get("generate_descriptions", True), key="gen_desc_chk")
    st.session_state["generate_descriptions"] = gen_desc
with gen_cols[3]:
    gen_attrs = st.checkbox("Generate Attributes", value=st.session_state.get("generate_attributes", True), key="gen_attrs_chk")
    st.session_state["generate_attributes"] = gen_attrs

# ═══════════════════════════════════════════════════════════════════════════
# 1E — Output Format
# ═══════════════════════════════════════════════════════════════════════════
st.header("5. Output Format")

output_format = st.radio(
    "Export Format",
    ["Match input file format", "Select marketplace template"],
    index=0 if st.session_state.get("output_format", "Match input file format") == "Match input file format" else 1,
    key="output_fmt",
    horizontal=True,
)
st.session_state["output_format"] = output_format

if output_format == "Select marketplace template":
    template_options = [
        "Amazon AU Flat File", "Amazon US Flat File", "Amazon UK Flat File",
        "Walmart Item Spec 5.0", "Woolworths GS1 NPC",
        "eBay File Exchange CSV", "Google Merchant Center Feed",
        "Universal Export (PILO internal)",
    ]
    selected_template = st.selectbox("Template", template_options, key="tmpl_sel")
    st.session_state["export_template"] = selected_template

# ═══════════════════════════════════════════════════════════════════════════
# 1F — Pattern Tool Integration
# ═══════════════════════════════════════════════════════════════════════════
st.header("6. Pattern Tool Integration")

col1, col2, col3 = st.columns(3)
with col1:
    pxm = st.checkbox(
        "PXM Export",
        value=st.session_state.get("pxm_integration", False),
        help="Enable PXM-compatible JSON export",
        key="pxm_chk",
    )
    st.session_state["pxm_integration"] = pxm
with col2:
    predict = st.checkbox(
        "Predict Keywords",
        value=st.session_state.get("predict_integration", False),
        help="Import keyword data from Pattern's Predict tool",
        key="predict_chk",
    )
    st.session_state["predict_integration"] = predict
with col3:
    shelf = st.checkbox(
        "Shelf Compliance",
        value=st.session_state.get("shelf_integration", False),
        help="Cross-reference with Shelf compliance scores",
        key="shelf_chk",
    )
    st.session_state["shelf_integration"] = shelf

# ═══════════════════════════════════════════════════════════════════════════
# 1G — AI Configuration
# ═══════════════════════════════════════════════════════════════════════════
st.header("7. AI Configuration")

# Model selection
all_models = list(BIFROST_MODELS.keys())
recommended = [m for m in RECOMMENDED_MODELS if m in all_models]
show_all = st.checkbox("Show all models", value=False, key="show_all_models")
model_list = all_models if show_all else recommended

current_model = st.session_state.get("model", "anthropic/claude-sonnet-4-6")
model = st.selectbox(
    "AI Model (via Bifrost)",
    model_list,
    index=model_list.index(current_model) if current_model in model_list else 0,
    key="model_in",
)
st.session_state["model"] = model

# Model info
model_info = BIFROST_MODELS.get(model, {})
if model_info:
    ci, co = st.columns(2)
    with ci:
        st.caption(f"Input: ${model_info.get('input_cost', 0)}/1M tokens | "
                   f"Output: ${model_info.get('output_cost', 0)}/1M tokens")
    with co:
        st.caption(f"Context: {model_info.get('context_window', 0):,} tokens | "
                   f"Max output: {model_info.get('max_output', 0):,}")

temperature = st.slider(
    "Temperature", 0.0, 1.0,
    value=st.session_state.get("temperature", 0.1),
    step=0.05, key="temp_in",
)
st.session_state["temperature"] = temperature

# API Keys
st.subheader("API Keys")
col1, col2 = st.columns(2)
with col1:
    default_bkey = _load_secret("BIFROST_API_KEY")
    bkey = st.text_input(
        "Bifrost API Key",
        value=st.session_state.get("bifrost_api_key", default_bkey),
        type="password", key="bkey_in",
    )
    st.session_state["bifrost_api_key"] = bkey

    base_url = st.text_input(
        "Bifrost Base URL",
        value=st.session_state.get("bifrost_base_url", "https://bifrost.pattern.com"),
        key="burl_in",
    )
    st.session_state["bifrost_base_url"] = base_url

with col2:
    default_skey = _load_secret("SCRAPINGBEE_API_KEY")
    skey = st.text_input(
        "ScrapingBee API Key (optional)",
        value=st.session_state.get("scrapingbee_api_key", default_skey),
        type="password", key="skey_in",
    )
    st.session_state["scrapingbee_api_key"] = skey

# ═══════════════════════════════════════════════════════════════════════════
# 1H — ScrapingBee Configuration
# ═══════════════════════════════════════════════════════════════════════════
st.header("8. ScrapingBee Configuration")
st.caption("Controls for web scraping via ScrapingBee API — used for Amazon product scraping and external website scraping.")

if not skey:
    st.info("Enter a ScrapingBee API key above to enable web scraping features.")

sb_col1, sb_col2 = st.columns(2)
with sb_col1:
    sb_render_js = st.checkbox(
        "Render JavaScript",
        value=st.session_state.get("sb_render_js", True),
        help="Enable JS rendering for dynamic pages (uses more credits)",
        key="sb_js_chk",
    )
    st.session_state["sb_render_js"] = sb_render_js

    sb_premium_proxy = st.checkbox(
        "Premium Proxy",
        value=st.session_state.get("sb_premium_proxy", True),
        help="Use premium residential proxies (better success rate, more credits)",
        key="sb_premium_chk",
    )
    st.session_state["sb_premium_proxy"] = sb_premium_proxy

with sb_col2:
    sb_timeout = st.number_input(
        "Request Timeout (seconds)",
        5, 120,
        value=int(st.session_state.get("sb_timeout", 30)),
        step=5,
        help="Timeout per scraping request",
        key="sb_timeout_in",
    )
    st.session_state["sb_timeout"] = sb_timeout

    sb_concurrency = st.number_input(
        "Max Concurrent Requests",
        1, 10,
        value=int(st.session_state.get("sb_concurrency", 1)),
        step=1,
        help="Number of simultaneous scraping requests",
        key="sb_concur_in",
    )
    st.session_state["sb_concurrency"] = sb_concurrency

sb_col3, sb_col4 = st.columns(2)
with sb_col3:
    sb_country = st.selectbox(
        "Default Proxy Country",
        ["Auto (match marketplace)", "us", "gb", "au", "de", "fr", "jp", "ca"],
        index=0,
        key="sb_country_in",
    )
    st.session_state["sb_country"] = sb_country

with sb_col4:
    sb_scrape_delay = st.number_input(
        "Delay Between Scrapes (seconds)",
        0.0, 30.0,
        value=float(st.session_state.get("sb_scrape_delay", 1.0)),
        step=0.5,
        help="Delay between individual scrape requests to avoid rate limits",
        key="sb_delay_in",
    )
    st.session_state["sb_scrape_delay"] = sb_scrape_delay

with st.expander("ScrapingBee Advanced Settings"):
    sb_block_ads = st.checkbox(
        "Block Ads & Trackers",
        value=st.session_state.get("sb_block_ads", True),
        help="Block ads and tracking scripts for faster page loads",
        key="sb_ads_chk",
    )
    st.session_state["sb_block_ads"] = sb_block_ads

    sb_block_resources = st.checkbox(
        "Block Images & CSS",
        value=st.session_state.get("sb_block_resources", False),
        help="Block images and CSS for faster scraping (text-only extraction)",
        key="sb_resources_chk",
    )
    st.session_state["sb_block_resources"] = sb_block_resources

    sb_custom_headers = st.text_area(
        "Custom Headers (JSON)",
        value=st.session_state.get("sb_custom_headers", ""),
        placeholder='e.g. {"Accept-Language": "en-AU"}',
        key="sb_headers_in",
        height=60,
    )
    st.session_state["sb_custom_headers"] = sb_custom_headers

# ── Save confirmation ──
st.divider()
if st.button("Save Configuration", type="primary", use_container_width=True):
    st.success("Configuration saved to session. Proceed to Data Ingestion.")
