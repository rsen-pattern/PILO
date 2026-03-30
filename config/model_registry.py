"""Available AI models via Pattern's Bifrost gateway."""

# Models available via Bifrost gateway (OpenAI-compatible)
BIFROST_MODELS = {
    # ===== Anthropic (direct via Bifrost) =====
    "anthropic/claude-opus-4-6": {"provider": "anthropic", "input_cost": 5.0, "output_cost": 25.0, "context": 1_000_000, "max_output": 128_000},
    "anthropic/claude-sonnet-4-6": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000, "max_output": 64_000},
    "anthropic/claude-sonnet-4-20250514": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000, "max_output": 64_000},
    "anthropic/claude-4-sonnet-20250514": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000, "max_output": 64_000},
    "anthropic/claude-opus-4-5": {"provider": "anthropic", "input_cost": 5.0, "output_cost": 25.0, "context": 200_000, "max_output": 64_000},
    "anthropic/claude-opus-4-5-20251101": {"provider": "anthropic", "input_cost": 5.0, "output_cost": 25.0, "context": 200_000, "max_output": 64_000},
    "anthropic/claude-sonnet-4-5": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 200_000, "max_output": 64_000},
    "anthropic/claude-sonnet-4-5-20250929": {"provider": "anthropic", "input_cost": 3.0, "output_cost": 15.0, "context": 200_000, "max_output": 64_000},
    "anthropic/claude-opus-4-1": {"provider": "anthropic", "input_cost": 15.0, "output_cost": 75.0, "context": 200_000, "max_output": 32_000},
    "anthropic/claude-opus-4-1-20250805": {"provider": "anthropic", "input_cost": 15.0, "output_cost": 75.0, "context": 200_000, "max_output": 32_000},
    "anthropic/claude-4-opus-20250514": {"provider": "anthropic", "input_cost": 15.0, "output_cost": 75.0, "context": 200_000, "max_output": 32_000},
    "anthropic/claude-haiku-4-5": {"provider": "anthropic", "input_cost": 1.0, "output_cost": 5.0, "context": 200_000, "max_output": 64_000},
    "anthropic/claude-haiku-4-5-20251001": {"provider": "anthropic", "input_cost": 1.0, "output_cost": 5.0, "context": 200_000, "max_output": 64_000},

    # ===== Bedrock — Anthropic models =====
    "bedrock/global.anthropic.claude-opus-4-6-v1": {"provider": "bedrock", "input_cost": 5.0, "output_cost": 25.0, "context": 1_000_000, "max_output": 128_000},
    "bedrock/global.anthropic.claude-sonnet-4-6": {"provider": "bedrock", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000, "max_output": 64_000},
    "bedrock/global.anthropic.claude-sonnet-4-20250514-v1:0": {"provider": "bedrock", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000, "max_output": 64_000},
    "bedrock/global.anthropic.claude-opus-4-5-20251101-v1:0": {"provider": "bedrock", "input_cost": 5.0, "output_cost": 25.0, "context": 200_000, "max_output": 64_000},
    "bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0": {"provider": "bedrock", "input_cost": 3.0, "output_cost": 15.0, "context": 200_000, "max_output": 64_000},
    "bedrock/global.anthropic.claude-haiku-4-5-20251001-v1:0": {"provider": "bedrock", "input_cost": 1.0, "output_cost": 5.0, "context": 200_000, "max_output": 64_000},
    "bedrock/us.anthropic.claude-opus-4-6-v1": {"provider": "bedrock", "input_cost": 5.5, "output_cost": 27.5, "context": 1_000_000, "max_output": 128_000},
    "bedrock/us.anthropic.claude-sonnet-4-6": {"provider": "bedrock", "input_cost": 3.3, "output_cost": 16.5, "context": 1_000_000, "max_output": 64_000},
    "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0": {"provider": "bedrock", "input_cost": 3.0, "output_cost": 15.0, "context": 1_000_000, "max_output": 64_000},
    "bedrock/us.anthropic.claude-opus-4-5-20251101-v1:0": {"provider": "bedrock", "input_cost": 5.5, "output_cost": 27.5, "context": 200_000, "max_output": 64_000},
    "bedrock/us.anthropic.claude-opus-4-1-20250805-v1:0": {"provider": "bedrock", "input_cost": 15.0, "output_cost": 75.0, "context": 200_000, "max_output": 32_000},
    "bedrock/us.anthropic.claude-opus-4-20250514-v1:0": {"provider": "bedrock", "input_cost": 15.0, "output_cost": 75.0, "context": 200_000, "max_output": 32_000},
    "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0": {"provider": "bedrock", "input_cost": 3.3, "output_cost": 16.5, "context": 200_000, "max_output": 64_000},
    "bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0": {"provider": "bedrock", "input_cost": 1.1, "output_cost": 5.5, "context": 200_000, "max_output": 64_000},

    # ===== Bedrock — Amazon Nova models =====
    "bedrock/global.amazon.nova-2-lite-v1:0": {"provider": "bedrock", "input_cost": 0.3, "output_cost": 2.5, "context": 1_000_000, "max_output": 64_000},
    "bedrock/us.amazon.nova-2-lite-v1:0": {"provider": "bedrock", "input_cost": 0.33, "output_cost": 2.75, "context": 1_000_000, "max_output": 64_000},
    "bedrock/us.amazon.nova-2-pro-preview-20251202-v1:0": {"provider": "bedrock", "input_cost": 2.19, "output_cost": 17.5, "context": 1_000_000, "max_output": 64_000},
    "bedrock/us.amazon.nova-lite-v1:0": {"provider": "bedrock", "input_cost": 0.06, "output_cost": 0.24, "context": 300_000, "max_output": 10_000},
    "bedrock/us.amazon.nova-micro-v1:0": {"provider": "bedrock", "input_cost": 0.035, "output_cost": 0.14, "context": 128_000, "max_output": 10_000},
    "bedrock/us.amazon.nova-premier-v1:0": {"provider": "bedrock", "input_cost": 2.5, "output_cost": 12.5, "context": 1_000_000, "max_output": 10_000},
    "bedrock/us.amazon.nova-pro-v1:0": {"provider": "bedrock", "input_cost": 0.8, "output_cost": 3.2, "context": 300_000, "max_output": 10_000},

    # ===== Bedrock — DeepSeek =====
    "bedrock/us.deepseek.v3.2": {"provider": "bedrock", "input_cost": 0.62, "output_cost": 1.85, "context": 163_840, "max_output": 163_840},

    # ===== OpenAI (via Bifrost) =====
    "openai/gpt-5.4": {"provider": "openai", "input_cost": 2.5, "output_cost": 15.0, "context": 1_050_000, "max_output": 128_000},
    "openai/gpt-5.4-mini": {"provider": "openai", "input_cost": 0.75, "output_cost": 4.5, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5.4-nano": {"provider": "openai", "input_cost": 0.2, "output_cost": 1.25, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5.4-pro": {"provider": "openai", "input_cost": 30.0, "output_cost": 180.0, "context": 1_050_000, "max_output": 128_000},
    "openai/gpt-5.2": {"provider": "openai", "input_cost": 1.75, "output_cost": 14.0, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5.2-pro": {"provider": "openai", "input_cost": 21.0, "output_cost": 168.0, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5.1": {"provider": "openai", "input_cost": 1.25, "output_cost": 10.0, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5": {"provider": "openai", "input_cost": 1.25, "output_cost": 10.0, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5-mini": {"provider": "openai", "input_cost": 0.25, "output_cost": 2.0, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5-nano": {"provider": "openai", "input_cost": 0.05, "output_cost": 0.4, "context": 272_000, "max_output": 128_000},
    "openai/gpt-5-pro": {"provider": "openai", "input_cost": 15.0, "output_cost": 120.0, "context": 128_000, "max_output": 272_000},
    "openai/gpt-4.1": {"provider": "openai", "input_cost": 2.0, "output_cost": 8.0, "context": 1_047_576, "max_output": 32_768},
    "openai/gpt-4.1-mini": {"provider": "openai", "input_cost": 0.4, "output_cost": 1.6, "context": 1_047_576, "max_output": 32_768},
    "openai/gpt-4.1-nano": {"provider": "openai", "input_cost": 0.1, "output_cost": 0.4, "context": 1_047_576, "max_output": 32_768},
    "openai/gpt-4o": {"provider": "openai", "input_cost": 2.5, "output_cost": 10.0, "context": 128_000, "max_output": 16_384},
    "openai/gpt-4o-mini": {"provider": "openai", "input_cost": 0.15, "output_cost": 0.6, "context": 128_000, "max_output": 16_384},
    "openai/o3": {"provider": "openai", "input_cost": 2.0, "output_cost": 8.0, "context": 200_000, "max_output": 100_000},
    "openai/o3-pro": {"provider": "openai", "input_cost": 20.0, "output_cost": 80.0, "context": 200_000, "max_output": 100_000},
    "openai/o3-mini": {"provider": "openai", "input_cost": 1.1, "output_cost": 4.4, "context": 200_000, "max_output": 100_000},
    "openai/o4-mini": {"provider": "openai", "input_cost": 1.1, "output_cost": 4.4, "context": 200_000, "max_output": 100_000},
    "openai/o1": {"provider": "openai", "input_cost": 15.0, "output_cost": 60.0, "context": 200_000, "max_output": 100_000},
    "openai/o1-pro": {"provider": "openai", "input_cost": 150.0, "output_cost": 600.0, "context": 200_000, "max_output": 100_000},
    "openai/codex-mini-latest": {"provider": "openai", "input_cost": 1.5, "output_cost": 6.0, "context": 200_000, "max_output": 100_000},

    # ===== Google Gemini (via Bifrost) =====
    "gemini/gemini-3.1-pro-preview": {"provider": "gemini", "input_cost": 2.0, "output_cost": 12.0, "context": 1_048_576, "max_output": 65_536},
    "gemini/gemini-3-pro-preview": {"provider": "gemini", "input_cost": 2.0, "output_cost": 12.0, "context": 1_048_576, "max_output": 65_535},
    "gemini/gemini-3-flash-preview": {"provider": "gemini", "input_cost": 0.5, "output_cost": 3.0, "context": 1_048_576, "max_output": 65_535},
    "gemini/gemini-3.1-flash-lite-preview": {"provider": "gemini", "input_cost": 0.25, "output_cost": 1.5, "context": 1_048_576, "max_output": 65_536},
    "gemini/gemini-2.5-pro": {"provider": "gemini", "input_cost": 1.25, "output_cost": 10.0, "context": 1_048_576, "max_output": 65_535},
    "gemini/gemini-2.5-flash": {"provider": "gemini", "input_cost": 0.3, "output_cost": 2.5, "context": 1_048_576, "max_output": 65_535},
    "gemini/gemini-2.5-flash-lite": {"provider": "gemini", "input_cost": 0.1, "output_cost": 0.4, "context": 1_048_576, "max_output": 65_535},
}

# Recommended models for PILO content generation (sorted by quality/cost balance)
RECOMMENDED_MODELS = [
    "anthropic/claude-sonnet-4-6",
    "anthropic/claude-opus-4-6",
    "anthropic/claude-sonnet-4-20250514",
    "anthropic/claude-haiku-4-5",
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
