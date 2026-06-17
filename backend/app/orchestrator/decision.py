"""决策引擎：把"EA 历史表现画像 + 当前市场环境"转成每个 EA 的"启停 + 权重"建议。

核心思路（可解释、无需深度学习）
──────────────────────────────────
1. 从历史分析结果拿每个 EA 在每种环境下的平均盈亏（avg_profit）。
2. 当前环境已有标签（trend_up / range / high_volatility …）。
3. 用 softmax-like 归一化把"环境匹配得分"转成 0-1 的"建议权重"：
   - 得分 > 0 → 权重 > 0，启用。
   - 得分 ≤ 0 → 权重 = 0，暂停（最差环境直接关掉，不是靠降权重）。
4. 强制约束：
   - 同时启用的 EA 数量上限（避免冲突过多）。
   - 权重之和归一（总仓位不膨胀）。
   - 样本量不足的 EA 默认给"中立权重"而非关掉，防止误杀新 EA。

设计原则
────────
- 不自动下单，只输出"建议"结构体（EADecision），调度器决定是否执行。
- 可解释：每个 EA 的决策都附上"理由"字符串，方便 Dashboard 展示。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from app.schemas import EAReport, RegimeLabel, RegimeSnapshot

_MIN_TRADES_REQUIRED = 5  # 样本不足时保持中立而非关闭


@dataclass
class EADecision:
    ea_name: str
    enabled: bool
    weight: float          # 0.0–1.0，表示"当前该给这个 EA 多少比例的仓位"
    score: float           # 原始环境匹配得分（avg_profit in current regime）
    reason: str


class DecisionEngine:
    """把 EA 表现报告 + 当前环境快照 → EA 启停 / 权重决策。"""

    def __init__(
        self,
        max_active_eas: int = 3,
        min_weight_to_enable: float = 0.05,
    ) -> None:
        self.max_active_eas = max_active_eas
        self.min_weight_to_enable = min_weight_to_enable

    def decide(
        self,
        reports: list[EAReport],
        current_regime: RegimeSnapshot,
    ) -> list[EADecision]:
        """主决策方法。"""
        if not reports:
            return []

        raw_scores: dict[str, tuple[float, str]] = {}
        for report in reports:
            score, reason = self._score_for_regime(report, current_regime)
            raw_scores[report.ea_name] = (score, reason)

        # softmax 归一化让得分可比
        weights = self._softmax_weights(
            {ea: s for ea, (s, _) in raw_scores.items()}
        )

        decisions: list[EADecision] = []
        for report in reports:
            score, reason = raw_scores[report.ea_name]
            w = weights.get(report.ea_name, 0.0)

            # 若当前环境在该 EA 的最差环境列表 → 直接关闭（覆盖权重）
            worst = set(report.worst_regimes)
            active_labels = set(current_regime.labels)
            is_worst_env = bool(worst & active_labels)

            if is_worst_env:
                enabled = False
                w = 0.0
                reason = f"当前环境 {[l.value for l in active_labels]} 在最差环境列表中，已暂停"
            elif report.total_trades < _MIN_TRADES_REQUIRED:
                enabled = True  # 样本不足：保持中立，权重保留，不关闭
                reason = f"样本不足（{report.total_trades} 笔），保持默认权重观察"
            else:
                enabled = w >= self.min_weight_to_enable

            decisions.append(
                EADecision(
                    ea_name=report.ea_name,
                    enabled=enabled,
                    weight=round(w, 4),
                    score=round(score, 4),
                    reason=reason,
                )
            )

        # 按权重降序，仅保留前 N 个启用（其余关闭，不改 reason）
        decisions.sort(key=lambda d: d.weight, reverse=True)
        active_count = 0
        for d in decisions:
            if d.enabled:
                active_count += 1
                if active_count > self.max_active_eas:
                    d.enabled = False
                    d.weight = 0.0
                    d.reason += f"（超过最大同时 EA 数量 {self.max_active_eas}，暂停）"

        # 对启用的 EA 权重再归一化
        total_w = sum(d.weight for d in decisions if d.enabled)
        if total_w > 0:
            for d in decisions:
                if d.enabled:
                    d.weight = round(d.weight / total_w, 4)

        return decisions

    @staticmethod
    def _score_for_regime(
        report: EAReport,
        regime: RegimeSnapshot,
    ) -> tuple[float, str]:
        """找出当前环境对应的 avg_profit 作为原始得分。

        优先找精确匹配标签的 EARegimePerformance；
        无匹配时退回到 overall avg_profit；
        样本不足时给中性 0 分。
        """
        active_labels = set(regime.labels)
        matched: list[float] = []
        for perf in report.by_regime:
            if perf.regime in active_labels and perf.trades >= _MIN_TRADES_REQUIRED:
                matched.append(perf.avg_profit)

        if not matched:
            if report.total_trades < _MIN_TRADES_REQUIRED:
                return 0.0, "样本不足，中性评分"
            overall = (
                report.total_profit / report.total_trades
                if report.total_trades > 0
                else 0.0
            )
            return overall, f"无当前环境数据，使用整体均值 {overall:.2f}"

        avg = sum(matched) / len(matched)
        label_str = "/".join(l.value for l in active_labels)
        return avg, f"在 {label_str} 环境下历史均盈亏 {avg:.2f}"

    @staticmethod
    def _softmax_weights(scores: dict[str, float]) -> dict[str, float]:
        """把任意实数得分转成 0-1 权重（不强制为 0，负分也给少量权重）。

        用 temperature=0.5 避免极化（一个 EA 独占权重）。
        """
        if not scores:
            return {}
        temperature = 0.5
        keys = list(scores.keys())
        vals = [scores[k] / temperature for k in keys]
        max_v = max(vals)
        exps = [math.exp(v - max_v) for v in vals]
        total = sum(exps)
        return {k: e / total for k, e in zip(keys, exps)}
