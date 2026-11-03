from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

from tradingagents.llm_clients.api_key_env import get_api_key_env
from tradingagents.llm_clients.model_catalog import MODEL_OPTIONS

logger = logging.getLogger(__name__)

# In-memory cache for live fetched models: {provider: (timestamp, data)}
_MODEL_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL = 300  # 5 minutes


# Curated defaults for providers that don't have static list or when offline
CURATED_DEFAULTS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "nvidia": {
        "quick": [
            ("Llama 3.1 8B Instruct (Fast)", "meta/llama-3.1-8b-instruct"),
            ("Mistral NeMo Minitron 8B (Fast)", "nvidia/mistral-nemo-minitron-8b-8k-instruct"),
            ("Gemma 3 12B IT (Balanced)", "google/gemma-3-12b-it"),
        ],
        "deep": [
            ("Llama 3.1 Nemotron 70B Instruct (Frontier)", "nvidia/llama-3.1-nemotron-70b-instruct"),
            ("Llama 3.3 70B Instruct (Reasoning)", "meta/llama-3.3-70b-instruct"),
            ("DeepSeek V4.1 Flash", "deepseek-ai/deepseek-v4.1-flash"),
            ("Mistral Large 2 Instruct (Frontier)", "mistralai/mistral-large-2-instruct"),
        ],
    },
    "groq": {
        "quick": [
            ("Llama 3.1 8B Instant (Ultra-fast)", "llama-3.1-8b-instant"),
            ("Gemma 2 9B IT", "gemma2-9b-it"),
        ],
        "deep": [
            ("Llama 3.3 70B Versatile (Frontier)", "llama-3.3-70b-versatile"),
            ("Mixtral 8x7B 32K", "mixtral-8x7b-32768"),
        ],
    },
    "openai_compatible": {
        "quick": [
            ("Llama 3.1 8B Instruct", "meta-llama/llama-3.1-8b-instruct"),
            ("Qwen 2.5 7B Instruct", "qwen/qwen-2.5-7b-instruct"),
            ("Mistral 7B Instruct", "mistralai/mistral-7b-instruct"),
        ],
        "deep": [
            ("Llama 3.3 70B Instruct", "meta-llama/llama-3.3-70b-instruct"),
            ("DeepSeek V3 / R1", "deepseek-ai/deepseek-r1"),
            ("Qwen 2.5 72B Instruct", "qwen/qwen-2.5-72b-instruct"),
        ],
    },
}


def _fetch_live_nvidia_models(api_key: str) -> list[str]:
    """Fetch live model IDs from NVIDIA NIM."""
    resp = requests.get(
        "https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=4,
    )
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        models = [m["id"] for m in data if "id" in m]
        # Filter for text/instruct models (exclude embed/rerank/guardrails for primary generation)
        chat_models = [
            m for m in models
            if not any(k in m.lower() for k in ["embed", "guard", "reward", "parse"])
        ]
        return sorted(chat_models) if chat_models else sorted(models)
    return []


def _fetch_live_groq_models(api_key: str) -> list[str]:
    """Fetch live model IDs from Groq."""
    resp = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=4,
    )
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        return sorted([m["id"] for m in data if "id" in m])
    return []


def _fetch_live_openrouter_models() -> list[str]:
    """Fetch live model IDs from OpenRouter."""
    resp = requests.get("https://openrouter.ai/api/v1/models", timeout=4)
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        return [m["id"] for m in data if "id" in m]
    return []


