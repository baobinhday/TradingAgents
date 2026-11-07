# PRD: Integrate OpenAI-Compatible Provider

**Status:** Completed
<!-- Lifecycle: Draft -> In Review -> Approved -> Completed -->
**Topic Path:** `.trellis/research/11-03-openai-compatible-provider/`

## 1. Goal & Overview
Enable comprehensive OpenAI-compatible endpoint configuration and usage across the TradingAgents platform (Web Console and Backend Execution Engine), prioritizing OpenAI-compatible as the default/recommended provider option while retaining existing providers (Google Gemini, Anthropic Claude, Azure OpenAI, Bedrock, etc.) for fallback and multi-provider setups.

## 2. User Decisions & Scope Confirmation
- **Strategy Confirmed by User**: Prioritize OpenAI-Compatible as the primary/default provider with full Web UI and Backend support (Base URL, custom API Key, model auto-discovery via `/v1/models`), while preserving existing providers in the provider list.
- **Target Environments**: Any standard OpenAI-compatible API endpoint, including:
  - Local inference servers: vLLM, LM Studio, Ollama, llama.cpp.
  - Multi-model cloud relays / gateways: LiteLLM, OpenRouter, DeepSeek, Cloudflare AI Gateway.

## 3. Detailed Requirements

### 3.1 Backend & Model Discovery (`tradingagents/api`)
- **Dynamic Model Fetching Endpoint**:
  - Extend `GET /config/models` (and `tradingagents/api/model_service.py`) to accept optional `base_url` and `api_key` parameters.
  - When `provider=openai_compatible` and `base_url` is provided:
    - Call `{base_url}/models` with standard Bearer authorization (if `api_key` provided).
    - Parse available model IDs into `all_models`, heuristics for `quick_models` (e.g. 7b/8b/mini/flash) and `deep_models`.
    - Handle network errors / unreachable endpoints gracefully with clear error messages and fallback to manual model entry.
- **Provider Ordering & Defaults**:
  - Update `tradingagents/api/routes/config.py` so that `openai_compatible` is clearly presented and prioritized in `provider_details` alongside active providers.
  - Support forwarding custom `api_key` from `config_overrides` into `build_llm_kwargs`.

### 3.2 Web UI (`web/src/components/ConfigPanel.tsx`)
- **OpenAI-Compatible Configuration Section**:
  - When `openai_compatible` is selected as the LLM Provider:
    - Display dedicated inputs for **Base URL** (e.g. `http://localhost:8000/v1`) with default/placeholder values.
    - Display optional **API Key** input (masked password field with toggle).
    - Provide a **"Fetch Models"** action button next to the Base URL to dynamically populate available models directly from the target endpoint.
    - Provide custom text inputs for **Deep Think Model** and **Quick Think Model** (or dropdown populated from the fetched list with custom override toggle).
- **Backtest Dispatch**:
  - Include `backend_url`, `api_key` (or `openai_compatible_api_key`), `deep_think_llm`, and `quick_think_llm` in `config_overrides` sent to `POST /api/backtest/run`.
  - Provide explicit user controls in Web UI to persist/toggle saving `Base URL` and `API Key` in browser `localStorage`, with visual status indicator and a button to clear cached credentials.

### 3.3 Core LLM Client Integration (`tradingagents/llm_clients`)
- Ensure `tradingagents/llm_clients/factory.py:build_llm_kwargs` forwards `api_key` when passed via config dictionary, allowing dynamically provided keys from the web UI to work without requiring system-wide environment variables.
- Maintain existing non-breaking compatibility with CLI (`tradingagents/cli/selections.py`) and environment variables (`OPENAI_COMPATIBLE_API_KEY`, `TRADINGAGENTS_LLM_BACKEND_URL`).

## 4. Acceptance Criteria
- [x] `GET /config/models?provider=openai_compatible&base_url=...` successfully queries and returns models from any OpenAI-compatible `/v1/models` server.
- [x] Web UI `ConfigPanel.tsx` allows entering Base URL and API Key for `openai_compatible`, fetching models, and entering custom model IDs.
- [x] Backtest execution launched from Web UI successfully invokes the OpenAI-compatible endpoint for both quick-think and deep-think roles.
- [x] Existing providers (OpenAI, Google, Anthropic, etc.) remain fully functional and selectable.
- [x] Unit tests for `model_service.py` and `test_openai_compatible_provider.py` pass without errors.
- [x] `npm run build` in `web/` and `ruff check` pass cleanly.
