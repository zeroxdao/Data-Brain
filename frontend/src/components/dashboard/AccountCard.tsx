"use client";
import useSWR from "swr";
import { TrendingUp, Wallet, ShieldAlert, ShieldCheck } from "lucide-react";
import { api, type OrchestratorStatus } from "@/lib/api";
import { Card, StatRow } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { fmt } from "@/lib/utils";

interface Props {
  accountId: string;
}

const CIRCUIT_VARIANT: Record<string, "green" | "red" | "yellow"> = {
  active: "green",
  tripped_drawdown: "red",
  tripped_daily_loss: "red",
  manually_stopped: "yellow",
};

const CIRCUIT_ZH: Record<string, string> = {
  active: "正常",
  tripped_drawdown: "回撤熔断",
  tripped_daily_loss: "日亏熔断",
  manually_stopped: "人工停止",
};

export function AccountCard({ accountId }: Props) {
  const { data: acc, isLoading: accLoading } =
    useSWR(`account-${accountId}`, () => api.account(accountId), { refreshInterval: 10000 });

  const { data: orch } =
    useSWR<OrchestratorStatus>(
      `orch-status-${accountId}`,
      () => api.orchestratorStatus(accountId).catch(() => null as unknown as OrchestratorStatus),
      { refreshInterval: 5000 }
    );

  if (accLoading) return <Card title="账户概览"><Spinner /></Card>;
  if (!acc) return null;

  const circuitStatus = orch?.circuit_status ?? "active";
  const isTripped = circuitStatus !== "active";

  return (
    <Card
      title="账户概览"
      action={
        <Badge variant={CIRCUIT_VARIANT[circuitStatus] ?? "default"}>
          {isTripped ? (
            <ShieldAlert className="w-3 h-3 mr-1" />
          ) : (
            <ShieldCheck className="w-3 h-3 mr-1" />
          )}
          {CIRCUIT_ZH[circuitStatus] ?? circuitStatus}
        </Badge>
      }
    >
      {/* Main metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <MetricBox
          label="余额"
          value={`${acc.currency} ${fmt(acc.balance)}`}
          icon={<Wallet className="w-4 h-4 text-[#8b949e]" />}
        />
        <MetricBox
          label="净值"
          value={`${acc.currency} ${fmt(acc.equity)}`}
          icon={<TrendingUp className="w-4 h-4 text-[#8b949e]" />}
          valueClass={acc.equity >= acc.balance ? "text-green-400" : "text-red-400"}
        />
      </div>

      <div className="border-t border-[#30363d] pt-3 space-y-0.5">
        <StatRow label="账号 ID" value={acc.account_id} />
        <StatRow label="券商" value={acc.broker ?? "—"} />
        <StatRow label="杠杆" value={`1:${acc.leverage}`} />
        <StatRow
          label="浮动盈亏"
          value={`${acc.equity - acc.balance >= 0 ? "+" : ""}${fmt(acc.equity - acc.balance)}`}
          valueClass={acc.equity >= acc.balance ? "text-green-400" : "text-red-400"}
        />
      </div>

      {isTripped && orch?.circuit_trip_reason && (
        <div className="mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
          ⚠️ {orch.circuit_trip_reason}
        </div>
      )}
    </Card>
  );
}

function MetricBox({
  label,
  value,
  icon,
  valueClass,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg bg-[#1c2330] border border-[#30363d] p-3">
      <div className="flex items-center gap-1.5 mb-1.5">
        {icon}
        <span className="text-xs text-[#8b949e]">{label}</span>
      </div>
      <div className={`text-base font-semibold ${valueClass ?? "text-[#e6edf3]"}`}>{value}</div>
    </div>
  );
}
