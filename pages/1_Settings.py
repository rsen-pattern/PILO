"""Page 1: Settings — Configure brand, category, marketplace, and AI parameters."""

import os

import streamlit as st

from config.category_defaults import CATEGORIES, CATEGORY_GUIDELINES
from config.marketplace_schemas import MARKETPLACE_OPTIONS
from config.model_registry import (
    BIFROST_MODELS,
    RECOMMENDED_MODELS,
    get_all_bifrost_model_ids,
    get_model_display_name,
)
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar

st.set_page_config(page_title="PILO — Settings", page_icon="\u2699\ufe0f", layout="wide")
inject_pattern_css()
pattern_sidebar()
pattern_page_header("Settings", "Configure PILO for your brand, category, and target marketplaces.")

# Load existing settings
settings = st.session_state.get("settings", {})


def _load_secret(key):
    """Load a secret from st.secrets, then environment, then return empty string."""
    try:
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(key, "")


# --- Brand Configuration ---
st.header("Brand Configuration")
col1, col2 = st.columns(2)

with col1:
    brand_name = st.text_input(
        "Brand Name",
        value=settings.get("brand_name", ""),
        placeholder="e.g., KONG",
    )

with col2:
    brand_tone = st.text_area(
        "Brand Tone of Voice",
        value=settings.get("brand_tone", ""),
        placeholder="e.g., Playful, confident, pet-parent focused. Use active voice. Avoid jargon.",
        height=100,
    )

brand_rules = st.text_area(
    "Brand Rules",
    value=settings.get("brand_rules", ""),
    placeholder="e.g., Always capitalise KONG. Never use 'chew toy' — use 'interactive dog toy'. Measurements in metric for AU.",
    height=100,
)

# --- Category Configuration ---
st.header("Category Configuration")
col1, col2 = st.columns(2)

with col1:
    category = st.selectbox(
        "Product Category",
        CATEGORIES,
        index=CATEGORIES.index(settings["category"]) if settings.get("category") in CATEGORIES else 0,
    )

with col2:
    default_guidelines = CATEGORY_GUIDELINES.get(category, "")
    category_guidelines = st.text_area(
        "Category Guidelines",
        value=settings.get("category_guidelines", default_guidelines),
        height=150,
    )

# --- Marketplace Configuration ---
st.header("Marketplace Configuration")
col1, col2 = st.columns(2)

with col1:
    target_marketplace = st.multiselect(
        "Target Marketplace(s)",
        MARKETPLACE_OPTIONS,
        default=settings.get("target_marketplace", ["Amazon AU"]),
    )

    language_variant = st.selectbox(
        "Language Variant",
        ["Australian English", "US English", "UK English"],
        index=["Australian English", "US English", "UK English"].index(
            settings.get("language_variant", "Australian English")
        ),
    )

with col2:
    title_char_limit = st.number_input(
        "Title Character Limit",
        value=settings.get("title_char_limit", 200),
        min_value=50,
        max_value=500,
    )
    bullet_count = st.number_input(
        "Number of Bullet Points",
        value=settings.get("bullet_count", 5),
        min_value=1,
        max_value=10,
    )
    bullet_char_limit = st.number_input(
        "Bullet Point Character Limit",
        value=settings.get("bullet_char_limit", 500),
        min_value=50,
        max_value=1000,
    )
    description_char_limit = st.number_input(
        "Description Character Limit",
        value=settings.get("description_char_limit", 2000),
        min_value=100,
        max_value=5000,
    )

# --- AI Configuration (Bifrost) ---
st.header("AI Configuration — Bifrost Gateway")
st.caption(
    "PILO uses Pattern's Bifrost gateway to access models from Anthropic, OpenAI, "
    "Google, and AWS Bedrock through a single API."
)

col1, col2 = st.columns(2)

with col1:
    # Auto-load from secrets/env, allow manual override
    default_key = settings.get("bifrost_api_key", "") or _load_secret("BIFROST_API_KEY")
    bifrost_api_key = st.text_input(
        "Bifrost API Key",
        value=default_key,
        type="password",
        help="Your Bifrost virtual key (sk-bf-...). Set in Streamlit secrets or BIFROST_API_KEY env var.",
    )
    if not bifrost_api_key:
        st.warning("Bifrost API key required for content generation. Add BIFROST_API_KEY to your Streamlit secrets (.streamlit/secrets.toml) or environment.")
    elif bifrost_api_key and not settings.get("bifrost_api_key"):
        st.info("Bifrost API key loaded from secrets/environment.")

    bifrost_base_url = st.text_input(
        "Bifrost Base URL",
        value=settings.get("bifrost_base_url", "https://bifrost.pattern.com"),
        help="Bifrost gateway endpoint.",
    )

with col2:
    st.markdown("**Model**")

    model_options = get_all_bifrost_model_ids()
    # Put recommended models first
    sorted_models = [m for m in RECOMMENDED_MODELS if m in model_options]
    sorted_models += [m for m in model_options if m not in sorted_models]

    current_model = settings.get("model", "anthropic/claude-sonnet-4-6")
    if current_model not in sorted_models:
        current_model = sorted_models[0]

    model = st.selectbox(
        "Select Model",
        sorted_models,
        index=sorted_models.index(current_model),
        format_func=get_model_display_name,
    )

    # Show model info card
    model_info = BIFROST_MODELS.get(model, {})
    if model_info:
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.markdown(f"**Provider:** `{model_info['provider']}`")
        with info_col2:
            st.markdown(f"**Context:** {model_info['context'] // 1000}K")
        with info_col3:
            st.markdown(f"**Cost:** ${model_info['input_cost']}/{model_info['output_cost']}")

temperature = st.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.0,
    value=settings.get("temperature", 0.1),
    step=0.05,
)

# --- ScrapingBee Configuration ---
st.header("ScrapingBee Configuration")

scraping_enabled = st.checkbox(
    "Enable web scraping",
    value=settings.get("scraping_enabled", False),
)

default_sb_key = settings.get("scrapingbee_api_key", "") or _load_secret("SCRAPINGBEE_API_KEY")
scrapingbee_api_key = ""

if scraping_enabled:
    scrapingbee_api_key = st.text_input(
        "ScrapingBee API Key",
        value=default_sb_key,
        type="password",
        help="Set in Streamlit secrets or SCRAPINGBEE_API_KEY env var.",
    )
    if not scrapingbee_api_key:
        st.warning("ScrapingBee API key required for web scraping. Add SCRAPINGBEE_API_KEY to your Streamlit secrets or environment.")
    elif scrapingbee_api_key and not settings.get("scrapingbee_api_key"):
        st.info("ScrapingBee API key loaded from secrets/environment.")
else:
    # Still try to load from secrets so it's available when toggled on
    scrapingbee_api_key = default_sb_key

# --- Save ---
st.divider()

if st.button("Save Settings", type="primary"):
    new_settings = {
        "brand_name": brand_name,
        "brand_tone": brand_tone,
        "brand_rules": brand_rules,
        "category": category,
        "category_guidelines": category_guidelines,
        "target_marketplace": target_marketplace,
        "language_variant": language_variant,
        "title_char_limit": title_char_limit,
        "bullet_count": bullet_count,
        "bullet_char_limit": bullet_char_limit,
        "description_char_limit": description_char_limit,
        "model": model,
        "temperature": temperature,
        "bifrost_api_key": bifrost_api_key,
        "bifrost_base_url": bifrost_base_url,
        "scraping_enabled": scraping_enabled,
        "scrapingbee_api_key": scrapingbee_api_key,
    }
    st.session_state["settings"] = new_settings
    st.success("Settings saved successfully!")
