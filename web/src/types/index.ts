export interface AnalystInfo {
  id: string;
  name: string;
  description: string;
}

export interface ProviderDetail {
  id: string;
  name: string;
  has_key: boolean;
  env_var: string | null;
}

export interface ModelOptionItem {
  id: string;
  name: string;
}

export interface ProviderModelsResponse {
  provider: string;
  is_live: boolean;
  default_deep: string;
  default_quick: string;
  quick_models: ModelOptionItem[];
  deep_models: ModelOptionItem[];
  all_models: ModelOptionItem[];
}

export interface ConfigResponse {
  default_config: Record<string, any>;
  supported_providers: string[];
  provider_details: ProviderDetail[];
  available_analysts: AnalystInfo[];
  available_asset_types: string[];
  available_markets?: string[];
}

export interface BacktestRunRequest {
  tickers: string[];
  start_date: string;
  end_date: string;
  every_n_days: number;
  asset_type: string;
  market?: string;
  selected_analysts: string[];
  config_overrides: Record<string, any>;
  run_id?: string | null;
}

export interface RatingScore {
  count: number;
  hit_rate: number | null;
  mean_alpha: number;
}

export interface BacktestSummary {
  resolved: number;
  pending: number;
  unscored: number;
  holding: string;
  by_rating: Record<string, RatingScore>;
  rendered_text: string;
}

export interface CellResult {
  ticker: string;
  date: string;
  rating?: string | null;
  alpha?: string | null;
  holding?: string | null;
  pending: boolean;
  decision?: string | Record<string, any> | null;
  reflection?: string | null;
  market_report?: string | null;
  fundamentals_report?: string | null;
  news_report?: string | null;
  sentiment_report?: string | null;
  investment_debate_state?: {
    bull_history?: string;
    bear_history?: string;
    history?: string;
    current_response?: string;
    [key: string]: any;
  } | null;
  investment_plan?: string | null;
  trader_investment_plan?: string | null;
  risk_debate_state?: {
    aggressive_history?: string;
    conservative_history?: string;
    neutral_history?: string;
    history?: string;
    [key: string]: any;
  } | null;
}

export interface RunDetailResponse {
  run_id: string;
  status: string;
  cells_run: number;
  skipped: number;
  failures: [string, string, string][];
  settlement_failures: [string, string][];
  summary: BacktestSummary | null;
  cells: CellResult[];
}

export interface RunListItem {
  run_id: string;
  created_at: string;
  has_log: boolean;
  cell_count: number;
  resolved_count: number;
  summary: BacktestSummary | null;
}

export interface ProgressData {
  done: number;
  total: number;
  percent: number;
  ticker: string;
  date: string;
}

export interface LogMessage {
  timestamp: string;
  level: string;
  message: string;
}

export interface AlgolabStatus {
  configured: boolean;
  connected: boolean;
  api_key_masked?: string | null;
  quota?: {
    used: number;
    limit: number;
    remaining?: number;
  } | null;
  error?: string | null;
}

export interface SsiStatus {
  configured: boolean;
  connected: boolean;
  client_id?: string | null;
  expires_in?: number | null;
  refreshed_at?: number | null;
  token_file?: string | null;
  error?: string | null;
}

export interface McpStatusResponse {
  algolab: AlgolabStatus;
  ssi: SsiStatus;
  market: string;
}

export interface McpTestResponse {
  status: string;
  vendor: string;
  latency_ms?: number | null;
  tools_count?: number | null;
  message?: string | null;
  quota?: {
    used: number;
    limit: number;
    remaining?: number;
  } | null;
}
