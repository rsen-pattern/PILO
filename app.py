"""PILO — Pattern Intelligence Listing Optimisation.

Main Streamlit entry point.
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
        "column_mapping": {},
        "scraped_df": None,
        "ingested_docs": [],
        "crossretail_df": None,
        "enriched_df": None,
        "source_map": None,
        "generated_results": {},
        "qa_decisions": {},
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


init_session_state()

from core.theme import inject_pattern_css, pattern_sidebar

inject_pattern_css()
pattern_sidebar()

# Main landing page
st.title("PILO")
st.markdown(
    """
<div style="font-size:1.1em;color:#94A3B8;margin-bottom:24px;">
Pattern Intelligence Listing Optimisation — AI-powered product content engine
that generates optimised titles, bullet points, descriptions, and supplemental
attributes for marketplace listings at scale.
</div>
""",
    unsafe_allow_html=True,
)

# Workflow cards
st.markdown("### Workflow")

workflow_steps = [
    ("1", "Settings", "Configure brand, category, marketplace, and API keys", "#7C3AED"),
    ("2", "Data Ingestion", "Upload your product feed and supplementary data", "#6D28D9"),
    ("3", "Enrichment", "Review merged and enriched data from all sources", "#5B21B6"),
    ("4", "Content Generation", "Run AI generation via Bifrost or Anthropic", "#06B6D4"),
    ("5", "QA Review", "Human review and edit generated content", "#0891B2"),
    ("6", "Export", "Download marketplace-formatted output files", "#0E7490"),
]

cols = st.columns(3)
for i, (num, name, desc, color) in enumerate(workflow_steps):
    with cols[i % 3]:
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
        st.metric("SKUs Generated", gen_count)
    with col4:
        approved = sum(
            1 for d in st.session_state.get("qa_decisions", {}).values()
            if d.get("status") in ("approved", "approved_with_edits")
        )
        st.metric("SKUs Approved", approved)
