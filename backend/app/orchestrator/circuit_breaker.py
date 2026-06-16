"""熔断保护器。

两道防线：
1. 回撤熔断：账户净值从历史高点回落超过阈值 → 全停。
2. 日亏熔断：当日累计亏损超过账户余额一定比例 → 全停。

熔断触发后需要人工（或 API 指令）重置，不会自动恢复，
避免系统在极端行情中反复尝试。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class CircuitStatus(str, Enum):
    ACTIVE = "active"          # 正常运行
    TRIPPED_DRAWDOWN = "tripped_drawdown"   # 回撤熔断
    TRIPPED_DAILY_LOSS = "tripped_daily_loss"  # 日亏熔断
    MANUALLY_STOPPED = "manually_stopped"   # 人工停止


@dataclass
class CircuitBreakerConfig:
    max_drawdown_pct: float = 10.0   # 最大允许回撤 %（从权益高点）
    max_daily_loss_pct: float = 3.0  # 最大允许日亏 %（相对账户余额）


@dataclass
class CircuitBreaker:
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)

    # 运行时状态
    _status: CircuitStatus = field(default=CircuitStatus.ACTIVE, init=False)
    _peak_equity: float = field(default=0.0, init=False)
    _day_start_balance: float = field(default=0.0, init=False)
    _day_start_date: date = field(default_factory=lambda: date.today(), init=False)
    _trip_reason: str = field(default="", init=False)

    @property
    def status(self) -> CircuitStatus:
        return self._status

    @property
    def is_tripped(self) -> bool:
        return self._status != CircuitStatus.ACTIVE

    def update(self, equity: float, balance: float) -> CircuitStatus:
        """每个调度周期调用一次，传入当前净值和余额，返回当前状态。"""
        if self.is_tripped:
            return self._status  # 熔断后不自动恢复

        today = datetime.now(timezone.utc).date()
        if today != self._day_start_date:
            # 新的一天，重置日亏计数
            self._day_start_date = today
            self._day_start_balance = balance

        if self._day_start_balance == 0:
            self._day_start_balance = balance
        if self._peak_equity == 0:
            self._peak_equity = equity

        # 更新权益高点
        if equity > self._peak_equity:
            self._peak_equity = equity

        # 检查回撤
        drawdown_pct = (self._peak_equity - equity) / self._peak_equity * 100
        if drawdown_pct >= self.config.max_drawdown_pct:
            self._trip(
                CircuitStatus.TRIPPED_DRAWDOWN,
                f"回撤 {drawdown_pct:.2f}% 超过阈值 {self.config.max_drawdown_pct}%",
            )
            return self._status

        # 检查日亏
        daily_loss_pct = (self._day_start_balance - balance) / self._day_start_balance * 100
        if daily_loss_pct >= self.config.max_daily_loss_pct:
            self._trip(
                CircuitStatus.TRIPPED_DAILY_LOSS,
                f"日亏 {daily_loss_pct:.2f}% 超过阈值 {self.config.max_daily_loss_pct}%",
            )
            return self._status

        return CircuitStatus.ACTIVE

    def trip_manually(self) -> None:
        self._trip(CircuitStatus.MANUALLY_STOPPED, "人工停止")

    def reset(self) -> None:
        """人工重置熔断（需谨慎，应先确认极端行情已过）。"""
        self._status = CircuitStatus.ACTIVE
        self._trip_reason = ""

    def _trip(self, status: CircuitStatus, reason: str) -> None:
        self._status = status
        self._trip_reason = reason

    @property
    def trip_reason(self) -> str:
        return self._trip_reason
