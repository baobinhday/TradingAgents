# Logging Guidelines

> Logging standards, levels, and console output conventions in TradingAgents.

---

## Overview

TradingAgents separates logging into three clear categories:
1. **Application Logging**: Python standard library `logging` module used across all core modules under `tradingagents/`.
2. **Terminal Console Display**: `rich.console.Console` used in `cli/` for human-facing interaction, status updates, and progress bars.
3. **Auditable Trading Memory**: Markdown-formatted records (`tradingagents/memory/log.py`) preserving decisions and post-trade reflections for agent context injection.

---

## Standard Library Logging Conventions

Every module in `tradingagents/` instantiates its own logger using `__name__`:

```python
import logging

logger = logging.getLogger(__name__)
```

### Log Levels

| Level | When to Use | Local Code Example |
|---|---|---|
| `DEBUG` | Fine-grained tracing, payload inspection, identity resolution | `logger.debug("Could not resolve instrument identity for %s: %s", ticker, exc)` (`tradingagents/agents/context.py:81`) |
| `INFO` | Major lifecycle milestones (fresh run start, checkpoint resume, model initialization) | `logger.info("Resuming from step %d for %s on %s", step, company_name, trade_date)` (`tradingagents/graph/trading_graph.py:216`) |
| `WARNING` | Non-fatal issues: fallback activations, API rate limits, missing optional data | `logger.warning("Vendor %r unavailable for %s: %s; trying next vendor.", vendor, method, e)` (`tradingagents/dataflows/router.py:238`) |
| `ERROR` | Unrecoverable failures or data corruption requiring intervention | Internal errors that prevent a graph node from continuing |

### Formatting Rule: Deferred Interpolation

Always use standard printf-style interpolation (`%s`, `%r`, `%d`) in `logger.*` calls rather than Python f-strings:

```python
# CORRECT: Arguments are evaluated only if the log level is active
logger.warning("Backtest cell %s %s failed: %s", ticker, date, exc)

# INCORRECT: Avoid f-strings in logging calls
logger.warning(f"Backtest cell {ticker} {date} failed: {exc}")
```

---

## Terminal Display Conventions (`cli/`)

Interactive terminal messages belong in `cli/` and must use `cli.display.console`:

```python
from cli.display import console
from rich.markup import escape

# Colored user feedback
console.print(f"[red]Error:[/red] {escape(message)}")
console.print(f"[green]Success:[/green] {escape(summary)}")
console.print(f"[dim][{done}/{total}] {ticker} {date}[/dim]")
```

### Escaping Dynamic Content
When passing dynamic strings (tickers, usernames, exception messages) to `console.print()`, wrap them with `rich.markup.escape()` to prevent Rich markup injection:

```python
# cli/main.py
console.print(f"[red]{escape(str(exc))}[/red]")
```

---

## What NOT to Log

- **Never log API keys or secrets**: Ensure `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and OAuth tokens are never passed to loggers or printed to the console unmasked.
- **Do not log raw personal credentials**: Mask user emails or OAuth refresh tokens.
