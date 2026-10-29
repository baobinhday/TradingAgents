# Backend & Core Development Guidelines

> Concrete coding guidelines, architectural boundaries, and design patterns for TradingAgents.

---

## Overview

TradingAgents is a multi-agent LLM financial trading framework. This directory documents the actual patterns used across the core library (`tradingagents/`), CLI application (`cli/`), and test suite (`tests/`).

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Package architecture, module responsibilities, and layer boundaries | Complete |
| [Error Handling](./error-handling.md) | Vendor error hierarchy, fallback loops, and CLI error exits | Complete |
| [Logging Guidelines](./logging-guidelines.md) | Standard library logging, Rich console output, and memory logs | Complete |
| [Persistence & Checkpointing](./database-guidelines.md) | SQLite checkpointer, market data caching, and filesystem persistence | Complete |
| [Quality Guidelines](./quality-guidelines.md) | Ruff linting rules, test isolation fixtures, and forbidden patterns | Complete |
| [CLI & Interactive Forms](./cli-interaction.md) | Typer commands, Questionary terminal forms, and authentication flows | Complete |

---

## Development Principles

1. **Reality Over Ideals**: Specs strictly reflect existing codebase patterns verified against source code and tests.
2. **Layering Integrity**: Data vendors remain encapsulated inside `tradingagents/dataflows/`; `tradingagents/` remains headless without depending on `cli/`.
3. **Deterministic Testing**: All unit tests run in offline isolation with mocked sockets, temporary filesystem roots, and deep-copied configuration.
