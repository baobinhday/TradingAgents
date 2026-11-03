# Market-aware routing foundation

## Goal

Add an explicit market concept (`market="VN" | "US" | ...`) and route every data path by market, completely eliminating direct Yahoo call sites for Vietnamese equities.

## Requirements

1. **Market Enum / Literal**:
   - Define supported markets (e.g. `US`, `VN`) in configuration and schemas.
   - Default to `US` when omitted to preserve backward compatibility.
2. **Eliminate Direct Yahoo Call Sites**:
   - Refactor `tradingagents/agents/context.py:9` (symbol resolution / metadata).
   - Refactor `tradingagents/agents/tools.py:15` (tool helper fallback).
   - Refactor `tradingagents/memory/settlement.py:11` (benchmark & price settlement).
   - All call sites must route via `tradingagents/dataflows/router.py` or a market-aware dispatcher.
3. **Symbol Normalization**:
   - Update `tradingagents/dataflows/symbols.py`: Vietnamese tickers (`SSI`, `VNM`, `VCB`, `BSR`, `PVS`) remain clean uppercase alphanumeric without `.VN` suffix when targeted at SSI MCP.
4. **Benchmark Mapping**:
   - Update `tradingagents/default_config.py` `benchmark_map` to map `VN` to `VNINDEX` (or `VN30`).

## Acceptance Criteria

- [x] All direct Yahoo call sites route through market-aware vendor abstraction.
- [x] Passing a Vietnamese ticker with `market="VN"` never invokes Yahoo Finance.
- [x] Existing US market behavior and regression tests remain 100% green.
- [x] Unit tests verify market parameter propagation from CLI, API schemas, and runtime agents.
