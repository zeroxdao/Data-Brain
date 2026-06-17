"use client";
import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { Play, Square, RotateCcw, Settings2 } from "lucide-react";
import { api, type OrchestratorStatus } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

interface Props {
  accountId: string;
  symbol: string;
}

export function OrchestratorControls({ accountId, symbol }: Props) {
  const { mutate } = useSWRConfig();
  const [busy, setBusy] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [cfg, setCfg] = useState({
    max_drawdown_pct: 10,
    max_daily_loss_pct: 3,
    max_active_eas: 3,
    interval_seconds: 60,
  });

  const { data: orch, isLoading } = useSWR<OrchestratorStatus | null>(
    `orch-ctrl-${accountId}`,
    () =>
      api.orchestratorStatus(accountId).catch(() => null),
    { refreshInterval: 4000 }
  );

  const invalidate = () => {
    mutate(`orch-ctrl-${accountId}`);
    mutate(`orch-status-${accountId}`);
    mutate(`orch-status-ea-${accountId}`);
  };

  const handleStart = async () => {
    setBusy(true);
    try {
      await api.startOrchestrator(accountId, { symbol, ...cfg });
      invalidate();
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    setBusy(true);
    try {
      await api.stopOrchestrator(accountId);
      invalidate();
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    setBusy(true);
    try {
      await api.resetCircuit(accountId);
      invalidate();
    } finally {
      setBusy(false);
    }
  };

  const running = orch?.scheduler_status === "running";
  const tripped =
    orch?.circuit_status && orch.circuit_status !== "active";

  return (
    <Card
      title="调度大脑控制"
      action={
        orch ? (
          <Badge variant={running ? "green" : "default"}>
            {running ? "运行中" : "已停止"}
          </Badge>
        ) : null
      }
    >
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-4">
          {/* Status row */}
          {orch && (
            <div className="text-xs text-[#8b949e] space-y-1">
              <div>账号: <span className="text-[#e6edf3]">{accountId}</span></div>
              <div>品种: <span className="text-[#e6edf3]">{orch.symbol}</span></div>
              {orch.last_updated && (
                <div>
                  上次更新:{" "}
                  <span className="text-[#e6edf3]">
                    {new Date(orch.last_updated).toLocaleTimeString("zh-CN")}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            {!running ? (
              <Button
                variant="primary"
                size="sm"
                loading={busy}
                onClick={handleStart}
              >
                <Play className="w-3.5 h-3.5" />
                启动调度
              </Button>
            ) : (
              <Button
                variant="danger"
                size="sm"
                loading={busy}
                onClick={handleStop}
              >
                <Square className="w-3.5 h-3.5" />
                停止调度
              </Button>
            )}

            {tripped && (
              <Button
                variant="outline"
                size="sm"
                loading={busy}
                onClick={handleReset}
              >
                <RotateCcw className="w-3.5 h-3.5" />
                重置熔断
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowConfig((v) => !v)}
            >
              <Settings2 className="w-3.5 h-3.5" />
              参数
            </Button>
          </div>

          {/* Config panel */}
          {showConfig && (
            <div className="rounded-lg bg-[#1c2330] border border-[#30363d] p-4 space-y-3">
              <h4 className="text-xs font-medium text-[#e6edf3] mb-2">调度参数</h4>
              <ConfigInput
                label="最大回撤熔断 (%)"
                value={cfg.max_drawdown_pct}
                onChange={(v) => setCfg((c) => ({ ...c, max_drawdown_pct: v }))}
              />
              <ConfigInput
                label="最大日亏熔断 (%)"
                value={cfg.max_daily_loss_pct}
                onChange={(v) => setCfg((c) => ({ ...c, max_daily_loss_pct: v }))}
              />
              <ConfigInput
                label="最多同时 EA 数"
                value={cfg.max_active_eas}
                onChange={(v) => setCfg((c) => ({ ...c, max_active_eas: v }))}
              />
              <ConfigInput
                label="调度间隔 (秒)"
                value={cfg.interval_seconds}
                onChange={(v) => setCfg((c) => ({ ...c, interval_seconds: v }))}
              />
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function ConfigInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <label className="text-xs text-[#8b949e] flex-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-20 text-xs text-right bg-[#0d1117] border border-[#30363d] rounded-md px-2 py-1.5 text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]"
      />
    </div>
  );
}