def _fetch_live_ollama_models() -> list[str]:
    """Fetch installed models from local Ollama instance."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        return [m["name"] for m in models if "name" in m]
    return []


def _fetch_live_openai_compatible_models(base_url: str, api_key: str | None = None) -> list[str]:
    """Fetch live model IDs from an OpenAI-compatible endpoint."""
    raw = base_url.strip().rstrip("/")
    if not raw:
        return []
    if raw.endswith("/models"):
        urls = [raw]
    elif raw.endswith("/v1"):
        urls = [f"{raw}/models"]
    else:
        urls = [f"{raw}/v1/models", f"{raw}/models"]

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                payload = resp.json()
                items = []
                if isinstance(payload, dict):
                    items = payload.get("data") or payload.get("models") or []
                elif isinstance(payload, list):
                    items = payload

                models = []
                for item in items:
                    if isinstance(item, dict):
                        mid = item.get("id") or item.get("name")
                        if mid:
                            models.append(str(mid))
                    elif isinstance(item, str):
                        models.append(item)
                if models:
                    return sorted(models)
        except Exception as exc:
            logger.debug("Failed checking models on %s: %s", url, exc)
            continue
    return []


def get_models_for_provider(
    provider: str,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Return available quick and deep models for a provider, using live API when possible."""
    p = provider.lower()
    now = time.time()
    cache_key = f"{p}:{base_url}" if (p == "openai_compatible" and base_url) else p

    # Check cache
    if cache_key in _MODEL_CACHE:
        timestamp, cached_data = _MODEL_CACHE[cache_key]
        if now - timestamp < CACHE_TTL:
            return cached_data

    quick_options: list[dict[str, str]] = []
    deep_options: list[dict[str, str]] = []
    all_options: list[dict[str, str]] = []
    is_live = False

    # 1. First, populate from catalog or curated defaults
    catalog_entry = MODEL_OPTIONS.get(p)
    if catalog_entry:
        for name, mid in catalog_entry.get("quick", []):
            if mid != "custom":
                quick_options.append({"id": mid, "name": name})
        for name, mid in catalog_entry.get("deep", []):
            if mid != "custom":
                deep_options.append({"id": mid, "name": name})

    curated = CURATED_DEFAULTS.get(p)
    if curated:
        if not quick_options:
            quick_options = [{"id": mid, "name": name} for name, mid in curated["quick"]]
        if not deep_options:
            deep_options = [{"id": mid, "name": name} for name, mid in curated["deep"]]

    # 2. Try live fetching if API key or service is available
    if not api_key:
        env_var = get_api_key_env(p)
        api_key = os.getenv(env_var) if env_var else None

    live_models: list[str] = []
    try:
        if p == "openai_compatible" and base_url:
            live_models = _fetch_live_openai_compatible_models(base_url, api_key)
        elif p == "nvidia" and api_key:
            live_models = _fetch_live_nvidia_models(api_key)
        elif p == "groq" and api_key:
            live_models = _fetch_live_groq_models(api_key)
        elif p == "openrouter":
            live_models = _fetch_live_openrouter_models()
        elif p == "ollama":
            live_models = _fetch_live_ollama_models()

        if live_models:
            is_live = True
            # Build all_options from live models
            all_options = [{"id": mid, "name": mid} for mid in live_models]

            # Prioritize matching or popular models in quick and deep
            existing_quick_ids = {m["id"] for m in quick_options}
            existing_deep_ids = {m["id"] for m in deep_options}

            # Add any live models not already in quick/deep
            for mid in live_models:
                lower = mid.lower()
                is_quick = any(k in lower for k in ["8b", "7b", "mini", "flash", "small", "lite"])
                if is_quick and mid not in existing_quick_ids:
                    quick_options.append({"id": mid, "name": mid})
                elif not is_quick and mid not in existing_deep_ids:
                    deep_options.append({"id": mid, "name": mid})
    except Exception as exc:
        logger.warning("Could not fetch live models for provider %s: %s", p, exc)

    if not all_options:
        # Merge quick and deep unique models
        seen = set()
        for item in deep_options + quick_options:
            if item["id"] not in seen:
                all_options.append(item)
                seen.add(item["id"])

    # Fallback defaults if still empty
    default_deep = deep_options[0]["id"] if deep_options else "default"
    default_quick = quick_options[0]["id"] if quick_options else "default"

    res = {
        "provider": p,
        "is_live": is_live,
        "default_deep": default_deep,
        "default_quick": default_quick,
        "quick_models": quick_options,
        "deep_models": deep_options,
        "all_models": all_options,
    }

    _MODEL_CACHE[cache_key] = (now, res)
    return res
