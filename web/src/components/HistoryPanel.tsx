import React, { useEffect, useState } from "react";
import { History, RefreshCw, Eye, Calendar, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Badge } from "./ui/badge";
import { fetchRuns } from "../lib/api";
import { RunListItem } from "../types";

interface HistoryPanelProps {
  onSelectRun: (runId: string) => void;
  activeRunId: string | null;
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({ onSelectRun, activeRunId }) => {
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRuns();
      setRuns(data);
    } catch (err: any) {
      setError(err.message || "Failed to load runs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  return (
    <Card className="border-border/60 bg-card/70 overflow-hidden">
      <CardHeader className="pb-3 border-b border-border/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Historical Backtest Runs</CardTitle>
          </div>
          <Button variant="outline" size="sm" onClick={loadRuns} disabled={loading} className="h-8">
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
        <CardDescription className="text-xs">
          Browse and inspect past decision logs and Alpha benchmarks saved in the results directory.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {error && (
          <div className="p-4 text-xs text-rose-400 bg-rose-500/10 border-b border-rose-500/20">
            {error}
          </div>
        )}

        <div className="divide-y divide-border/30">
          {runs.length === 0 ? (
            <div className="py-12 text-center text-xs text-muted-foreground">
              {loading ? "Scanning run directories..." : "No historical backtests found on disk."}
            </div>
          ) : (
            runs.map((run) => {
              const isCurrent = activeRunId === run.run_id;
              return (
                <div
                  key={run.run_id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/20 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2.5">
                      <span className="font-mono font-bold text-sm text-foreground">
                        {run.run_id}
                      </span>
                      {isCurrent && (
                        <Badge variant="default" className="text-[10px] py-0 px-1.5 bg-primary/20 text-primary border-primary/30">
                          Active
                        </Badge>
                      )}
                      {run.has_log ? (
                        <Badge variant="success" className="text-[10px] py-0 px-1.5">
                          <CheckCircle2 className="w-2.5 h-2.5 mr-1" /> Logged
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-zinc-500">
                          Empty
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center space-x-3 text-xs text-muted-foreground font-mono">
                      <span className="flex items-center">
                        <Calendar className="w-3 h-3 mr-1" />
                        {run.created_at}
                      </span>
                      <span>·</span>
                      <span>{run.cell_count} cells ({run.resolved_count} resolved)</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onSelectRun(run.run_id)}
                      className="h-8 text-xs"
                    >
                      <Eye className="w-3.5 h-3.5 mr-1.5" /> Inspect Results
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
};
