"use client";
import useSWR from "swr";
import { CheckCircle2, PauseCircle, TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { fmt, pct, REGIME_LABEL_ZH } from "@/lib/utils";

interface Props {
  accountId: string;
  symbol: string;
}

export function EACards({ accountId, symbol }: Props) {
  const { data: orch, isLoading } = useSWR(
    `orch-status-ea-${accountId}`,
    () =>
      api
        .orchestratorStatus(accountId)
        .catch(() => null),
    { refreshInterval: 5000 }
  );

  const { data: analysis } = useSWR(
    `analysis-ea-${accountId}-${symbol}`,
    () => api.analysis(accountId, symbol, 60),
    { refreshInterval: 60000 }
  );

  if (isLoading) return <Card title="EA 调度状态"><Spinner /></Card>;

  const decisions = orch?.active_decisions ?? [];
  const reports = analysis?.reports ?? [];

  return (
    <Card title="EA 调度状态">
      {decisions.length === 0 ? (
        <p className="text-xs text-[#8b949e]">调度大脑未启动，暂无 EA 决策。</p>
      ) : (
        <div className="space-y-3">
          {decisions.map((d) => {
            const report = reports.find((r) => r.ea_name === d.ea_name);
            return (
              <div
                key={d.ea_name}
                className={`rounded-lg border p-3.5 transition-colors ${
                  d.enabled
                    ? "border-green-500/30 bg-green-500/5"
                    : "border-[#30363d] bg-[#1c2330]"
                }`}
              >
                {/* Header */}
                <div className="flex items-center gap-2 mb-2.5">
                  {d.enabled ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                  ) : (
                    <PauseCircle className="w-4 h-4 text-[#8b949e] shrink-0" />
                  )}
                  <span className="text-sm font-medium text-[#e6edf3] flex-1 truncate">
                    {d.ea_name}
                  </span>
                  <Badge variant={d.enabled ? "green" : "default"}>
                    {d.enabled ? "启用" : "暂停"}
                  </Badge>
                </div>

                {/* Weight bar */}
                {d.enabled && (
                  <div className="mb-2.5">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs text-[#8b949e]">权重</span>
                      <span className="text-xs font-medium text-[#58a6ff]">
                        {pct(d.weight)}
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[#0d1117] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#58a6ff] transition-all duration-700"
                        style={{ width: `${d.weight * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Reason */}
                <p className="text-xs text-[#8b949e] leading-relaxed mb-2.5">{d.reason}</p>

                {/* From analysis report */}
                {report && (
                  <div className="border-t border-[#30363d] pt-2 grid grid-cols-3 gap-2">
                    <Mini
                      label="胜率"
                      value={pct(report.overall_win_rate)}
                      ok={report.overall_win_rate >= 0.5}
                    />
                    <Mini
                      label="总盈亏"
                      value={(report.total_profit >= 0 ? "+" : "") + fmt(report.total_profit)}
                      ok={report.total_profit >= 0}
                    />
                    <Mini label="笔数" value={String(report.total_trades)} />
                  </div>
                )}

                {/* Best/worst regimes */}
                {report && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {report.best_regimes.map((r) => (
                      <span
                        key={r}
                        className="inline-flex items-center gap-1 text-[10px] text-green-400"
                      >
                        <TrendingUp className="w-2.5 h-2.5" />
                        {REGIME_LABEL_ZH[r] ?? r}
                      </span>
                    ))}
                    {report.worst_regimes.map((r) => (
                      <span
                        key={r}
                        className="inline-flex items-center gap-1 text-[10px] text-red-400"
                      >
                        <TrendingDown className="w-2.5 h-2.5" />
                        {REGIME_LABEL_ZH[r] ?? r}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

function Mini({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <div className="text-center">
      <div
        className={`text-sm font-semibold ${
          ok === undefined
            ? "text-[#e6edf3]"
            : ok
            ? "text-green-400"
            : "text-red-400"
        }`}
      >
        {value}
      </div>
      <div className="text-[10px] text-[#8b949e]">{label}</div>
    </div>
  );
}
