"""Page 4: Content Generation — Run AI generation via Bifrost or Anthropic."""

import streamlit as st

from core.generator import run_generation
from core.theme import inject_pattern_css, pattern_sidebar
from core.utils import calculate_completeness

st.set_page_config(page_title="PILO — Content Generation", page_icon="\U0001f916", layout="wide")
inject_pattern_css()
pattern_sidebar()
st.title("Content Generation")
st.caption("Generate optimised product content via Bifrost gateway or direct Anthropic API.")

# Check prerequisites
if st.session_state.get("enriched_df") is None:
    st.warning("Please complete Enrichment first.")
    st.stop()

settings = st.session_state.get("settings", {})

if not settings.get("bifrost_api_key"):
    st.warning("Bifrost API key is not configured. Please set it in Settings.")
    st.stop()

enriched_df = st.session_state["enriched_df"]

# --- Pre-Generation Setup ---
st.subheader("Generation Setup")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("SKUs Available", len(enriched_df))
with col2:
    model_display = settings.get("model", "anthropic/claude-sonnet-4-6")
    if "/" in model_display:
        model_display = model_display.split("/")[1]
    st.metric("Model", model_display)
with col3:
    marketplaces = ", ".join(settings.get("target_marketplace", []))
    st.metric("Marketplaces", marketplaces or "Not set")

st.markdown(
    f'<div style="background:#141B2D;border:1px solid #1E293B;border-radius:8px;padding:12px 16px;'
    f'color:#94A3B8;font-size:0.9em;">API Backend: '
    f'<span style="color:#7C3AED;font-weight:600;">Bifrost Gateway</span> | '
    f'Model: <span style="color:#06B6D4;font-weight:600;">{settings.get("model", "N/A")}</span></div>',
    unsafe_allow_html=True,
)

# What to generate
st.subheader("Content to Generate")
col1, col2 = st.columns(2)
with col1:
    gen_title = st.checkbox("Optimised Title", value=True)
    gen_bullets = st.checkbox(f"Bullet Points ({settings.get('bullet_count', 5)})", value=True)
with col2:
    gen_description = st.checkbox("Product Description", value=True)
    gen_attributes = st.checkbox("Supplementary Attributes (fill missing)", value=True)

# SKU selection
st.subheader("SKU Selection")
sku_mode = st.radio(
    "Select SKUs to process",
    ["All SKUs", "Only SKUs below completeness threshold", "Specific SKUs"],
    horizontal=True,
)

sku_list = enriched_df["sku"].tolist() if "sku" in enriched_df.columns else []

selected_skus = sku_list
if sku_mode == "Only SKUs below completeness threshold":
    threshold = st.slider("Completeness threshold (%)", 0, 100, 70)
    selected_skus = []
    for _, row in enriched_df.iterrows():
        row_df = row.to_frame().T
        comp = calculate_completeness(row_df)
        if comp < threshold:
            selected_skus.append(row.get("sku"))
    st.info(f"{len(selected_skus)} SKUs below {threshold}% completeness")

elif sku_mode == "Specific SKUs":
    selected_skus = st.multiselect("Select SKUs", sku_list, default=sku_list)

# Cap at 50
MAX_SKUS = 50
if len(selected_skus) > MAX_SKUS:
    st.warning(
        f"Feed has {len(selected_skus)} SKUs. For MVP, processing is capped at {MAX_SKUS} SKUs "
        f"to manage API costs. The first {MAX_SKUS} SKUs will be processed."
    )
    selected_skus = selected_skus[:MAX_SKUS]

st.info(f"**{len(selected_skus)} SKUs** will be processed")

# --- Generate ---
st.divider()

if st.button("Generate Content", type="primary", disabled=len(selected_skus) == 0):
    generate_options = {
        "title": gen_title,
        "bullets": gen_bullets,
        "description": gen_description,
        "attributes": gen_attributes,
    }

    results, errors = run_generation(
        enriched_df, settings, selected_skus, generate_options
    )

    st.session_state["generated_results"] = results
    st.session_state["generation_errors"] = errors

    st.rerun()

# --- Post-Generation Summary ---
if st.session_state.get("generated_results"):
    results = st.session_state["generated_results"]
    errors = st.session_state.get("generation_errors", [])

    st.divider()
    st.subheader("Generation Summary")

    titles_count = sum(1 for r in results.values() if r.get("title"))
    bullets_count = sum(1 for r in results.values() if r.get("bullets"))
    desc_count = sum(1 for r in results.values() if r.get("description"))
    attrs_filled = sum(
        sum(1 for v in r.get("attributes", {}).values() if v and v != "NEEDS_REVIEW")
        for r in results.values()
    )
    needs_review = sum(
        sum(1 for v in r.get("attributes", {}).values() if v == "NEEDS_REVIEW")
        for r in results.values()
    )
    time_saved_hours = round(len(results) * 15 / 60, 1)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("SKUs Processed", len(results))
        st.metric("Titles Generated", titles_count)
    with col2:
        st.metric("Bullet Sets Generated", bullets_count)
        st.metric("Descriptions Generated", desc_count)
    with col3:
        st.metric("Attributes Filled", attrs_filled)
        st.metric("NEEDS_REVIEW Items", needs_review)
    with col4:
        st.metric("API Errors", len(errors))
        st.metric("Est. Time Saved", f"{time_saved_hours} hrs")

    if errors:
        with st.expander("Errors"):
            for err in errors:
                st.error(err)

    st.success("Content generation complete! Proceed to QA Review.")
