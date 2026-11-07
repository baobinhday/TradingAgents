# Implementation Plan: Web UI for Configuration & Backtesting

**Status:** Completed
<!-- Lifecycle: Planning -> In Progress -> Verification -> Completed (or Blocked) -->
**PRD Reference:** [prd.md](./prd.md)
**Design Reference:** [design.md](./design.md)

## 1. Ordered Implementation Checklist
*(Execute directly in the active session: verify each step and tick `[x]` as progress is made)*

## Phase 1: Backend API (`tradingagents/api`)
- [x] **Step 1.1**: Update `pyproject.toml` to include optional or core web dependencies (`fastapi`, `uvicorn`, `sse-starlette`).
- [x] **Step 1.2**: Create `tradingagents/api/manager.py` for background backtest execution, event queuing, and SSE streaming.
- [x] **Step 1.3**: Create `tradingagents/api/routes/config.py` for reading default configuration, providers, models, and analysts.
- [x] **Step 1.4**: Create `tradingagents/api/routes/backtest.py` for starting backtests, streaming events (SSE), fetching run status, and listing past runs.
- [x] **Step 1.5**: Create `tradingagents/api/app.py` unifying routes, CORS middleware, and static asset mount.
- [x] **Step 1.6**: Add tests for backend API routes under `tests/test_api.py`.

## Phase 2: Frontend Scaffold (`web/`)
- [x] **Step 2.1**: Initialize Vite React TypeScript project in `web/`.
- [x] **Step 2.2**: Configure Tailwind CSS and setup base theme (dark/light, styling tokens).
- [x] **Step 2.3**: Install and scaffold shadcn/ui components (Card, Button, Input, Progress, Tabs, Badge).
- [x] **Step 2.4**: Setup API clients and TypeScript types matching backend schemas (`types/index.ts`, `lib/api.ts`).

## Phase 3: Frontend Feature Views
- [x] **Step 3.1**: Implement `ConfigPanel.tsx` with presets, date picker, analyst checkboxes, and LLM configuration.
- [x] **Step 3.2**: Implement `LiveMonitor.tsx` with circular/linear progress, current cell indicator, and real-time SSE terminal feed.
- [x] **Step 3.3**: Implement `ResultsPanel.tsx` with KPI metrics cards, rating performance breakdown, and searchable cell results table.
- [x] **Step 3.4**: Implement `HistoryPanel.tsx` to list and load previous runs from the backend.
- [x] **Step 3.5**: Integrate all panels in `App.tsx` with a clean trading dashboard layout and tab navigation.

## Phase 4: CLI Command & Production Integration
- [x] **Step 4.1**: Add `web` subcommand to `cli/main.py` allowing `tradingagents web` to launch the API and open browser.
- [x] **Step 4.2**: Configure FastAPI static files mounting to serve pre-built Vite assets (`web/dist`).
- [x] **Step 4.3**: Add convenience npm / python build and run scripts.

## Phase 5: Verification & Quality Gate
- [x] **Step 5.1**: Test API endpoints with pytest (`tests/test_api.py` passed).
- [x] **Step 5.2**: Test Vite build (`npm run build` passed).
- [x] **Step 5.3**: Run CLI tests (`tests/test_cli_commands.py` passed).
- [x] **Step 5.4**: Run code linter (`ruff check` passed on all packages).
