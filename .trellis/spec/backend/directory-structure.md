# Directory Structure & Layering Guidelines

> Architectural layout, package boundaries, and layering conventions for TradingAgents.

---

## Overview

TradingAgents is a Python framework organized into two top-level runtime packages:
1. `cli/`: Terminal interface, interactive prompts, argument parsing, and display rendering.
2. `tradingagents/`: Core multi-agent financial analysis library, LangGraph workflows, dataflows, LLM clients, and memory persistence.

Tests live at the top-level `tests/` directory and enforce architectural boundaries.

---

## Directory Layout

```
.
├── cli/                                  # Terminal CLI application (Typer + Questionary + Rich)
│   ├── main.py                           # Typer entry points (analyze, backtest, login, logout)
│   ├── prompts.py                        # Interactive terminal forms (Questionary prompts & validators)
│   ├── display.py                        # Rich console output formatting & token display
│   ├── prefs.py                          # Local CLI preferences persistence (~/.tradingagents/cli_prefs.json)
│   ├── models.py                         # CLI data types and Enums (AnalystType, AssetType)
│   ├── run.py                            # Execution runner bridging CLI flags to core graph
│   └── static/                           # CLI welcome banner assets
├── tradingagents/                        # Core library and multi-agent framework
│   ├── agents/                           # Agent definitions, prompts, and tool attachments
│   │   ├── analysts/                     # Market, news, fundamentals, sentiment analysts
│   │   ├── managers/                     # Research and portfolio managers
│   │   ├── researchers/                  # Bull and bear thesis debators
│   │   ├── risk_mgmt/                    # Conservative, aggressive, neutral risk debators
│   │   ├── tools.py                      # Tool bindings bridging agent calls to dataflows
│   │   └── context.py                    # Prompt building, localization, and instrument context
│   ├── dataflows/                        # Financial data providers and vendor abstraction
│   │   ├── router.py                     # Central vendor router with fallback chains (route_to_vendor)
│   │   ├── errors.py                     # VendorError hierarchy for error categorization
│   │   ├── symbols.py                    # Ticker sanitization, normalization, and alias mapping
│   │   ├── date_window.py                # Look-ahead prevention and date window utilities
│   │   ├── files.py                      # Local file-based caching for vendor data
│   │   ├── config.py                     # Runtime dataflows configuration accessor
│   │   └── vendors/                      # Isolated vendor implementations
│   │       ├── yahoo/                    # Yahoo Finance market, OHLCV, fundamentals, news
│   │       ├── alpha_vantage/            # Alpha Vantage indicators and stock data
│   │       ├── sec_edgar.py              # SEC 10-K/10-Q filing retrieval
│   │       ├── reddit.py                 # Reddit social sentiment
│   │       ├── stocktwits.py             # StockTwits sentiment
│   │       ├── polymarket.py             # Prediction market data
│   │       └── fred.py                   # Federal Reserve macroeconomic data
│   ├── graph/                            # LangGraph state machine & execution flow
│   │   ├── trading_graph.py              # TradingAgentsGraph orchestration engine
│   │   ├── setup.py                      # Graph compilation and analyst turn routing
│   │   ├── conditional_logic.py          # Conditional branching logic for debate rounds
│   │   └── checkpointer.py               # SQLite per-ticker checkpoint manager
│   ├── llm_clients/                      # Multi-provider LLM abstraction
│   │   ├── factory.py                    # Client instantiation factory
│   │   ├── api_key_env.py                # Mapping providers to environment variable keys
│   │   ├── openai_client.py              # OpenAI, OpenRouter, Ollama, xAI, DeepSeek, Qwen, GLM
│   │   ├── anthropic_client.py           # Anthropic Claude client
│   │   ├── google_client.py              # Google Gemini client
│   │   ├── azure_client.py               # Azure OpenAI enterprise client
│   │   ├── bedrock_client.py             # AWS Bedrock client
│   │   ├── chatgpt_auth.py               # OAuth PKCE flow for ChatGPT Plus/Pro subscription
│   │   ├── capabilities.py               # Provider feature flags (thinking, json_schema, tools)
│   │   └── model_catalog.py              # Catalog of supported models and tiers
│   ├── memory/                           # Historical trade logging and reflection
│   │   ├── log.py                        # Markdown memory log parser & prompt injector
│   │   ├── settlement.py                 # Post-trade price resolution and PnL settlement
│   │   └── reflection.py                 # Post-mortem evaluation of past decisions
│   ├── default_config.py                 # Global defaults and TRADINGAGENTS_* env-var ingestion
│   ├── portfolio.py                      # JSON portfolio holdings loader
│   ├── reporting.py                      # Markdown report compilation
│   ├── report_html.py                    # Static, CSP-hardened HTML report generator
│   └── backtest.py                       # Historical backtesting grid runner
└── tests/                                # Automated tests with strict sandbox isolation
    ├── conftest.py                       # Autouse fixtures: no network, temp dirs, dummy keys
    ├── test_layering.py                  # Architectural boundary enforcement test
    └── ...                               # Unit and integration test modules
```

---

## Architectural Boundaries & Layering Rules

1. **Vendor Library Isolation**:
   - Only `tradingagents/dataflows/` may import vendor-specific client libraries (e.g., `yfinance`).
   - Direct imports of vendor libraries from `cli/` or other `tradingagents/` modules are strictly forbidden.
   - Enforced by AST check in `tests/test_layering.py`:
     ```python
     # tests/test_layering.py
     def test_vendor_libraries_are_imported_only_by_the_data_layer():
         data_layer = ROOT / "tradingagents" / "dataflows"
         ...
     ```

2. **One-Way Dependency (`cli/` -> `tradingagents/`)**:
   - `cli/` modules import from `tradingagents/` to run analyses, load portfolios, and inspect models.
   - `tradingagents/` must **never** import anything from `cli/`. Core library functionality must remain completely headless and scriptable without terminal dependencies.

3. **Vendor Router Abstraction**:
   - Agents and tools must never call vendor functions directly. They must invoke `tradingagents.dataflows.router.route_to_vendor(method, *args, **kwargs)` (`tradingagents/agents/tools.py`).
   - Vendor modules raise specific subclasses of `VendorError` from `tradingagents.dataflows.errors`. The router catches them and initiates fallback chains or yields clean sentinels (`no_data_available()`, `vendor_unavailable()`).

4. **Configuration Precedence**:
   - `DEFAULT_CONFIG` (`tradingagents/default_config.py`) sets baselines and automatically loads `TRADINGAGENTS_*` environment variables.
   - CLI flags override configuration settings for the current execution.
   - Direct programmatic parameters to `TradingAgentsGraph(config=...)` take highest precedence.
