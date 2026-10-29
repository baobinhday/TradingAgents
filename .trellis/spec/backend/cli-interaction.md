# CLI & Interactive Form Guidelines

> Conventions for Typer commands, Questionary interactive prompts ("terminal forms"), and authentication flows.

---

## Overview

TradingAgents does not include a web frontend or HTML forms. The terminal interface in `cli/` provides two interaction modes:
1. **Interactive Prompt Mode ("Terminal Forms")**: Interactive step-by-step questions powered by `questionary` when arguments are omitted.
2. **Headless / Unattended Mode**: Non-interactive execution driven by CLI flags or `TRADINGAGENTS_*` environment variables.

---

## Interactive Forms with Questionary (`cli/prompts.py`)

Interactive questionnaires serve as the project's input forms. All prompts follow consistent styling and validation conventions:

### Menu Styling
Menus share a unified style defined in `cli/prompts.py`:

```python
_MENU_STYLE = questionary.Style([
    ("selected", "fg:magenta noinherit"),
    ("highlighted", "fg:magenta noinherit"),
    ("pointer", "fg:magenta noinherit"),
])
```

### Form Input Types

1. **Validated Text Inputs (`questionary.text`)**:
   - Used for ticker entry, dates, and custom model IDs.
   - Always supply an inline `validate` callback returning `True` or an informative error message string.
   - Example (`cli/prompts.py: get_ticker`):
     ```python
     ticker = questionary.text(
         f"Enter ticker symbol (e.g. {TICKER_INPUT_EXAMPLES}):",
         validate=lambda x: (
             is_valid_ticker_input(x)
             or "Please enter a valid ticker symbol, e.g. AAPL, 000404.SZ, 0700.HK, GC=F."
         ),
     ).ask()
     if ticker is None:  # User cancelled via Ctrl-C or Esc
         exit(1)
     ```

2. **Single-Select Dropdowns (`questionary.select`)**:
   - Used for choosing LLM providers, thinking depth, analysis modes, and languages.
   - Encapsulate options into `questionary.Choice(display_text, value=internal_value)`.
   - Always supply a default choice matching previous user preferences or recommended defaults:
     ```python
     choice = questionary.select(
         "Select thinking depth:",
         choices=[questionary.Choice(display, value=value) for display, value in DEPTH_OPTIONS],
         default=previous_preference,
         style=_MENU_STYLE,
     ).ask()
     ```

3. **Multi-Select Checkboxes (`questionary.checkbox`)**:
   - Used for selecting analysts (Market, Sentiment, News, Fundamentals).
   - Pre-check default choices based on asset type compatibility.

4. **Secret / Password Prompts (`questionary.password`)**:
   - Used for prompting missing API keys (`cli/prompts.py: prompt_api_key`) without echoing text.
   - Offers to persist the entered key into local `.env` using `python-dotenv`'s `set_key()`.

### Handling Cancellation & Non-Interactive Terminals
- **Ctrl-C / Esc**: `questionary.*.ask()` returns `None`. Check for `None` immediately and exit cleanly without raising unhandled `KeyboardInterrupt` exceptions.
- **Missing Console Buffer**: Windows non-interactive or piped shells raise `NoConsoleScreenBufferError`. Catch `_NO_CONSOLE_ERRORS` at the CLI boundary (`cli/main.py`) and emit a clear error advising the user to pass explicit CLI flags or run in an interactive terminal.

---

## Typer Command Conventions (`cli/main.py`)

Commands use `typer.Typer`:

```python
app = typer.Typer(
    name="TradingAgents",
    help="TradingAgents CLI: Multi-Agents LLM Financial Trading Framework",
    add_completion=True,
)
```

1. **Default Action as Callback**:
   - The primary command `analyze` is defined as `@app.callback(invoke_without_command=True)`.
   - Running `tradingagents` with no subcommand invokes `analyze`.
   - Check `if ctx.invoked_subcommand is not None: return` so subcommands (`backtest`, `login`) do not inadvertently run the analysis pipeline.

2. **Flag Conventions**:
   - Boolean toggles: Use paired flags, e.g., `--checkpoint/--no-checkpoint`, `--save/--no-save`, `--html/--no-html`.
   - Comma-separated strings: Multi-value flags (`--tickers NVDA,AAPL`, `--analysts market,news`) should be parsed and split cleanly with whitespace stripped.

---

## Authentication Patterns (`tradingagents/llm_clients/`)

1. **Provider Key Mapping (`api_key_env.py`)**:
   - Maintain the single source of truth in `PROVIDER_API_KEY_ENV`.
   - Use `get_api_key_env(provider)` to resolve environment variable names.
   - Use `require_api_key(provider)` before initializing provider clients.

2. **OAuth PKCE for ChatGPT (`chatgpt_auth.py`)**:
   - Used only for ChatGPT Plus/Pro subscriptions.
   - Generates PKCE code challenge and opens verification URL in terminal.
   - Caches tokens in OS keyring or permissions-restricted file (`0600`).
