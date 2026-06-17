"""把"交易历史 + 环境标签"聚合成每个 EA 的环境表现报告。

逻辑（功能2 分析版）：
1. 抓取账户的历史成交（按 EA 名分组）。
2. 抓取同期 K 线，算出环境快照序列。
3. 给每笔交易按"平仓时刻的环境标签"归因。
4. 聚合每个 EA 在每个环境标签下的：笔数、胜率、总盈亏、盈利因子。
5. 给出最佳/最差环境与可读洞察（供调度大脑或人工参考）。

注意：这里只做"分析与洞察"，不自动下单。自动切换属于阶段2。
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.bridge.base import TradingBridge
from app.regime import RegimeClassifier
from app.schemas import (
    AnalysisResponse,
    Deal,
    EARegimePerformance,
    EAReport,
    RegimeLabel,
    RegimeSnapshot,
)

_MIN_TRADES_FOR_INSIGHT = 3


# 无亏损单时用一个上限值代替 inf（保持 JSON 可序列化）
_PROFIT_FACTOR_CAP = 999.0


def _profit_factor(profits: list[float]) -> float:
    gains = sum(p for p in profits if p > 0)
    losses = -sum(p for p in profits if p < 0)
    if losses == 0:
        return _PROFIT_FACTOR_CAP if gains > 0 else 0.0
    return round(min(gains / losses, _PROFIT_FACTOR_CAP), 3)


class EAPerformanceAnalyzer:
    def __init__(self, bridge: TradingBridge, classifier: RegimeClassifier | None = None) -> None:
        self.bridge = bridge
        self.classifier = classifier or RegimeClassifier()

    async def analyze(
        self,
        account_id: str,
        symbol: str,
        start: datetime,
        end: datetime,
        ea_name_overrides: dict[str, str] | None = None,
        timeframe: str = "H1",
    ) -> AnalysisResponse:
        deals = await self.bridge.get_deals(account_id, start, end, symbol=symbol)
        candles = await self.bridge.get_candles(symbol, timeframe, start, end)
        snapshots = self.classifier.classify(candles, symbol)

        # 可选：用用户标注覆盖/补充 EA 名称
        if ea_name_overrides:
            for d in deals:
                if d.deal_id in ea_name_overrides:
                    d.ea_name = ea_name_overrides[d.deal_id]

        reports = self._build_reports(deals, snapshots)
        return AnalysisResponse(
            account_id=account_id,
            symbol=symbol,
            analyzed_deals=len(deals),
            reports=reports,
        )

    def _build_reports(
        self, deals: list[Deal], snapshots: list[RegimeSnapshot]
    ) -> list[EAReport]:
        # 按 EA -> 环境标签 -> 该标签下的盈亏列表
        by_ea: dict[str, dict[RegimeLabel, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        ea_all: dict[str, list[float]] = defaultdict(list)

        for d in deals:
            ea = d.ea_name or "未标注EA"
            snap = RegimeClassifier.label_at(snapshots, d.close_time)
            ea_all[ea].append(d.profit)
            if snap is None:
                continue
            for label in snap.labels:
                by_ea[ea][label].append(d.profit)

        reports: list[EAReport] = []
        for ea, profits in ea_all.items():
            per_regime: list[EARegimePerformance] = []
            for label, plist in by_ea[ea].items():
                if not plist:
                    continue
                wins = sum(1 for p in plist if p > 0)
                per_regime.append(
                    EARegimePerformance(
                        ea_name=ea,
                        regime=label,
                        trades=len(plist),
                        win_rate=round(wins / len(plist), 3),
                        total_profit=round(sum(plist), 2),
                        avg_profit=round(sum(plist) / len(plist), 2),
                        profit_factor=_profit_factor(plist),
                    )
                )

            # 最佳/最差环境：以平均盈亏排序，且样本量达标
            ranked = sorted(
                [r for r in per_regime if r.trades >= _MIN_TRADES_FOR_INSIGHT],
                key=lambda r: r.avg_profit,
                reverse=True,
            )
            best = [r.regime for r in ranked if r.avg_profit > 0][:2]
            worst = [r.regime for r in reversed(ranked) if r.avg_profit < 0][:2]

            wins = sum(1 for p in profits if p > 0)
            reports.append(
                EAReport(
                    ea_name=ea,
                    total_trades=len(profits),
                    total_profit=round(sum(profits), 2),
                    overall_win_rate=round(wins / len(profits), 3) if profits else 0.0,
                    by_regime=sorted(per_regime, key=lambda r: r.regime.value),
                    best_regimes=best,
                    worst_regimes=worst,
                    insight=self._insight(ea, best, worst, len(profits)),
                )
            )
        return sorted(reports, key=lambda r: r.total_profit, reverse=True)

    @staticmethod
    def _insight(
        ea: str,
        best: list[RegimeLabel],
        worst: list[RegimeLabel],
        total: int,
    ) -> str:
        if total < _MIN_TRADES_FOR_INSIGHT:
            return f"{ea}: 样本不足（{total} 笔），暂无可靠结论，建议积累更多交易。"
        parts: list[str] = []
        if best:
            parts.append("在 " + "、".join(b.value for b in best) + " 环境下表现最好")
        if worst:
            parts.append("在 " + "、".join(w.value for w in worst) + " 环境下亏损")
        if not parts:
            return f"{ea}: 各环境表现接近，未见明显环境偏好。"
        suggestion = ""
        if best and worst:
            suggestion = "；建议：仅在最佳环境启用该 EA，在最差环境暂停或降仓。"
        return f"{ea}: " + "，".join(parts) + suggestion
