"""Page 5: QA Review — Human review and edit of generated content."""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="PILO — QA Review", page_icon="\u2705", layout="wide")
st.title("QA Review")
st.caption("Review, edit, and approve generated content before export.")

# Check prerequisites
if not st.session_state.get("generated_results"):
    st.warning("Please complete Content Generation first.")
    st.stop()

enriched_df = st.session_state.get("enriched_df")
results = st.session_state["generated_results"]
qa_decisions = st.session_state.get("qa_decisions", {})
settings = st.session_state.get("settings", {})

sku_list = list(results.keys())

if not sku_list:
    st.warning("No generated content to review.")
    st.stop()

# --- Batch Actions ---
st.subheader("Batch Actions")
col1, col2, col3 = st.columns(3)

with col1:
    reviewed = sum(1 for d in qa_decisions.values() if d.get("status") != "pending")
    st.metric("Reviewed", f"{reviewed}/{len(sku_list)}")

with col2:
    if st.button("Approve All Remaining"):
        for sku in sku_list:
            if sku not in qa_decisions or qa_decisions[sku].get("status") == "pending":
                qa_decisions[sku] = {"status": "approved"}
        st.session_state["qa_decisions"] = qa_decisions
        st.rerun()

with col3:
    # Export QA report
    qa_rows = []
    for sku in sku_list:
        d = qa_decisions.get(sku, {})
        qa_rows.append({"sku": sku, "status": d.get("status", "pending"), "notes": d.get("notes", "")})
    qa_csv = pd.DataFrame(qa_rows).to_csv(index=False)
    st.download_button("Export QA Report", data=qa_csv, file_name="pilo_qa_report.csv", mime="text/csv")

st.divider()

# --- SKU Navigation ---
col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])

# Initialise current index
if "qa_sku_index" not in st.session_state:
    st.session_state["qa_sku_index"] = 0

with col_nav1:
    if st.button("\u25c0 Previous") and st.session_state["qa_sku_index"] > 0:
        st.session_state["qa_sku_index"] -= 1
        st.rerun()

with col_nav2:
    selected_idx = st.selectbox(
        "Select SKU",
        range(len(sku_list)),
        index=st.session_state["qa_sku_index"],
        format_func=lambda i: f"{sku_list[i]} ({qa_decisions.get(sku_list[i], {}).get('status', 'pending')})",
    )
    if selected_idx != st.session_state["qa_sku_index"]:
        st.session_state["qa_sku_index"] = selected_idx
        st.rerun()

with col_nav3:
    if st.button("Next \u25b6") and st.session_state["qa_sku_index"] < len(sku_list) - 1:
        st.session_state["qa_sku_index"] += 1
        st.rerun()

current_sku = sku_list[st.session_state["qa_sku_index"]]
generated = results.get(current_sku, {})
current_decision = qa_decisions.get(current_sku, {})

# Get original data
original = {}
if enriched_df is not None and "sku" in enriched_df.columns:
    mask = enriched_df["sku"] == current_sku
    if mask.any():
        original = enriched_df[mask].iloc[0].to_dict()
        for k, v in original.items():
            if pd.isna(v):
                original[k] = ""

# Use edited content if previously saved
if current_decision.get("status") == "approved_with_edits" and "edited" in current_decision:
    generated = current_decision["edited"]

st.subheader(f"SKU: {current_sku}")
status = current_decision.get("status", "pending")
status_colors = {"approved": "green", "approved_with_edits": "green", "rejected": "red", "skipped": "gray", "pending": "orange"}
st.markdown(f"Status: :{status_colors.get(status, 'orange')}[**{status.upper()}**]")

# --- Title ---
st.markdown("---")
st.markdown("### Title")
col_orig, col_gen = st.columns(2)

title_limit = settings.get("title_char_limit", 200)

with col_orig:
    st.markdown("**Original**")
    st.text_area("Original Title", value=str(original.get("title", "")), height=80, disabled=True, key="orig_title", label_visibility="collapsed")

with col_gen:
    st.markdown("**Generated**")
    gen_title = st.text_area("Generated Title", value=generated.get("title", ""), height=80, key="gen_title", label_visibility="collapsed")
    char_count = len(gen_title)
    color = "green" if char_count <= title_limit else "red"
    st.markdown(f":{color}[{char_count}/{title_limit} characters]")

# --- Bullet Points ---
st.markdown("---")
st.markdown("### Bullet Points")

bullet_limit = settings.get("bullet_char_limit", 500)
bullet_count = settings.get("bullet_count", 5)
gen_bullets = generated.get("bullets", [])

