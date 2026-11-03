import React, { useEffect, useState } from "react";
import { Play, Settings2, Users, Calendar, AlertCircle, RefreshCw, Cpu, Database } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { fetchProviderModels } from "../lib/api";
import { BacktestRunRequest, ConfigResponse, ProviderModelsResponse } from "../types";

interface ConfigPanelProps {
  config: ConfigResponse | null;
  isRunning: boolean;
  onStart: (req: BacktestRunRequest) => void;
  onNavigateToMcp?: () => void;
}

const US_PRESET_TICKERS = [
  { label: "Tech Giants", tickers: "NVDA, AAPL, MSFT, GOOGL" },
  { label: "Semiconductors", tickers: "NVDA, AMD, TSM, AVGO" },
  { label: "Gold & Commodities", tickers: "XAUUSD, SILVER, WTI" },
  { label: "Crypto Top", tickers: "BTC, ETH, SOL" },
];

const VN_PRESET_TICKERS = [
  { label: "VN30 Core", tickers: "VNM, FPT, HPG, VCB, SSI, MWG" },
  { label: "Banking", tickers: "VCB, BID, CTG, TCB, MBB, ACB" },
  { label: "Securities & Tech", tickers: "SSI, VND, VCI, HCM, FPT" },
  { label: "Real Estate & Steel", tickers: "VHM, VIC, KDH, HPG, HSG" },
];

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, isRunning, onStart, onNavigateToMcp }) => {
  // Today's date YYYY-MM-DD
  const today = new Date().toISOString().split("T")[0];
  const defaultStart = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().split("T")[0];

  const [tickers, setTickers] = useState("NVDA, AAPL");
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);
  const [everyNDays, setEveryNDays] = useState(7);
  const [assetType, setAssetType] = useState("stock");
  const [market, setMarket] = useState("US");
  const [selectedAnalysts, setSelectedAnalysts] = useState<string[]>([
    "market",
    "social",
    "news",
    "fundamentals",
  ]);

  const vnWindowDays = config?.default_config?.vn_data_window_days || 730;
  const earliestVnDate = new Date(Date.now() - vnWindowDays * 24 * 3600 * 1000).toISOString().split("T")[0];

  // Model & Agent overrides
  const [llmProvider, setLlmProvider] = useState("nvidia");
  const [quickThinkLlm, setQuickThinkLlm] = useState("meta/llama-3.1-8b-instruct");
  const [deepThinkLlm, setDeepThinkLlm] = useState("nvidia/llama-3.1-nemotron-70b-instruct");
  const [maxDebateRounds, setMaxDebateRounds] = useState(1);
  const [maxRiskRounds, setMaxRiskRounds] = useState(1);
  const [runId, setRunId] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Dynamic models for selected provider
  const [providerModels, setProviderModels] = useState<ProviderModelsResponse | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const [customDeep, setCustomDeep] = useState(false);
  const [customQuick, setCustomQuick] = useState(false);

  // Fetch models whenever provider changes
  const loadModels = async (provider: string) => {
    setLoadingModels(true);
    try {
      const data = await fetchProviderModels(provider);
      setProviderModels(data);

      const deepIds = (data.deep_models || []).map((m) => m.id);
      const quickIds = (data.quick_models || []).map((m) => m.id);

      if (!deepIds.includes(deepThinkLlm) && !customDeep) {
        setDeepThinkLlm(data.default_deep);
      }
      if (!quickIds.includes(quickThinkLlm) && !customQuick) {
        setQuickThinkLlm(data.default_quick);
      }
    } catch (err) {
      console.warn("Could not load provider models", err);
    } finally {
      setLoadingModels(false);
    }
  };

  // Sync initial provider when config loads
  useEffect(() => {
    if (config?.default_config?.llm_provider) {
      setLlmProvider(config.default_config.llm_provider);
      if (config.default_config.deep_think_llm) {
        setDeepThinkLlm(config.default_config.deep_think_llm);
      }
      if (config.default_config.quick_think_llm) {
        setQuickThinkLlm(config.default_config.quick_think_llm);
      }
      if (config.default_config.market) {
        setMarket(config.default_config.market);
        if (config.default_config.market === "VN") {
          setTickers("VNM, FPT");
        }
      }
    } else if (config?.provider_details && config.provider_details.length > 0) {
      const active = config.provider_details.find((d) => d.has_key) || config.provider_details[0];
      setLlmProvider(active.id);
    }
  }, [config]);

  // Load models whenever llmProvider changes
  useEffect(() => {
    if (llmProvider) {
      loadModels(llmProvider);
    }
  }, [llmProvider]);

  const handleProviderChange = (newProvider: string) => {
    setLlmProvider(newProvider);
    setCustomDeep(false);
    setCustomQuick(false);
  };

  const handleMarketChange = (newMarket: string) => {
    setMarket(newMarket);
    setError(null);
    if (newMarket === "VN") {
      if (tickers === "NVDA, AAPL" || !tickers.trim()) {
        setTickers("VNM, FPT");
      }
      if (new Date(startDate) < new Date(earliestVnDate)) {
        setStartDate(earliestVnDate);
      }
    } else if (tickers === "VNM, FPT") {
      setTickers("NVDA, AAPL");
    }
  };

  const toggleAnalyst = (id: string) => {
    setSelectedAnalysts((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const setDuration = (days: number) => {
    const end = new Date();
    let startDays = days;
    if (market === "VN" && days > vnWindowDays) {
      startDays = vnWindowDays;
    }
    const start = new Date(Date.now() - startDays * 24 * 3600 * 1000);
    setEndDate(end.toISOString().split("T")[0]);
    setStartDate(start.toISOString().split("T")[0]);
  };

  const handleLaunch = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const tickerList = tickers
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);

    if (tickerList.length === 0) {
      setError("Please specify at least one ticker symbol.");
      return;
    }

    if (!startDate || !endDate) {
      setError("Please provide both start and end analysis dates.");
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError("Start date must be before or equal to end date.");
      return;
    }

    if (selectedAnalysts.length === 0) {
      setError("Please select at least one analyst.");
      return;
    }

    if (market === "VN" && new Date(startDate) < new Date(earliestVnDate)) {
      setError(
        `Date '${startDate}' is outside the supported Vietnam market data window (configured limit: ${vnWindowDays} days, earliest supported date: ${earliestVnDate}). Please choose a start date on or after ${earliestVnDate}.`
      );
      return;
    }

    const req: BacktestRunRequest = {
      tickers: tickerList,
      start_date: startDate,
      end_date: endDate,
      every_n_days: Number(everyNDays) || 7,
      asset_type: assetType,
      market: market,
      selected_analysts: selectedAnalysts,
      config_overrides: {
        llm_provider: llmProvider,
        quick_think_llm: quickThinkLlm,
        deep_think_llm: deepThinkLlm,
        max_debate_rounds: Number(maxDebateRounds),
        max_risk_discuss_rounds: Number(maxRiskRounds),
        market: market,
        ...(market === "VN" ? { benchmark_ticker: "VNINDEX" } : {}),
      },
      run_id: runId.trim() ? runId.trim() : null,
    };

    onStart(req);
  };

  return (
    <form onSubmit={handleLaunch} className="space-y-6">
      {error && (
        <div className="bg-destructive/15 border border-destructive/30 text-rose-300 px-4 py-3 rounded-lg flex items-center space-x-2 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Target Assets & Grid */}
      <Card className="border-border/60 bg-card/70">
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Instruments & Time Window</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Define the universe of assets and dates over which agent ratings will be evaluated.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">
              Ticker Symbols (comma-separated)
            </label>
            <Input
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
              placeholder="e.g. NVDA, AAPL, MSFT, XAUUSD"
              className="font-mono text-sm"
              disabled={isRunning}
            />
            <div className="flex flex-wrap gap-1.5 mt-2">
              <span className="text-[11px] text-muted-foreground self-center mr-1">Presets:</span>
              {(market === "VN" ? VN_PRESET_TICKERS : US_PRESET_TICKERS).map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => setTickers(preset.tickers)}
                  disabled={isRunning}
                  className="text-[11px] px-2 py-0.5 rounded bg-muted/70 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors border border-border/40"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Market</label>
              <select
                value={market}
                onChange={(e) => handleMarketChange(e.target.value)}
                disabled={isRunning}
                className="w-full h-9 rounded-md border border-input bg-background/50 px-2.5 text-xs focus:outline-none text-foreground"
              >
                <option value="US" className="bg-card text-foreground">United States (US)</option>
                <option value="VN" className="bg-card text-foreground">Vietnam (VN)</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Asset Type</label>
              <select
                value={assetType}
                onChange={(e) => setAssetType(e.target.value)}
                disabled={isRunning}
                className="w-full h-9 rounded-md border border-input bg-background/50 px-2.5 text-xs focus:outline-none text-foreground"
              >
                <option value="stock" className="bg-card text-foreground">Stock</option>
                {market !== "VN" && <option value="crypto" className="bg-card text-foreground">Crypto</option>}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Start Date</label>
              <Input
                type="date"
                min={market === "VN" ? earliestVnDate : undefined}
                max={today}
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={isRunning}
                className="text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">End Date</label>
              <Input
                type="date"
                min={market === "VN" ? earliestVnDate : undefined}
                max={today}
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={isRunning}
                className="text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Interval (Days)</label>
              <Input
                type="number"
                min={1}
                value={everyNDays}
                onChange={(e) => setEveryNDays(Math.max(1, parseInt(e.target.value) || 1))}
                disabled={isRunning}
                className="text-xs font-mono"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            <span className="text-[11px] text-muted-foreground self-center mr-1">Quick Range:</span>
            {[
              { label: "1 Month", days: 30 },
              { label: "3 Months", days: 90 },
              { label: "6 Months", days: 180 },
              { label: "1 Year", days: 365 },
            ].map((btn) => (
              <button
                key={btn.label}
                type="button"
                onClick={() => setDuration(btn.days)}
                disabled={isRunning}
                className="text-xs px-2.5 py-1 rounded bg-secondary/80 hover:bg-secondary text-secondary-foreground transition-colors border border-border/40"
              >
                {btn.label}
              </button>
            ))}
          </div>

          {market === "VN" && (
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs mt-2">
              <div className="flex items-center space-x-2 text-blue-300">
                <Database className="w-4 h-4 text-blue-400 shrink-0" />
                <span>Vietnam Market active: AlgoLab MCP + SSI MCP data pipeline</span>
              </div>
              {onNavigateToMcp && (
                <button
                  type="button"
                  onClick={onNavigateToMcp}
                  className="text-[11px] font-semibold text-primary hover:underline flex items-center space-x-1"
                >
                  <span>Manage MCP Auth</span>
                  <span>→</span>
                </button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analyst Team Selection */}
      <Card className="border-border/60 bg-card/70">
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Analyst Squad Configuration</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Select specialized agent analysts participating in the research phase before the trader debate.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { id: "market", name: "Market Analyst", desc: "Technical momentum, trend, moving averages" },
              { id: "social", name: "Social Sentiment", desc: "Social momentum, Reddit & StockTwits signals" },
              { id: "news", name: "News Analyst", desc: "Macro news, company events & headline sentiment" },
              { id: "fundamentals", name: "Fundamentals Analyst", desc: "Balance sheet, income statements & SEC filings" },
            ].map((analyst) => {
              const checked = selectedAnalysts.includes(analyst.id);
              return (
                <div
                  key={analyst.id}
                  onClick={() => !isRunning && toggleAnalyst(analyst.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    checked
                      ? "bg-primary/10 border-primary/40 text-foreground"
                      : "bg-muted/30 border-border/40 text-muted-foreground opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold">{analyst.name}</span>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {}}
                      disabled={isRunning}
                      className="rounded accent-primary w-4 h-4"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{analyst.desc}</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* LLM & Debate Parameters */}
      <Card className="border-border/60 bg-card/70">
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2">
            <Settings2 className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Model & Debate Hyperparameters</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Select LLM provider, auto-fetch models, and adjust multi-agent debate iterations.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* LLM Provider Select */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-muted-foreground">LLM Provider</label>
                <div className="flex items-center space-x-1.5">
                  {providerModels?.is_live && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                      Live ({providerModels.all_models.length})
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => loadModels(llmProvider)}
                    disabled={loadingModels || isRunning}
                    title="Refresh available models"
                    className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                  >
                    <RefreshCw className={`w-3 h-3 ${loadingModels ? "animate-spin" : ""}`} />
                  </button>
                </div>
              </div>
              <select
                value={llmProvider}
                onChange={(e) => handleProviderChange(e.target.value)}
                disabled={isRunning}
                className="w-full h-9 rounded-md border border-input bg-background/50 px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring text-foreground"
              >
                {(config?.provider_details || []).length > 0
                  ? config!.provider_details.map((p) => (
                      <option key={p.id} value={p.id} className="bg-card text-foreground">
                        {p.name} {p.has_key ? "✓ (Key Active)" : ""}
                      </option>
                    ))
                  : (config?.supported_providers || ["nvidia", "openai", "google"]).map((p) => (
                      <option key={p} value={p} className="bg-card text-foreground">
                        {p.toUpperCase()}
                      </option>
                    ))}
              </select>
            </div>

            {/* Deep Think Model */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-muted-foreground flex items-center space-x-1">
                  <Cpu className="w-3 h-3 text-primary" />
                  <span>Deep Think Model</span>
                </label>
                {customDeep ? (
                  <button
                    type="button"
                    onClick={() => setCustomDeep(false)}
                    className="text-[10px] text-primary hover:underline"
                  >
                    List
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setCustomDeep(true)}
                    className="text-[10px] text-muted-foreground hover:text-foreground"
                  >
                    Custom
                  </button>
                )}
              </div>

              {!customDeep && providerModels?.deep_models && providerModels.deep_models.length > 0 ? (
                <select
                  value={deepThinkLlm}
                  onChange={(e) => {
                    if (e.target.value === "__custom__") {
                      setCustomDeep(true);
                    } else {
                      setDeepThinkLlm(e.target.value);
                    }
                  }}
                  disabled={isRunning || loadingModels}
                  className="w-full h-9 rounded-md border border-input bg-background/50 px-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-ring text-foreground font-mono"
                >
                  {providerModels.deep_models.map((m) => (
                    <option key={m.id} value={m.id} className="bg-card text-foreground">
                      {m.name}
                    </option>
                  ))}
                  <option value="__custom__" className="bg-card text-primary font-sans">
                    ✏️ Enter Custom ID...
                  </option>
                </select>
              ) : (
                <Input
                  value={deepThinkLlm}
                  onChange={(e) => setDeepThinkLlm(e.target.value)}
                  disabled={isRunning}
                  placeholder="e.g. meta/llama-3.3-70b-instruct"
                  className="text-xs font-mono"
                />
              )}
            </div>

            {/* Quick Think Model */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-muted-foreground flex items-center space-x-1">
                  <Cpu className="w-3 h-3 text-emerald-400" />
                  <span>Quick Think Model</span>
                </label>
                {customQuick ? (
                  <button
                    type="button"
                    onClick={() => setCustomQuick(false)}
                    className="text-[10px] text-primary hover:underline"
                  >
                    List
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setCustomQuick(true)}
                    className="text-[10px] text-muted-foreground hover:text-foreground"
                  >
                    Custom
                  </button>
                )}
              </div>

              {!customQuick && providerModels?.quick_models && providerModels.quick_models.length > 0 ? (
                <select
                  value={quickThinkLlm}
                  onChange={(e) => {
                    if (e.target.value === "__custom__") {
                      setCustomQuick(true);
                    } else {
                      setQuickThinkLlm(e.target.value);
                    }
                  }}
                  disabled={isRunning || loadingModels}
                  className="w-full h-9 rounded-md border border-input bg-background/50 px-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-ring text-foreground font-mono"
                >
                  {providerModels.quick_models.map((m) => (
                    <option key={m.id} value={m.id} className="bg-card text-foreground">
                      {m.name}
                    </option>
                  ))}
                  <option value="__custom__" className="bg-card text-primary font-sans">
                    ✏️ Enter Custom ID...
                  </option>
                </select>
              ) : (
                <Input
                  value={quickThinkLlm}
                  onChange={(e) => setQuickThinkLlm(e.target.value)}
                  disabled={isRunning}
                  placeholder="e.g. meta/llama-3.1-8b-instruct"
                  className="text-xs font-mono"
                />
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                Max Bull/Bear Debate Rounds
              </label>
              <Input
                type="number"
                min={1}
                max={5}
                value={maxDebateRounds}
                onChange={(e) => setMaxDebateRounds(parseInt(e.target.value) || 1)}
                disabled={isRunning}
                className="text-xs font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                Max Risk Discussion Rounds
              </label>
              <Input
                type="number"
                min={1}
                max={5}
                value={maxRiskRounds}
                onChange={(e) => setMaxRiskRounds(parseInt(e.target.value) || 1)}
                disabled={isRunning}
                className="text-xs font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                Resume Sweep ID (Optional)
              </label>
              <Input
                value={runId}
                onChange={(e) => setRunId(e.target.value)}
                disabled={isRunning}
                placeholder="e.g. 20261102_120000"
                className="text-xs font-mono"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end pt-2">
        <Button
          type="submit"
          size="lg"
          disabled={isRunning}
          className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-8 shadow-lg shadow-primary/20"
        >
          <Play className="w-4 h-4 mr-2 fill-current" />
          Launch Backtest Sweep
        </Button>
      </div>
    </form>
  );
};
