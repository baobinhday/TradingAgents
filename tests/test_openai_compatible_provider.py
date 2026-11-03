"""Generic OpenAI-compatible provider (vLLM / LM Studio / llama.cpp / relays).

Verifies the user-supplied base_url is required and honored, the key is optional
(keyless local default), Chat Completions (not the Responses API) is used, any
model name is accepted, and the env backend URL precedence (#978).
"""

import pytest

from tradingagents.llm_clients.api_key_env import get_api_key_env
from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.openai_client import LocalCompatibleChatOpenAI, OpenAIClient
from tradingagents.llm_clients.validators import validate_model


@pytest.mark.unit
def test_factory_routes_to_openai_client():
    client = create_llm_client(
        provider="openai_compatible", model="my-model", base_url="http://localhost:8000/v1"
    )
    assert isinstance(client, OpenAIClient)


@pytest.mark.unit
def test_base_url_required(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="requires a base_url"):
        create_llm_client(provider="openai_compatible", model="m").get_llm()


@pytest.mark.unit
def test_keyless_local_uses_placeholder_and_chat_completions(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    llm = create_llm_client(
        provider="openai_compatible", model="qwen2.5", base_url="http://localhost:8000/v1"
    ).get_llm()
    assert isinstance(llm, LocalCompatibleChatOpenAI)
    assert str(llm.openai_api_base) == "http://localhost:8000/v1"
    # keyless local servers: a placeholder key is sent
    key = llm.openai_api_key.get_secret_value() if hasattr(llm.openai_api_key, "get_secret_value") else llm.openai_api_key
    assert key == "EMPTY"
    # must use Chat Completions, not OpenAI's Responses API
    assert getattr(llm, "use_responses_api", False) in (False, None)


@pytest.mark.unit
def test_optional_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "sk-relay-123")
    llm = create_llm_client(
        provider="openai_compatible", model="m", base_url="https://relay.example/v1"
    ).get_llm()
    key = llm.openai_api_key.get_secret_value() if hasattr(llm.openai_api_key, "get_secret_value") else llm.openai_api_key
    assert key == "sk-relay-123"


@pytest.mark.unit
def test_any_model_accepted_no_forced_key():
    assert validate_model("openai_compatible", "literally-anything") is True
    # The key env exists (read for keyed relays) but the provider is marked
    # key-optional, so the CLI never forces a prompt and keyless servers work.
    assert get_api_key_env("openai_compatible") == "OPENAI_COMPATIBLE_API_KEY"
    from tradingagents.llm_clients.openai_client import OPENAI_COMPATIBLE_PROVIDERS
    assert OPENAI_COMPATIBLE_PROVIDERS["openai_compatible"].key_optional is True


@pytest.mark.unit
def test_env_backend_url_precedence():
    # #978: explicit env URL wins over the menu/default regardless of provider source.
    from cli.prompts import resolve_backend_url
    assert resolve_backend_url("openai", "https://api.openai.com/v1", env_url="http://proxy/v1") == "http://proxy/v1"
    assert resolve_backend_url("openai", "https://api.openai.com/v1", env_url=None) == "https://api.openai.com/v1"
    assert resolve_backend_url("deepseek", None, None) == "https://api.deepseek.com"


@pytest.mark.unit
def test_structured_output_suppresses_object_tool_choice(monkeypatch):
    # LM Studio / vLLM reject the object-form tool_choice langchain sends for
    # function-calling structured output (#1057). The generic provider binds the
    # schema as a tool but must not force tool_choice.
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel

    class Schema(BaseModel):
        x: int

    captured = {}
    monkeypatch.setattr(
        ChatOpenAI,
        "with_structured_output",
        lambda self, schema, method=None, **kw: captured.update({"method": method, **kw}) or "BOUND",
    )
    llm = create_llm_client(
        provider="openai_compatible", model="local-llm-30b", base_url="http://localhost:1234/v1"
    ).get_llm()
    out = llm.with_structured_output(Schema)
    assert out == "BOUND"
    assert captured["method"] == "function_calling"
    assert captured["tool_choice"] is None  # not the object form


@pytest.mark.unit
def test_build_llm_kwargs_forwards_api_key():
    from tradingagents.llm_clients.factory import build_llm_kwargs
    kw = build_llm_kwargs({"llm_provider": "openai_compatible", "api_key": "my-secret-key"})
    assert kw["api_key"] == "my-secret-key"

    kw2 = build_llm_kwargs({"llm_provider": "openai_compatible", "openai_compatible_api_key": "my-secret-key-2"})
    assert kw2["api_key"] == "my-secret-key-2"


@pytest.mark.unit
def test_get_models_for_openai_compatible(monkeypatch):
    from unittest.mock import MagicMock

    import requests

    from tradingagents.api.model_service import get_models_for_provider

    # Without base_url, returns curated defaults
    res = get_models_for_provider("openai_compatible")
    assert res["provider"] == "openai_compatible"
    assert len(res["quick_models"]) > 0
    assert len(res["deep_models"]) > 0

    # With base_url, hits mock endpoint
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "meta-llama/Llama-3.1-8B-Instruct"},
            {"id": "deepseek-ai/DeepSeek-V3"},
        ]
    }
    monkeypatch.setattr(requests, "get", lambda *a, **kw: mock_resp)

    res_live = get_models_for_provider("openai_compatible", base_url="http://mock-server:8000/v1")
    assert res_live["is_live"] is True
    model_ids = [m["id"] for m in res_live["all_models"]]
    assert "meta-llama/Llama-3.1-8B-Instruct" in model_ids
    assert "deepseek-ai/DeepSeek-V3" in model_ids

