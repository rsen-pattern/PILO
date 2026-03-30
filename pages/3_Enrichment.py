"""Page 3: Enrichment — Merge all data layers and review enriched dataset."""

import pandas as pd
import streamlit as st

from core.enrichment import get_enrichment_stats, merge_layers
from core.utils import calculate_completeness

st.set_page_config(page_title="PILO — Enrichment", page_icon="\U0001f9e9", layout="wide")
st.title("Enrichment")
st.caption("Merge all four data layers into a single enriched dataset.")

# Check prerequisites
if st.session_state.get("feed_df") is None:
    st.warning("Please complete Data Ingestion first — upload a product feed.")
    st.stop()

feed_df = st.session_state["feed_df"]
scraped_df = st.session_state.get("scraped_df")
crossretail_df = st.session_state.get("crossretail_df")

# Options
overwrite = st.checkbox(
    "Allow scraped/cross-retail data to overwrite existing values",
    value=False,
)

# Run enrichment
if st.button("Run Enrichment", type="primary") or st.session_state.get("enriched_df") is not None:
    if st.session_state.get("enriched_df") is None or st.button("Re-run Enrichment"):
        with st.spinner("Merging data layers..."):
            enriched_df, source_map = merge_layers(
                feed_df, scraped_df, crossretail_df, overwrite=overwrite
            )
            st.session_state["enriched_df"] = enriched_df
            st.session_state["source_map"] = source_map

    enriched_df = st.session_state["enriched_df"]
    source_map = st.session_state["source_map"]

    # Stats
    stats = get_enrichment_stats(feed_df, enriched_df, source_map)

    st.subheader("Enrichment Results")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Before", f"{stats['completeness_before']}%")
    with col2:
        st.metric("After", f"{stats['completeness_after']}%")
    with col3:
        st.metric("Improvement", f"+{stats['improvement']}pp")
    with col4:
        total_filled = stats["scraped_cells_filled"] + stats["crossretail_cells_filled"]
        st.metric("Cells Filled", total_filled)

    st.progress(stats["completeness_after"] / 100)
    st.caption(
        f"Completeness: {stats['completeness_before']}% \u2192 {stats['completeness_after']}% "
        f"(+{stats['improvement']} percentage points from enrichment)"
    )

    if stats["scraped_cells_filled"] > 0:
        st.caption(f"Scraped data filled {stats['scraped_cells_filled']} cells")
    if stats["crossretail_cells_filled"] > 0:
        st.caption(f"Cross-retail data filled {stats['crossretail_cells_filled']} cells")

    # Display enriched dataframe with colour coding
    st.subheader("Enriched Dataset")
    st.caption("Green = primary feed | Blue = scraped | Orange = cross-retail | Red = missing")

    # Build a styled view
    def style_cell(source_val):
        if source_val == "feed":
            return "background-color: #d4edda"  # green
        elif source_val == "scraped":
            return "background-color: #cce5ff"  # blue
        elif source_val == "crossretail":
            return "background-color: #fff3cd"  # orange
        else:
            return "background-color: #f8d7da"  # red/empty

    styled_df = enriched_df.style.apply(
        lambda col: source_map[col.name].map(style_cell) if col.name in source_map.columns else [""] * len(col),
        axis=0,
    )

    st.dataframe(styled_df, use_container_width=True, height=400)

    # Row detail viewer
    st.subheader("SKU Detail View")
    if "sku" in enriched_df.columns:
        selected_sku = st.selectbox("Select SKU", enriched_df["sku"].tolist())
        if selected_sku:
            row_idx = enriched_df[enriched_df["sku"] == selected_sku].index[0]
            row_data = enriched_df.loc[row_idx]
            row_sources = source_map.loc[row_idx]

            detail_data = []
            for col in enriched_df.columns:
                detail_data.append({
                    "Attribute": col,
                    "Value": str(row_data[col]) if pd.notna(row_data[col]) and str(row_data[col]).strip() else "",
                    "Source": row_sources[col] if row_sources[col] else "missing",
                })

            detail_df = pd.DataFrame(detail_data)
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # Actions
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Accept Enrichment", type="primary"):
            st.success("Enrichment accepted! Proceed to Content Generation.")

    with col2:
        csv = enriched_df.to_csv(index=False)
        st.download_button(
            "Export Enriched Data (CSV)",
            data=csv,
            file_name="pilo_enriched_data.csv",
            mime="text/csv",
        )
