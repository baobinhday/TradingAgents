import React from "react";
import { Activity, ShieldCheck, Terminal, Cpu } from "lucide-react";
import { Badge } from "./ui/badge";

interface HeaderProps {
  status: string;
  activeRunId: string | null;
}

export const Header: React.FC<HeaderProps> = ({ status, activeRunId }) => {
  return (
    <header className="border-b border-border/50 bg-card/60 backdrop-blur px-6 py-3.5 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center p-1.5 shadow-sm">
            <img src="/logo.svg" alt="TradingAgents" className="w-full h-full object-contain" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold tracking-tight text-foreground">TradingAgents</h1>
              <Badge variant="outline" className="text-[10px] py-0 px-1.5 font-mono">v0.7.1</Badge>
            </div>
            <p className="text-xs text-muted-foreground hidden sm:block">
              Multi-Agent LLM Financial Trading & Backtesting Console
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {activeRunId && (
            <div className="flex items-center space-x-2 text-xs bg-muted/50 border border-border/60 px-2.5 py-1 rounded-md font-mono">
              <Terminal className="w-3.5 h-3.5 text-primary" />
              <span className="text-muted-foreground">Run:</span>
              <span className="text-foreground font-semibold">{activeRunId}</span>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <span className="text-xs text-muted-foreground hidden md:inline">Engine:</span>
            {status === "running" ? (
              <Badge variant="default" className="bg-amber-500/15 text-amber-400 border border-amber-500/30 animate-pulse">
                <Activity className="w-3 h-3 mr-1.5 animate-spin" /> Running
              </Badge>
            ) : status === "completed" ? (
              <Badge variant="success" className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="w-3 h-3 mr-1" /> Idle / Ready
              </Badge>
            ) : (
              <Badge variant="outline" className="text-zinc-400">
                <Cpu className="w-3 h-3 mr-1 text-zinc-500" /> Ready
              </Badge>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
