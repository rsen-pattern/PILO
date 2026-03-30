"""Page 4: Content Generation — Multi-marketplace prompt chain with progress matrix."""

import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from core.generator import run_generation
from config.marketplace_configs import MARKETPLACE_CONFIGS, MARKETPLACE_KEY_BY_NAME

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Content Generation", "AI-powered multi-marketplace content creation")

enriched_df = st.session_state.get("enriched_df")
if enriched_df is None:
    st.warning("No enriched data available. Complete the Enrichment step first.")
    st.stop()

# ── Configuration summary ──
marketplace_keys = st.session_state.get("target_marketplace", ["amazon_au"])
marketplace_names = [MARKETPLACE_CONFIGS.get(k, {}).get("name", k) for k in marketplace_keys]
model = st.session_state.get("model", "anthropic/claude-sonnet-4-6")
keyword_enh = st.session_state.get("keyword_enhancement", True)

st.subheader("Generation Configuration")
col1, col2, col3 = st.columns(3)
with col1:
    st.write(f"**Model:** {model}")
    st.write(f"**Temperature:** {st.session_state.get('temperature', 0.1)}")
with col2:
    st.write(f"**Marketplaces:** {', '.join(marketplace_names)}")
    st.write(f"**Keyword Enhancement:** {'On' if keyword_enh else 'Off'}")
with col3:
    st.write(f"**Products:** {len(enriched_df)}")
    total_runs = len(enriched_df) * len(marketplace_keys)
    st.write(f"**Total Chain Runs:** {total_runs}")

st.divider()

# ── SKU selection ──
st.subheader("SKU Selection")
selection_mode = st.radio(
    "Select SKUs to generate",
    ["All SKUs", "Below completeness threshold", "Specific SKUs"],
    horizontal=True, key="sku_sel_mode",
)

selected_skus = []
if "sku" in enriched_df.columns:
    all_skus = enriched_df["sku"].tolist()

    if selection_mode == "All SKUs":
        selected_skus = all_skus

    elif selection_mode == "Below completeness threshold":
        from core.utils import calculate_completeness
        threshold = st.slider("Completeness Threshold (%)", 0, 100, 80, key="comp_thresh")
        for sku in all_skus:
            row = enriched_df[enriched_df["sku"] == sku].iloc[0]
            filled = sum(1 for v in row if str(v).strip() not in ("", "nan", "None"))
            pct = (filled / len(row)) * 100
            if pct < threshold:
                selected_skus.append(sku)
        st.write(f"**{len(selected_skus)}** SKUs below {threshold}% completeness")

    elif selection_mode == "Specific SKUs":
        selected_skus = st.multiselect("Select SKUs", all_skus, default=all_skus[:5], key="sku_multi")

# Cap at 50
if len(selected_skus) > 50:
    st.warning(f"Capping at 50 SKUs (from {len(selected_skus)}). Select fewer for larger batches.")
    selected_skus = selected_skus[:50]

st.write(f"**{len(selected_skus)} SKUs** x **{len(marketplace_keys)} marketplaces** = "
         f"**{len(selected_skus) * len(marketplace_keys)} chain runs**")

# ── Chain steps preview ──
with st.expander("Prompt Chain Steps"):
    for mp_key in marketplace_keys:
        cfg = MARKETPLACE_CONFIGS.get(mp_key, {})
        steps = []
        if keyword_enh:
            steps.append("1. Keyword Generation")
        steps.append(f"{'2' if keyword_enh else '1'}. Title Generation (≤{cfg.get('title', {}).get('char_limit', 200)} chars)")
        bc = cfg.get("bullets", {}).get("count", 0)
        if bc > 0:
            steps.append(f"{'3' if keyword_enh else '2'}. Bullet Points (x{bc})")
        steps.append(f"{'4' if keyword_enh else '3'}. Description (≤{cfg.get('description', {}).get('char_limit', 2000)} chars)")
        steps.append(f"{'5' if keyword_enh else '4'}. Attributes")
        if cfg.get("special_features_count", 0) > 0:
            steps.append(f"{'6' if keyword_enh else '5'}. Special Features (x{cfg['special_features_count']})")
        steps.append(f"{'7' if keyword_enh else '6'}. Item Type Classification")
        st.write(f"**{cfg.get('name', mp_key)}:**")
        for s in steps:
            st.write(f"  {s}")

st.divider()

# ── Generate button ──
if st.button("Generate Content", type="primary", use_container_width=True,
             disabled=len(selected_skus) == 0):

    settings = dict(st.session_state)
    results, errors, cost_tracker = run_generation(
        enriched_df=enriched_df,
        settings=settings,
        selected_skus=selected_skus,
    )

    st.session_state["generated_results"] = results
    st.session_state["generation_errors"] = errors
    st.session_state["cost_tracker"] = cost_tracker

    st.success(f"Generated content for {len(results)} SKU×marketplace combinations.")
    if errors:
        with st.expander(f"{len(errors)} Errors"):
            for err in errors:
                st.error(err)

# ── Results preview ──
results = st.session_state.get("generated_results", {})
if results:
    st.divider()
    st.subheader("Generation Results")

    # Progress matrix: SKUs down, marketplaces across
    if len(marketplace_keys) > 1:
        st.caption("Progress Matrix: SKUs × Marketplaces")
        matrix_data = []
        for sku in selected_skus if selected_skus else []:
            row_data = {"SKU": sku}
            for mp_key in marketplace_keys:
                key = (sku, mp_key)
                if key in results:
                    r = results[key]
                    steps = len(r.get("steps_completed", []))
                    errs = len(r.get("errors", []))
                    if errs > 0:
                        row_data[mp_key] = f"⚠️ {steps} steps ({errs} errors)"
                    else:
                        row_data[mp_key] = f"✅ {steps} steps"
                else:
                    row_data[mp_key] = "—"
            matrix_data.append(row_data)

        import pandas as pd
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

    # Sample preview
    st.subheader("Content Preview")
    preview_keys = list(results.keys())[:5]
    for key in preview_keys:
        sku, mp = key
        r = results[key]
        mp_name = MARKETPLACE_CONFIGS.get(mp, {}).get("name", mp)
        with st.expander(f"{sku} — {mp_name}"):
            if r.get("title"):
                st.write(f"**Title** ({len(r['title'])} chars): {r['title']}")
            if r.get("bullets"):
                st.write("**Bullets:**")
                for i, b in enumerate(r["bullets"], 1):
                    st.write(f"  {i}. {b}")
            if r.get("description"):
                st.write(f"**Description** ({len(r['description'])} chars):")
                st.caption(r["description"][:300] + "..." if len(r["description"]) > 300 else r["description"])
            if r.get("attributes"):
                st.write(f"**Attributes:** {len(r['attributes'])} filled")
            if r.get("errors"):
                for err in r["errors"]:
                    st.error(f"Step '{err['step']}': {err['error']}")

    st.divider()
    st.success(f"Content generated! Proceed to QA Review.")
