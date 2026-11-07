# Technical Design: Bootstrap Guidelines

**Status:** Completed
<!-- Lifecycle: Draft -> Approved -> Completed -->
**Topic Path:** `.trellis/research/00-bootstrap-guidelines/`
**PRD Reference:** [prd.md](./prd.md)

## 1. Architecture & Component Boundaries
- Standardizes durable conventions under `.trellis/spec/backend/`:
  - `directory-structure.md`: Layout of tradingagents, agents, dataflows, web, tests.
  - `database-guidelines.md`: Caching, persistence, and data schema rules.
  - `error-handling.md`: Vendor error mapping, fallback policies, exception hierarchies.
  - `logging-guidelines.md`: Structured logging, trace formats, log paths.
  - `quality-guidelines.md`: Code review standards, pytest verification, ruff linting.
  - `cli-interaction.md`: CLI commands, argument parsing, prompt standards.

---

## 2. Invariants & Implementation Standards
- Spec documents reflect current code reality rather than aspirational designs.
- All guidelines reference real codebase examples from TradingAgents.
