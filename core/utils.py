"""Shared utility functions for PILO."""

import json
import re

import pandas as pd


def calculate_completeness(df, exclude_cols=None):
    """Calculate attribute completeness as percentage of non-empty cells.

    Args:
        df: DataFrame to analyze.
        exclude_cols: Columns to exclude from completeness calculation.

    Returns:
        Float between 0 and 100 representing completeness percentage.
    """
    if exclude_cols is None:
        exclude_cols = ["sku", "asin", "price", "image_url"]

    attr_cols = [c for c in df.columns if c not in exclude_cols]
    if not attr_cols:
        return 0.0

    attr_df = df[attr_cols]
    total_cells = attr_df.size
    if total_cells == 0:
        return 0.0

    non_empty = attr_df.apply(
        lambda col: col.astype(str).str.strip().replace("", pd.NA).notna().sum()
    ).sum()
    return round((non_empty / total_cells) * 100, 1)


def parse_json_response(text):
    """Parse JSON from Claude's response, handling markdown code fences."""
    # Strip markdown code fences if present
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            return json.loads(match.group())
        raise


def get_missing_attributes(row, exclude_cols=None):
    """Get list of attribute columns that are empty for a given row."""
    if exclude_cols is None:
        exclude_cols = ["sku", "asin", "price", "image_url", "title", "brand",
                        "product_type", "bullet_1", "bullet_2", "bullet_3",
                        "bullet_4", "bullet_5", "description"]

    missing = []
    for col, val in row.items():
        if col in exclude_cols:
            continue
        if pd.isna(val) or str(val).strip() == "":
            missing.append(col)
    return missing


def row_to_dict(row):
    """Convert a DataFrame row to a clean dict, replacing NaN/empty with empty string."""
    d = {}
    for k, v in row.items():
        if pd.isna(v):
            d[k] = ""
        else:
            d[k] = v
    return d
