"""Page 5: QA Review — Multi-marketplace tabs with confidence badges and source provenance."""

import pandas as pd
import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from config.marketplace_configs import MARKETPLACE_CONFIGS

inject_pattern_css()
pattern_sidebar()
pattern_page_header("QA Review", "Human review, edit, and approval workflow")

enriched_df = st.session_state.get("enriched_df")
generated_results = st.session_state.get("generated_results", {})

if enriched_df is None or not generated_results:
    st.warning("No generated content to review. Complete Content Generation first.")
    st.stop()

marketplace_keys = st.session_state.get("target_marketplace", ["amazon_au"])
research_results = st.session_state.get("research_results", {})
shelf_scores = st.session_state.get("shelf_scores", {})
qa_decisions = st.session_state.get("qa_decisions", {})

# ── Get SKUs that have generated content ──
skus_with_content = sorted(set(sku for (sku, _) in generated_results.keys()))
if not skus_with_content:
    st.info("No content has been generated yet.")
    st.stop()

# ── QA summary ──
total_items = len(skus_with_content) * len(marketplace_keys)
approved_count = 0
rejected_count = 0
pending_count = 0
for sku in skus_with_content:
    for mp in marketplace_keys:
        dec = qa_decisions.get(sku, {}).get(mp, {})
        status = dec.get("status", "pending")
        if status in ("approved", "approved_with_edits"):
            approved_count += 1
        elif status == "rejected":
            rejected_count += 1
        else:
            pending_count += 1

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total", total_items)
with col2:
    st.metric("Approved", approved_count)
with col3:
    st.metric("Rejected", rejected_count)
with col4:
    st.metric("Pending", pending_count)

st.divider()

# ── Batch actions ──
col1, col2 = st.columns(2)
with col1:
    if st.button("Approve All Remaining", key="approve_all"):
        for sku in skus_with_content:
            if sku not in qa_decisions:
                qa_decisions[sku] = {}
            for mp in marketplace_keys:
                if qa_decisions[sku].get(mp, {}).get("status", "pending") == "pending":
                    qa_decisions[sku][mp] = {"status": "approved", "notes": "Batch approved"}
        st.session_state["qa_decisions"] = qa_decisions
        st.rerun()

# ── SKU selector with navigation arrows ──
st.subheader("Review Products")
current_sku_idx = st.session_state.get("qa_sku_idx", 0)
if current_sku_idx >= len(skus_with_content):
    current_sku_idx = 0

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 6, 2])
with nav_col1:
    if st.button("< Prev", key="qa_prev", disabled=current_sku_idx <= 0):
        st.session_state["qa_sku_idx"] = current_sku_idx - 1
        st.rerun()
with nav_col2:
    if st.button("Next >", key="qa_next", disabled=current_sku_idx >= len(skus_with_content) - 1):
        st.session_state["qa_sku_idx"] = current_sku_idx + 1
        st.rerun()
with nav_col3:
    selected_sku = st.selectbox(
        "Select SKU",
        skus_with_content,
        index=min(current_sku_idx, len(skus_with_content) - 1),
        key="qa_sku_select",
        label_visibility="collapsed",
    )
    st.session_state["qa_sku_idx"] = skus_with_content.index(selected_sku)
with nav_col4:
    st.caption(f"{current_sku_idx + 1} / {len(skus_with_content)}")

# ── Confidence badge for this SKU ──
sku_research = research_results.get(selected_sku, {})
if sku_research:
    conf = sku_research.get("confidence", 0)
    badge = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.5 else "🔴"
    st.info(f"AI Research Confidence: {badge} {conf:.2f}")

# Shelf scores overlay
sku_shelf = shelf_scores.get(selected_sku, {})
if sku_shelf:
    shelf_cols = st.columns(4)
    for i, (metric, val) in enumerate(sku_shelf.items()):
        with shelf_cols[i % 4]:
            st.caption(f"Shelf {metric}: {val}")

# ── Multi-marketplace tabs ──
if len(marketplace_keys) > 1:
    tab_labels = [MARKETPLACE_CONFIGS.get(k, {}).get("name", k) for k in marketplace_keys]
    tabs = st.tabs(tab_labels)
else:
    tabs = [st.container()]

