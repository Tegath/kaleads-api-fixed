"""
OpenRouter client wrapper for cost-optimized model routing.

Supports multiple cheap models:
- DeepSeek-Chat ($0.14/$0.28 per 1M tokens)
- Gemini Flash 1.5 ($0.075/$0.30 per 1M tokens)
- Kimi-k2 (Free, rate-limited)
- GPT-4o-mini ($0.15/$0.60 per 1M tokens) - fallback
- Claude Sonnet ($3/$15 per 1M tokens) - premium
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
import openai
from pydantic import BaseModel


class ModelTier(str, Enum):
    """Model tiers based on cost and quality."""
    ULTRA_CHEAP = "ultra_cheap"  # DeepSeek, Kimi-k2
    CHEAP = "cheap"              # Gemini Flash
    BALANCED = "balanced"         # GPT-4o-mini
    PREMIUM = "premium"           # Claude Sonnet


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    cost_per_1m_input: float
    cost_per_1m_output: float
    tier: ModelTier
    max_tokens: int = 4096
    supports_json: bool = True


# Model routing table - Best practices #7
MODEL_ROUTING_TABLE = {
    ModelTier.ULTRA_CHEAP: ModelConfig(
        name="deepseek/deepseek-chat",
        cost_per_1m_input=0.14,
        cost_per_1m_output=0.28,
        tier=ModelTier.ULTRA_CHEAP
    ),
    ModelTier.CHEAP: ModelConfig(
        name="openai/gpt-4o-mini",
        cost_per_1m_input=0.075,
        cost_per_1m_output=0.30,
        tier=ModelTier.CHEAP
    ),
    ModelTier.BALANCED: ModelConfig(
        name="openai/gpt-4o-mini",
        cost_per_1m_input=0.15,
        cost_per_1m_output=0.60,
        tier=ModelTier.BALANCED
    ),
    ModelTier.PREMIUM: ModelConfig(
        name="anthropic/claude-3-5-sonnet",
        cost_per_1m_input=3.0,
        cost_per_1m_output=15.0,
        tier=ModelTier.PREMIUM
    )
}


def select_model_by_complexity(
    task_complexity: int,
    quality_needed: float = 0.7,
    prefer_cheap: bool = True
) -> ModelConfig:
    """
    Dynamic model selection based on task complexity.

    Best practice #7: Use cheapest model that meets quality requirements.

    Args:
        task_complexity: 1-5 scale (1=simple, 5=complex)
        quality_needed: 0-1 scale (0.7=acceptable, 0.9=high quality)
        prefer_cheap: If True, bias toward cheaper models

    Returns:
        ModelConfig for the selected model

    Examples:
        >>> select_model_by_complexity(1, 0.7)  # Simple task, low quality
        deepseek/deepseek-chat (ultra cheap)

        >>> select_model_by_complexity(4, 0.9)  # Complex task, high quality
        anthropic/claude-3-5-sonnet (premium)
    """
    # Simple tasks → ultra cheap models (70% of workload)
    if task_complexity <= 2 and quality_needed <= 0.7:
        return MODEL_ROUTING_TABLE[ModelTier.ULTRA_CHEAP]

    # Medium tasks → cheap models
    if task_complexity <= 3 and quality_needed <= 0.8:
        return MODEL_ROUTING_TABLE[ModelTier.CHEAP]

    # Premium tasks → Claude Sonnet (10% of workload)
    if task_complexity >= 5 or quality_needed >= 0.9:
        return MODEL_ROUTING_TABLE[ModelTier.PREMIUM]

    # Default → balanced (20% of workload)
    return MODEL_ROUTING_TABLE[ModelTier.BALANCED]


class OpenRouterClient:
    """
    OpenRouter API client compatible with instructor.

    Usage:
        client = OpenRouterClient(api_key="sk-or-...")
        instructor_client = instructor.from_openai(client.get_client())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_tier: ModelTier = ModelTier.ULTRA_CHEAP
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (or OPENROUTER_API_KEY env var)
            default_tier: Default model tier to use
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. "
                "Set OPENROUTER_API_KEY env var or pass api_key parameter."
            )

        self.default_tier = default_tier
        self.base_url = "https://openrouter.ai/api/v1"

    def get_client(self, model_tier: Optional[ModelTier] = None) -> openai.OpenAI:
        """
        Get OpenAI-compatible client for instructor.

        Args:
            model_tier: Override default tier

        Returns:
            OpenAI client configured for OpenRouter
        """
        return openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def get_model_name(
        self,
        tier: Optional[ModelTier] = None,
        task_complexity: Optional[int] = None,
        quality_needed: Optional[float] = None
    ) -> str:
        """
        Get model name for a specific tier or auto-select by complexity.

        Args:
            tier: Specific tier to use (overrides auto-selection)
            task_complexity: 1-5 scale for auto-selection
            quality_needed: 0-1 scale for auto-selection

        Returns:
            Model name (e.g., "deepseek/deepseek-chat")
        """
        if tier:
            return MODEL_ROUTING_TABLE[tier].name

        if task_complexity is not None and quality_needed is not None:
            config = select_model_by_complexity(task_complexity, quality_needed)
            return config.name

        return MODEL_ROUTING_TABLE[self.default_tier].name

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_tier: ModelTier
    ) -> float:
        """
        Estimate cost for a request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_tier: Model tier used

        Returns:
            Estimated cost in USD
        """
        config = MODEL_ROUTING_TABLE[model_tier]

        input_cost = (input_tokens / 1_000_000) * config.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * config.cost_per_1m_output

        return input_cost + output_cost


# Task complexity assessment for each agent type
AGENT_COMPLEXITY_MAP = {
    "persona_extractor": {
        "complexity": 2,
        "quality_needed": 0.7,
        "recommended_tier": ModelTier.ULTRA_CHEAP
    },
    "competitor_finder": {
        "complexity": 3,
        "quality_needed": 0.75,
        "recommended_tier": ModelTier.CHEAP
    },
    "pain_point": {
        "complexity": 3,
        "quality_needed": 0.8,
        "recommended_tier": ModelTier.BALANCED
    },
    "signal_generator": {
        "complexity": 4,
        "quality_needed": 0.8,
        "recommended_tier": ModelTier.BALANCED
    },
    "system_builder": {
        "complexity": 2,
        "quality_needed": 0.7,
        "recommended_tier": ModelTier.ULTRA_CHEAP
    },
    "case_study": {
        "complexity": 3,
        "quality_needed": 0.8,
        "recommended_tier": ModelTier.BALANCED
    },
    "pci_filter": {
        "complexity": 1,
        "quality_needed": 0.7,
        "recommended_tier": ModelTier.ULTRA_CHEAP
    }
}


def get_recommended_model_for_agent(agent_type: str) -> ModelConfig:
    """
    Get recommended model configuration for a specific agent.

    Args:
        agent_type: Agent type (e.g., "persona_extractor")

    Returns:
        ModelConfig for the recommended model
    """
    if agent_type not in AGENT_COMPLEXITY_MAP:
        return MODEL_ROUTING_TABLE[ModelTier.BALANCED]

    recommended_tier = AGENT_COMPLEXITY_MAP[agent_type]["recommended_tier"]
    return MODEL_ROUTING_TABLE[recommended_tier]
