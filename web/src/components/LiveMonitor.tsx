import React, { useEffect, useRef, useState } from "react";
import { Activity, Square, Terminal, CheckCircle2, Clock, RotateCcw } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "./ui/progress";
import { LogMessage, ProgressData } from "../types";

interface LiveMonitorProps {
  isRunning: boolean;
  activeRunId: string | null;
  progress: ProgressData | null;
  logs: LogMessage[];
  onStop: () => void;
  onReset?: () => void;
  onViewResults: () => void;
}

export const LiveMonitor: React.FC<LiveMonitorProps> = ({
  isRunning,
  activeRunId,
  progress,
  logs,
  onStop,
  onReset,
  onViewResults,
}) => {
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  // Timer while running
  useEffect(() => {
    let interval: any;
    if (isRunning) {
      interval = setInterval(() => setSecondsElapsed((s) => s + 1), 1000);
    } else {
      setSecondsElapsed(0);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  // Auto-scroll terminal
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-6">
      {/* Progress Status Bar */}
      <Card className="border-border/60 bg-card/70 overflow-hidden">
        <CardHeader className="pb-3 border-b border-border/40 bg-muted/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className={`w-4 h-4 ${isRunning ? "text-amber-400 animate-spin" : "text-emerald-400"}`} />
              <CardTitle className="text-base">
                {isRunning ? "Backtest Sweep In Progress" : "Sweep Execution Status"}
              </CardTitle>
              {activeRunId && (
                <span className="text-xs font-mono text-muted-foreground ml-2">({activeRunId})</span>
              )}
            </div>
            <div className="flex items-center space-x-3">
              {isRunning && (
                <div className="flex items-center space-x-1 text-xs text-muted-foreground font-mono">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{formatTime(secondsElapsed)}</span>
                </div>
              )}
              {isRunning ? (
                <Button variant="destructive" size="sm" onClick={onStop} className="h-8">
                  <Square className="w-3.5 h-3.5 mr-1.5 fill-current" /> Stop Sweep
                </Button>
              ) : (
                <div className="flex items-center space-x-2">
                  {onReset && (
                    <Button variant="outline" size="sm" onClick={onReset} className="h-8">
                      <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Reset Engine
                    </Button>
                  )}
                  <Button variant="default" size="sm" onClick={onViewResults} className="h-8">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> View Results
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5 space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-foreground text-sm">
                {progress ? `${progress.percent}%` : "0%"}
              </span>
              <span>
                ({progress ? `${progress.done} of ${progress.total} cells` : "Awaiting start..."})
              </span>
            </div>
            {progress?.ticker && (
              <div className="flex items-center space-x-1.5 font-mono text-xs bg-muted/60 px-2 py-0.5 rounded border border-border/50">
                <span className="text-muted-foreground">Active Cell:</span>
                <span className="text-primary font-bold">{progress.ticker}</span>
                <span className="text-muted-foreground">·</span>
                <span className="text-foreground">{progress.date}</span>
              </div>
            )}
          </div>
          <Progress value={progress?.percent || 0} className="h-2.5 bg-muted" />
        </CardContent>
      </Card>

      {/* Real-time Streaming Terminal */}
      <Card className="border-border/60 bg-zinc-950 font-mono text-xs shadow-2xl overflow-hidden">
        <div className="bg-zinc-900/90 border-b border-zinc-800 px-4 py-2.5 flex items-center justify-between text-zinc-400">
          <div className="flex items-center space-x-2">
            <Terminal className="w-3.5 h-3.5 text-zinc-400" />
            <span className="font-semibold text-zinc-300">Live Engine Console</span>
            <span className="text-[10px] text-zinc-500">({logs.length} lines)</span>
          </div>
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-1.5 text-[11px] cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded bg-zinc-800 border-zinc-700 accent-primary w-3.5 h-3.5"
              />
              <span>Auto-scroll</span>
            </label>
          </div>
        </div>
        <div className="p-4 h-96 overflow-y-auto space-y-1 select-text">
          {logs.length === 0 ? (
            <div className="text-zinc-600 italic py-8 text-center">
              Logs and agent debate outputs will stream here in real-time when a sweep starts...
            </div>
          ) : (
            logs.map((log, index) => {
              let levelColor = "text-zinc-400";
              if (log.level === "WARNING") levelColor = "text-amber-400";
              if (log.level === "ERROR") levelColor = "text-rose-400 font-bold";
              return (
                <div key={index} className="flex space-x-2 leading-relaxed">
                  <span className="text-zinc-600 select-none flex-shrink-0">[{log.timestamp}]</span>
                  <span className={`select-none flex-shrink-0 w-12 font-semibold ${levelColor}`}>
                    {log.level}
                  </span>
                  <span className="text-zinc-200 whitespace-pre-wrap break-all">{log.message}</span>
                </div>
              );
            })
          )}
          <div ref={terminalEndRef} />
        </div>
      </Card>
    </div>
  );
};
