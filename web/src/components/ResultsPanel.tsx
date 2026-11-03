import React, { useState } from "react";
import {
  TrendingUp,
  Percent,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  BarChart3,
  FileText,
  Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { formatAlpha, getAlphaColor, getRatingBadgeClass } from "../lib/utils";
import { BacktestSummary, CellResult } from "../types";
import { ReasoningModal } from "./ReasoningModal";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface ResultsPanelProps {
  runId: string | null;
  summary: BacktestSummary | null;
  cells: CellResult[];
  failures?: [string, string, string][];
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({
  runId,
  summary,
  cells,
  failures = [],
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRating, setSelectedRating] = useState<string>("ALL");
  const [selectedCell, setSelectedCell] = useState<CellResult | null>(null);

  if (!summary && cells.length === 0) {
    return (
      <div className="text-center py-16 bg-card/40 rounded-xl border border-dashed border-border/60">
        <FileText className="w-10 h-10 mx-auto text-muted-foreground/60 mb-3" />
        <h3 className="text-sm font-semibold text-foreground">No Results Available</h3>
        <p className="text-xs text-muted-foreground max-w-sm mx-auto mt-1">
          Launch a new backtest sweep from the Configuration panel or select an earlier run from the History tab.
        </p>
      </div>
    );
  }

  // Calculate overall hit rate
  let totalDirectedCount = 0;
  let totalHits = 0;
  let totalWeightedAlpha = 0;
  let totalResolvedForAlpha = 0;

  if (summary?.by_rating) {
    Object.entries(summary.by_rating).forEach(([, score]) => {
      if (score.hit_rate !== null && score.count > 0) {
        totalDirectedCount += score.count;
        totalHits += score.hit_rate * score.count;
      }
      if (score.count > 0) {
        totalWeightedAlpha += score.mean_alpha * score.count;
        totalResolvedForAlpha += score.count;
      }
    });
  }

  const overallHitRate =
    totalDirectedCount > 0 ? (totalHits / totalDirectedCount) * 100 : null;
  const overallMeanAlpha =
    totalResolvedForAlpha > 0 ? (totalWeightedAlpha / totalResolvedForAlpha) * 100 : 0;

  // Chart data
  const chartData = summary?.by_rating
    ? Object.entries(summary.by_rating).map(([rating, score]) => ({
        rating,
        alpha: Number((score.mean_alpha * 100).toFixed(2)),
        count: score.count,
        hitRate: score.hit_rate !== null ? `${(score.hit_rate * 100).toFixed(0)}%` : "N/A",
      }))
    : [];

  // Filter cells
  const filteredCells = cells.filter((c) => {
    const matchesSearch =
      c.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.date.includes(searchTerm);
    const matchesRating =
      selectedRating === "ALL" ||
      c.rating?.toLowerCase() === selectedRating.toLowerCase();
    return matchesSearch && matchesRating;
  });

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center space-x-2">
            <span>Backtest Evaluation</span>
            {runId && (
              <Badge variant="outline" className="font-mono text-xs">
                {runId}
              </Badge>
            )}
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Measured against regional benchmark over {summary?.holding || "the configured window"}.
          </p>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Hit Rate */}
        <Card className="border-border/60 bg-card/70">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Directional Hit Rate</span>
              <Percent className="w-3.5 h-3.5 text-muted-foreground" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono">
              {overallHitRate !== null ? `${overallHitRate.toFixed(1)}%` : "N/A"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-muted-foreground">
              {totalDirectedCount} directional calls (Buy / Sell)
            </p>
          </CardContent>
        </Card>

        {/* Mean Alpha */}
        <Card className="border-border/60 bg-card/70">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Mean Alpha vs Benchmark</span>
              <TrendingUp className="w-3.5 h-3.5 text-muted-foreground" />
            </CardDescription>
            <CardTitle
              className={`text-2xl font-bold font-mono ${
                overallMeanAlpha > 0
                  ? "text-emerald-400"
                  : overallMeanAlpha < 0
                  ? "text-rose-400"
                  : "text-foreground"
              }`}
            >
              {overallMeanAlpha > 0 ? `+${overallMeanAlpha.toFixed(2)}%` : `${overallMeanAlpha.toFixed(2)}%`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-muted-foreground">
              Outperformance over buy & hold benchmark
            </p>
          </CardContent>
        </Card>

        {/* Resolved Cells */}
        <Card className="border-border/60 bg-card/70">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Resolved Cells</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono">
              {summary?.resolved ?? cells.length}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-muted-foreground">
              Settled against market outcome
            </p>
          </CardContent>
        </Card>

        {/* Pending / Unscored Cells */}
        <Card className="border-border/60 bg-card/70">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs flex items-center justify-between">
              <span>Pending / Unscored</span>
              <Clock className="w-3.5 h-3.5 text-amber-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold font-mono">
              {summary ? summary.pending + summary.unscored : 0}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-muted-foreground">
              Awaiting window close or settlement
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Ratings Breakdown Grid & Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rating Cards */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {summary?.by_rating &&
            Object.entries(summary.by_rating).map(([rating, score]) => (
              <Card key={rating} className="border-border/60 bg-card/70">
                <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
                  <Badge variant="outline" className={getRatingBadgeClass(rating)}>
                    {rating}
                  </Badge>
                  <span className="text-xs text-muted-foreground font-mono">
                    n = {score.count}
                  </span>
                </CardHeader>
                <CardContent className="p-4 pt-1 space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Hit Rate:</span>
                    <span className="font-semibold font-mono text-foreground">
                      {score.hit_rate !== null ? `${(score.hit_rate * 100).toFixed(0)}%` : "Neutral"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Mean Alpha:</span>
                    <span className={`font-semibold font-mono ${score.mean_alpha > 0 ? "text-emerald-400" : score.mean_alpha < 0 ? "text-rose-400" : "text-zinc-400"}`}>
                      {score.mean_alpha > 0 ? `+${(score.mean_alpha * 100).toFixed(2)}%` : `${(score.mean_alpha * 100).toFixed(2)}%`}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>

        {/* Alpha Bar Chart */}
        <Card className="border-border/60 bg-card/70">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <CardTitle className="text-sm">Alpha by Rating (%)</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            {chartData.length > 0 ? (
              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <XAxis dataKey="rating" stroke="#71717a" fontSize={10} tickLine={false} />
                    <YAxis stroke="#71717a" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: 8, fontSize: 12 }}
                    />
                    <Bar dataKey="alpha" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.alpha >= 0 ? "#10b981" : "#f43f5e"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-44 flex items-center justify-center text-xs text-muted-foreground">
                No alpha chart data
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Failures Banner (if any) */}
      {failures.length > 0 && (
        <Card className="border-amber-500/30 bg-amber-500/10">
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-xs font-semibold text-amber-300">
              Cell Execution Warnings / Failures ({failures.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3 space-y-1 text-xs text-amber-200/90 font-mono">
            {failures.map(([ticker, date, reason], idx) => (
              <div key={idx}>
                • {ticker} {date}: {reason}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Evaluated Cells Table */}
      <Card className="border-border/60 bg-card/70 overflow-hidden">
        <CardHeader className="pb-3 border-b border-border/40">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <CardTitle className="text-sm font-semibold">
              Analyzed Cells ({filteredCells.length})
            </CardTitle>
            <div className="flex items-center space-x-2">
              <div className="relative w-44">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-muted-foreground" />
                <Input
                  placeholder="Filter ticker/date..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="h-8 pl-8 text-xs"
                />
              </div>
              <div className="flex items-center space-x-1 text-xs">
                <Filter className="w-3.5 h-3.5 text-muted-foreground" />
                <select
                  value={selectedRating}
                  onChange={(e) => setSelectedRating(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background/50 px-2 text-xs focus:outline-none"
                >
                  <option value="ALL">All Ratings</option>
                  <option value="BUY">Buy</option>
                  <option value="OVERWEIGHT">Overweight</option>
                  <option value="HOLD">Hold</option>
                  <option value="UNDERWEIGHT">Underweight</option>
                  <option value="SELL">Sell</option>
                </select>
              </div>
            </div>
          </div>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-muted/40 text-muted-foreground border-b border-border/40">
              <tr>
                <th className="py-2.5 px-4 font-medium">Ticker</th>
                <th className="py-2.5 px-4 font-medium">Analysis Date</th>
                <th className="py-2.5 px-4 font-medium">Rating</th>
                <th className="py-2.5 px-4 font-medium">Realized Alpha</th>
                <th className="py-2.5 px-4 font-medium">Holding Window</th>
                <th className="py-2.5 px-4 font-medium">Status</th>
                <th className="py-2.5 px-4 font-medium text-right">Reasoning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {filteredCells.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-muted-foreground">
                    No cells matching criteria.
                  </td>
                </tr>
              ) : (
                filteredCells.map((cell, idx) => (
                  <tr key={idx} className="hover:bg-muted/20 transition-colors">
                    <td className="py-2.5 px-4 font-mono font-bold text-foreground">
                      {cell.ticker}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-muted-foreground">
                      {cell.date}
                    </td>
                    <td className="py-2.5 px-4">
                      {cell.rating ? (
                        <Badge variant="outline" className={getRatingBadgeClass(cell.rating)}>
                          {cell.rating}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className={`py-2.5 px-4 font-mono font-semibold ${getAlphaColor(cell.alpha)}`}>
                      {formatAlpha(cell.alpha)}
                    </td>
                    <td className="py-2.5 px-4 text-muted-foreground">
                      {cell.holding || "-"}
                    </td>
                    <td className="py-2.5 px-4">
                      {cell.pending ? (
                        <span className="text-amber-400 font-medium">Pending</span>
                      ) : (
                        <span className="text-emerald-400 font-medium">Settled</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      {cell.decision || cell.market_report || cell.reflection ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedCell(cell)}
                          className="h-7 px-2 text-xs text-primary hover:text-primary hover:bg-primary/10"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" /> View
                        </Button>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Multi-Agent Reasoning Modal */}
      <ReasoningModal cell={selectedCell} onClose={() => setSelectedCell(null)} />
    </div>
  );
};
