import React, { useState, useEffect } from "react";
import {
  FileText,
  TrendingUp,
  Building2,
  Newspaper,
  Swords,
  Shield,
  Sparkles,
  Briefcase,
  X,
  Copy,
  Check,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { formatAlpha, getAlphaColor, getRatingBadgeClass } from "../lib/utils";
import { CellResult } from "../types";

interface ReasoningModalProps {
  cell: CellResult | null;
  onClose: () => void;
}

type TabKey =
  | "decision"
  | "market"
  | "fundamentals"
  | "news"
  | "debate"
  | "trader"
  | "risk"
  | "reflection";

interface TabItem {
  id: TabKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  available: boolean;
}

export const ReasoningModal: React.FC<ReasoningModalProps> = ({ cell, onClose }) => {
  const [activeTab, setActiveTab] = useState<TabKey>("decision");
  const [debateFilter, setDebateFilter] = useState<"history" | "bull" | "bear">("history");
  const [riskFilter, setRiskFilter] = useState<
    "history" | "aggressive" | "conservative" | "neutral"
  >("history");
  const [newsFilter, setNewsFilter] = useState<"both" | "news" | "sentiment">("both");
  const [copied, setCopied] = useState(false);

  // Available tabs calculation
  const tabs: TabItem[] = cell
    ? [
        {
          id: "decision",
          label: "Agent Decision",
          icon: FileText,
          available: Boolean(cell.decision),
        },
        {
          id: "market",
          label: "Market Analyst",
          icon: TrendingUp,
          available: Boolean(cell.market_report),
        },
        {
          id: "fundamentals",
          label: "Fundamentals",
          icon: Building2,
          available: Boolean(cell.fundamentals_report),
        },
        {
          id: "news",
          label: "News & Sentiment",
          icon: Newspaper,
          available: Boolean(cell.news_report || cell.sentiment_report),
        },
        {
          id: "debate",
          label: "Research Debate",
          icon: Swords,
          available: Boolean(cell.investment_debate_state || cell.investment_plan),
        },
        {
          id: "trader",
          label: "Trader Proposal",
          icon: Briefcase,
          available: Boolean(cell.trader_investment_plan),
        },
        {
          id: "risk",
          label: "Risk Management",
          icon: Shield,
          available: Boolean(cell.risk_debate_state),
        },
        {
          id: "reflection",
          label: "Settlement Reflection",
          icon: Sparkles,
          available: Boolean(cell.reflection),
        },
      ]
    : [];

  const availableTabs = tabs.filter((t) => t.available);

  // Whenever the selected cell changes, ensure active tab is valid
  useEffect(() => {
    if (!cell) return;
    const currentTabAvailable = availableTabs.some((t) => t.id === activeTab);
    if (!currentTabAvailable && availableTabs.length > 0) {
      setActiveTab(availableTabs[0].id);
    }
  }, [cell, availableTabs, activeTab]);

  if (!cell) return null;

  // Active text to copy
  const getActiveContent = (): string => {
    switch (activeTab) {
      case "decision":
        return typeof cell.decision === "string"
          ? cell.decision
          : JSON.stringify(cell.decision, null, 2);
      case "market":
        return cell.market_report || "";
      case "fundamentals":
        return cell.fundamentals_report || "";
      case "news":
        return [cell.news_report, cell.sentiment_report].filter(Boolean).join("\n\n---\n\n");
      case "debate":
        return [
          cell.investment_plan ? `## Investment Plan\n\n${cell.investment_plan}` : "",
          cell.investment_debate_state?.history || "",
        ]
          .filter(Boolean)
          .join("\n\n---\n\n");
      case "trader":
        return cell.trader_investment_plan || "";
      case "risk":
        return cell.risk_debate_state?.history || "";
      case "reflection":
        return cell.reflection || "";
      default:
        return "";
    }
  };

  const handleCopy = () => {
    const text = getActiveContent();
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5">
      <div className="bg-card border border-border/80 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-border/60 flex items-center justify-between bg-muted/20 gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono font-bold text-base text-foreground tracking-tight">
              {cell.ticker}
            </span>
            <span className="text-xs text-muted-foreground font-mono">({cell.date})</span>

            {cell.rating && (
              <Badge variant="outline" className={getRatingBadgeClass(cell.rating)}>
                {cell.rating}
              </Badge>
            )}

            {cell.alpha && (
              <Badge
                variant="outline"
                className={`font-mono text-xs font-semibold ${getAlphaColor(cell.alpha)} bg-card/60`}
              >
                Alpha: {formatAlpha(cell.alpha)}
              </Badge>
            )}

            {cell.holding && (
              <Badge variant="outline" className="text-xs text-zinc-400 bg-muted/20">
                Hold: {cell.holding}
              </Badge>
            )}

            {cell.pending ? (
              <Badge variant="outline" className="text-amber-400 border-amber-500/30 bg-amber-500/10">
                Pending
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
              >
                Settled
              </Badge>
            )}
          </div>

          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 px-2.5 text-xs text-muted-foreground hover:text-foreground"
              title="Copy active tab content"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 mr-1" />
                  <span>Copy</span>
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 rounded-full text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-border/40 bg-card/60 px-3 pt-2">
          <div className="flex items-center space-x-1 overflow-x-auto pb-2 scrollbar-thin">
            {availableTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                    isActive
                      ? "bg-primary/15 text-primary border border-primary/30 font-semibold shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/40 border border-transparent"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs leading-relaxed flex-1 max-h-[calc(90vh-140px)]">
          {/* Tab: PM Decision */}
          {activeTab === "decision" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-primary" />
                  <span>Portfolio Manager: Decision & Thesis</span>
                </h4>
              </div>
              <div className="bg-muted/20 p-4 rounded-xl border border-border/40 whitespace-pre-wrap font-sans text-zinc-300">
                {typeof cell.decision === "string"
                  ? cell.decision
                  : JSON.stringify(cell.decision, null, 2)}
              </div>
            </div>
          )}

          {/* Tab: Market Analyst */}
          {activeTab === "market" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  <span>Market Analyst (Technical Indicators & Momentum)</span>
                </h4>
              </div>
              <div className="bg-cyan-950/10 p-4 rounded-xl border border-cyan-500/20 whitespace-pre-wrap font-sans text-zinc-300">
                {cell.market_report}
              </div>
            </div>
          )}

          {/* Tab: Fundamentals Analyst */}
          {activeTab === "fundamentals" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-amber-400" />
                  <span>Fundamentals Analyst (Financial Statements & Performance)</span>
                </h4>
              </div>
              <div className="bg-amber-950/10 p-4 rounded-xl border border-amber-500/20 whitespace-pre-wrap font-sans text-zinc-300">
                {cell.fundamentals_report}
              </div>
            </div>
          )}

          {/* Tab: News & Sentiment */}
          {activeTab === "news" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <Newspaper className="w-4 h-4 text-indigo-400" />
                  <span>News & Social Sentiment Analyst</span>
                </h4>
                {cell.news_report && cell.sentiment_report && (
                  <div className="flex space-x-1 bg-muted/40 p-0.5 rounded-md border border-border/40">
                    <button
                      onClick={() => setNewsFilter("both")}
                      className={`px-2 py-0.5 rounded text-[11px] ${newsFilter === "both" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      All
                    </button>
                    <button
                      onClick={() => setNewsFilter("news")}
                      className={`px-2 py-0.5 rounded text-[11px] ${newsFilter === "news" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      News
                    </button>
                    <button
                      onClick={() => setNewsFilter("sentiment")}
                      className={`px-2 py-0.5 rounded text-[11px] ${newsFilter === "sentiment" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      Sentiment
                    </button>
                  </div>
                )}
              </div>

              {(newsFilter === "both" || newsFilter === "news") && cell.news_report && (
                <div className="space-y-2">
                  <span className="font-semibold text-zinc-400 block text-xs">
                    📰 News Analyst Report
                  </span>
                  <div className="bg-indigo-950/10 p-4 rounded-xl border border-indigo-500/20 whitespace-pre-wrap font-sans text-zinc-300">
                    {cell.news_report}
                  </div>
                </div>
              )}

              {(newsFilter === "both" || newsFilter === "sentiment") && cell.sentiment_report && (
                <div className="space-y-2">
                  <span className="font-semibold text-zinc-400 block text-xs">
                    💬 Social Sentiment Report
                  </span>
                  <div className="bg-purple-950/10 p-4 rounded-xl border border-purple-500/20 whitespace-pre-wrap font-sans text-zinc-300">
                    {cell.sentiment_report}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab: Research Debate */}
          {activeTab === "debate" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <Swords className="w-4 h-4 text-rose-400" />
                  <span>Research Team Debate (Bull vs. Bear)</span>
                </h4>

                {cell.investment_debate_state && (
                  <div className="flex space-x-1 bg-muted/40 p-0.5 rounded-md border border-border/40">
                    <button
                      onClick={() => setDebateFilter("history")}
                      className={`px-2 py-0.5 rounded text-[11px] ${debateFilter === "history" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      Full Debate
                    </button>
                    {cell.investment_debate_state.bull_history && (
                      <button
                        onClick={() => setDebateFilter("bull")}
                        className={`px-2 py-0.5 rounded text-[11px] ${debateFilter === "bull" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                      >
                        Bull View
                      </button>
                    )}
                    {cell.investment_debate_state.bear_history && (
                      <button
                        onClick={() => setDebateFilter("bear")}
                        className={`px-2 py-0.5 rounded text-[11px] ${debateFilter === "bear" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                      >
                        Bear View
                      </button>
                    )}
                  </div>
                )}
              </div>

              {cell.investment_plan && (
                <div className="bg-primary/10 border border-primary/25 rounded-xl p-4">
                  <span className="font-semibold text-primary block mb-1 text-xs">
                    📋 Research Manager: Consolidated Investment Plan
                  </span>
                  <div className="whitespace-pre-wrap font-sans text-zinc-200 leading-relaxed">
                    {cell.investment_plan}
                  </div>
                </div>
              )}

              {cell.investment_debate_state && (
                <div>
                  <span className="font-semibold text-zinc-400 block mb-2 text-xs">
                    {debateFilter === "history" && "💬 Full Debate Transcript"}
                    {debateFilter === "bull" && "🐂 Bull Analyst Arguments"}
                    {debateFilter === "bear" && "🐻 Bear Analyst Arguments"}
                  </span>
                  <div className="bg-muted/20 p-4 rounded-xl border border-border/40 whitespace-pre-wrap font-sans text-zinc-300">
                    {debateFilter === "history" &&
                      (cell.investment_debate_state.history || "No debate history available.")}
                    {debateFilter === "bull" &&
                      (cell.investment_debate_state.bull_history ||
                        "No bull arguments recorded.")}
                    {debateFilter === "bear" &&
                      (cell.investment_debate_state.bear_history ||
                        "No bear arguments recorded.")}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab: Trader Proposal */}
          {activeTab === "trader" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <Briefcase className="w-4 h-4 text-emerald-400" />
                  <span>Trader: Execution Plan & Proposal</span>
                </h4>
              </div>
              <div className="bg-muted/20 p-4 rounded-xl border border-border/40 whitespace-pre-wrap font-sans text-zinc-300">
                {cell.trader_investment_plan}
              </div>
            </div>
          )}

          {/* Tab: Risk Management */}
          {activeTab === "risk" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h4 className="font-semibold text-zinc-200 flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <span>Risk Management Discussion</span>
                </h4>

                {cell.risk_debate_state && (
                  <div className="flex space-x-1 bg-muted/40 p-0.5 rounded-md border border-border/40">
                    <button
                      onClick={() => setRiskFilter("history")}
                      className={`px-2 py-0.5 rounded text-[11px] ${riskFilter === "history" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      Full Discussion
                    </button>
                    {cell.risk_debate_state.aggressive_history && (
                      <button
                        onClick={() => setRiskFilter("aggressive")}
                        className={`px-2 py-0.5 rounded text-[11px] ${riskFilter === "aggressive" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                      >
                        Aggressive
                      </button>
                    )}
                    {cell.risk_debate_state.conservative_history && (
                      <button
                        onClick={() => setRiskFilter("conservative")}
                        className={`px-2 py-0.5 rounded text-[11px] ${riskFilter === "conservative" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                      >
                        Conservative
                      </button>
                    )}
                    {cell.risk_debate_state.neutral_history && (
                      <button
                        onClick={() => setRiskFilter("neutral")}
                        className={`px-2 py-0.5 rounded text-[11px] ${riskFilter === "neutral" ? "bg-card text-foreground font-semibold shadow" : "text-muted-foreground hover:text-foreground"}`}
                      >
                        Neutral
                      </button>
                    )}
                  </div>
                )}
              </div>

              {cell.risk_debate_state && (
                <div className="bg-muted/20 p-4 rounded-xl border border-border/40 whitespace-pre-wrap font-sans text-zinc-300">
                  {riskFilter === "history" &&
                    (cell.risk_debate_state.history || "No risk debate history available.")}
                  {riskFilter === "aggressive" &&
                    (cell.risk_debate_state.aggressive_history || "No aggressive view recorded.")}
                  {riskFilter === "conservative" &&
                    (cell.risk_debate_state.conservative_history ||
                      "No conservative view recorded.")}
                  {riskFilter === "neutral" &&
                    (cell.risk_debate_state.neutral_history || "No neutral view recorded.")}
                </div>
              )}
            </div>
          )}

          {/* Tab: Settlement Reflection */}
          {activeTab === "reflection" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-emerald-400 flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  <span>Settlement Reflection (Post-Holding Evaluation & Lessons)</span>
                </h4>
              </div>
              <div className="bg-emerald-500/5 p-4 rounded-xl border border-emerald-500/20 whitespace-pre-wrap font-sans text-zinc-300">
                {cell.reflection}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border/40 bg-muted/10 flex items-center justify-between">
          <span className="text-[11px] text-muted-foreground">
            TradingAgents Multi-Agent Reasoning Trace
          </span>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
