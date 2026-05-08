"""
PILO Deep Enrichment Engine — Category-Aware V2.
Handles deep attribute mapping, category constraints, and detailed justification.
"""

import os
import pandas as pd
import json

MASTER_CATEGORY_INTELLIGENCE_PROMPT = """
Role:
You are the PILO Category Intelligence Engine. Your task is to process raw product data and map it to the specific Amazon AU Master File requirements for the identified category.

Task Phase 1: Category Identification & Constraint Loading
- Identify Product Type (PT): {category_name}
- Knowledge Module: {knowledge_module}

Task Phase 2: Attribute Extraction (The 150+ Fields)
Scan the Product Summary to find values for these priority fields:
1. Discovery Attributes: Map raw text to valid values for special_features, material_type, and target_audience.
2. Compliance Attributes: Ensure ingredients and safety_warning are present if applicable.
3. Variation Logic: Ensure color_name and size_name match the valid values reference.

Valid Values Reference:
{valid_values_ref}

Product Summary:
{product_summary}

Instructions:
- Use strict mapping. Never hallucinate.
- For every attribute, provide a [Mapped Valid Value] and a [Justification from Source Data].
- Priority: Ensure 100% fill rate for all 'Discovery-Critical' fields.

Output Format:
Return JSON with a key "enrichment_details" containing a list of objects:
{{
  "attribute": "Amazon Field Name",
  "value": "Mapped Valid Value",
  "source": "Justification (e.g., Scraped site, PDF Page 4)"
}}
"""

def get_valid_values(category):
    """Pre-Filter step: Load relevant valid values for the category."""
    csv_path = os.path.join("config", "valid_values.csv")
    if not os.path.exists(csv_path):
        return ""

    try:
        df = pd.read_csv(csv_path)
        filtered_df = df[df["category"] == category]
        if filtered_df.empty:
            return ""

        values_str = ""
        for attr in filtered_df["attribute"].unique():
            vals = filtered_df[filtered_df["attribute"] == attr]["valid_value"].tolist()
            values_str += f"- {attr}: {', '.join(vals)}\n"
        return values_str
    except Exception:
        return ""

from core.utils import load_category_config

def run_deep_enrichment(client, model, product_data, category, temperature=0.1):
    """Run the category-aware deep enrichment LLM call."""
    valid_values_ref = get_valid_values(category)
    cat_config = load_category_config().get(category, {})

    knowledge_module = f"Guidelines: {cat_config.get('guidelines', '')}\nCompliance: {cat_config.get('compliance_guardrails', '')}"

    # Construct Product Summary
    summary_parts = []
    for k, v in product_data.items():
        if v and str(v).strip() not in ("", "nan", "None"):
            summary_parts.append(f"{k}: {v}")
    product_summary = "\n".join(summary_parts)

    prompt = MASTER_CATEGORY_INTELLIGENCE_PROMPT.format(
        category_name=category,
        knowledge_module=knowledge_module,
        valid_values_ref=valid_values_ref or "Use logical mapping for standard fields.",
        product_summary=product_summary
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "You are the PILO Category Intelligence Engine. Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        result = _parse_json(raw)

        details = []
        for entry in result.get("enrichment_details", []):
            attr = entry.get("attribute")
            val = entry.get("value")
            src = entry.get("source")
            if attr and val:
                details.append(f"{attr}: {val} | (Source: {src})")

        return "\n".join(details), result.get("enrichment_details", [])
    except Exception as e:
        return f"Error in category intelligence mapping: {str(e)}", []

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
