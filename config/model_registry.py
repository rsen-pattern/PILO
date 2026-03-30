"""Available AI models via Pattern's Bifrost gateway."""

# Models available via Bifrost gateway (OpenAI-compatible)
BIFROST_MODELS = {
    # --- Anthropic (via Bifrost) ---
    "anthropic/claude-sonnet-4-20250514": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000},
    "anthropic/claude-opus-4-6": {"provider": "anthropic", "input_cost": 5.0, "output_cost": 25.0, "context": 1_000_000},
    "anthropic/claude-sonnet-4-6": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000},
    "anthropic/claude-haiku-4-5-20251001": {"provider": "anthropic", "input_cost": 1.0, "output_cost": 5.0, "context": 200_000},
    "anthropic/claude-opus-4-5-20251101": {"provider": "anthropic", "input_cost": 5.0, "output_cost": 25.0, "context": 200_000},
    "anthropic/claude-sonnet-4-5-20250929": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 200_000},
    # --- OpenAI (via Bifrost) ---
    "openai/gpt-4o": {"provider": "openai", "input_cost": 2.5, "output_cost": 10.0, "context": 128_000},
    "openai/gpt-4o-mini": {"provider": "openai", "input_cost": 0.15, "output_cost": 0.6, "context": 128_000},
    "openai/gpt-4.1": {"provider": "openai", "input_cost": 2.0, "output_cost": 8.0, "context": 1_047_576},
    "openai/gpt-4.1-mini": {"provider": "openai", "input_cost": 0.4, "output_cost": 1.6, "context": 1_047_576},
    "openai/gpt-4.1-nano": {"provider": "openai", "input_cost": 0.1, "output_cost": 0.4, "context": 1_047_576},
    "openai/gpt-5": {"provider": "openai", "input_cost": 1.25, "output_cost": 10.0, "context": 272_000},
    "openai/gpt-5-mini": {"provider": "openai", "input_cost": 0.25, "output_cost": 2.0, "context": 272_000},
    "openai/gpt-5.4": {"provider": "openai", "input_cost": 2.5, "output_cost": 15.0, "context": 1_050_000},
    "openai/o3": {"provider": "openai", "input_cost": 2.0, "output_cost": 8.0, "context": 200_000},
    "openai/o4-mini": {"provider": "openai", "input_cost": 1.1, "output_cost": 4.4, "context": 200_000},
    # --- Google (via Bifrost) ---
    "gemini/gemini-2.5-flash": {"provider": "gemini", "input_cost": 0.3, "output_cost": 2.5, "context": 1_048_576},
    "gemini/gemini-2.5-pro": {"provider": "gemini", "input_cost": 1.25, "output_cost": 10.0, "context": 1_048_576},
    "gemini/gemini-3-pro-preview": {"provider": "gemini", "input_cost": 2.0, "output_cost": 12.0, "context": 1_048_576},
    # --- Bedrock (via Bifrost) ---
    "bedrock/us.anthropic.claude-sonnet-4-6": {"provider": "bedrock", "input_cost": 3.3, "output_cost": 16.5, "context": 1_000_000},
    "bedrock/us.anthropic.claude-opus-4-6-v1": {"provider": "bedrock", "input_cost": 5.5, "output_cost": 27.5, "context": 1_000_000},
}

# Recommended models for PILO content generation (sorted by quality/cost balance)
RECOMMENDED_MODELS = [
    "anthropic/claude-sonnet-4-6",
    "anthropic/claude-sonnet-4-20250514",
    "anthropic/claude-opus-4-6",
    "openai/gpt-4.1",
    "openai/gpt-5",
    "gemini/gemini-2.5-pro",
]


def get_model_display_name(model_id):
    """Get a human-readable display name for a model."""
    info = BIFROST_MODELS.get(model_id)
    if info:
        cost_str = f"${info['input_cost']}/{info['output_cost']} per 1M tokens"
        ctx = f"{info['context'] // 1000}K ctx"
        return f"{model_id}  ({ctx}, {cost_str})"
    return model_id


def get_all_bifrost_model_ids():
    """Get all Bifrost model IDs sorted by provider then name."""
    return sorted(BIFROST_MODELS.keys())
