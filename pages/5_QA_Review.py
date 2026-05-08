"""Page 5: QA Review — Multi-marketplace tabs with confidence badges and source provenance."""

from datetime import datetime

import pandas as pd
import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from config.marketplace_configs import MARKETPLACE_CONFIGS
from core.validator import validate_sku_content, calculate_cdq_score
from core.variant_checker import find_variant_groups, check_variant_consistency

inject_pattern_css()
pattern_sidebar()
pattern_page_header("QA Review", "Human review, edit, and approval workflow")

enriched_df = st.session_state.get("enriched_df")
generated_results = st.session_state.get("generated_results", {})
source_map = st.session_state.get("source_map")  # may be None if enrichment skipped

if enriched_df is None or not generated_results:
    st.warning("No generated content to review. Complete Content Generation first.")
    st.stop()

_SOURCE_BADGES = {
    "feed":        "🟢 Primary Feed",
    "document":    "🔵 Client Doc",
    "scraped":     "🟣 Web Scraped",
    "crossretail": "🟠 Cross-Retail",
    "ai_research": "🟡 AI Research",
    "external":    "🔴 External Scrape",
}


def get_field_source(sku, field_name, source_map, enriched_df) -> str:
    """Return the source label for a field, or empty string if unknown."""
    if source_map is None or enriched_df is None:
        return ""
    try:
        if "sku" not in enriched_df.columns or field_name not in source_map.columns:
            return ""
        mask = enriched_df["sku"] == sku
        if not mask.any():
            return ""
        row_idx = enriched_df.index[mask][0]
        return str(source_map.at[row_idx, field_name])
    except Exception:
        return ""


def _source_badge(source: str, confidence=None) -> str:
    if source == "ai_research" and confidence is not None:
        return f"🟡 AI Research (confidence: {confidence:.2f})"
    return _SOURCE_BADGES.get(source, "⬜ Unknown source")


marketplace_keys = st.session_state.get("target_marketplace", ["amazon_au"])
research_results = st.session_state.get("research_results", {})
shelf_scores = st.session_state.get("shelf_scores", {})
qa_decisions = st.session_state.get("qa_decisions", {})

# Pre-compute variant groups once per page load
_variant_groups = find_variant_groups(enriched_df)
# Build reverse map: sku → parent_id
_sku_to_variant_parent = {
    sku: parent for parent, skus in _variant_groups.items() for sku in skus
}

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
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("Approve All Remaining", key="approve_all", use_container_width=True):
        for sku in skus_with_content:
            if sku not in qa_decisions:
                qa_decisions[sku] = {}
            for mp in marketplace_keys:
                if qa_decisions[sku].get(mp, {}).get("status", "pending") == "pending":
                    qa_decisions[sku][mp] = {"status": "approved", "notes": "Batch approved"}
        st.session_state["qa_decisions"] = qa_decisions
        st.rerun()

with col2:
    if st.button("Clear All Decisions", key="clear_all", use_container_width=True):
        st.session_state["qa_decisions"] = {}
        st.rerun()

# ── Reviewer name ──
st.text_input("Reviewer Name", key="reviewer_name",
              value=st.session_state.get("reviewer_name", ""),
              placeholder="Enter your name for the audit trail")

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
research_col, cdq_col = st.columns(2)
with research_col:
    sku_research = research_results.get(selected_sku, {})
    if sku_research:
        conf = sku_research.get("confidence", 0)
        badge = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.5 else "🔴"
        st.info(f"AI Research Confidence: {badge} {conf:.2f}")

