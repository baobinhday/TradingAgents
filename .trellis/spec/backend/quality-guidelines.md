# Quality & Testing Guidelines

> Code standards, linting rules, test isolation, and forbidden patterns in TradingAgents.

---

## Overview

TradingAgents enforces strict quality gates through automated Ruff linting, architectural layering tests, and isolated Pytest execution.

---

## Linting & Code Style (`pyproject.toml`)

The repository enforces Ruff with targeted rule suites:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
extend-exclude = ["results"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"**/__init__.py" = ["F401"]   # intentional re-exports

[tool.ruff.lint.isort]
combine-as-imports = true
```

### Key Linting Rules
- **Import Ordering (isort `I`)**: Imports must be organized in standard library, third-party, and first-party blocks. Combine multiple aliased names from one module into a single statement.
- **Python 3.11 Modernization (`UP`)**: Use built-in type union syntax (`str | None` instead of `Optional[str]`), `list[str]` instead of `List[str]`, etc.
- **Comprehensions & Simplifications (`C4`, `SIM`)**: Prefer direct dict/set/list comprehensions and simplified boolean checks.

---

## Testing Standards (`tests/`)

### Test Markers & Invocation
Pytest runs in offline unit test mode by default:

```bash
# Run standard unit tests (integration tests skipped)
pytest

# Run only integration tests requiring external connectivity
pytest -m integration
```

### Strict Test Isolation (`tests/conftest.py`)
All unit tests are subject to autouse isolation fixtures:

1. **Network Lockdown (`_no_network`)**:
   - `socket.socket.connect`, `socket.socket.connect_ex`, `socket.getaddrinfo`, and `curl_cffi` sessions are monkeypatched to throw `OSError` immediately if touched during unit tests.
   - External API calls in unit tests must be mocked (e.g., using `unittest.mock.patch` or fixture injection).

2. **Filesystem Isolation (`_own_file_locations`, `_own_cli_prefs`)**:
   - Cache, results, and memory log locations are directed to temporary directories (`tempfile.mkdtemp`).
   - Tests must **never** read from or write to `~/.tradingagents/`.

3. **Environment & API Key Sanitization (`_blank_settings_overlay`, `_dummy_api_keys`)**:
   - Contributor `.env` files are neutralized so local developer settings do not alter test expectations.
   - Provider API keys (`OPENAI_API_KEY`, etc.) are assigned placeholder values so absence of real keys does not fail test runs.

4. **Global Config Reset (`_isolate_config`)**:
   - The global `tradingagents.dataflows.config._config` dictionary is deep-copied from `DEFAULT_CONFIG` before and restored after every single test.

---

## CLI Testing Pattern

CLI commands are tested via Typer's `CliRunner` without launching separate sub-processes:

```python
# tests/test_cli_commands.py
from typer.testing import CliRunner
import cli.main as m

@pytest.mark.unit
def test_cli_command(monkeypatch):
    runner = CliRunner()
    # Mock underlying action to record parameters
    calls = []
    monkeypatch.setattr(m, "run_analysis", lambda **kw: calls.append(kw))
    
    result = runner.invoke(m.app, ["--checkpoint"])
    assert result.exit_code == 0
    assert calls[0]["checkpoint"] is True
```

---

## Forbidden Patterns

| Forbidden Pattern | Reason | Enforced By |
|---|---|---|
| Direct import of `yfinance` outside `tradingagents/dataflows/` | Bypasses error handling, caching, and rate limiting | `tests/test_layering.py` |
| Import of `cli` from inside `tradingagents` | Breaks library decoupling and makes headless use impossible | Code review & tests |
| Unmocked socket connection in a unit test | Causes slow runs, non-deterministic CI failures, and leaks network calls | `tests/conftest.py: _no_network` |
| Writing test artifacts to `~/.tradingagents` | Pollutes contributor's local machine and creates state leakage | `tests/conftest.py: _own_file_locations` |
| Unhandled exceptions leaking tracebacks to CLI users | Degrades user experience; errors must be styled and exited via `typer.Exit(1)` | Code review & CLI tests |
| Returning string error descriptions instead of raising `VendorError` | Prevents vendor router from executing fallback logic | Router contracts |
