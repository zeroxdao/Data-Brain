"use client";
import useSWR from "swr";
import { Activity } from "lucide-react";
import { api } from "@/lib/api";
import { Card, StatRow } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { REGIME_BG, REGIME_LABEL_ZH } from "@/lib/utils";

interface Props {
  symbol: string;
}

const BADGE_VARIANT: Record<string, "green" | "red" | "yellow" | "purple" | "blue"> = {
  trend_up: "green",
  trend_down: "red",
  range: "yellow",
  high_volatility: "purple",
  low_volatility: "blue",
};

export function RegimePanel({ symbol }: Props) {
  const { data, isLoading } = useSWR(
    `regime-${symbol}`,
    () => api.regime(symbol, 30, 5),
    { refreshInterval: 30000 }
  );

  const latest = data?.[data.length - 1];

  return (
    <Card title="当前市场环境" action={<Activity className="w-4 h-4 text-[#8b949e]" />}>
      {isLoading ? (
        <Spinner />
      ) : !latest ? (
        <p className="text-xs text-[#8b949e]">无数据</p>
      ) : (
        <>
          {/* Label badges */}
          <div className="flex flex-wrap gap-2 mb-4">
            {latest.labels.map((l) => (
              <Badge key={l} variant={BADGE_VARIANT[l] ?? "default"}>
                {REGIME_LABEL_ZH[l] ?? l}
              </Badge>
            ))}
            <Badge variant="default">
              {REGIME_LABEL_ZH[latest.session] ?? latest.session}
            </Badge>
          </div>

          {/* Indicators */}
          <div className="space-y-2">
            <IndicatorBar label="ADX（趋势强度）" value={latest.adx} max={60} color="#58a6ff" />
            <StatRow label="ATR" value={latest.atr.toFixed(5)} />
            <StatRow
              label="已实现波动率"
              value={(latest.realized_vol * 100).toFixed(3) + "%"}
            />
            <StatRow
              label="更新时间"
              value={new Date(latest.time).toLocaleTimeString("zh-CN")}
            />
          </div>
        </>
      )}
    </Card>
  );
}

function IndicatorBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-[#8b949e]">{label}</span>
        <span className="text-xs font-medium text-[#e6edf3]">{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[#1c2330] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
