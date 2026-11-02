from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BacktestRunRequest(BaseModel):
    tickers: list[str] = Field(..., description="List of ticker symbols to backtest")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    every_n_days: int = Field(7, ge=1, description="Interval in days between analysis dates")
    asset_type: str = Field("stock", description="'stock' or 'crypto'")
    selected_analysts: list[str] = Field(
        default_factory=lambda: ["market", "social", "news", "fundamentals"],
        description="List of analyst modules to run",
    )
    config_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration overrides (e.g. llm_provider, deep_think_llm, rounds)",
    )
    portfolio: dict[str, Any] | None = Field(
        None, description="Optional portfolio context (holdings, cash)"
    )
    run_id: str | None = Field(
        None, description="Optional run_id to resume or append to an earlier sweep"
    )


class RatingScoreResponse(BaseModel):
    count: int
    hit_rate: float | None = None
    mean_alpha: float


class BacktestSummaryResponse(BaseModel):
    resolved: int
    pending: int
    unscored: int = 0
    holding: str = ""
    by_rating: dict[str, RatingScoreResponse] = Field(default_factory=dict)
    rendered_text: str = ""


class CellResult(BaseModel):
    ticker: str
    date: str
    rating: str | None = None
    alpha: str | None = None
    holding: str | None = None
    pending: bool = False
    decision: dict[str, Any] | None = None


class RunDetailResponse(BaseModel):
    run_id: str
    status: str
    cells_run: int = 0
    skipped: int = 0
    failures: list[tuple[str, str, str]] = Field(default_factory=list)
    settlement_failures: list[tuple[str, str]] = Field(default_factory=list)
    summary: BacktestSummaryResponse | None = None
    cells: list[CellResult] = Field(default_factory=list)


class RunListItem(BaseModel):
    run_id: str
    created_at: str
    has_log: bool
    cell_count: int = 0
    resolved_count: int = 0
    summary: BacktestSummaryResponse | None = None


class ProviderDetail(BaseModel):
    id: str
    name: str
    has_key: bool = False
    env_var: str | None = None


class ConfigResponse(BaseModel):
    default_config: dict[str, Any]
    supported_providers: list[str]
    provider_details: list[ProviderDetail] = Field(default_factory=list)
    available_analysts: list[dict[str, str]]
    available_asset_types: list[str]
