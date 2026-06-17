"use client";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { REGIME_LABEL_ZH } from "@/lib/utils";

interface Props {
  accountId: string;
}

export function DecisionLog({ accountId }: Props) {
  const { data, isLoading } = useSWR(
    `log-${accountId}`,
    () =>
      api.orchestratorLog(accountId, 15).catch(() => null),
    { refreshInterval: 10000 }
  );

  return (
    <Card title="决策日志">
      {isLoading ? (
        <Spinner />
      ) : !data?.entries.length ? (
        <p className="text-xs text-[#8b949e]">暂无记录，启动调度大脑后将自动生成。</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#30363d] text-[#8b949e]">
                <th className="text-left pb-2 pr-4 font-medium">时间</th>
                <th className="text-left pb-2 pr-4 font-medium">环境</th>
                <th className="text-left pb-2 pr-4 font-medium">EA 决策</th>
                <th className="text-left pb-2 font-medium">熔断</th>
              </tr>
            </thead>
            <tbody>
              {[...data.entries].reverse().map((entry, i) => (
                <tr
                  key={i}
                  className="border-b border-[#30363d]/50 hover:bg-white/2 transition-colors"
                >
                  <td className="py-2.5 pr-4 text-[#8b949e] whitespace-nowrap">
                    {new Date(entry.timestamp).toLocaleTimeString("zh-CN")}
                  </td>
                  <td className="py-2.5 pr-4">
                    <div className="flex flex-wrap gap-1">
                      {entry.regime_labels.map((l) => (
                        <span key={l} className="text-[#8b949e]">
                          {REGIME_LABEL_ZH[l] ?? l}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2.5 pr-4">
                    <div className="flex flex-wrap gap-1.5">
                      {entry.decisions.map((d) => (
                        <Badge
                          key={d.ea_name}
                          variant={d.enabled ? "green" : "default"}
                        >
                          {d.ea_name} {d.enabled ? `${(d.weight * 100).toFixed(0)}%` : "—"}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="py-2.5">
                    <Badge
                      variant={
                        entry.circuit_status === "active" ? "green" : "red"
                      }
                    >
                      {entry.circuit_status === "active" ? "正常" : entry.circuit_status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
