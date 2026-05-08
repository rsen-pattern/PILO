"""
PILO Deep Enrichment Engine — Part 2.
Handles deep attribute mapping and justification.
"""

import os
import pandas as pd
import json

MASTER_ENRICHMENT_PROMPT = """
Role:
You are a Senior Amazon Data Architect and CDQ (Composite Data Quality) specialist. Your goal is to extract every possible product attribute from raw source data and map them to Amazon’s valid values schema.

Task:
Analyze the provided Product Summary and the Valid Values Reference. Extract and structure all available metadata to populate the Product Enrichment tab.

Inputs:
Product Summary: {product_summary}
Valid Values Reference: {valid_values_ref}

Instructions & Constraints:
1. Strict Mapping: Only use values that exist in the "Valid Values" list. If a specific value isn't found, use the closest logical match or leave it blank—never hallucinate.
2. Supplement Discovery: Look specifically for the "hidden" 150+ attributes (e.g., item_form, active_ingredients, target_gender, is_expiration_dated_product, material_features).
3. Justification: For every attribute filled, include a brief "Source Note" (e.g., "Extracted from scraped brand website" or "Mapped from Ingredients list").
4. Formatting: Output the data as a structured list with justification.

Output Format:
Return JSON with a key "enrichment_details" containing a list of objects:
{{
  "attribute": "Attribute Name",
  "value": "Mapped Valid Value",
  "source": "Context/Justification"
}}
"""

def get_valid_values(category):
    """Pre-Filter step: Load relevant valid values for the category."""
    csv_path = os.path.join("config", "valid_values.csv")
    if not os.path.exists(csv_path):
        return ""

    try:
        df = pd.read_csv(csv_path)
        # Map app category names to valid values categories if needed
        # e.g. "Pet Supplies" -> "Pet Supplies"
        filtered_df = df[df["category"] == category]
        if filtered_df.empty:
            # Fallback or broad match
            return ""

        values_str = ""
        for attr in filtered_df["attribute"].unique():
            vals = filtered_df[filtered_df["attribute"] == attr]["valid_value"].tolist()
            values_str += f"- {attr}: {', '.join(vals)}\n"
        return values_str
    except Exception:
        return ""

def run_deep_enrichment(client, model, product_data, category, temperature=0.1):
    """Run the deep enrichment LLM call."""
    valid_values_ref = get_valid_values(category)

    # Construct Product Summary from available data layers
    summary_parts = []
    for k, v in product_data.items():
        if v and str(v).strip() not in ("", "nan", "None"):
            summary_parts.append(f"{k}: {v}")
    product_summary = "\n".join(summary_parts)

    prompt = MASTER_ENRICHMENT_PROMPT.format(
        product_summary=product_summary,
        valid_values_ref=valid_values_ref or "None provided. Use logical mapping for standard fields."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "You are a Senior Amazon Data Architect. Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        result = _parse_json(raw)

        # Format the output for the Product Enrichment Details column
        details = []
        for entry in result.get("enrichment_details", []):
            attr = entry.get("attribute")
            val = entry.get("value")
            src = entry.get("source")
            if attr and val:
                details.append(f"{attr}: {val} | (Source: {src})")

        return "\n".join(details), result.get("enrichment_details", [])
    except Exception as e:
        return f"Error in deep enrichment: {str(e)}", []

def _parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except Exception:
        return {"enrichment_details": []}
