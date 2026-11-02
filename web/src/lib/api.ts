import {
  BacktestRunRequest,
  ConfigResponse,
  ProviderModelsResponse,
  RunDetailResponse,
  RunListItem,
} from "../types";

const BASE_URL = "/api";

export async function fetchConfig(): Promise<ConfigResponse> {
  const res = await fetch(`${BASE_URL}/config`);
  if (!res.ok) throw new Error("Failed to fetch configuration");
  return res.json();
}

export async function fetchProviderModels(provider: string): Promise<ProviderModelsResponse> {
  const res = await fetch(`${BASE_URL}/config/models?provider=${encodeURIComponent(provider)}`);
  if (!res.ok) throw new Error(`Failed to fetch models for ${provider}`);
  return res.json();
}

export async function startBacktest(req: BacktestRunRequest): Promise<{ run_id: string; total_cells: number }> {
  const res = await fetch(`${BASE_URL}/backtest/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to start backtest");
  }
  return res.json();
}

export async function stopBacktest(run_id?: string): Promise<{ status: string }> {
  const url = run_id ? `${BASE_URL}/backtest/stop?run_id=${encodeURIComponent(run_id)}` : `${BASE_URL}/backtest/stop`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to stop backtest");
  }
  return res.json();
}

export async function resetBacktest(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE_URL}/backtest/reset`, { method: "POST" });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to reset backtest engine");
  }
  return res.json();
}

export async function fetchRuns(): Promise<RunListItem[]> {
  const res = await fetch(`${BASE_URL}/backtest/runs`);
  if (!res.ok) throw new Error("Failed to fetch run history");
  return res.json();
}

export async function fetchRunDetail(run_id: string): Promise<RunDetailResponse> {
  const res = await fetch(`${BASE_URL}/backtest/runs/${encodeURIComponent(run_id)}`);
  if (!res.ok) throw new Error(`Failed to fetch run ${run_id}`);
  return res.json();
}
