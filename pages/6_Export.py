"""Page 6: Export — Multi-format marketplace export with PXM and comparison output."""

import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from core.exporter import (
    build_marketplace_export, build_match_input_export,
    build_universal_export, build_comparison_output,
    build_multi_tab_excel, build_pxm_export_json, build_zip_export,
    df_to_excel_bytes,
)
from core.utils import row_to_dict, calculate_completeness
from config.marketplace_configs import MARKETPLACE_CONFIGS

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Export", "Download marketplace-formatted output files")

enriched_df = st.session_state.get("enriched_df")
generated_results = st.session_state.get("generated_results", {})
qa_decisions = st.session_state.get("qa_decisions", {})

if enriched_df is None or not generated_results:
    st.warning("No content to export. Complete QA Review first.")
    st.stop()

marketplace_keys = st.session_state.get("target_marketplace", ["amazon_au"])
output_format = st.session_state.get("output_format", "Match input file format")

# ── Summary ──
st.subheader("Export Summary")
total_approved = 0
for sku, decisions in qa_decisions.items():
    if isinstance(decisions, dict):
        for mp, dec in decisions.items():
            if isinstance(dec, dict) and dec.get("status") in ("approved", "approved_with_edits"):
                total_approved += 1

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Approved Items", total_approved)
with col2:
    st.metric("Marketplaces", len(marketplace_keys))
with col3:
    completeness_before = calculate_completeness(st.session_state.get("feed_df", enriched_df))
    completeness_after = calculate_completeness(enriched_df)
    st.metric("Completeness", f"{completeness_before:.0f}% → {completeness_after:.0f}%")

if total_approved == 0:
    st.warning("No approved items to export. Go back to QA Review to approve content.")
    st.stop()

# ── Time saved estimate ──
time_saved = total_approved * 15  # 15 min per SKU manual estimate
st.info(f"Estimated time saved: **{time_saved} minutes** ({time_saved / 60:.1f} hours) "
        f"vs manual content creation at 15 min/SKU")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# Marketplace-specific exports
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("Marketplace Exports")

for mp_key in marketplace_keys:
    mp_name = MARKETPLACE_CONFIGS.get(mp_key, {}).get("name", mp_key)

    with st.expander(f"{mp_name}", expanded=True):
        if output_format == "Match input file format":
            original_df = st.session_state.get("feed_df")
            export_df = build_match_input_export(
                original_df, enriched_df, generated_results,
                qa_decisions, mp_key,
            )
        else:
            export_df = build_marketplace_export(
                enriched_df, generated_results, qa_decisions, mp_key,
            )

        if export_df is not None and not export_df.empty:
            st.write(f"{len(export_df)} rows")
            st.dataframe(export_df.head(5), use_container_width=True)
            st.download_button(
                f"Download {mp_name} Export (.xlsx)",
                data=df_to_excel_bytes(export_df),
                file_name=f"pilo_export_{mp_key}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{mp_key}",
            )
        else:
            st.info(f"No approved content for {mp_name}.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# Universal & comparison exports
# ═══════════════════════════════════════════════════════════════════════════
st.subheader("Additional Exports")

tab_univ, tab_comp, tab_multi, tab_pxm, tab_zip = st.tabs([
    "Universal Export", "Comparison", "Multi-Tab Excel", "PXM JSON", "ZIP Archive",
])

with tab_univ:
    universal_df = build_universal_export(enriched_df, generated_results, qa_decisions, marketplace_keys)
    if not universal_df.empty:
        st.write(f"{len(universal_df)} rows × {len(universal_df.columns)} columns")
        st.dataframe(universal_df.head(5), use_container_width=True)
        st.download_button(
            "Download Universal Export (.xlsx)",
            data=df_to_excel_bytes(universal_df),
            file_name="pilo_universal_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_universal",
        )

with tab_comp:
    comp_df = build_comparison_output(enriched_df, generated_results, qa_decisions, marketplace_keys)
    if not comp_df.empty:
        st.write(f"{len(comp_df)} field changes tracked")
        st.dataframe(comp_df.head(10), use_container_width=True)
        st.download_button(
            "Download Comparison (.xlsx)",
            data=df_to_excel_bytes(comp_df),
            file_name="pilo_comparison.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_comp",
        )

with tab_multi:
    multi_bytes = build_multi_tab_excel(enriched_df, generated_results, qa_decisions, marketplace_keys)
    st.download_button(
        "Download Multi-Tab Excel (.xlsx)",
        data=multi_bytes,
        file_name="pilo_full_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_multi",
    )

with tab_pxm:
    if st.session_state.get("pxm_integration"):
        product_data = {}
        if "sku" in enriched_df.columns:
            for _, row in enriched_df.iterrows():
                product_data[row["sku"]] = row_to_dict(row)
        pxm_json = build_pxm_export_json(generated_results, product_data, marketplace_keys)
        st.code(pxm_json[:2000] + "..." if len(pxm_json) > 2000 else pxm_json, language="json")
        st.download_button(
            "Download PXM JSON",
            data=pxm_json,
            file_name="pilo_pxm_export.json",
            mime="application/json",
            key="dl_pxm",
        )
    else:
        st.info("Enable PXM integration in Control Centre to use this export.")

with tab_zip:
    st.caption("Download all exports as a single ZIP archive.")
    if st.button("Build ZIP Archive", key="build_zip"):
        exports = {}

        # Marketplace exports
        for mp_key in marketplace_keys:
            if output_format == "Match input file format":
                exp_df = build_match_input_export(
                    st.session_state.get("feed_df"), enriched_df,
                    generated_results, qa_decisions, mp_key,
                )
            else:
                exp_df = build_marketplace_export(
                    enriched_df, generated_results, qa_decisions, mp_key,
                )
            if exp_df is not None and not exp_df.empty:
                exports[f"{mp_key}_export.xlsx"] = df_to_excel_bytes(exp_df)

        # Multi-tab
        exports["full_export.xlsx"] = multi_bytes

        # Comparison
        if not comp_df.empty:
            exports["comparison.xlsx"] = df_to_excel_bytes(comp_df)

        # PXM
        if st.session_state.get("pxm_integration"):
            exports["pxm_export.json"] = pxm_json.encode("utf-8")

        zip_bytes = build_zip_export(exports)
        st.download_button(
            "Download ZIP Archive",
            data=zip_bytes,
            file_name="pilo_exports.zip",
            mime="application/zip",
            key="dl_zip",
        )
