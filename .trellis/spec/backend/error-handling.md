# Error Handling Guidelines

> Error hierarchies, propagation strategies, and failure handling conventions in TradingAgents.

---

## Overview

TradingAgents separates error handling by architectural layer:
1. **Dataflows Layer**: Structured exception hierarchy rooted in `VendorError`. Caught by the router to trigger fallback vendors without crashing the agent pipeline.
2. **LLM Client Layer**: Explicit credential validation and domain errors (`ChatGPTAuthError`, `ValueError`).
3. **CLI Layer**: Clean interception of domain exceptions; errors are rendered in red via Rich and terminated via `typer.Exit(code=1)` without printing raw stack traces.

---

## Error Hierarchies

### 1. Data Vendor Errors (`tradingagents/dataflows/errors.py`)

All vendor data failures inherit from `VendorError`. The number of error classes corresponds to distinct router reactions:

```python
# tradingagents/dataflows/errors.py
class VendorError(Exception):
    """Base for all vendor data retrieval failures."""

class NoMarketDataError(VendorError):
    """Symbol unknown, delisted, or no records exist for the requested timeframe.
    Router reaction: Treats symbol data as absent; falls back or returns sentinel."""

class VendorUnavailableError(VendorError):
    """Remote service failure: timeout, 5xx, or unresolvable rate limit.
    Router reaction: Skips to next configured vendor in the fallback chain."""

class VendorNotConfiguredError(VendorError):
    """Missing API key or required environment variables.
    Router reaction: Warns and attempts next vendor without failing the entire run."""
```

### 2. Authentication Errors (`tradingagents/llm_clients/`)

- `ChatGPTAuthError` (`tradingagents/llm_clients/chatgpt_auth.py`): Raised when OAuth PKCE flow fails, token refresh is rejected, or signature validation fails.
- Missing API keys raise `ValueError` from `require_api_key(provider)` (`tradingagents/llm_clients/api_key_env.py`) with instructions on setting the required environment variable.

---

## Error Handling Patterns

### Dataflow Fallback Pattern (`tradingagents/dataflows/router.py`)

Vendors should raise `VendorError` subclasses instead of returning error strings or swallowing exceptions. The router manages the fallback sequence:

```python
# tradingagents/dataflows/router.py
for vendor in vendor_chain:
    try:
        return vendor_func(*args, **kwargs)
    except VendorUnavailableError as e:
        logger.warning("Vendor %r unavailable for %s: %s; trying next vendor.", vendor, method, e)
    except VendorNotConfiguredError as e:
        logger.warning("Vendor %r not configured for %s; trying next vendor.", vendor, method)
    except NoMarketDataError as e:
        logger.warning("No market data from %r for %s: %s", vendor, method, e)
```

### CLI Boundary Handling Pattern (`cli/main.py`)

Expected validation and setup errors must be caught at the CLI command boundary. Output formatted error text to the console and exit cleanly:

```python
# cli/main.py
try:
    dates = iter_grid(start, end, every)
    book = load_portfolio(portfolio) if portfolio else None
except ValueError as exc:
    console.print(f"[red]{exc}[/red]")
    raise typer.Exit(code=1) from None
```

### Terminal Environment Handling

When running interactively, catch platform-specific headless terminal errors (`prompt_toolkit` buffer errors on Windows) cleanly:

```python
# cli/main.py
try:
    run_analysis(checkpoint=checkpoint, portfolio=portfolio_context, flags=flags)
except _NO_CONSOLE_ERRORS:
    typer.echo("Error: no Windows console available. Run from an interactive console.", err=True)
    raise typer.Exit(code=1) from None
```

---

## Anti-Patterns to Avoid

- **No Silent Exception Swallowing**: Never write `except Exception: pass` in vendors or agent nodes. At minimum, log the failure at `WARNING` level with `logger.warning(...)`.
- **No Direct CLI Tracebacks**: Do not let standard library exceptions (`ValueError`, `FileNotFoundError`, `KeyError`) bubble past Typer command functions without user-friendly messaging.
- **No Raw String Error Returns**: Do not return `"Error: failed"` as a string return value when data retrieval fails. Raise `NoMarketDataError` or `VendorUnavailableError` so the router can make informed fallback decisions.