with cdq_col:
    # We calculate CDQ for the primary marketplace for now
    primary_mp = st.session_state.get("primary_marketplace", "amazon_au")
    gen_primary = generated_results.get((selected_sku, primary_mp), {})
    if gen_primary:
        flags = validate_sku_content(gen_primary, st.session_state.get("category", "Other"), st.session_state.get("settings", {}))
        score = calculate_cdq_score(flags)
        badge = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
        st.info(f"CDQ Score: {badge} {score}/100")

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

        # ── Variant inconsistency warnings ──
        _parent = _sku_to_variant_parent.get(selected_sku)
        if _parent:
            _vgroup = _variant_groups[_parent]
            _inconsistencies = check_variant_consistency(
                _vgroup, generated_results, mp_key
            )
            for inc in _inconsistencies:
                vals_str = " | ".join(f"{s}: {v}" for s, v in inc["values"].items())
                st.warning(
                    f"⚠️ Variant inconsistency: '{inc['field']}' differs across variants — {vals_str}"
                )

        # Get original data
        orig_row = enriched_df[enriched_df["sku"] == selected_sku].iloc[0] if "sku" in enriched_df.columns else None

        # ── Title (Side-by-Side) ──
        st.markdown("### Title")
        title_limit = mp_cfg.get("title", {}).get("char_limit", 200)
        orig_title = str(orig_row["title"]) if orig_row is not None and "title" in orig_row.index else ""

        col_orig, col_pilo = st.columns(2)
        with col_orig:
            st.caption("Original Feed")
            st.info(orig_title if orig_title and orig_title != "nan" else "(Empty)")
        with col_pilo:
            st.caption(f"PILO Generated ({len(gen.get('title', ''))} / {title_limit} chars)")
            _src = get_field_source(selected_sku, "title", source_map, enriched_df)
            _conf = research_results.get(selected_sku, {}).get("confidence")
            st.caption(_source_badge(_src, _conf if _src == "ai_research" else None))

            # Mobile truncation indicator
            title_val = gen.get('title', '')
            safe_zone = title_val[:80]
            truncated = title_val[80:]
            if truncated:
                st.caption("Mobile Safe Zone (80 chars):")
                st.code(f"{safe_zone}[TRUNCATED]", language=None)

            edited_title = st.text_area(
                "Title Edit",
                value=gen.get("title", ""),
                key=f"title_{selected_sku}_{mp_key}",
                height=100,
                label_visibility="collapsed"
            )
        chars = len(edited_title)
        if chars > title_limit:
            st.warning(f"Title exceeds limit: {chars}/{title_limit}")

        # ── Bullets (Side-by-Side) ──
        bullet_count = mp_cfg.get("bullets", {}).get("count", 0)
        bullets = gen.get("bullets", [])
        edited_bullets = []

        if bullet_count > 0:
            st.markdown("### Bullet Points")
            _bsrc = get_field_source(selected_sku, "bullet_1", source_map, enriched_df)
            _bconf = research_results.get(selected_sku, {}).get("confidence")
            st.caption(_source_badge(_bsrc, _bconf if _bsrc == "ai_research" else None))
            bullet_limit = mp_cfg.get("bullets", {}).get("char_limit", 500)
            guides = mp_cfg.get("bullets", {}).get("guides", {})

            for i in range(bullet_count):
                guide = guides.get(i + 1, "")
                orig_bullet = ""
                if orig_row is not None and f"bullet_{i+1}" in orig_row.index:
                    orig_bullet = str(orig_row[f"bullet_{i+1}"])
                    if orig_bullet in ("nan", ""):
                        orig_bullet = ""
                elif orig_row is not None and f"bullet_point_{i+1}" in orig_row.index:
                    orig_bullet = str(orig_row[f"bullet_point_{i+1}"])
                    if orig_bullet in ("nan", ""):
                        orig_bullet = ""

                st.markdown(f"**Bullet {i+1}**" + (f" — *{guide}*" if guide else ""))
                col_orig_b, col_pilo_b = st.columns(2)
                with col_orig_b:
                    st.info(orig_bullet if orig_bullet else "(Empty)")
                with col_pilo_b:
                    current_val = bullets[i] if i < len(bullets) else ""
                    edited = st.text_area(
                        f"Bullet {i+1} Edit",
                        value=current_val,
                        key=f"bullet_{i+1}_{selected_sku}_{mp_key}",
                        height=80,
                        label_visibility="collapsed"
                    )
                    edited_bullets.append(edited)

        # ── Description (Side-by-Side) ──
        st.markdown("### Description")
        desc_limit = mp_cfg.get("description", {}).get("char_limit", 2000)
        orig_desc = str(orig_row["description"]) if orig_row is not None and "description" in orig_row.index else ""

        col_orig_d, col_pilo_d = st.columns(2)
        with col_orig_d:
            st.caption("Original Feed")
            st.info(orig_desc if orig_desc and orig_desc != "nan" else "(Empty)")
        with col_pilo_d:
            st.caption(f"PILO Generated ({len(gen.get('description', ''))} / {desc_limit} chars)")
            _dsrc = get_field_source(selected_sku, "description", source_map, enriched_df)
            _dconf = research_results.get(selected_sku, {}).get("confidence")
            st.caption(_source_badge(_dsrc, _dconf if _dsrc == "ai_research" else None))
            edited_desc = st.text_area(
                "Description Edit",
                value=gen.get("description", ""),
                key=f"desc_{selected_sku}_{mp_key}",
                height=200,
                label_visibility="collapsed"
            )
        if len(edited_desc) > desc_limit:
            st.warning(f"Description exceeds limit: {len(edited_desc)}/{desc_limit}")

        # ── Attributes (With Flags) ──
        attrs = gen.get("attributes", {})
        if attrs:
            st.markdown("### Attributes")

            # Show CDQ flags for this specific marketplace
            sku_flags = validate_sku_content(gen, st.session_state.get("category", "Other"), st.session_state.get("settings", {}))
            attr_flags = [f for f in sku_flags if f["field"].startswith("attr_") or f["field"].startswith("bullet_")]
            if attr_flags:
                for f in attr_flags:
                    if f["level"] == "error":
                        st.error(f["message"])
                    else:
                        st.warning(f["message"])

            edited_attrs = {}

            # Identify which attributes might be "thin" or conflicting
            # For now, we flag empty or "NEEDS_REVIEW"
            attr_cols = st.columns(3)
            for i, (attr_key, attr_val) in enumerate(attrs.items()):
                with attr_cols[i % 3]:
                    _asrc = get_field_source(selected_sku, attr_key, source_map, enriched_df)
                    st.caption(_source_badge(_asrc))
                    display_val = str(attr_val) if attr_val and str(attr_val) != "nan" else ""

                    # Confidence Flag
                    is_thin = display_val == ""
                    is_review = display_val == "NEEDS_REVIEW"

                    label = attr_key
                    if is_thin:
                        label += " ⚠️ (Thin)"
                    if is_review:
                        label += " 🔴 (Review)"

                    edited_val = st.text_input(
                        label,
                        value=display_val,
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
                "reviewer": st.session_state.get("reviewer_name", "Unknown") or "Unknown",
                "timestamp": datetime.now().isoformat(),
                "char_counts": {
                    "title": len(edited_title),
                    "description": len(edited_desc),
                    "bullets": [len(b) for b in edited_bullets],
                },
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
