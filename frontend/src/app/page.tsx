import { TopBar } from "@/components/dashboard/TopBar";
import { AccountCard } from "@/components/dashboard/AccountCard";
import { RegimePanel } from "@/components/dashboard/RegimePanel";
import { EACards } from "@/components/dashboard/EACards";
import { OrchestratorControls } from "@/components/dashboard/OrchestratorControls";
import { CandleChart } from "@/components/dashboard/CandleChart";

const ACCOUNT_ID = "acc-1";
const SYMBOL = "XAUUSD";

export default function DashboardPage() {
  return (
    <>
      <TopBar
        title="总览"
        subtitle={`${ACCOUNT_ID} · ${SYMBOL}`}
      />
      <div className="flex-1 p-6 grid grid-cols-12 gap-5 auto-rows-min">

        {/* Left column: account + controls */}
        <div className="col-span-12 lg:col-span-3 space-y-5">
          <AccountCard accountId={ACCOUNT_ID} />
          <OrchestratorControls accountId={ACCOUNT_ID} symbol={SYMBOL} />
          <RegimePanel symbol={SYMBOL} />
        </div>

        {/* Center: chart + EA cards */}
        <div className="col-span-12 lg:col-span-6 space-y-5">
          <CandleChart symbol={SYMBOL} days={30} />
          <EACards accountId={ACCOUNT_ID} symbol={SYMBOL} />
        </div>

        {/* Right column: regime history */}
        <div className="col-span-12 lg:col-span-3 space-y-5">
          <RegimeHistoryCard symbol={SYMBOL} />
        </div>

      </div>
    </>
  );
}

// ── Regime history (inline, keeps page self-contained) ────────────────────────
import { Suspense } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

function RegimeHistoryCard({ symbol }: { symbol: string }) {
  return (
    <Card title="环境历史（最近 10 根）">
      <Suspense fallback={<p className="text-xs text-[#8b949e]">加载中…</p>}>
        <RegimeHistoryList symbol={symbol} />
      </Suspense>
    </Card>
  );
}

// Client component for live updates
import { RegimeHistoryList } from "@/components/dashboard/RegimeHistoryList";