for tab_idx, tab in enumerate(tabs):
    mp_key = marketplace_keys[tab_idx]
    mp_name = MARKETPLACE_CONFIGS.get(mp_key, {}).get("name", mp_key)
    mp_cfg = MARKETPLACE_CONFIGS.get(mp_key, {})

    with tab:
        key = (selected_sku, mp_key)
        gen = generated_results.get(key, {})

        if not gen:
            st.info(f"No content generated for {mp_name}.")
            continue

        # Get original data
        orig_row = enriched_df[enriched_df["sku"] == selected_sku].iloc[0] if "sku" in enriched_df.columns else None

        # ── Title ──
        st.markdown("**Title**")
        title_limit = mp_cfg.get("title", {}).get("char_limit", 200)
        orig_title = orig_row["title"] if orig_row is not None and "title" in orig_row.index else ""
        if orig_title:
            st.caption(f"Original: {orig_title}")

        edited_title = st.text_area(
            f"Generated Title ({len(gen.get('title', ''))} / {title_limit} chars)",
            value=gen.get("title", ""),
            key=f"title_{selected_sku}_{mp_key}",
            height=80,
        )
        chars = len(edited_title)
        if chars > title_limit:
            st.warning(f"Title exceeds limit: {chars}/{title_limit}")

        # ── Bullets ──
        bullet_count = mp_cfg.get("bullets", {}).get("count", 0)
        bullets = gen.get("bullets", [])
        edited_bullets = []

        if bullet_count > 0:
            st.markdown("**Bullet Points**")
            bullet_limit = mp_cfg.get("bullets", {}).get("char_limit", 500)
            guides = mp_cfg.get("bullets", {}).get("guides", {})

            for i in range(bullet_count):
                guide = guides.get(i + 1, "")
                orig_bullet = ""
                if orig_row is not None and f"bullet_{i+1}" in orig_row.index:
                    orig_bullet = str(orig_row[f"bullet_{i+1}"])
                    if orig_bullet in ("nan", ""):
                        orig_bullet = ""

                label = f"Bullet {i+1}" + (f" — {guide}" if guide else "")
                current_val = bullets[i] if i < len(bullets) else ""
                edited = st.text_area(
                    label,
                    value=current_val,
                    key=f"bullet_{i+1}_{selected_sku}_{mp_key}",
                    height=60,
                )
                edited_bullets.append(edited)

        # ── Description ──
        st.markdown("**Description**")
        desc_limit = mp_cfg.get("description", {}).get("char_limit", 2000)
        edited_desc = st.text_area(
            f"Generated Description ({len(gen.get('description', ''))} / {desc_limit} chars)",
            value=gen.get("description", ""),
            key=f"desc_{selected_sku}_{mp_key}",
            height=150,
        )
        if len(edited_desc) > desc_limit:
            st.warning(f"Description exceeds limit: {len(edited_desc)}/{desc_limit}")

        # ── Attributes ──
        attrs = gen.get("attributes", {})
        if attrs:
            st.markdown("**Attributes**")
            edited_attrs = {}
            attr_cols = st.columns(2)
            for i, (attr_key, attr_val) in enumerate(attrs.items()):
                with attr_cols[i % 2]:
                    display_val = str(attr_val) if attr_val else ""
                    needs_review = display_val == "NEEDS_REVIEW"
                    if needs_review:
                        st.warning(f"{attr_key}: NEEDS REVIEW")
                    edited_val = st.text_input(
                        attr_key, value=display_val,
                        key=f"attr_{attr_key}_{selected_sku}_{mp_key}",
                    )
                    edited_attrs[attr_key] = edited_val

        # ── Special Features ──
        special_features = gen.get("special_features", [])
        edited_features = []
        if special_features:
            st.markdown("**Special Features**")
            for i, feat in enumerate(special_features):
                edited = st.text_input(
                    f"Feature {i+1}", value=feat,
                    key=f"feat_{i+1}_{selected_sku}_{mp_key}",
                )
                edited_features.append(edited)

        # ── Search Terms ──
        if gen.get("search_terms"):
            st.markdown("**Search Terms**")
            edited_search = st.text_area(
                "Search Terms",
                value=gen.get("search_terms", ""),
                key=f"search_{selected_sku}_{mp_key}",
                height=60,
            )

        # ── QA Decision ──
        st.divider()
        decision_col1, decision_col2 = st.columns([2, 1])

        with decision_col1:
            decision = st.radio(
                f"Decision for {selected_sku} / {mp_name}",
                ["Approve", "Approve with Edits", "Reject", "Skip"],
                index=0, horizontal=True,
                key=f"decision_{selected_sku}_{mp_key}",
            )

        with decision_col2:
            notes = st.text_input(
                "Reviewer Notes",
                key=f"notes_{selected_sku}_{mp_key}",
            )

        if st.button(f"Save Decision", key=f"save_{selected_sku}_{mp_key}"):
            if selected_sku not in qa_decisions:
                qa_decisions[selected_sku] = {}

            status_map = {
                "Approve": "approved",
                "Approve with Edits": "approved_with_edits",
                "Reject": "rejected",
                "Skip": "pending",
            }

            decision_data = {
                "status": status_map[decision],
                "notes": notes,
            }

            # Save edited content if approved with edits
            if decision == "Approve with Edits":
                decision_data["edited"] = {
                    "title": edited_title,
                    "bullets": edited_bullets,
                    "description": edited_desc,
                    "attributes": edited_attrs if attrs else {},
                    "special_features": edited_features,
                }

            qa_decisions[selected_sku][mp_key] = decision_data
            st.session_state["qa_decisions"] = qa_decisions
            st.success(f"Saved: {selected_sku} / {mp_name} → {decision}")

# ── Navigation ──
st.divider()
if approved_count > 0:
    st.success(f"{approved_count} items approved. Proceed to Export.")
