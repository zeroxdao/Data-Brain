import { TopBar } from "@/components/dashboard/TopBar";
import { DecisionLog } from "@/components/dashboard/DecisionLog";

const ACCOUNT_ID = "acc-1";

export default function LogPage() {
  return (
    <>
      <TopBar title="决策日志" subtitle="调度大脑历史决策记录" />
      <div className="flex-1 p-6 max-w-5xl">
        <DecisionLog accountId={ACCOUNT_ID} />
      </div>
    </>
  );
}
