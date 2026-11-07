# Implementation Plan: Integrate OpenAI-Compatible Provider

**Status:** Completed
<!-- Lifecycle: Planning -> In Progress -> Verification -> Completed (or Blocked) -->
**PRD Reference:** [prd.md](./prd.md)
**Design Reference:** [design.md](./design.md)

## 1. Ordered Implementation Checklist
*(Execute directly in the active session: verify each step and tick `[x]` as progress is made)*

## Phase 1: Backend Model Service & Factory Enhancements
- [x] **Step 1.1**: Update `tradingagents/api/model_service.py` to support `base_url` and `api_key` parameters in `get_models_for_provider`, with a dedicated `_fetch_live_openai_compatible_models` helper.
- [x] **Step 1.2**: Update `tradingagents/api/routes/config.py` to accept query params `base_url` and `api_key` on `/config/models`.
- [x] **Step 1.3**: Update `tradingagents/llm_clients/factory.py` (`build_llm_kwargs`) to forward `api_key` when present in config dictionary.
- [x] **Step 1.4**: Write unit tests in `tests/test_openai_compatible_provider.py` and `tests/test_api.py` covering live model querying and config overriding.

## Phase 2: Web UI Endpoint & Model Configuration
- [x] **Step 2.1**: Update `web/src/lib/api.ts` `fetchProviderModels` to accept `base_url` and `api_key` query parameters.
- [x] **Step 2.2**: Update `web/src/components/ConfigPanel.tsx` to display Base URL and API Key controls when `openai_compatible` is selected.
- [x] **Step 2.3**: Add "Fetch Models" trigger with loading/error state and auto-populate model selection or manual input.
- [x] **Step 2.4**: Pass `backend_url` and `api_key` in `config_overrides` when submitting `handleLaunch`.
- [x] **Step 2.5**: Persist last-used `openai_compatible_base_url` in browser `localStorage`.

## Phase 3: Verification & Quality Gate
- [x] **Step 3.1**: Run pytest test suite for backend API and LLM clients.
- [x] **Step 3.2**: Run `npm run build` in `web/` to verify TypeScript types and build assets.
- [x] **Step 3.3**: Run `ruff check` on modified backend files.
