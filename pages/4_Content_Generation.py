"""Page 4: Content Generation — Multi-marketplace prompt chain with progress matrix."""

import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
import pandas as pd

from core.generator import run_generation, load_cached_run
from core.validator import validate_feed_preflight
from core.cost_tracker import estimate_run_cost
from config.marketplace_configs import MARKETPLACE_CONFIGS, MARKETPLACE_KEY_BY_NAME

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Content Generation", "AI-powered multi-marketplace content creation")

enriched_df = st.session_state.get("enriched_df")
if enriched_df is None:
    st.markdown(
        """
        <div style="
            background: rgba(239,68,68,0.08);
            border: 1px solid rgba(239,68,68,0.3);
            border-left: 4px solid #EF4444;
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 24px;
        ">
            <div style="color:#EF4444;font-weight:600;font-size:1em;margin-bottom:6px;">
                ⚠ Step not ready
            </div>
            <div style="color:#E2E8F0;font-size:0.95em;margin-bottom:16px;">
                No enriched data available. Run the Enrichment merge before generating content.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/3_Enrichment.py", label="← Go to Enrichment", icon="🔄")
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

# ── Resume previous run ──
_last_cache = st.session_state.get("last_run_cache_file", "")
if _last_cache and __import__("os").path.exists(_last_cache):
    if st.button("Resume previous run", key="resume_run"):
        st.session_state["generated_results"] = load_cached_run(_last_cache)
        st.success(f"Loaded {len(st.session_state['generated_results'])} cached results.")
        st.rerun()

# ── Pre-flight validation ──
preflight = validate_feed_preflight(enriched_df, marketplace_keys)
for msg in preflight["errors"]:
    st.error(f"Feed error: {msg}")
for msg in preflight["warnings"]:
    st.warning(f"Feed warning: {msg}")
if preflight["passed"]:
    st.success("Feed validated — ready to generate")
else:
    st.stop()

conf_thresh = st.session_state.get("confidence_threshold", 0.7)
low_conf = sum(
    1 for r in st.session_state.get("research_results", {}).values()
    if r.get("confidence", 1.0) < conf_thresh
)
if low_conf > 0:
    st.info(
        f"{low_conf} SKU(s) have AI research below the {conf_thresh:.0%} confidence threshold. "
        f"Research will be flagged in prompts — feed data will take priority."
    )

# ── Cost estimate (only shown when preflight passed) ──
est = estimate_run_cost(
    sku_count=len(selected_skus),
    marketplace_keys=marketplace_keys,
    model=model,
    keyword_enhancement=keyword_enh,
    generate_titles=st.session_state.get("generate_titles", True),
    generate_bullets=st.session_state.get("generate_bullets", True),
    generate_descriptions=st.session_state.get("generate_descriptions", True),
    generate_attributes=st.session_state.get("generate_attributes", True),
)
with st.container(border=True):
    st.caption(
        f"Estimated cost: **${est['estimated_cost_usd']:.4f}** | "
        f"{est['total_api_calls']} API calls | "
        f"**${est['cost_per_sku']:.4f}** per SKU"
    )
    _brows = [
        {"Marketplace": MARKETPLACE_CONFIGS.get(k, {}).get("name", k),
         "Steps": v["steps"], "API Calls": v["api_calls"], "Est. Cost": f"${v['cost']:.4f}"}
        for k, v in est["breakdown"].items()
    ]
    st.dataframe(pd.DataFrame(_brows), width="stretch", hide_index=True)

_est_cost = est["estimated_cost_usd"]
_confirmed = True
if _est_cost > 20.0:
    st.error(f"Large run — estimated cost ${_est_cost:.2f} exceeds $20.00. Confirm to proceed.")
    _confirmed = st.checkbox("I confirm I want to proceed with this run", key="cost_confirm")
elif _est_cost > 5.0:
    st.warning(f"Large run — review estimate before proceeding (${_est_cost:.2f})")

# ── Generate button ──
if st.button("Generate Content", type="primary", width="stretch",
             disabled=len(selected_skus) == 0 or not _confirmed):

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
        st.dataframe(pd.DataFrame(matrix_data), width="stretch", hide_index=True)

    # Sample preview
    st.subheader("Content Preview")
    preview_keys = list(results.keys())[:5]
    for key in preview_keys:
        sku, mp = key
        r = results[key]
        mp_name = MARKETPLACE_CONFIGS.get(mp, {}).get("name", mp)
        with st.expander(f"{sku} — {mp_name}"):
            title_text = r.get("title") or ""
            if title_text:
                st.write(f"**Title** ({len(title_text)} chars): {title_text}")
            if r.get("bullets"):
                st.write("**Bullets:**")
                for i, b in enumerate(r["bullets"], 1):
                    st.write(f"  {i}. {b}")
            desc_text = r.get("description") or ""
            if desc_text:
                st.write(f"**Description** ({len(desc_text)} chars):")
                st.caption(desc_text[:300] + "..." if len(desc_text) > 300 else desc_text)
            if r.get("attributes"):
                st.write(f"**Attributes:** {len(r['attributes'])} filled")
            if r.get("errors"):
                for err in r["errors"]:
                    st.error(f"Step '{err['step']}': {err['error']}")

    st.divider()
    col_stat, col_nav = st.columns([3, 1])
    with col_stat:
        st.success(f"Content generated for {len(results)} combinations.")
    with col_nav:
        st.page_link("pages/5_QA_Review.py", label="Next: QA Review →", icon="✏️")
