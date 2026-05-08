import pytest
from unittest.mock import MagicMock
import pandas as pd
import os

from core.enrichment_engine import get_valid_values, run_deep_enrichment
from core.validator import validate_sku_content

def test_get_valid_values():
    # Test for Health & Beauty (formerly Hair Care)
    ref = get_valid_values("Health & Beauty")
    assert "hair_type" in ref
    assert "Fine Hair" in ref

    # Test for unknown category
    ref = get_valid_values("Unknown")
    assert ref == ""

def test_validate_sku_content_deep():
    sku_result = {
        "title": "KONG Classic Dog Toy",
        "attributes": {"material": "Natural Rubber", "target_species": "Dog"},
        "bullets": ["SAFE AND DURABLE – Made from natural rubber.", "FUN TO CHEW – Great for dogs.", "BOUNCY – Fun bounce.", "TREAT FILLABLE – Fill with kibble.", "MADE IN USA – Trusted quality."]
    }
    # These bullets are actually too short based on the 100-250 rule, so we expect flags
    flags = validate_sku_content(sku_result, "Pet Supplies", {})
    # Check for discovery-critical attribute check
    # Pet Supplies critical: material, size_suitability, breed_size
    assert any("size_suitability" in f["message"] for f in flags)

def test_mapper_logic_mock():
    from core.exporter import _map_to_amazon
    row = {"sku": "SKU001", "asin": "ASIN001", "brand": "BrandX"}
    generated = {
        "title": "TitleX",
        "bullets": ["B1", "B2", "B3", "B4", "B5"],
        "attributes": {"color": "Red"},
        "deep_enrichment_data": [{"attribute": "item_form", "value": "Capsule", "source": "test"}]
    }
    mapped = _map_to_amazon(row, generated)
    assert mapped["item_form"] == "Capsule"
    assert mapped["item_name"] == "TitleX"

if __name__ == "__main__":
    # Simple manual run
    test_get_valid_values()
    test_validate_sku_content_deep()
    test_mapper_logic_mock()
    print("All integration tests passed!")
