from __future__ import annotations

import os

from fastapi import APIRouter

from tradingagents.api.schemas import ConfigResponse, ProviderDetail
from tradingagents.default_config import build_default_config
from tradingagents.llm_clients.api_key_env import PROVIDER_API_KEY_ENV

router = APIRouter(prefix="/config", tags=["Configuration"])

PROVIDER_NAMES: dict[str, str] = {
    "nvidia": "NVIDIA NIM",
    "openai": "OpenAI",
    "google": "Google Gemini",
    "anthropic": "Anthropic Claude",
    "deepseek": "DeepSeek",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "mistral": "Mistral AI",
    "kimi": "Kimi (Moonshot)",
    "xai": "xAI (Grok)",
    "qwen": "Qwen",
    "glm": "GLM",
    "minimax": "MiniMax",
    "azure": "Azure OpenAI",
    "bedrock": "Amazon Bedrock",
    "ollama": "Ollama (Local)",
    "chatgpt": "ChatGPT Subscription",
    "openai_compatible": "Custom OpenAI-compatible",
}

AVAILABLE_ANALYSTS = [
    {"id": "market", "name": "Market Analyst", "description": "Technical indicators & price momentum"},
    {"id": "social", "name": "Social Sentiment Analyst", "description": "Social media sentiment (Reddit, StockTwits)"},
    {"id": "news", "name": "News Analyst", "description": "Current news sentiment & macro headlines"},
    {"id": "fundamentals", "name": "Fundamentals Analyst", "description": "Financial statements & SEC filings"},
]

AVAILABLE_ASSET_TYPES = ["stock", "crypto"]


@router.get("", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    """Return default configuration, supported providers, analysts, and asset types."""
    cfg = build_default_config()
    safe_cfg = {k: v for k, v in cfg.items() if not k.lower().endswith("key")}

    provider_details: list[ProviderDetail] = []
    for pid, env_var in PROVIDER_API_KEY_ENV.items():
        if pid.endswith("-cn"):
            continue
        has_key = bool(os.getenv(env_var)) if env_var else True
        name = PROVIDER_NAMES.get(pid, pid.upper())
        provider_details.append(
            ProviderDetail(
                id=pid,
                name=name,
                has_key=has_key,
                env_var=env_var,
            )
        )

    # Sort so providers with active keys appear first
    provider_details.sort(key=lambda p: (not p.has_key, p.name))
    supported_providers = [p.id for p in provider_details]

    return ConfigResponse(
        default_config=safe_cfg,
        supported_providers=supported_providers,
        provider_details=provider_details,
        available_analysts=AVAILABLE_ANALYSTS,
        available_asset_types=AVAILABLE_ASSET_TYPES,
    )


@router.get("/models")
def get_provider_models(provider: str):
    """Return available models for a given provider, querying live APIs when available."""
    from tradingagents.api.model_service import get_models_for_provider
    return get_models_for_provider(provider)

