import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Key,
  CheckCircle2,
  Clock,
  Layers,
  Database,
  Lock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import {
  fetchMcpStatus,
  startSsiAuth,
  submitSsiTokens,
  testSsiConnection,
  submitAlgolabKey,
  testAlgolabConnection,
} from "../lib/api";
import { McpStatusResponse, McpTestResponse } from "../types";

export const McpPanel: React.FC = () => {
  const [status, setStatus] = useState<McpStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [testSsiLoading, setTestSsiLoading] = useState(false);
  const [testAlgolabLoading, setTestAlgolabLoading] = useState(false);

  // Manual token input states
  const [showManualSsi, setShowManualSsi] = useState(false);
  const [manualAccessToken, setManualAccessToken] = useState("");
  const [manualRefreshToken, setManualRefreshToken] = useState("");
  const [manualClientId, setManualClientId] = useState("");
  const [savingTokens, setSavingTokens] = useState(false);

  // AlgoLab key input states
  const [algolabKeyInput, setAlgolabKeyInput] = useState("");
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [savingAlgolabKey, setSavingAlgolabKey] = useState(false);

  // Test result notices
  const [ssiTestResult, setSsiTestResult] = useState<McpTestResponse | null>(null);
  const [algolabTestResult, setAlgolabTestResult] = useState<McpTestResponse | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await fetchMcpStatus();
      setStatus(data);
    } catch (err: any) {
      console.error("Failed to load MCP status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();

    // Listen for OAuth completion message from popup
    const handleAuthMessage = (event: MessageEvent) => {
      if (event.data?.type === "SSI_AUTH_SUCCESS") {
        setActionMessage({
          type: "success",
          text: "SSI MCP successfully authenticated via OAuth PKCE!",
        });
        loadStatus();
      }
    };
    window.addEventListener("message", handleAuthMessage);
    return () => window.removeEventListener("message", handleAuthMessage);
  }, []);

  const handleStartSsiOAuth = async () => {
    setOauthLoading(true);
    setActionMessage(null);
    try {
      // Current origin for callback
      const redirectUri = `${window.location.origin}/api/mcp/ssi/callback`;
      const res = await startSsiAuth(redirectUri);

      // Open OAuth authorize popup
      const width = 540;
      const height = 740;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;
      const popup = window.open(
        res.auth_url,
        "SSI_MCP_Auth",
        `width=${width},height=${height},left=${left},top=${top},status=0,toolbar=0,menubar=0`
      );

      // Polling fallback while popup is open
      const pollTimer = setInterval(() => {
        if (!popup || popup.closed) {
          clearInterval(pollTimer);
          setOauthLoading(false);
          loadStatus();
        }
      }, 2000);
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to start SSI OAuth",
      });
      setOauthLoading(false);
    }
  };

  const handleSaveManualTokens = async () => {
    if (!manualAccessToken.trim()) {
      alert("Please provide at least the Access Token");
      return;
    }
    setSavingTokens(true);
    setActionMessage(null);
    try {
      await submitSsiTokens(manualAccessToken, manualRefreshToken, manualClientId);
      setActionMessage({
        type: "success",
        text: "SSI tokens successfully stored and updated!",
      });
      setManualAccessToken("");
      setManualRefreshToken("");
      setShowManualSsi(false);
      loadStatus();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to save tokens",
      });
    } finally {
      setSavingTokens(false);
    }
  };

  const handleTestSsi = async () => {
    setTestSsiLoading(true);
    setSsiTestResult(null);
    try {
      const res = await testSsiConnection();
      setSsiTestResult(res);
    } catch (err: any) {
      setSsiTestResult({
        status: "error",
        vendor: "ssi",
        message: err.message || "Connection failed",
      });
    } finally {
      setTestSsiLoading(false);
    }
  };

  const handleSaveAlgolabKey = async () => {
    if (!algolabKeyInput.trim()) {
      alert("Please enter a valid AlgoLab API Key");
      return;
    }
    setSavingAlgolabKey(true);
    setActionMessage(null);
    try {
      const res = await submitAlgolabKey(algolabKeyInput);
      setActionMessage({
        type: "success",
        text: res.message || "AlgoLab key updated!",
      });
      setAlgolabKeyInput("");
      setShowKeyInput(false);
      loadStatus();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to update AlgoLab key",
      });
    } finally {
      setSavingAlgolabKey(false);
    }
  };

  const handleTestAlgolab = async () => {
    setTestAlgolabLoading(true);
    setAlgolabTestResult(null);
    try {
      const res = await testAlgolabConnection();
      setAlgolabTestResult(res);
    } catch (err: any) {
      setAlgolabTestResult({
        status: "error",
        vendor: "algolab",
        message: err.message || "Connection failed",
      });
    } finally {
      setTestAlgolabLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-card/40 border border-border/60 p-5 rounded-xl backdrop-blur-sm">
        <div>
          <div className="flex items-center space-x-2.5 mb-1">
            <Database className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold tracking-tight text-foreground">
              Market Data & MCP Server Management
            </h2>
          </div>
          <p className="text-xs text-muted-foreground">
            Manage authentication, OAuth PKCE tokens, and API credentials for Vietnam market data providers (AlgoLab & SSI).
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadStatus}
          disabled={loading}
          className="self-start sm:self-auto text-xs flex items-center space-x-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-primary" : ""}`} />
          <span>Refresh Status</span>
        </Button>
      </div>

      {/* Global alert feedback */}
      {actionMessage && (
        <div
          className={`p-3.5 rounded-lg border text-xs flex items-start space-x-2.5 ${
            actionMessage.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-destructive/10 border-destructive/30 text-destructive-foreground"
          }`}
        >
          {actionMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
          )}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* 2-Column Vendor Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. SSI MCP Server Card */}
        <Card className="border-border/60 bg-card/60 shadow-sm flex flex-col justify-between">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                  <Layers className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold">SSI Securities MCP</CardTitle>
                  <CardDescription className="text-xs">
                    OAuth 2.0 PKCE • Fallback for Prices • Co-source for News
                  </CardDescription>
                </div>
              </div>

              {status?.ssi.connected ? (
                <Badge variant="success" className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-xs">
                  <ShieldCheck className="w-3 h-3 mr-1" /> Connected
                </Badge>
              ) : status?.ssi.configured ? (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-xs">
                  <Clock className="w-3 h-3 mr-1" /> Token Check
                </Badge>
              ) : (
                <Badge variant="destructive" className="text-xs">
                  Not Configured
                </Badge>
              )}
            </div>
          </CardHeader>

          <CardContent className="space-y-4 pt-1 flex-1">
            {/* Status details */}
            <div className="rounded-lg bg-muted/40 border border-border/50 p-3 space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center text-muted-foreground">
                <span>Transport:</span>
                <span className="text-foreground">Streamable HTTP POST (SSE)</span>
              </div>
              <div className="flex justify-between items-center text-muted-foreground">
                <span>Endpoint:</span>
                <span className="text-foreground truncate max-w-[200px]">https://mcp.ssi.com.vn/mcp</span>
              </div>
              {status?.ssi.client_id && (
                <div className="flex justify-between items-center text-muted-foreground">
                  <span>Client ID:</span>
                  <span className="text-foreground font-semibold truncate max-w-[200px]">
                    {status.ssi.client_id}
                  </span>
                </div>
              )}
              {status?.ssi.token_file && (
                <div className="flex justify-between items-center text-muted-foreground">
                  <span>Credentials Cache:</span>
                  <span className="text-foreground truncate max-w-[200px]" title={status.ssi.token_file}>
                    {status.ssi.token_file}
                  </span>
                </div>
              )}
              {status?.ssi.error && (
                <div className="pt-1 text-destructive font-sans">
                  <b>Error:</b> {status.ssi.error}
                </div>
              )}
            </div>

            {/* Test result output */}
            {ssiTestResult && (
              <div
                className={`p-2.5 rounded-md text-xs border ${
                  ssiTestResult.status === "ok"
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                    : "bg-destructive/10 border-destructive/20 text-destructive-foreground"
                }`}
              >
                {ssiTestResult.status === "ok" ? (
                  <div className="flex items-center justify-between">
                    <span>✓ {ssiTestResult.message}</span>
                    <span className="font-mono text-[11px] opacity-80">{ssiTestResult.latency_ms} ms</span>
                  </div>
                ) : (
                  <div>✕ {ssiTestResult.message}</div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2.5 pt-2">
              <Button
                onClick={handleStartSsiOAuth}
                disabled={oauthLoading}
                className="w-full text-xs font-semibold flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white shadow-sm"
              >
                {oauthLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ExternalLink className="w-3.5 h-3.5" />
                )}
                <span>Connect SSI Account (OAuth 2.0 PKCE)</span>
              </Button>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTestSsi}
                  disabled={testSsiLoading || !status?.ssi.configured}
                  className="flex-1 text-xs"
                >
                  {testSsiLoading ? (
                    <RefreshCw className="w-3 h-3 mr-1.5 animate-spin" />
                  ) : (
                    <ShieldCheck className="w-3 h-3 mr-1.5" />
                  )}
                  Test Connection
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowManualSsi(!showManualSsi)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  {showManualSsi ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
                  Manual Tokens
                </Button>
              </div>

              {/* Manual Tokens Accordion */}
              {showManualSsi && (
                <div className="p-3 bg-muted/30 border border-border/50 rounded-lg space-y-2.5 mt-2 text-xs">
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Access Token</label>
                    <Input
                      type="password"
                      placeholder="Paste SSI access_token..."
                      value={manualAccessToken}
                      onChange={(e) => setManualAccessToken(e.target.value)}
                      className="text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Refresh Token (Optional)</label>
                    <Input
                      type="password"
                      placeholder="Paste SSI refresh_token..."
                      value={manualRefreshToken}
                      onChange={(e) => setManualRefreshToken(e.target.value)}
                      className="text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Client ID (Optional)</label>
                    <Input
                      type="text"
                      placeholder="e.g. dcr-..."
                      value={manualClientId}
                      onChange={(e) => setManualClientId(e.target.value)}
                      className="text-xs font-mono"
                    />
                  </div>
                  <Button
                    size="sm"
                    onClick={handleSaveManualTokens}
                    disabled={savingTokens || !manualAccessToken.trim()}
                    className="w-full text-xs"
                  >
                    {savingTokens ? "Saving..." : "Save Tokens to Disk"}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 2. AlgoLab MCP Server Card */}
        <Card className="border-border/60 bg-card/60 shadow-sm flex flex-col justify-between">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <Database className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold">AlgoLab MCP</CardTitle>
                  <CardDescription className="text-xs">
                    Primary for Index & OHLCV • Market Recap & Macro
                  </CardDescription>
                </div>
              </div>

              {status?.algolab.connected ? (
                <Badge variant="success" className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-xs">
                  <ShieldCheck className="w-3 h-3 mr-1" /> Connected
                </Badge>
              ) : status?.algolab.configured ? (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-xs">
                  Key Configured
                </Badge>
              ) : (
                <Badge variant="destructive" className="text-xs">
                  Missing Key
                </Badge>
              )}
            </div>
          </CardHeader>

          <CardContent className="space-y-4 pt-1 flex-1">
            {/* Status details */}
            <div className="rounded-lg bg-muted/40 border border-border/50 p-3 space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center text-muted-foreground">
                <span>Transport:</span>
                <span className="text-foreground">Streamable HTTP POST (SSE)</span>
              </div>
              <div className="flex justify-between items-center text-muted-foreground">
                <span>Endpoint:</span>
                <span className="text-foreground truncate max-w-[200px]">https://mcp.algolab.vn</span>
              </div>
              <div className="flex justify-between items-center text-muted-foreground">
                <span>API Key:</span>
                <span className="text-foreground font-semibold">
                  {status?.algolab.api_key_masked || "None"}
                </span>
              </div>
              {status?.algolab.error && (
                <div className="pt-1 text-destructive font-sans">
                  <b>Error:</b> {status.algolab.error}
                </div>
              )}
            </div>

            {/* Quota Gauge / display if available */}
            {algolabTestResult?.quota && (
              <div className="p-2.5 rounded-lg bg-muted/30 border border-border/50 space-y-1.5 text-xs">
                <div className="flex justify-between text-muted-foreground">
                  <span>Daily Quota Usage:</span>
                  <span className="font-semibold text-foreground">
                    {algolabTestResult.quota.used} / {algolabTestResult.quota.limit} requests
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all"
                    style={{
                      width: `${Math.min(
                        100,
                        (algolabTestResult.quota.used / algolabTestResult.quota.limit) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Test result output */}
            {algolabTestResult && (
              <div
                className={`p-2.5 rounded-md text-xs border ${
                  algolabTestResult.status === "ok"
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                    : "bg-destructive/10 border-destructive/20 text-destructive-foreground"
                }`}
              >
                {algolabTestResult.status === "ok" ? (
                  <div className="flex items-center justify-between">
                    <span>✓ {algolabTestResult.message}</span>
                    <span className="font-mono text-[11px] opacity-80">{algolabTestResult.latency_ms} ms</span>
                  </div>
                ) : (
                  <div>✕ {algolabTestResult.message}</div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2.5 pt-2">
              {!showKeyInput ? (
                <Button
                  variant="outline"
                  onClick={() => setShowKeyInput(true)}
                  className="w-full text-xs flex items-center justify-center space-x-1.5"
                >
                  <Key className="w-3.5 h-3.5 text-primary" />
                  <span>Update ALGOLAB_API_KEY</span>
                </Button>
              ) : (
                <div className="space-y-2 p-2.5 bg-muted/30 border border-border/50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] text-muted-foreground">Enter ALGOLAB_API_KEY</label>
                    <button
                      type="button"
                      onClick={() => setShowKeyInput(false)}
                      className="text-[10px] text-muted-foreground hover:text-foreground"
                    >
                      Cancel
                    </button>
                  </div>
                  <Input
                    type="password"
                    placeholder="alm_..."
                    value={algolabKeyInput}
                    onChange={(e) => setAlgolabKeyInput(e.target.value)}
                    className="text-xs font-mono"
                  />
                  <Button
                    size="sm"
                    onClick={handleSaveAlgolabKey}
                    disabled={savingAlgolabKey || !algolabKeyInput.trim()}
                    className="w-full text-xs"
                  >
                    {savingAlgolabKey ? "Saving & Testing..." : "Save to .env & Verify"}
                  </Button>
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={handleTestAlgolab}
                disabled={testAlgolabLoading || !status?.algolab.configured}
                className="w-full text-xs"
              >
                {testAlgolabLoading ? (
                  <RefreshCw className="w-3 h-3 mr-1.5 animate-spin" />
                ) : (
                  <ShieldCheck className="w-3 h-3 mr-1.5" />
                )}
                Test AlgoLab Connection & Check Quota
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Vietnam Market Architecture Architecture Callout */}
      <Card className="border-border/60 bg-muted/20">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-foreground">
            <Lock className="w-3.5 h-3.5 text-primary" />
            <span>Dual-Vendor Resiliency for Vietnam Market Data</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            TradingAgents uses a resilient <b>whole-series fallback</b> pattern: AlgoLab is the primary source for OHLCV bars, VN-Index benchmark closes, and technical signals. If AlgoLab experiences an outage or quota limit, SSI immediately serves 100% of the price series to ensure seamless backtesting without mixed data sources. For news and corporate events, both vendors are <b>co-sourced side-by-side</b> with duplicate URL filtering.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
