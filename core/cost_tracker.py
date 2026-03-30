"""
API cost tracking for Bifrost calls.
Tracks token usage and estimated costs per model, per marketplace, per SKU.
"""

from config.model_registry import BIFROST_MODELS


class CostTracker:
    """Track API costs across generation runs."""

    def __init__(self):
        self.entries = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def record(self, model: str, input_tokens: int, output_tokens: int,
               sku: str = "", marketplace: str = "", step: str = ""):
        """Record a single API call's token usage."""
        model_info = BIFROST_MODELS.get(model, {})
        input_cost_per_m = model_info.get("input_cost", 3.0)
        output_cost_per_m = model_info.get("output_cost", 15.0)

        input_cost = (input_tokens / 1_000_000) * input_cost_per_m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_m
        total_cost = input_cost + output_cost

        entry = {
            "model": model,
            "sku": sku,
            "marketplace": marketplace,
            "step": step,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }
        self.entries.append(entry)
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        return entry

    @property
    def total_cost(self) -> float:
        return sum(e["total_cost"] for e in self.entries)

    @property
    def total_input_tokens(self) -> int:
        return self._total_input_tokens

    @property
    def total_output_tokens(self) -> int:
        return self._total_output_tokens

    @property
    def total_tokens(self) -> int:
        return self._total_input_tokens + self._total_output_tokens

    def cost_by_marketplace(self) -> dict:
        """Return {marketplace: total_cost}."""
        by_mp = {}
        for e in self.entries:
            mp = e["marketplace"] or "unknown"
            by_mp[mp] = by_mp.get(mp, 0) + e["total_cost"]
        return by_mp

    def cost_by_sku(self) -> dict:
        """Return {sku: total_cost}."""
        by_sku = {}
        for e in self.entries:
            sku = e["sku"] or "unknown"
            by_sku[sku] = by_sku.get(sku, 0) + e["total_cost"]
        return by_sku

    def cost_by_step(self) -> dict:
        """Return {step: total_cost}."""
        by_step = {}
        for e in self.entries:
            step = e["step"] or "unknown"
            by_step[step] = by_step.get(step, 0) + e["total_cost"]
        return by_step

    def cost_by_model(self) -> dict:
        """Return {model: total_cost}."""
        by_model = {}
        for e in self.entries:
            m = e["model"]
            by_model[m] = by_model.get(m, 0) + e["total_cost"]
        return by_model

    def keyword_enhancement_cost(self) -> float:
        """Return total cost of keyword generation steps."""
        return sum(e["total_cost"] for e in self.entries if e["step"] == "keywords")

    def cost_per_product(self) -> float:
        """Average cost per unique SKU."""
        skus = set(e["sku"] for e in self.entries if e["sku"])
        if not skus:
            return 0.0
        return self.total_cost / len(skus)

    def summary(self) -> dict:
        """Return a summary dict for display."""
        skus = set(e["sku"] for e in self.entries if e["sku"])
        marketplaces = set(e["marketplace"] for e in self.entries if e["marketplace"])
        return {
            "total_cost": self.total_cost,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_api_calls": len(self.entries),
            "unique_skus": len(skus),
            "unique_marketplaces": len(marketplaces),
            "cost_per_product": self.cost_per_product(),
            "keyword_cost": self.keyword_enhancement_cost(),
            "cost_by_marketplace": self.cost_by_marketplace(),
            "cost_by_step": self.cost_by_step(),
        }

    def reset(self):
        """Clear all tracked entries."""
        self.entries.clear()
        self._total_input_tokens = 0
        self._total_output_tokens = 0