for i in range(bullet_count):
    col_orig, col_gen = st.columns(2)
    orig_bullet = str(original.get(f"bullet_{i+1}", ""))
    gen_bullet = gen_bullets[i] if i < len(gen_bullets) else ""

    with col_orig:
        if i == 0:
            st.markdown("**Original**")
        st.text_area(
            f"Original Bullet {i+1}",
            value=orig_bullet,
            height=60,
            disabled=True,
            key=f"orig_bullet_{i}",
            label_visibility="collapsed",
        )

    with col_gen:
        if i == 0:
            st.markdown("**Generated**")
        edited_bullet = st.text_area(
            f"Generated Bullet {i+1}",
            value=gen_bullet,
            height=60,
            key=f"gen_bullet_{i}",
            label_visibility="collapsed",
        )
        bc = len(edited_bullet)
        bcolor = "green" if bc <= bullet_limit else "red"
        st.markdown(f":{bcolor}[{bc}/{bullet_limit}]")

# --- Description ---
st.markdown("---")
st.markdown("### Description")

desc_limit = settings.get("description_char_limit", 2000)
col_orig, col_gen = st.columns(2)

with col_orig:
    st.markdown("**Original**")
    st.text_area("Original Desc", value=str(original.get("description", "")), height=200, disabled=True, key="orig_desc", label_visibility="collapsed")

with col_gen:
    st.markdown("**Generated**")
    gen_desc = st.text_area("Generated Desc", value=generated.get("description", ""), height=200, key="gen_desc", label_visibility="collapsed")
    dc = len(gen_desc)
    dcolor = "green" if dc <= desc_limit else "red"
    st.markdown(f":{dcolor}[{dc}/{desc_limit} characters]")

# --- Supplementary Attributes ---
st.markdown("---")
st.markdown("### Supplementary Attributes")

gen_attrs = generated.get("attributes", {})
if gen_attrs:
    attr_rows = []
    for attr_name, gen_val in gen_attrs.items():
        orig_val = str(original.get(attr_name, ""))
        status_icon = "\u2705" if gen_val and gen_val != "NEEDS_REVIEW" else "\u26a0\ufe0f" if gen_val == "NEEDS_REVIEW" else ""
        attr_rows.append({
            "Attribute": attr_name,
            "Original Value": orig_val,
            "Generated Value": gen_val,
            "Status": status_icon,
        })

    attr_df = pd.DataFrame(attr_rows)

    # Highlight NEEDS_REVIEW
    def highlight_needs_review(row):
        if row["Generated Value"] == "NEEDS_REVIEW":
            return ["background-color: #fff3cd"] * len(row)
        return [""] * len(row)

    styled = attr_df.style.apply(highlight_needs_review, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Editable attributes
    st.caption("Edit attributes below if needed:")
    edited_attrs = {}
    cols = st.columns(2)
    for j, (attr_name, gen_val) in enumerate(gen_attrs.items()):
        with cols[j % 2]:
            edited_attrs[attr_name] = st.text_input(
                attr_name,
                value=gen_val,
                key=f"attr_{current_sku}_{attr_name}",
            )
else:
    st.info("No supplementary attributes were generated for this SKU.")
    edited_attrs = {}

# --- QA Actions ---
st.markdown("---")
st.subheader("Actions")

reviewer_notes = st.text_input("Reviewer notes (optional)", value=current_decision.get("notes", ""), key="reviewer_notes")

col1, col2, col3, col4 = st.columns(4)

# Collect edited content
def get_edited_content():
    edited_bullets = []
    for i in range(bullet_count):
        edited_bullets.append(st.session_state.get(f"gen_bullet_{i}", ""))
    return {
        "title": st.session_state.get("gen_title", ""),
        "bullets": edited_bullets,
        "description": st.session_state.get("gen_desc", ""),
        "attributes": edited_attrs,
    }

with col1:
    if st.button("Approve All", type="primary"):
        qa_decisions[current_sku] = {"status": "approved", "notes": reviewer_notes}
        st.session_state["qa_decisions"] = qa_decisions
        st.success("Approved!")
        st.rerun()

with col2:
    if st.button("Approve with Edits"):
        qa_decisions[current_sku] = {
            "status": "approved_with_edits",
            "notes": reviewer_notes,
            "edited": get_edited_content(),
        }
        st.session_state["qa_decisions"] = qa_decisions
        st.success("Approved with edits!")
        st.rerun()

with col3:
    if st.button("Reject \u2014 Regenerate"):
        qa_decisions[current_sku] = {"status": "rejected", "notes": reviewer_notes}
        st.session_state["qa_decisions"] = qa_decisions
        st.warning("Rejected. SKU queued for regeneration.")
        st.rerun()

with col4:
    if st.button("Skip"):
        qa_decisions[current_sku] = {"status": "skipped", "notes": reviewer_notes}
        st.session_state["qa_decisions"] = qa_decisions
        st.info("Skipped.")
        st.rerun()
