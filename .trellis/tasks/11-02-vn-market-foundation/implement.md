# Implementation Plan: Market-Aware Routing Foundation

## Work Breakdown

### Step 1: Configuration & Schemas
- [ ] Edit `tradingagents/default_config.py`:
  - Add `TRADINGAGENTS_MARKET: "market"` to `_ENV_OVERRIDES`.
  - Add `"market": "US"` to default config.
  - Add `".VN": "VNINDEX"` to `benchmark_map`.
  - Add `"vn_data_vendors"` to default config with `"algolab,ssi"`.
- [ ] Edit `tradingagents/api/schemas.py`:
  - Add `market: str = Field("US", description="Target market ('US', 'VN')")` to `BacktestRunRequest`.
  - Add `available_markets: list[str] = Field(default_factory=lambda: ["US", "VN"])` to `ConfigResponse`.
- [ ] Edit `tradingagents/api/routes/config.py`:
  - Include `available_markets=["US", "VN"]` in `ConfigResponse`.
- [ ] Edit `tradingagents/agents/state.py`:
  - Add `market: Annotated[str, "Target market (e.g. US, VN)"]` to `AgentState`.
- [ ] Edit `tradingagents/graph/propagation.py`:
  - Update `create_initial_state` to take `market: str = "US"` and set `"market": market`.

### Step 2: Symbol Normalization
- [ ] Edit `tradingagents/dataflows/symbols.py`:
  - Update `normalize_symbol(raw: str, market: str | None = None) -> str`.
  - Handle `market == "VN"` or `.VN` suffix:
    - Strip `.VN`.
    - Clean uppercase alphanumeric.
    - Bypass US forex/metals/crypto conversions for Vietnamese tickers.

### Step 3: Router & Call Sites Refactoring
- [ ] Edit `tradingagents/dataflows/router.py`:
  - Register `get_verified_market_snapshot`, `get_company_profile`, and `get_closes` in `TOOLS_CATEGORIES` and `VENDOR_METHODS`.
  - Provide `_vn_vendor_stub` or VN routing logic that strictly avoids Yahoo Finance.
  - Make `get_vendor` market-aware: uses VN vendor chain when `market == "VN"`.
  - In `route_to_vendor`: enforce guard that strips `yfinance`/`yahoo` when `market == "VN"`.
  - Provide typed helper `get_closes(symbol: str, start_date: str, end_date: str, market: str | None = None) -> pd.Series`.
  - Provide typed helper `get_company_profile(ticker: str, market: str | None = None) -> dict`.
- [ ] Edit `tradingagents/agents/context.py`:
  - Remove direct import of `get_company_profile` from `yahoo.fundamentals`.
  - Import `get_company_profile` from `tradingagents.dataflows.router`.
  - Update `resolve_instrument_identity(ticker: str, market: str | None = None) -> dict`.
- [ ] Edit `tradingagents/agents/tools.py`:
  - Remove direct import of `build_verified_market_snapshot` from `yahoo.snapshot`.
  - Call `route_to_vendor("get_verified_market_snapshot", symbol, as_of(curr_date, trade_date), look_back_days)`.
- [ ] Edit `tradingagents/memory/settlement.py`:
  - Remove direct import of `get_closes` from `yahoo.market`.
  - Import `get_closes` from `tradingagents.dataflows.router`.
  - Update `resolve_benchmark`: when `config.get("market") == "VN"`, return `VNINDEX`.

### Step 4: Graph Propagation & CLI Integration
- [ ] Edit `tradingagents/graph/trading_graph.py`:
  - Pass `market=self.config.get("market", "US")` in `create_run_state` and `resolve_instrument_context`.
- [ ] Edit `cli/main.py`:
  - Add `--market` option to `analyze` and `backtest` commands.
- [ ] Edit `cli/run.py` & `cli/prompts.py`:
  - Support `market` selection and normalization.

### Step 5: Verification & Tests
- [ ] Add `tests/test_market_foundation.py`:
  - Test market config and env override (`TRADINGAGENTS_MARKET=VN`).
  - Test symbol normalization for VN vs US (`VNM.VN -> VNM`, `vnm -> VNM`, `AAPL -> AAPL`, `XAUUSD -> GC=F`).
  - Test benchmark resolution (`market="VN" -> VNINDEX`, `market="US" -> SPY`).
  - Test that `market="VN"` strictly never calls Yahoo across:
    - `resolve_instrument_identity`
    - `get_verified_market_snapshot`
    - `settlement.get_closes` / `fetch_returns`
    - `route_to_vendor`
  - Test market propagation into `AgentState` via `create_run_state`.
- [ ] Run full test suite (`uv run pytest`) and linting (`uv run ruff check`).
