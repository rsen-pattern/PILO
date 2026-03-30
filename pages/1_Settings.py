"""Page 1: Settings — Configure brand, category, marketplace, and AI parameters."""

import streamlit as st

from config.category_defaults import CATEGORIES, CATEGORY_GUIDELINES
from config.marketplace_schemas import MARKETPLACE_OPTIONS

st.set_page_config(page_title="PILO — Settings", page_icon="\u2699\ufe0f", layout="wide")
st.title("Settings")
st.caption("Configure PILO for your brand, category, and target marketplaces.")

# Load existing settings
settings = st.session_state.get("settings", {})

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

# --- AI Configuration ---
st.header("AI Configuration")
col1, col2 = st.columns(2)

with col1:
    model = st.selectbox(
        "Model",
        ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        index=0 if settings.get("model", "claude-sonnet-4-20250514") == "claude-sonnet-4-20250514" else 1,
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=settings.get("temperature", 0.1),
        step=0.05,
    )

with col2:
    anthropic_api_key = st.text_input(
        "Anthropic API Key",
        value=settings.get("anthropic_api_key", ""),
        type="password",
        help="Your Claude API key. Can also be set via ANTHROPIC_API_KEY environment variable or Streamlit secrets.",
    )

    # Try to load from secrets or env
    if not anthropic_api_key:
        import os
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        try:
            anthropic_api_key = anthropic_api_key or st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
        if anthropic_api_key:
            st.info("API key loaded from environment/secrets.")

# --- ScrapingBee Configuration ---
st.header("ScrapingBee Configuration (Optional)")

scraping_enabled = st.checkbox(
    "Enable web scraping",
    value=settings.get("scraping_enabled", False),
)

scrapingbee_api_key = ""
if scraping_enabled:
    scrapingbee_api_key = st.text_input(
        "ScrapingBee API Key",
        value=settings.get("scrapingbee_api_key", ""),
        type="password",
    )
    if not scrapingbee_api_key:
        import os
        scrapingbee_api_key = os.environ.get("SCRAPINGBEE_API_KEY", "")
        try:
            scrapingbee_api_key = scrapingbee_api_key or st.secrets.get("SCRAPINGBEE_API_KEY", "")
        except Exception:
            pass

# --- Save ---
st.divider()

if st.button("Save Settings", type="primary"):
    st.session_state["settings"] = {
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
        "anthropic_api_key": anthropic_api_key,
        "scraping_enabled": scraping_enabled,
        "scrapingbee_api_key": scrapingbee_api_key,
    }
    st.success("Settings saved successfully!")
