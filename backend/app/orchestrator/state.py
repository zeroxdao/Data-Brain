"""调度状态管理。

每个账号维护一个 AccountOrchestratorState：
- 当前调度状态（运行/停止）
- 当前激活的 EA 列表 + 权重
- 当前市场环境快照
- 历史决策日志（最近 N 条）
- 熔断器实例

OrchestratorState 是全局单例注册表，管理所有账号的状态。
MVP 用内存存储；后续可换成 Redis。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.orchestrator.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitStatus
from app.orchestrator.decision import EADecision
from app.schemas import RegimeSnapshot


class SchedulerStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"


_MAX_DECISION_LOG = 50  # 保留最近 N 条历史决策


@dataclass
class DecisionLogEntry:
    timestamp: datetime
    regime_labels: list[str]
    decisions: list[EADecision]
    circuit_status: CircuitStatus


@dataclass
class AccountOrchestratorState:
    account_id: str
    symbol: str
    scheduler_status: SchedulerStatus = SchedulerStatus.STOPPED
    current_regime: Optional[RegimeSnapshot] = None
    active_decisions: list[EADecision] = field(default_factory=list)
    decision_log: list[DecisionLogEntry] = field(default_factory=list)
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    last_updated: Optional[datetime] = None

    def record_decision(
        self, decisions: list[EADecision], regime: RegimeSnapshot
    ) -> None:
        self.active_decisions = decisions
        self.current_regime = regime
        self.last_updated = datetime.now(timezone.utc)
        entry = DecisionLogEntry(
            timestamp=self.last_updated,
            regime_labels=[l.value for l in regime.labels],
            decisions=list(decisions),
            circuit_status=self.circuit_breaker.status,
        )
        self.decision_log.append(entry)
        if len(self.decision_log) > _MAX_DECISION_LOG:
            self.decision_log = self.decision_log[-_MAX_DECISION_LOG:]

    def to_status_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "symbol": self.symbol,
            "scheduler_status": self.scheduler_status.value,
            "circuit_status": self.circuit_breaker.status.value,
            "circuit_trip_reason": self.circuit_breaker.trip_reason,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "current_regime": {
                "labels": [l.value for l in self.current_regime.labels],
                "adx": self.current_regime.adx,
                "atr": self.current_regime.atr,
                "session": self.current_regime.session.value,
            }
            if self.current_regime
            else None,
            "active_decisions": [
                {
                    "ea_name": d.ea_name,
                    "enabled": d.enabled,
                    "weight": d.weight,
                    "reason": d.reason,
                }
                for d in self.active_decisions
            ],
        }


class OrchestratorState:
    """全局状态注册表（内存单例）。"""

    def __init__(self) -> None:
        self._accounts: dict[str, AccountOrchestratorState] = {}

    def get_or_create(
        self,
        account_id: str,
        symbol: str,
        circuit_config: CircuitBreakerConfig | None = None,
    ) -> AccountOrchestratorState:
        if account_id not in self._accounts:
            breaker = CircuitBreaker(
                config=circuit_config or CircuitBreakerConfig()
            )
            self._accounts[account_id] = AccountOrchestratorState(
                account_id=account_id,
                symbol=symbol,
                circuit_breaker=breaker,
            )
        return self._accounts[account_id]

    def get(self, account_id: str) -> AccountOrchestratorState | None:
        return self._accounts.get(account_id)

    def all_account_ids(self) -> list[str]:
        return list(self._accounts.keys())


# 应用级单例
_global_state = OrchestratorState()


def get_orchestrator_state() -> OrchestratorState:
    return _global_state
