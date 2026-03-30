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

# Sidebar — workflow progress
with st.sidebar:
    st.title("PILO")
    st.caption("Pattern Intelligence Listing Optimisation")
    st.divider()

    steps = [
        ("Settings", st.session_state.get("settings", {}).get("brand_name")),
        ("Data Ingestion", st.session_state.get("feed_df") is not None),
        ("Enrichment", st.session_state.get("enriched_df") is not None),
        ("Content Generation", bool(st.session_state.get("generated_results"))),
        ("QA Review", bool(st.session_state.get("qa_decisions"))),
        ("Export", False),
    ]

    st.subheader("Workflow Progress")
    for step_name, completed in steps:
        icon = "\u2705" if completed else "\u2b1c"
        st.markdown(f"{icon} {step_name}")

    st.divider()
    st.caption("Navigate using the pages in the sidebar above.")

# Main landing page
st.title("PILO — Pattern Intelligence Listing Optimisation")
st.markdown(
    """
**AI-powered product content engine** that takes a raw product feed and generates
optimised titles, bullet points, descriptions, and supplemental attributes for
marketplace listings at scale.

### Workflow

1. **Settings** — Configure brand, category, marketplace, and API keys
2. **Data Ingestion** — Upload your product feed and supplementary data
3. **Enrichment** — Review merged and enriched data
4. **Content Generation** — Run AI generation with Claude
5. **QA Review** — Human review and edit generated content
6. **Export** — Download marketplace-formatted output files

Use the sidebar to navigate between pages.
"""
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
