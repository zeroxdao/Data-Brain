"use client";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { fmt, pct, REGIME_LABEL_ZH } from "@/lib/utils";

interface Props {
  accountId: string;
  symbol: string;
}

export function AnalysisReport({ accountId, symbol }: Props) {
  const { data, isLoading } = useSWR(
    `analysis-report-${accountId}-${symbol}`,
    () => api.analysis(accountId, symbol, 60),
    { refreshInterval: 120000 }
  );

  return (
    <Card title={`EA 历史表现分析 — ${data?.analyzed_deals ?? "…"} 笔交易`}>
      {isLoading ? (
        <Spinner />
      ) : !data?.reports.length ? (
        <p className="text-xs text-[#8b949e]">无分析数据</p>
      ) : (
        <div className="space-y-5">
          {data.reports.map((r) => (
            <div key={r.ea_name} className="rounded-lg bg-[#1c2330] border border-[#30363d] p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-[#e6edf3]">{r.ea_name}</span>
                <Badge variant={r.total_profit >= 0 ? "green" : "red"}>
                  {r.total_profit >= 0 ? "+" : ""}
                  {fmt(r.total_profit)} USD
                </Badge>
              </div>

              {/* Overview */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <Stat label="胜率" value={pct(r.overall_win_rate)} ok={r.overall_win_rate >= 0.5} />
                <Stat label="总笔数" value={String(r.total_trades)} />
                <Stat
                  label="均盈亏"
                  value={(r.total_trades > 0 ? fmt(r.total_profit / r.total_trades) : "—")}
                  ok={r.total_profit >= 0}
                />
              </div>

              {/* Per-regime table */}
              <div className="overflow-x-auto mb-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[#8b949e] border-b border-[#30363d]">
                      <th className="text-left pb-1.5 font-medium">环境</th>
                      <th className="text-right pb-1.5 font-medium">笔数</th>
                      <th className="text-right pb-1.5 font-medium">胜率</th>
                      <th className="text-right pb-1.5 font-medium">均盈亏</th>
                      <th className="text-right pb-1.5 font-medium">盈利因子</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.by_regime.map((p) => (
                      <tr key={p.regime} className="border-b border-[#30363d]/40">
                        <td className="py-1.5 pr-2">
                          <span className={p.avg_profit >= 0 ? "text-green-400" : "text-red-400"}>
                            {REGIME_LABEL_ZH[p.regime] ?? p.regime}
                          </span>
                        </td>
                        <td className="py-1.5 text-right text-[#8b949e]">{p.trades}</td>
                        <td className="py-1.5 text-right text-[#8b949e]">{pct(p.win_rate)}</td>
                        <td className={`py-1.5 text-right ${p.avg_profit >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {p.avg_profit >= 0 ? "+" : ""}{fmt(p.avg_profit)}
                        </td>
                        <td className="py-1.5 text-right text-[#8b949e]">
                          {p.profit_factor === 999 ? "∞" : fmt(p.profit_factor)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Insight */}
              <p className="text-xs text-[#8b949e] leading-relaxed border-t border-[#30363d] pt-3">
                💡 {r.insight}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="text-center bg-[#0d1117] rounded-lg p-2">
      <div
        className={`text-sm font-semibold ${
          ok === undefined ? "text-[#e6edf3]" : ok ? "text-green-400" : "text-red-400"
        }`}
      >
        {value}
      </div>
      <div className="text-[10px] text-[#8b949e] mt-0.5">{label}</div>
    </div>
  );
}
