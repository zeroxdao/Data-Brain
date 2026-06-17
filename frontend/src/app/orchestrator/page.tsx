import { TopBar } from "@/components/dashboard/TopBar";
import { OrchestratorControls } from "@/components/dashboard/OrchestratorControls";
import { EACards } from "@/components/dashboard/EACards";
import { DecisionLog } from "@/components/dashboard/DecisionLog";

const ACCOUNT_ID = "acc-1";
const SYMBOL = "XAUUSD";

export default function OrchestratorPage() {
  return (
    <>
      <TopBar title="调度大脑" subtitle="EA 环境感知调度 · 熔断保护 · 决策日志" />
      <div className="flex-1 p-6 grid grid-cols-12 gap-5 auto-rows-min">
        <div className="col-span-12 lg:col-span-4 space-y-5">
          <OrchestratorControls accountId={ACCOUNT_ID} symbol={SYMBOL} />
          <EACards accountId={ACCOUNT_ID} symbol={SYMBOL} />
        </div>
        <div className="col-span-12 lg:col-span-8">
          <DecisionLog accountId={ACCOUNT_ID} />
        </div>
      </div>
    </>
  );
}
