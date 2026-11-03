# Technical Design: Market-Aware Routing Foundation

## Context and Problem

TradingAgents currently assumes US-centric data flows with hardcoded Yahoo Finance call sites.
Specifically:
1. `tradingagents/agents/context.py:9` imports `get_company_profile` directly from `yahoo.fundamentals` for instrument identity.
2. `tradingagents/agents/tools.py:15` imports `build_verified_market_snapshot` directly from `yahoo.snapshot`.
3. `tradingagents/memory/settlement.py:11` imports `get_closes` directly from `yahoo.market`.
4. `tradingagents/dataflows/router.py` does not take `market` into account when selecting vendor chains.
5. `tradingagents/dataflows/symbols.py` normalizes symbols only for Yahoo conventions (e.g. `XAUUSD -> GC=F`, `BTCUSD -> BTC-USD`).
6. `tradingagents/default_config.py` and `tradingagents/api/schemas.py` have no explicit `market` field.

Per user requirements and architectural decisions for Vietnam stock market support:
- Vietnamese tickers (`VNM`, `SSI`, `VCB`, etc.) with `market="VN"` must **never** touch Yahoo Finance under any circumstances.
- All data paths must be market-aware and routed through the dataflows routing layer.
- Existing US market behavior and tests must remain 100% green and backwards-compatible.

## Architecture

```
[CLI / API / Graph State]
         │ (market="US" | "VN")
         ▼
[TradingAgents Configuration & State]
         │
         ├──► symbols.py: normalize_symbol(ticker, market)
         │       - market="VN" or .VN suffix: clean uppercase, strip .VN
         │       - market="US": Yahoo/crypto/forex rules
         │
         ├──► settlement.py: resolve_benchmark(ticker, config)
         │       - market="VN": default to VNINDEX (from benchmark_map[".VN"])
         │       - market="US": default to SPY
         │
         └──► router.py: route_to_vendor(method, *args, **kwargs)
                 ├── market="VN":
                 │     - Vendor chain: algolab, ssi
                 │     - Strict Yahoo filter: yfinance/yahoo disallowed
                 │     - Foundation stubs / typed errors if vendors not yet mounted
                 │
                 └── market="US":
                       - Vendor chain: yfinance (default) / alpha_vantage / sec_edgar
```

## Detailed Component Changes

### 1. `tradingagents/default_config.py`
- Add `"TRADINGAGENTS_MARKET": "market"` to `_ENV_OVERRIDES`.
- Add `"market": "US"` to default config dict.
- Add `".VN": "VNINDEX"` to `benchmark_map`.
- Add `"vn_data_vendors"` dict defining the default vendor chain for Vietnam (`"algolab,ssi"`).

### 2. `tradingagents/dataflows/symbols.py`
- Extend `normalize_symbol(raw: str, market: str | None = None) -> str`.
- If `market == "VN"` or `s.endswith(".VN")`:
  - Strip trailing `.VN` if present.
  - Return clean uppercase symbol.
  - Do not apply US/forex/metals rules.
- Retain `safe_ticker_component` behavior.

### 3. `tradingagents/dataflows/router.py`
- Register the missing methods in `TOOLS_CATEGORIES` and `VENDOR_METHODS`:
  - `get_verified_market_snapshot`: in `core_stock_apis`, mapped to Yahoo snapshot for US, stubs for VN.
  - `get_company_profile`: in `fundamental_data`, mapped to Yahoo fundamentals for US, stubs for VN.
  - `get_closes`: in `core_stock_apis`, mapped to Yahoo market for US, stubs for VN.
- Make `get_vendor` market-aware:
  - When `market == "VN"`, reads `vn_tool_vendors` / `vn_data_vendors` or defaults to `"algolab,ssi"`.
- In `route_to_vendor`:
  - Enforce guard: if `market == "VN"`, filter out `yfinance` and `yahoo` from `vendor_chain`.
  - Provide typed helper `get_closes(symbol: str, start_date: str, end_date: str) -> pd.Series`.
  - Provide typed helper `get_company_profile(ticker: str) -> dict`.

### 4. Direct Yahoo Call Sites Elimination
- `tradingagents/agents/context.py`:
  - Replace direct import of `get_company_profile` from `yahoo.fundamentals` with import from `tradingagents.dataflows.router`.
  - Pass `market` parameter down through `resolve_instrument_identity(ticker, market=None)`.
- `tradingagents/agents/tools.py`:
  - Replace direct import of `build_verified_market_snapshot` from `yahoo.snapshot`.
  - `get_verified_market_snapshot` delegates entirely to `route_to_vendor("get_verified_market_snapshot", symbol, as_of(curr_date, trade_date), look_back_days)`.
- `tradingagents/memory/settlement.py`:
  - Replace direct import of `get_closes` from `yahoo.market` with import from `tradingagents.dataflows.router`.
  - Update `resolve_benchmark` to handle `market == "VN"` returning `VNINDEX`.

### 5. API Schemas & Runtime State
- `tradingagents/api/schemas.py`:
  - `BacktestRunRequest`: add `market: str = Field("US", description="Target market ('US', 'VN')")`.
  - `ConfigResponse`: add `available_markets: list[str] = Field(default_factory=lambda: ["US", "VN"])`.
- `tradingagents/api/routes/config.py`:
  - Expose `available_markets=["US", "VN"]`.
- `tradingagents/agents/state.py`:
  - Add `market: Annotated[str, "Target market (e.g. US, VN)"]` to `AgentState`.
- `tradingagents/graph/propagation.py`:
  - Update `create_initial_state` to accept and set `market: str = "US"`.
- `tradingagents/graph/trading_graph.py`:
  - Propagate `market` from `self.config` to `create_run_state`, `resolve_instrument_context`, and initial state.
