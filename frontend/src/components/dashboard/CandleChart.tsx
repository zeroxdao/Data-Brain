"use client";
import { useEffect, useRef } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

interface Props {
  symbol: string;
  days?: number;
}

const REGIME_COLORS: Record<string, string> = {
  trend_up: "#3fb950",
  trend_down: "#f85149",
  range: "#d29922",
  high_volatility: "#bc8cff",
  low_volatility: "#58a6ff",
};

const REGIME_ZH: Record<string, string> = {
  trend_up: "上涨趋势",
  trend_down: "下跌趋势",
  range: "震荡",
  high_volatility: "高波动",
  low_volatility: "低波动",
};

export function CandleChart({ symbol, days = 30 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const seriesRef = useRef<any>(null);

  const { data: candles, isLoading } = useSWR(
    `candles-${symbol}-${days}`,
    () => api.candles(symbol, days),
    { refreshInterval: 60000 }
  );

  // Init chart on mount
  useEffect(() => {
    if (!containerRef.current) return;

    let chart: any;
    let series: any;

    // Dynamic import to avoid SSR issues
    import("lightweight-charts").then((lc) => {
      if (!containerRef.current) return;
      chart = lc.createChart(containerRef.current, {
        layout: {
          background: { type: lc.ColorType.Solid, color: "#161b22" },
          textColor: "#8b949e",
        },
        grid: {
          vertLines: { color: "#30363d" },
          horzLines: { color: "#30363d" },
        },
        crosshair: { mode: lc.CrosshairMode.Normal },
        rightPriceScale: { borderColor: "#30363d" },
        timeScale: {
          borderColor: "#30363d",
          timeVisible: true,
          secondsVisible: false,
        },
        width: containerRef.current.clientWidth,
        height: 280,
      });

      series = chart.addSeries(lc.CandlestickSeries, {
        upColor: "#3fb950",
        downColor: "#f85149",
        borderUpColor: "#3fb950",
        borderDownColor: "#f85149",
        wickUpColor: "#3fb950",
        wickDownColor: "#f85149",
      });

      chartRef.current = chart;
      seriesRef.current = series;

      const ro = new ResizeObserver(() => {
        if (containerRef.current && chart)
          chart.resize(containerRef.current.clientWidth, 280);
      });
      ro.observe(containerRef.current);

      return () => {
        ro.disconnect();
        chart.remove();
      };
    });

    return () => {
      chartRef.current?.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update data
  useEffect(() => {
    if (!seriesRef.current || !candles?.length) return;
    const data = candles.map((c) => ({
      time: Math.floor(new Date(c.time).getTime() / 1000) as unknown as import("lightweight-charts").Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    seriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return (
    <Card title={`K 线图 — ${symbol}`}>
      {isLoading ? (
        <div className="flex items-center justify-center h-[280px]">
          <Spinner />
        </div>
      ) : (
        <div ref={containerRef} className="w-full" />
      )}
      <div className="flex flex-wrap gap-3 mt-3 pt-3 border-t border-[#30363d]">
        {Object.entries(REGIME_COLORS).map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-3 h-2 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-xs text-[#8b949e]">{REGIME_ZH[label]}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
