"""PILO — Pattern Intelligence Listing Optimisation.

Main Streamlit entry point. V3 — marketplace-driven, multi-marketplace generation.
"""

import streamlit as st

st.set_page_config(
    page_title="PILO — Pattern Intelligence Listing Optimisation",
    page_icon="\U0001f6d2",
    layout="wide",
)


def init_session_state():
    """Initialise session state keys if they don't exist."""
    defaults = {
        "settings": {},
        "feed_df": None,
        "feed_format": None,
        "feed_metadata": None,
        "column_mapping": {},
        "scraped_df": None,
        "ingested_docs": [],
        "crossretail_df": None,
        "enriched_df": None,
        "source_map": None,
        "generated_results": {},
        "qa_decisions": {},
        "research_results": {},
        "predict_keywords_raw": [],
        "shelf_scores": {},
        "cost_tracker": None,
        # Control Centre defaults
        "target_marketplace": ["amazon_au"],
        "primary_marketplace": "amazon_au",
        "brand_name": "",
        "brand_tone": "Professional",
        "brand_rules": "",
        "category": "Pet Supplies",
        "keyword_enhancement": True,
        "research_method": "AI Deep Research",
        "confidence_threshold": 0.7,
        "output_format": "Match input file format",
        "pxm_integration": False,
        "predict_integration": False,
        "shelf_integration": False,
        "model": "anthropic/claude-sonnet-4-6",
        "temperature": 0.1,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


init_session_state()

from core.theme import PATTERN_HERO_LOGO_HTML, inject_pattern_css, pattern_sidebar

inject_pattern_css()
pattern_sidebar()

# Main landing page — hero section with Pattern logo
st.markdown(PATTERN_HERO_LOGO_HTML, unsafe_allow_html=True)
st.title("PILO")
st.markdown(
    """
<div style="font-size:1.1em;color:#94A3B8;margin-bottom:24px;">
Pattern Intelligence Listing Optimisation — AI-powered product content engine
that generates optimised titles, bullet points, descriptions, keywords,
supplemental attributes, and special features for marketplace listings at scale.
</div>
""",
    unsafe_allow_html=True,
)

# V3 feature highlights
st.markdown(
    """<div style="background:#141B2D;border:1px solid #1E293B;border-radius:12px;
    padding:16px;margin-bottom:20px;">
    <div style="color:#7C3AED;font-weight:700;font-size:0.9em;margin-bottom:8px;">V3 FEATURES</div>
    <div style="color:#94A3B8;font-size:0.9em;">
    Marketplace-driven configuration · 7-step prompt chain · Multi-marketplace generation ·
    AI research with confidence scoring · 6-source enrichment with provenance tracking ·
    eBay + Google Shopping support · PXM / Predict / Shelf integration ·
    Match-input-format export · Cost dashboard
    </div></div>""",
    unsafe_allow_html=True,
)

# Workflow cards
st.markdown("### Workflow")

workflow_steps = [
    ("1", "Control Centre", "Configure marketplace, brand, AI model, and output format", "#7C3AED"),
    ("2", "Data Ingestion", "Upload feed, documents, cross-retail data, run AI research", "#6D28D9"),
    ("3", "Enrichment", "Merge all data layers with source provenance tracking", "#5B21B6"),
    ("4", "Content Generation", "Run 7-step prompt chain per SKU × marketplace", "#06B6D4"),
    ("5", "QA Review", "Multi-marketplace review with confidence badges", "#0891B2"),
    ("6", "Export", "Marketplace-formatted files, PXM JSON, comparison output", "#0E7490"),
    ("7", "Cost Dashboard", "API usage breakdown per marketplace, step, and model", "#155E75"),
]

cols = st.columns(4)
for i, (num, name, desc, color) in enumerate(workflow_steps):
    with cols[i % 4]:
        st.markdown(
            f"""<div style="background:#141B2D;border:1px solid #1E293B;border-radius:12px;
            padding:20px;margin-bottom:12px;border-left:4px solid {color};">
            <div style="color:{color};font-weight:700;font-size:0.85em;margin-bottom:4px;">STEP {num}</div>
            <div style="color:#E2E8F0;font-weight:600;margin-bottom:6px;">{name}</div>
            <div style="color:#94A3B8;font-size:0.9em;">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

# Quick stats if data is loaded
if st.session_state.get("feed_df") is not None:
    st.divider()
    st.subheader("Current Session")
    feed_df = st.session_state["feed_df"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SKUs Loaded", len(feed_df))
    with col2:
        from core.utils import calculate_completeness
        st.metric("Feed Completeness", f"{calculate_completeness(feed_df):.0f}%")
    with col3:
        gen_count = len(st.session_state.get("generated_results", {}))
        st.metric("Content Generated", gen_count)
    with col4:
        marketplaces = st.session_state.get("target_marketplace", [])
        st.metric("Marketplaces", len(marketplaces))
