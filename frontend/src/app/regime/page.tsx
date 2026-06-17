import { TopBar } from "@/components/dashboard/TopBar";
import { RegimePanel } from "@/components/dashboard/RegimePanel";
import { CandleChart } from "@/components/dashboard/CandleChart";

const SYMBOL = "XAUUSD";

export default function RegimePage() {
  return (
    <>
      <TopBar title="市场环境" subtitle="ADX · ATR · 波动率 · 交易时段" />
      <div className="flex-1 p-6 grid grid-cols-12 gap-5 auto-rows-min">
        <div className="col-span-12 lg:col-span-4">
          <RegimePanel symbol={SYMBOL} />
        </div>
        <div className="col-span-12 lg:col-span-8">
          <CandleChart symbol={SYMBOL} days={30} />
        </div>
      </div>
    </>
  );
}
