"""Page 7: Cost Dashboard — API cost tracking and breakdown."""

import pandas as pd
import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from config.marketplace_configs import MARKETPLACE_CONFIGS

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Cost Dashboard", "API usage and cost breakdown")

generated_results = st.session_state.get("generated_results", {})
cost_tracker = st.session_state.get("cost_tracker")

# ── Calculate costs from generated results (estimate if tracker unavailable) ──
model = st.session_state.get("model", "anthropic/claude-sonnet-4-6")
marketplace_keys = st.session_state.get("target_marketplace", ["amazon_au"])

if not generated_results:
    st.info("No generation data available. Run Content Generation to see cost breakdowns.")
    st.stop()

# Estimate costs from results
from config.model_registry import BIFROST_MODELS
model_info = BIFROST_MODELS.get(model, {})
input_cost_per_m = model_info.get("input_cost", 3.0)
output_cost_per_m = model_info.get("output_cost", 15.0)

# Approximate token usage per chain run
EST_INPUT_TOKENS = 2000   # avg input per step
EST_OUTPUT_TOKENS = 800   # avg output per step
keyword_enh = st.session_state.get("keyword_enhancement", True)

# Count steps per marketplace
step_counts = {}
for mp_key in marketplace_keys:
    cfg = MARKETPLACE_CONFIGS.get(mp_key, {})
    steps = 2  # title + description (always)
    if keyword_enh:
        steps += 1  # keywords
    if cfg.get("bullets", {}).get("count", 0) > 0:
        steps += 1  # bullets
    steps += 1  # attributes
    if cfg.get("special_features_count", 0) > 0:
        steps += 1  # special features
    steps += 1  # item type
    step_counts[mp_key] = steps

# Group results by SKU and marketplace
skus_done = set()
mp_calls = {mp: 0 for mp in marketplace_keys}
total_calls = 0

for (sku, mp_key), result in generated_results.items():
    skus_done.add(sku)
    steps_done = len(result.get("steps_completed", []))
    mp_calls[mp_key] = mp_calls.get(mp_key, 0) + steps_done
    total_calls += steps_done

total_input = total_calls * EST_INPUT_TOKENS
total_output = total_calls * EST_OUTPUT_TOKENS
est_input_cost = (total_input / 1_000_000) * input_cost_per_m
est_output_cost = (total_output / 1_000_000) * output_cost_per_m
est_total = est_input_cost + est_output_cost

# ═══════════════════════════════════════════════════════════════════════════
# Overview
# ═══════════════════════════════════════════════════════════════════════════
st.header("Cost Overview")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Estimated Total Cost", f"${est_total:.4f}")
with col2:
    st.metric("API Calls", total_calls)
with col3:
    cost_per_product = est_total / len(skus_done) if skus_done else 0
    st.metric("Cost per Product", f"${cost_per_product:.4f}")
with col4:
    st.metric("Products × Marketplaces", f"{len(skus_done)} × {len(marketplace_keys)}")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# Cost by Marketplace
# ═══════════════════════════════════════════════════════════════════════════
st.header("Cost by Marketplace")

mp_data = []
for mp_key in marketplace_keys:
    mp_name = MARKETPLACE_CONFIGS.get(mp_key, {}).get("name", mp_key)
    calls = mp_calls.get(mp_key, 0)
    mp_input = calls * EST_INPUT_TOKENS
    mp_output = calls * EST_OUTPUT_TOKENS
    mp_cost = ((mp_input / 1_000_000) * input_cost_per_m +
               (mp_output / 1_000_000) * output_cost_per_m)
    mp_data.append({
        "Marketplace": mp_name,
        "API Calls": calls,
        "Est. Input Tokens": f"{mp_input:,}",
        "Est. Output Tokens": f"{mp_output:,}",
        "Est. Cost": f"${mp_cost:.4f}",
    })

st.dataframe(pd.DataFrame(mp_data), use_container_width=True, hide_index=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# Cost by Step
# ═══════════════════════════════════════════════════════════════════════════
st.header("Cost by Chain Step")

step_labels = {
    "keywords": "1. Keyword Generation",
    "title": "2. Title Generation",
    "bullets": "3. Bullet Points",
    "description": "4. Description",
    "attributes": "5. Attributes",
    "special_features": "6. Special Features",
    "item_type": "7. Item Type",
}

step_data = []
for step_key, label in step_labels.items():
    count = 0
    for (_, _mp), result in generated_results.items():
        if step_key in result.get("steps_completed", []):
            count += 1
    if count > 0:
        step_cost = ((count * EST_INPUT_TOKENS / 1_000_000) * input_cost_per_m +
                     (count * EST_OUTPUT_TOKENS / 1_000_000) * output_cost_per_m)
        step_data.append({
            "Step": label,
            "Calls": count,
            "Est. Cost": f"${step_cost:.4f}",
        })

st.dataframe(pd.DataFrame(step_data), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# Keyword Enhancement Cost Toggle
# ═══════════════════════════════════════════════════════════════════════════
st.divider()
st.header("Keyword Enhancement Impact")

kw_calls = sum(
    1 for (_, _), r in generated_results.items()
    if "keywords" in r.get("steps_completed", [])
)
kw_cost = ((kw_calls * EST_INPUT_TOKENS / 1_000_000) * input_cost_per_m +
           (kw_calls * EST_OUTPUT_TOKENS / 1_000_000) * output_cost_per_m)

non_kw_cost = est_total - kw_cost

col1, col2 = st.columns(2)
with col1:
    st.metric("With Keyword Enhancement", f"${est_total:.4f}",
              help=f"Includes {kw_calls} keyword generation calls")
with col2:
    st.metric("Without Keyword Enhancement", f"${non_kw_cost:.4f}",
              delta=f"-${kw_cost:.4f}")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# Model Info
# ═══════════════════════════════════════════════════════════════════════════
st.header("Model Details")
st.write(f"**Model:** {model}")
st.write(f"**Provider:** {model_info.get('provider', 'Unknown')}")
st.write(f"**Input Cost:** ${input_cost_per_m}/1M tokens")
st.write(f"**Output Cost:** ${output_cost_per_m}/1M tokens")
st.write(f"**Context Window:** {model_info.get('context_window', 0):,} tokens")

st.caption("Note: Costs are estimates based on average token usage per chain step. "
           "Actual costs depend on product complexity and content length.")
