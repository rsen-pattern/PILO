"""Page 3: Enrichment — 6-source merge with confidence and provenance tracking."""

import pandas as pd
import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from core.enrichment import merge_layers, get_enrichment_stats, SOURCE_COLOURS, style_source_cell
from core.utils import calculate_completeness

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Enrichment", "Merge all data layers and review enriched dataset")

feed_df = st.session_state.get("feed_df")
if feed_df is None:
    st.warning("No product feed loaded. Go to Data Ingestion first.")
    st.stop()

# ── Gather all data layers ──
scraped_df = st.session_state.get("scraped_df")
crossretail_df = st.session_state.get("crossretail_df")

# Build document data dict from ingested docs
document_data = None
ingested_docs = st.session_state.get("ingested_docs", [])
# (Document text doesn't directly map to fields — used in generation prompts instead)

# Build AI research data dict
ai_research_data = {}
research_results = st.session_state.get("research_results", {})
for sku, res in research_results.items():
    if not isinstance(res, dict):
        continue
    research = res.get("research", {})
    if isinstance(research, dict):
        flat = {}
        if research.get("materials"):
            flat["material"] = research["materials"]
        if research.get("target_audience"):
            flat["target_audience"] = research["target_audience"]
        if research.get("dimensions"):
            flat["dimensions"] = research["dimensions"]
        if research.get("product_summary"):
            flat["research_summary"] = research["product_summary"]
        if flat:
            ai_research_data[sku] = flat

# ── Run merge ──
if st.button("Run Enrichment Merge", type="primary"):
    enriched_df, source_map = merge_layers(
        feed_df=feed_df,
        scraped_df=scraped_df,
        crossretail_df=crossretail_df,
        ai_research_data=ai_research_data if ai_research_data else None,
    )
    st.session_state["enriched_df"] = enriched_df
    st.session_state["source_map"] = source_map
    st.success("Enrichment complete!")

enriched_df = st.session_state.get("enriched_df")
source_map = st.session_state.get("source_map")

if enriched_df is None:
    st.info("Click 'Run Enrichment Merge' to combine all data layers.")
    st.stop()

# ── Statistics ──
stats = get_enrichment_stats(feed_df, enriched_df, source_map)

st.subheader("Enrichment Impact")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Before", f"{stats['completeness_before']:.0f}%")
with col2:
    st.metric("After", f"{stats['completeness_after']:.0f}%",
              delta=f"+{stats['improvement']:.1f}%")
with col3:
    st.metric("Products", len(enriched_df))

# Source breakdown
st.subheader("Data Sources")
source_cols = st.columns(len(SOURCE_COLOURS))
for i, (source, info) in enumerate(SOURCE_COLOURS.items()):
    count = stats.get(f"{source}_cells", 0)
    with source_cols[i]:
        colour_dot = f"<span style='color:{info['fg']};font-size:1.2em;'>●</span>"
        st.markdown(f"{colour_dot} **{info['label']}**", unsafe_allow_html=True)
        st.caption(f"{count} cells")

empty_count = stats.get("empty_cells", 0)
if empty_count > 0:
    st.caption(f"⬜ Still empty: {empty_count} cells")

st.divider()

# ── Confidence indicators for AI-researched products ──
if research_results:
    st.subheader("AI Research Confidence")
    conf_threshold = st.session_state.get("confidence_threshold", 0.7)

    conf_data = []
    for sku, res in research_results.items():
        conf = res.get("confidence", 0)
        badge = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.5 else "🔴"
        flagged = "Yes" if conf < conf_threshold else ""
        conf_data.append({
            "SKU": sku,
            "Confidence": f"{badge} {conf:.2f}",
            "Score": conf,
            "Flagged": flagged,
        })

    conf_df = pd.DataFrame(conf_data)
    st.dataframe(
        conf_df[["SKU", "Confidence", "Flagged"]],
        use_container_width=True, hide_index=True,
    )

st.divider()

# ── Enriched data table with source colour coding ──
st.subheader("Enriched Dataset")

# Apply source-based styling
def style_enriched_table(df, source_map):
    """Apply background colours based on data source."""
    styled = pd.DataFrame("", index=df.index, columns=df.columns)
    for col in df.columns:
        if col in source_map.columns:
            for idx in df.index:
                source = source_map.at[idx, col] if idx in source_map.index else ""
                styled.at[idx, col] = style_source_cell(source)
    return styled

# Show a subset for performance
display_cols = [c for c in enriched_df.columns if not c.startswith("_")]
display_df = enriched_df[display_cols].head(50)
source_subset = source_map[[c for c in display_cols if c in source_map.columns]].head(50)

styled = display_df.style.apply(
    lambda _: style_enriched_table(display_df, source_subset),
    axis=None,
)
st.dataframe(styled, use_container_width=True, height=500)

# ── Legend ──
with st.expander("Colour Legend"):
    for source, info in SOURCE_COLOURS.items():
        st.markdown(
            f"<span style='background:{info['bg']};color:{info['fg']};padding:2px 8px;border-radius:4px;'>"
            f"{info['label']}</span> — {info['trust']} trust",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<span style='background:#1a1a2e;color:#6b7280;padding:2px 8px;border-radius:4px;'>"
        "Empty</span> — Still missing",
        unsafe_allow_html=True,
    )

# ── SKU detail view ──
st.divider()
st.subheader("SKU Detail View")
if "sku" in enriched_df.columns:
    skus = enriched_df["sku"].tolist()
    selected_sku = st.selectbox("Select SKU", skus, key="enrich_sku_detail")
    if selected_sku:
        row_mask = enriched_df["sku"] == selected_sku
        if row_mask.any():
            row = enriched_df[row_mask].iloc[0]
            src_row = source_map[row_mask].iloc[0] if row_mask.any() else None

            detail_data = []
            for col in enriched_df.columns:
                val = row[col]
                source = src_row[col] if src_row is not None and col in source_map.columns else ""
                info = SOURCE_COLOURS.get(source, {"label": "Empty" if not source else source})
                detail_data.append({
                    "Field": col,
                    "Value": str(val) if pd.notna(val) and str(val).strip() not in ("", "nan") else "",
                    "Source": info.get("label", source),
                })
            st.dataframe(pd.DataFrame(detail_data), use_container_width=True, hide_index=True)

            # Show research confidence if available
            sku_research = research_results.get(selected_sku)
            if sku_research:
                conf = sku_research.get("confidence", 0)
                badge = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.5 else "🔴"
                st.info(f"AI Research Confidence: {badge} {conf:.2f}")
                if sku_research.get("research", {}).get("product_summary"):
                    st.caption(sku_research["research"]["product_summary"])

st.divider()
st.success(f"Enriched dataset ready: {len(enriched_df)} products at {stats['completeness_after']:.0f}% completeness. Proceed to Content Generation.")
