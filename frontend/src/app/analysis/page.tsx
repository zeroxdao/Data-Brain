import { TopBar } from "@/components/dashboard/TopBar";
import { AnalysisReport } from "@/components/dashboard/AnalysisReport";

const ACCOUNT_ID = "acc-1";
const SYMBOL = "XAUUSD";

export default function AnalysisPage() {
  return (
    <>
      <TopBar title="EA 分析" subtitle="按市场环境分析 EA 历史表现" />
      <div className="flex-1 p-6 max-w-4xl">
        <AnalysisReport accountId={ACCOUNT_ID} symbol={SYMBOL} />
      </div>
    </>
  );
}
