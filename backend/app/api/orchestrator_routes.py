"""调度大脑 API 路由。

POST /api/orchestrator/{account_id}/start   — 启动账号的自动调度
POST /api/orchestrator/{account_id}/stop    — 停止调度
POST /api/orchestrator/{account_id}/reset   — 重置熔断（人工确认后用）
GET  /api/orchestrator/{account_id}/status  — 查看当前状态 + 激活 EA + 环境
GET  /api/orchestrator/{account_id}/log     — 历史决策日志
GET  /api/orchestrator/accounts             — 列出所有已注册账号
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from app.bridge import TradingBridge, get_bridge
from app.orchestrator.circuit_breaker import CircuitBreakerConfig
from app.orchestrator.scheduler import OrchestratorScheduler
from app.orchestrator.state import (
    OrchestratorState,
    SchedulerStatus,
    get_orchestrator_state,
)

orch_router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

# ── 应用级调度器单例（与 FastAPI lifespan 配合）────────────────────────────────
_scheduler: OrchestratorScheduler | None = None


def get_scheduler(
    bridge: TradingBridge = Depends(get_bridge),
    state: OrchestratorState = Depends(get_orchestrator_state),
) -> OrchestratorScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = OrchestratorScheduler(bridge=bridge, state=state, interval_seconds=60)
    return _scheduler


# ── 请求 / 响应 Schema ─────────────────────────────────────────────────────────


class StartRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "H1"
    max_drawdown_pct: float = 10.0
    max_daily_loss_pct: float = 3.0
    max_active_eas: int = 3
    interval_seconds: int = 60


# ── 路由 ───────────────────────────────────────────────────────────────────────


@orch_router.post("/{account_id}/start")
async def start_orchestrator(
    account_id: str,
    req: StartRequest = Body(default=StartRequest()),
    bridge: TradingBridge = Depends(get_bridge),
    state: OrchestratorState = Depends(get_orchestrator_state),
) -> dict:
    global _scheduler
    from app.orchestrator.decision import DecisionEngine
    from app.regime import RegimeClassifier

    _scheduler = OrchestratorScheduler(
        bridge=bridge,
        state=state,
        interval_seconds=req.interval_seconds,
        decision_engine=DecisionEngine(max_active_eas=req.max_active_eas),
        classifier=RegimeClassifier(),
    )
    circuit_cfg = CircuitBreakerConfig(
        max_drawdown_pct=req.max_drawdown_pct,
        max_daily_loss_pct=req.max_daily_loss_pct,
    )
    acc_state = state.get_or_create(account_id, req.symbol, circuit_cfg)
    _scheduler.start(account_id, symbol=req.symbol, timeframe=req.timeframe)
    return {
        "message": f"调度大脑已启动（account={account_id}）",
        "config": req.model_dump(),
    }


@orch_router.post("/{account_id}/stop")
async def stop_orchestrator(
    account_id: str,
    scheduler: OrchestratorScheduler = Depends(get_scheduler),
) -> dict:
    scheduler.stop(account_id)
    return {"message": f"调度大脑已停止（account={account_id}）"}


@orch_router.post("/{account_id}/reset")
async def reset_circuit(
    account_id: str,
    state: OrchestratorState = Depends(get_orchestrator_state),
) -> dict:
    acc_state = state.get(account_id)
    if not acc_state:
        raise HTTPException(404, f"账号 {account_id} 未注册")
    if not acc_state.circuit_breaker.is_tripped:
        return {"message": "熔断未触发，无需重置"}
    acc_state.circuit_breaker.reset()
    return {"message": "熔断已重置，可重新启动调度"}


@orch_router.get("/accounts")
async def list_accounts(
    state: OrchestratorState = Depends(get_orchestrator_state),
) -> dict:
    return {"accounts": state.all_account_ids()}


@orch_router.get("/{account_id}/status")
async def get_status(
    account_id: str,
    state: OrchestratorState = Depends(get_orchestrator_state),
) -> dict:
    acc_state = state.get(account_id)
    if not acc_state:
        raise HTTPException(404, f"账号 {account_id} 未注册，请先 start")
    return acc_state.to_status_dict()


@orch_router.get("/{account_id}/log")
async def get_decision_log(
    account_id: str,
    limit: int = Query(20, ge=1, le=50),
    state: OrchestratorState = Depends(get_orchestrator_state),
) -> dict:
    acc_state = state.get(account_id)
    if not acc_state:
        raise HTTPException(404, f"账号 {account_id} 未注册")
    entries = acc_state.decision_log[-limit:]
    return {
        "account_id": account_id,
        "entries": [
            {
                "timestamp": e.timestamp.isoformat(),
                "regime_labels": e.regime_labels,
                "circuit_status": e.circuit_status.value,
                "decisions": [
                    {
                        "ea_name": d.ea_name,
                        "enabled": d.enabled,
                        "weight": d.weight,
                        "reason": d.reason,
                    }
                    for d in e.decisions
                ],
            }
            for e in entries
        ],
    }
