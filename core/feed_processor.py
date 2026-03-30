"""Feed upload, parsing, and column mapping utilities."""

import pandas as pd
import streamlit as st


STANDARD_FIELDS = [
    "sku",
    "asin",
    "title",
    "brand",
    "bullet_1",
    "bullet_2",
    "bullet_3",
    "bullet_4",
    "bullet_5",
    "description",
    "product_type",
    "price",
    "image_url",
]


def load_feed(uploaded_file):
    """Load a CSV or Excel file into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {name}")


def display_feed_preview(df):
    """Display feed summary and preview."""
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)

    st.subheader("Columns")
    col_info = pd.DataFrame({
        "Column": df.columns,
        "Type": [str(df[c].dtype) for c in df.columns],
        "Non-null Count": [df[c].notna().sum() for c in df.columns],
    })
    st.dataframe(col_info, use_container_width=True, hide_index=True)


def build_column_mapping_ui(df):
    """Show selectboxes for mapping uploaded columns to standard fields.

    Returns a dict mapping standard field names to source column names.
    """
    st.subheader("Column Mapping")
    st.caption("Map your feed columns to PILO's standard fields.")

    source_cols = ["(not mapped)"] + list(df.columns)
    mapping = {}

    cols_per_row = 3
    for i in range(0, len(STANDARD_FIELDS), cols_per_row):
        row_fields = STANDARD_FIELDS[i : i + cols_per_row]
        cols = st.columns(len(row_fields))
        for col_ui, field in zip(cols, row_fields):
            with col_ui:
                # Try to auto-detect matching columns
                default_idx = 0
                for j, src in enumerate(source_cols):
                    if src.lower().replace(" ", "_") == field:
                        default_idx = j
                        break
                    if field in src.lower().replace(" ", "_"):
                        default_idx = j
                        break

                chosen = st.selectbox(
                    field,
                    source_cols,
                    index=default_idx,
                    key=f"map_{field}",
                )
                if chosen != "(not mapped)":
                    mapping[field] = chosen

    return mapping


def apply_column_mapping(df, mapping):
    """Rename columns in the dataframe according to the mapping.

    Unmapped columns are kept as-is (treated as extra attributes).
    """
    reverse_map = {v: k for k, v in mapping.items()}
    renamed = df.rename(columns=reverse_map)
    return renamed
