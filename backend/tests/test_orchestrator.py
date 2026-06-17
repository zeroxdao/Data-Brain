"""调度大脑测试。

覆盖：决策引擎、熔断器、状态管理、调度 tick、API 路由。
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.bridge.mock import MockBridge
from app.main import app
from app.orchestrator.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitStatus
from app.orchestrator.decision import DecisionEngine
from app.orchestrator.scheduler import OrchestratorScheduler
from app.orchestrator.state import OrchestratorState
from app.analysis import EAPerformanceAnalyzer
from app.regime import RegimeClassifier

client = TestClient(app)

# ── 辅助 ──────────────────────────────────────────────────────────────────────


def _make_reports():
    """用 mock 数据生成 EA 报告（同步包装）。"""
    bridge = MockBridge()
    analyzer = EAPerformanceAnalyzer(bridge)
    end = datetime(2024, 3, 1)
    start = end - timedelta(days=40)
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(analyzer.analyze("acc-1", "XAUUSD", start, end))
    finally:
        loop.close()


# ── 决策引擎 ──────────────────────────────────────────────────────────────────


def test_decision_produces_output():
    result = _make_reports()
    engine = DecisionEngine(max_active_eas=2)
    from app.regime import RegimeClassifier
    bridge = MockBridge()
    end = datetime(2024, 3, 1)
    start = end - timedelta(days=10)
    loop = asyncio.new_event_loop()
    try:
        candles = loop.run_until_complete(bridge.get_candles("XAUUSD", "H1", start, end))
    finally:
        loop.close()
    clf = RegimeClassifier()
    snaps = clf.classify(candles, "XAUUSD")
    assert snaps
    decisions = engine.decide(result.reports, snaps[-1])
    assert decisions
    for d in decisions:
        assert d.reason
        assert 0.0 <= d.weight <= 1.0


def test_max_active_eas_respected():
    result = _make_reports()
    engine = DecisionEngine(max_active_eas=1)
    bridge = MockBridge()
    end = datetime(2024, 3, 1)
    start = end - timedelta(days=10)
    loop = asyncio.new_event_loop()
    try:
        candles = loop.run_until_complete(bridge.get_candles("XAUUSD", "H1", start, end))
    finally:
        loop.close()
    snaps = RegimeClassifier().classify(candles, "XAUUSD")
    decisions = engine.decide(result.reports, snaps[-1])
    enabled = [d for d in decisions if d.enabled]
    assert len(enabled) <= 1


def test_enabled_weights_sum_to_one():
    result = _make_reports()
    engine = DecisionEngine(max_active_eas=3)
    bridge = MockBridge()
    end = datetime(2024, 3, 1)
    start = end - timedelta(days=10)
    loop = asyncio.new_event_loop()
    try:
        candles = loop.run_until_complete(bridge.get_candles("XAUUSD", "H1", start, end))
    finally:
        loop.close()
    snaps = RegimeClassifier().classify(candles, "XAUUSD")
    decisions = engine.decide(result.reports, snaps[-1])
    total_w = sum(d.weight for d in decisions if d.enabled)
    if total_w > 0:
        assert abs(total_w - 1.0) < 1e-4


# ── 熔断器 ────────────────────────────────────────────────────────────────────


def test_circuit_ok_below_threshold():
    cb = CircuitBreaker(CircuitBreakerConfig(max_drawdown_pct=10, max_daily_loss_pct=3))
    status = cb.update(equity=10000, balance=10000)
    assert status == CircuitStatus.ACTIVE


def test_drawdown_trips_circuit():
    cb = CircuitBreaker(CircuitBreakerConfig(max_drawdown_pct=10))
    cb.update(equity=10000, balance=10000)   # 建立高点
    status = cb.update(equity=8900, balance=8900)   # 回撤 11%
    assert status == CircuitStatus.TRIPPED_DRAWDOWN
    assert "回撤" in cb.trip_reason


def test_daily_loss_trips_circuit():
    cb = CircuitBreaker(CircuitBreakerConfig(max_daily_loss_pct=3))
    cb.update(equity=10000, balance=10000)
    status = cb.update(equity=9650, balance=9650)   # 日亏 3.5%
    assert status == CircuitStatus.TRIPPED_DAILY_LOSS


def test_circuit_reset():
    cb = CircuitBreaker(CircuitBreakerConfig(max_drawdown_pct=10))
    cb.update(equity=10000, balance=10000)
    cb.update(equity=8000, balance=8000)
    assert cb.is_tripped
    cb.reset()
    assert not cb.is_tripped
    assert cb.status == CircuitStatus.ACTIVE


# ── 调度器 tick ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scheduler_tick_records_decision():
    bridge = MockBridge()
    state = OrchestratorState()
    scheduler = OrchestratorScheduler(bridge=bridge, state=state, interval_seconds=9999)
    end = datetime(2024, 3, 1)
    start = end - timedelta(days=5)

    acc_state = state.get_or_create("test-acc", "XAUUSD")
    # 直接调用一次 tick（不等调度循环）
    await scheduler._tick(acc_state, "XAUUSD", "H1")

    assert acc_state.current_regime is not None
    assert acc_state.active_decisions
    assert acc_state.decision_log


# ── API 路由 ──────────────────────────────────────────────────────────────────


def test_orchestrator_start_stop():
    r = client.post("/api/orchestrator/acc-x/start", json={"interval_seconds": 9999})
    assert r.status_code == 200
    assert "启动" in r.json()["message"]

    r = client.post("/api/orchestrator/acc-x/stop")
    assert r.status_code == 200
    assert "停止" in r.json()["message"]


def test_orchestrator_status_not_found():
    r = client.get("/api/orchestrator/nonexistent/status")
    assert r.status_code == 404


def test_orchestrator_accounts_list():
    client.post("/api/orchestrator/acc-list-test/start", json={"interval_seconds": 9999})
    client.post("/api/orchestrator/acc-list-test/stop")
    r = client.get("/api/orchestrator/accounts")
    assert "acc-list-test" in r.json()["accounts"]


def test_orchestrator_reset_no_trip():
    client.post("/api/orchestrator/acc-reset/start", json={"interval_seconds": 9999})
    client.post("/api/orchestrator/acc-reset/stop")
    r = client.post("/api/orchestrator/acc-reset/reset")
    assert r.status_code == 200
    assert "无需重置" in r.json()["message"]
