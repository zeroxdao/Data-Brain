"use client";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { REGIME_LABEL_ZH } from "@/lib/utils";

const BADGE_VARIANT: Record<string, "green" | "red" | "yellow" | "purple" | "blue"> = {
  trend_up: "green",
  trend_down: "red",
  range: "yellow",
  high_volatility: "purple",
  low_volatility: "blue",
};

export function RegimeHistoryList({ symbol }: { symbol: string }) {
  const { data, isLoading } = useSWR(
    `regime-history-${symbol}`,
    () => api.regime(symbol, 30, 10),
    { refreshInterval: 30000 }
  );

  if (isLoading) return <Spinner />;
  if (!data?.length) return <p className="text-xs text-[#8b949e]">无数据</p>;

  return (
    <div className="space-y-2">
      {[...data].reverse().map((snap, i) => (
        <div
          key={snap.time}
          className="flex items-start gap-2 text-xs"
        >
          <span className="text-[#8b949e] whitespace-nowrap pt-0.5 w-14 shrink-0">
            {new Date(snap.time).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
          </span>
          <div className="flex flex-wrap gap-1">
            {snap.labels.map((l) => (
              <Badge key={l} variant={BADGE_VARIANT[l] ?? "default"} className="text-[10px] py-0">
                {REGIME_LABEL_ZH[l] ?? l}
              </Badge>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
