# Persistence & Checkpointing Guidelines

> Data persistence, SQLite checkpointing, and local storage conventions in TradingAgents.

---

## Overview

TradingAgents **does not use a traditional relational ORM or migration framework** (such as SQLAlchemy, Django ORM, or Alembic).

State and persistence in this codebase are managed through:
1. **SQLite Checkpointing**: Resumable multi-agent execution state via LangGraph's `SqliteSaver`.
2. **File-Based Market Data Caching**: Local disk caching for vendor data to reduce network overhead and respect rate limits.
3. **Markdown Memory Logging**: Append-only markdown logs storing decisions, rationales, and settlement outcomes.
4. **Local Configuration & Preferences**: JSON files storing user CLI preferences and securely cached auth tokens.

---

## SQLite Checkpointing (`tradingagents/graph/checkpointer.py`)

Checkpoints enable interrupted analysis workflows to resume without repeating completed analyst nodes.

### Per-Ticker Isolation
Each ticker has its own dedicated SQLite database file under `<cache_dir>/checkpoints/<ticker>.db`. This prevents lock contention when running concurrent ticker analyses:

```python
# tradingagents/graph/checkpointer.py
def get_checkpointer(data_dir: str | Path, ticker: str) -> Generator[SqliteSaver, None, None]:
    p = Path(data_dir) / "checkpoints"
    p.mkdir(parents=True, exist_ok=True)
    db = p / f"{ticker}.db"
    conn = sqlite3.connect(str(db), check_same_thread=False)
    yield SqliteSaver(conn)
```

### Path Sanitization Guard
Ticker inputs are sanitized before forming database paths to prevent directory traversal:

```python
# tradingagents/graph/checkpointer.py
safe_ticker = safe_ticker_component(ticker)
```

### Checkpoint Lifecycle
- **Resumption**: `TradingAgentsGraph.begin_checkpoint(...)` inspects `checkpoint_step(...)` to determine if a valid prior step exists.
- **Cleanup on Success**: Completed runs delete the checkpoint (`clear_checkpoint_on_success(...)`) to avoid retaining stale execution state.
- **WAL & Sidecar File Cleanup**: When clearing checkpoint databases, SQLite Write-Ahead Log files (`.db-wal` and `.db-shm`) must also be removed:
  ```python
  # tradingagents/graph/checkpointer.py
  for suffix in ("", "-wal", "-shm"):
      sidecar = db.with_name(db.name + suffix)
      if sidecar.exists():
          sidecar.unlink()
  ```

---

## File-Based Persistence Conventions

### 1. Market Data Cache (`tradingagents/dataflows/files.py`)
- Cached vendor payloads are stored in the configured `data_cache_dir` (default: `~/.tradingagents/cache/`).
- File operations catch lock errors gracefully (`logger.warning("Kept the cached %s; it is in use", path.name)`).
- Look-ahead guards ensure that cached data fetched for a past date does not leak subsequent trading bars.

### 2. Decision Memory Log (`tradingagents/memory/log.py`)
- Stored as Markdown at `TRADINGAGENTS_MEMORY_LOG_PATH` (default: `~/.tradingagents/trading_memory.md`).
- Contains sections for date, ticker, analyst findings, bull/bear debates, risk manager scores, and final decisions.
- Loaded into prompt context for future agent runs to enable historical reflection.

### 3. Local CLI Preferences (`cli/prefs.py`)
- User selections (last-used analysts, preferred providers, model choices) persist in `~/.tradingagents/cli_prefs.json`.
- In unit tests, `tests/conftest.py` automatically overrides `cli.prefs._PREFS_PATH` to point to a temporary test directory.

### 4. Auth Credential Storage (`tradingagents/llm_clients/chatgpt_auth.py`)
- ChatGPT tokens use OS keyring first; if unavailable, fallback storage writes to a JSON file explicitly constrained to owner-only permissions (`0600` via `os.chmod`).
