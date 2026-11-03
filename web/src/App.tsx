import { useEffect, useState } from "react";
import { Sliders, Activity, BarChart2, History, Database } from "lucide-react";
import { Header } from "./components/Header";
import { ConfigPanel } from "./components/ConfigPanel";
import { LiveMonitor } from "./components/LiveMonitor";
import { ResultsPanel } from "./components/ResultsPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { McpPanel } from "./components/McpPanel";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./components/ui/tabs";
import {
  fetchConfig,
  fetchRunDetail,
  resetBacktest,
  startBacktest,
  stopBacktest,
} from "./lib/api";
import {
  BacktestRunRequest,
  BacktestSummary,
  CellResult,
  ConfigResponse,
  LogMessage,
  ProgressData,
} from "./types";

export function App() {
  const [activeTab, setActiveTab] = useState("config");
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [status, setStatus] = useState("idle");
  const [runningRunId, setRunningRunId] = useState<string | null>(null);
  const [viewingRunId, setViewingRunId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [summary, setSummary] = useState<BacktestSummary | null>(null);
  const [cells, setCells] = useState<CellResult[]>([]);
  const [failures, setFailures] = useState<[string, string, string][]>([]);

  // Fetch initial config
  useEffect(() => {
    fetchConfig()
      .then((cfg) => setConfig(cfg))
      .catch((err) => console.error("Could not load config:", err));
  }, []);

  // Connect to SSE stream
  useEffect(() => {
    const eventSource = new EventSource("/api/backtest/events");

    eventSource.addEventListener("status", (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.status) setStatus(data.status);
        if (data.run_id) {
          setRunningRunId(data.run_id);
          if (!viewingRunId) setViewingRunId(data.run_id);
        }
        if (data.recent_logs && Array.isArray(data.recent_logs)) {
          setLogs(data.recent_logs);
        }
      } catch (err) {
        console.error("Error parsing status event", err);
      }
    });

    eventSource.addEventListener("start", (e) => {
      try {
        const data = JSON.parse(e.data);
        setStatus("running");
        setRunningRunId(data.run_id);
        setViewingRunId(data.run_id);
        setLogs([]);
        setProgress({
          done: 0,
          total: data.total_cells,
          percent: 0,
          ticker: data.tickers[0] || "",
          date: data.dates[0] || "",
        });
        setActiveTab("monitor");
      } catch (err) {
        console.error("Error parsing start event", err);
      }
    });

    eventSource.addEventListener("progress", (e) => {
      try {
        const data = JSON.parse(e.data);
        setProgress(data);
      } catch (err) {
        console.error("Error parsing progress event", err);
      }
    });

    eventSource.addEventListener("log", (e) => {
      try {
        const data = JSON.parse(e.data);
        setLogs((prev) => [...prev, data]);
      } catch (err) {
        console.error("Error parsing log event", err);
      }
    });

    eventSource.addEventListener("complete", (e) => {
      try {
        const data = JSON.parse(e.data);
        setStatus("completed");
        setSummary(data.summary);
        setFailures(data.failures || []);
        // Load details for cell breakdown
        if (data.run_id) {
          setViewingRunId(data.run_id);
          fetchRunDetail(data.run_id)
            .then((detail) => {
              setCells(detail.cells);
              setActiveTab("results");
            })
            .catch(console.error);
        }
      } catch (err) {
        console.error("Error parsing complete event", err);
      }
    });

    eventSource.addEventListener("stopped", () => {
      setStatus("stopped");
    });

    eventSource.addEventListener("error", () => {
      setStatus("failed");
    });

    eventSource.addEventListener("reset", () => {
      setStatus("idle");
      setRunningRunId(null);
    });

    return () => {
      eventSource.close();
    };
  }, [viewingRunId]);

  const handleStart = async (req: BacktestRunRequest) => {
    try {
      const res = await startBacktest(req);
      setRunningRunId(res.run_id);
      setViewingRunId(res.run_id);
      setStatus("running");
      setActiveTab("monitor");
    } catch (err: any) {
      alert(err.message || "Failed to start backtest");
    }
  };

  const handleStop = async () => {
    try {
      await stopBacktest();
      setStatus("stopped");
    } catch (err: any) {
      alert(err.message || "Failed to stop backtest");
    }
  };

  const handleReset = async () => {
    try {
      await resetBacktest();
      setStatus("idle");
      setRunningRunId(null);
    } catch (err: any) {
      alert(err.message || "Failed to reset backtest engine");
    }
  };

  const handleSelectRun = async (runId: string) => {
    try {
      const detail = await fetchRunDetail(runId);
      setViewingRunId(runId);
      setSummary(detail.summary);
      setCells(detail.cells);
      setFailures(detail.failures);
      setActiveTab("results");
    } catch (err: any) {
      alert(err.message || "Failed to load run detail");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header
        status={status}
        activeRunId={status === "running" ? runningRunId : viewingRunId}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 gap-3">
            <TabsList>
              <TabsTrigger value="config" className="flex items-center space-x-2">
                <Sliders className="w-4 h-4" />
                <span>Configuration</span>
              </TabsTrigger>
              <TabsTrigger value="monitor" className="flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>Live Monitor</span>
                {status === "running" && (
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping inline-block ml-1" />
                )}
              </TabsTrigger>
              <TabsTrigger value="results" className="flex items-center space-x-2">
                <BarChart2 className="w-4 h-4" />
                <span>Results & Analytics</span>
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center space-x-2">
                <History className="w-4 h-4" />
                <span>History</span>
              </TabsTrigger>
              <TabsTrigger value="mcp" className="flex items-center space-x-2">
                <Database className="w-4 h-4" />
                <span>Data & MCP</span>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="config">
            <ConfigPanel
              config={config}
              isRunning={status === "running"}
              onStart={handleStart}
              onNavigateToMcp={() => setActiveTab("mcp")}
            />
          </TabsContent>

          <TabsContent value="monitor">
            <LiveMonitor
              isRunning={status === "running"}
              activeRunId={runningRunId}
              progress={progress}
              logs={logs}
              onStop={handleStop}
              onReset={handleReset}
              onViewResults={() => setActiveTab("results")}
            />
          </TabsContent>

          <TabsContent value="results">
            <ResultsPanel
              runId={viewingRunId}
              summary={summary}
              cells={cells}
              failures={failures}
            />
          </TabsContent>

          <TabsContent value="history">
            <HistoryPanel
              onSelectRun={handleSelectRun}
              runningRunId={runningRunId}
              viewingRunId={viewingRunId}
              status={status}
            />
          </TabsContent>

          <TabsContent value="mcp">
            <McpPanel />
          </TabsContent>
        </Tabs>
      </main>

      <footer className="border-t border-border/40 py-4 px-6 text-center text-xs text-muted-foreground bg-card/30">
        TradingAgents • LLM Multi-Agent Decision Framework • Evaluated against Benchmark Alpha
      </footer>
    </div>
  );
}
export default App;
