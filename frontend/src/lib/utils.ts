import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`;
}

/** Colour helpers for regime labels */
export const REGIME_COLOR: Record<string, string> = {
  trend_up: "text-green-400",
  trend_down: "text-red-400",
  range: "text-yellow-400",
  high_volatility: "text-purple-400",
  low_volatility: "text-blue-400",
};

export const REGIME_BG: Record<string, string> = {
  trend_up: "bg-green-500/10 border-green-500/30 text-green-400",
  trend_down: "bg-red-500/10 border-red-500/30 text-red-400",
  range: "bg-yellow-500/10 border-yellow-500/30 text-yellow-400",
  high_volatility: "bg-purple-500/10 border-purple-500/30 text-purple-400",
  low_volatility: "bg-blue-500/10 border-blue-500/30 text-blue-400",
};

export const REGIME_LABEL_ZH: Record<string, string> = {
  trend_up: "上涨趋势",
  trend_down: "下跌趋势",
  range: "震荡盘整",
  high_volatility: "高波动",
  low_volatility: "低波动",
  asia: "亚盘",
  europe: "欧盘",
  us: "美盘",
  off_hours: "盘后",
};
