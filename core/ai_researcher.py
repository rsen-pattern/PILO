"""
AI research module with confidence scoring.
Uses Bifrost (OpenAI-compatible) to research products when web scraping isn't available.
"""

import json
import time

from config.default_prompts import RESEARCH_PROMPT, CONFIDENCE_PROMPT


def create_research_client(settings: dict):
    """Create an OpenAI-compatible client for Bifrost research calls."""
    from openai import OpenAI
    api_key = settings.get("bifrost_api_key", "")
    base_url = settings.get("bifrost_base_url", "https://bifrost.pattern.com")
    client = OpenAI(base_url=base_url, api_key=api_key)
    model = settings.get("model", "anthropic/claude-sonnet-4-6")
    return client, model


def research_product(client, model: str, product_name: str, brand_name: str,
                     category: str, existing_data: dict,
                     additional_context: str = "",
                     temperature: float = 0.3) -> dict:
    """Research a single product using AI.

    Returns:
        {
            "research": { ... parsed research JSON ... },
            "confidence": float (0.0-1.0),
            "raw_response": str,
            "error": str or None
        }
    """
    existing_str = "\n".join(f"  {k}: {v}" for k, v in existing_data.items() if v)

    prompt = RESEARCH_PROMPT.format(
        product_name=product_name,
        brand_name=brand_name,
        category=category,
        existing_data=existing_str or "(none)",
        additional_context=additional_context or "",
    )

    try:
        # Step 1: Research call
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "You are a product research specialist. Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        research = _parse_json(raw)

        # Step 2: Confidence self-assessment
        conf_response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": "You are a product research specialist."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": raw},
                {"role": "user", "content": CONFIDENCE_PROMPT},
            ],
            max_tokens=10,
        )
        conf_text = conf_response.choices[0].message.content.strip()
        confidence = _parse_confidence(conf_text)

        return {
            "research": research,
            "confidence": confidence,
            "raw_response": raw,
            "error": None,
        }

    except Exception as e:
        return {
            "research": {},
            "confidence": 0.0,
            "raw_response": "",
            "error": str(e),
        }


def batch_research(client, model: str, products: list, settings: dict,
                   progress_callback=None, delay: float = 0.5) -> dict:
    """Research multiple products. Returns {sku: research_result}.

    Args:
        products: list of dicts, each with at least 'sku', 'title', 'brand'
        progress_callback: optional callable(sku, idx, total, result)
    """
    results = {}
    total = len(products)

    for idx, product in enumerate(products):
        sku = product.get("sku", f"unknown_{idx}")
        result = research_product(
            client=client,
            model=model,
            product_name=product.get("title", sku),
            brand_name=product.get("brand", ""),
            category=product.get("product_type", settings.get("category", "")),
            existing_data=product,
            additional_context=settings.get("research_context", ""),
            temperature=settings.get("temperature", 0.3),
        )
        results[sku] = result

        if progress_callback:
            progress_callback(sku, idx + 1, total, result)

        if idx < total - 1 and delay > 0:
            time.sleep(delay)

    return results


def confidence_badge(score: float) -> str:
    """Return an emoji badge for a confidence score."""
    if score >= 0.8:
        return "🟢"
    elif score >= 0.5:
        return "🟡"
    else:
        return "🔴"


def confidence_label(score: float) -> str:
    """Return a text label for a confidence score."""
    if score >= 0.8:
        return f"High ({score:.2f})"
    elif score >= 0.5:
        return f"Medium ({score:.2f})"
    else:
        return f"Low ({score:.2f})"


def _parse_json(text: str) -> dict:
    """Parse JSON from a response that may contain markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}


def _parse_confidence(text: str) -> float:
    """Parse a confidence score (0.0-1.0) from text."""
    text = text.strip()
    for token in text.split():
        try:
            val = float(token)
            if 0.0 <= val <= 1.0:
                return val
        except ValueError:
            continue
    return 0.5  # default if unparseable
