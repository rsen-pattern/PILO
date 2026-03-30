"""
PXM (Product Experience Management) JSON export connector.
For MVP: export-only — generates PXM-compatible JSON from PILO results.
"""

import json

from config.pattern_tool_schemas import to_pxm_product, build_pxm_export


def generate_pxm_export(generated_results: dict, product_data: dict,
                        marketplaces: list) -> dict:
    """Build a PXM-compatible JSON export from PILO generation results.

    Args:
        generated_results: {(sku, marketplace): chain_result_dict}
        product_data: {sku: product_dict} (original product data)
        marketplaces: list of marketplace keys

    Returns:
        PXM export dict ready for JSON serialization
    """
    products = []

    # Group by SKU
    skus = set()
    for (sku, _mp) in generated_results.keys():
        skus.add(sku)

    for sku in sorted(skus):
        original = product_data.get(sku, {})
        marketplace_content = {}

        for mp in marketplaces:
            key = (sku, mp)
            if key not in generated_results:
                continue
            chain_result = generated_results[key]

            # Build generated dict for PXM mapping
            generated = {}
            if chain_result.get("title"):
                generated["title"] = chain_result["title"]
            if chain_result.get("description"):
                generated["description"] = chain_result["description"]
            if chain_result.get("bullets"):
                generated["bullets"] = chain_result["bullets"]
            if chain_result.get("attributes"):
                generated["attributes"] = chain_result["attributes"]
            if chain_result.get("search_terms"):
                generated["search_terms"] = chain_result["search_terms"]
            if chain_result.get("special_features"):
                generated["special_features"] = chain_result["special_features"]
            if chain_result.get("item_type"):
                generated["item_type"] = chain_result["item_type"]

            pxm_product = to_pxm_product(original, mp, generated)
            marketplace_content[mp] = pxm_product

        products.append({
            "sku": sku,
            "marketplace_content": marketplace_content,
        })

    return build_pxm_export(products)


def export_pxm_json(pxm_data: dict) -> str:
    """Serialize PXM export to JSON string."""
    return json.dumps(pxm_data, indent=2, ensure_ascii=False)
