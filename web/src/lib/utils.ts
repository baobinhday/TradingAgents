import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatAlpha(alpha: string | null | undefined): string {
  if (!alpha) return "-";
  return alpha.startsWith("+") || alpha.startsWith("-") ? alpha : `+${alpha}`;
}

export function getAlphaColor(alpha: string | null | undefined): string {
  if (!alpha) return "text-muted-foreground";
  const num = parseFloat(alpha.replace("%", "").replace("+", ""));
  if (isNaN(num)) return "text-muted-foreground";
  if (num > 0) return "text-emerald-400";
  if (num < 0) return "text-rose-400";
  return "text-zinc-400";
}

export function getRatingBadgeClass(rating: string | null | undefined): string {
  switch (rating?.toLowerCase()) {
    case "buy":
      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    case "overweight":
      return "bg-teal-500/20 text-teal-300 border-teal-500/30";
    case "hold":
      return "bg-amber-500/20 text-amber-300 border-amber-500/30";
    case "underweight":
      return "bg-orange-500/20 text-orange-300 border-orange-500/30";
    case "sell":
      return "bg-rose-500/20 text-rose-300 border-rose-500/30";
    default:
      return "bg-zinc-800 text-zinc-400 border-zinc-700";
  }
}
