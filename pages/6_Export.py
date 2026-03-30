"""Page 6: Export — Download marketplace-formatted output files."""

import streamlit as st

from core.theme import inject_pattern_css, pattern_sidebar
from core.exporter import (
    build_universal_excel,
    build_zip_export,
    df_to_excel_bytes,
    export_amazon,
    export_google_shopping,
    export_universal,
    export_walmart,
    export_woolworths,
)
from core.utils import calculate_completeness

st.set_page_config(page_title="PILO — Export", page_icon="\U0001f4e6", layout="wide")
inject_pattern_css()
pattern_sidebar()
st.title("Export")
st.caption("Download marketplace-formatted output files.")

# Check prerequisites
if not st.session_state.get("generated_results"):
    st.warning("Please complete Content Generation first.")
    st.stop()

enriched_df = st.session_state["enriched_df"]
generated_results = st.session_state["generated_results"]
qa_decisions = st.session_state.get("qa_decisions", {})
settings = st.session_state.get("settings", {})

# Count approved SKUs
approved_count = sum(
    1 for d in qa_decisions.values()
    if d.get("status") in ("approved", "approved_with_edits")
)

if approved_count == 0:
    st.warning("No SKUs have been approved in QA Review. Please approve at least one SKU before exporting.")
    st.info("You can use 'Approve All Remaining' in the QA Review page for quick approval.")
    st.stop()

st.metric("Approved SKUs for Export", approved_count)

# --- Marketplace Exports ---
st.divider()
st.subheader("Marketplace Exports")

target_marketplaces = settings.get("target_marketplace", [])
all_exports = {}

# Amazon exports
amazon_markets = [m for m in target_marketplaces if "Amazon" in m]
if amazon_markets:
    with st.container():
        st.markdown(f"### Amazon ({', '.join(amazon_markets)})")
        amazon_df = export_amazon(enriched_df, generated_results, qa_decisions)
        if not amazon_df.empty:
            st.caption(f"{len(amazon_df)} SKUs")
            st.dataframe(amazon_df.head(), use_container_width=True)
            excel_bytes = df_to_excel_bytes(amazon_df)
            st.download_button(
                "Download Amazon Flat File (XLSX)",
                data=excel_bytes,
                file_name="pilo_amazon_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            all_exports["pilo_amazon_export.xlsx"] = excel_bytes
        else:
            st.info("No approved SKUs for Amazon export.")

# Walmart export
if "Walmart US" in target_marketplaces:
    with st.container():
        st.markdown("### Walmart US")
        walmart_df = export_walmart(enriched_df, generated_results, qa_decisions)
        if not walmart_df.empty:
            st.caption(f"{len(walmart_df)} SKUs")
            st.dataframe(walmart_df.head(), use_container_width=True)
            excel_bytes = df_to_excel_bytes(walmart_df)
            st.download_button(
                "Download Walmart File (XLSX)",
                data=excel_bytes,
                file_name="pilo_walmart_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            all_exports["pilo_walmart_export.xlsx"] = excel_bytes
        else:
            st.info("No approved SKUs for Walmart export.")

# Woolworths export
if "Woolworths AU" in target_marketplaces:
    with st.container():
        st.markdown("### Woolworths AU")
        woolworths_df = export_woolworths(enriched_df, generated_results, qa_decisions)
        if not woolworths_df.empty:
            st.caption(f"{len(woolworths_df)} SKUs")
            st.dataframe(woolworths_df.head(), use_container_width=True)
            excel_bytes = df_to_excel_bytes(woolworths_df)
            st.download_button(
                "Download Woolworths File (XLSX)",
                data=excel_bytes,
                file_name="pilo_woolworths_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            all_exports["pilo_woolworths_export.xlsx"] = excel_bytes
        else:
            st.info("No approved SKUs for Woolworths export.")

# Google Shopping export
if "Google Shopping" in target_marketplaces:
    with st.container():
        st.markdown("### Google Shopping")
        google_df = export_google_shopping(enriched_df, generated_results, qa_decisions)
        if not google_df.empty:
            st.caption(f"{len(google_df)} SKUs")
            st.dataframe(google_df.head(), use_container_width=True)
            excel_bytes = df_to_excel_bytes(google_df)
            st.download_button(
                "Download Google Shopping File (XLSX)",
                data=excel_bytes,
                file_name="pilo_google_shopping_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            all_exports["pilo_google_shopping_export.xlsx"] = excel_bytes
        else:
            st.info("No approved SKUs for Google Shopping export.")

# Universal Export
st.divider()
st.markdown("### Universal Export")
st.caption("Full enriched dataset with all generated content, attributes, and QA status.")

universal_bytes = build_universal_excel(enriched_df, generated_results, qa_decisions)
st.download_button(
    "Download Universal Export (XLSX)",
    data=universal_bytes,
    file_name="pilo_universal_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
all_exports["pilo_universal_export.xlsx"] = universal_bytes

# Download All as ZIP
if len(all_exports) > 1:
    st.divider()
    zip_bytes = build_zip_export(all_exports)
    st.download_button(
        "Download All Exports (ZIP)",
        data=zip_bytes,
        file_name="pilo_all_exports.zip",
        mime="application/zip",
        type="primary",
    )

# --- Completeness Comparison ---
st.divider()
st.subheader("Impact Summary")

before_completeness = calculate_completeness(st.session_state.get("feed_df", enriched_df))

# Calculate after completeness including generated content
universal_df = export_universal(enriched_df, generated_results, qa_decisions)
if not universal_df.empty:
    after_completeness = calculate_completeness(universal_df)
else:
    after_completeness = before_completeness

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Before PILO", f"{before_completeness}%")

with col2:
    st.metric("After PILO", f"{after_completeness}%")

with col3:
    skus_processed = len(generated_results)
    time_manual = round(skus_processed * 15 / 60, 1)
    st.metric("Est. Manual Time Saved", f"{time_manual} hours")

st.progress(after_completeness / 100)
st.caption(f"Before PILO: {before_completeness}% \u2192 After PILO: {after_completeness}%")
