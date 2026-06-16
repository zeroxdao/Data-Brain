"""调度循环：定时触发"环境识别 → 决策 → 熔断检查 → 桥接下发"。

每个账号独立运行一个异步循环（asyncio.Task），互不阻塞。
调度步骤（每个 tick）：
  1. 读取账户信息（余额/净值）→ 更新熔断器。
  2. 若熔断触发 → 关闭全部 EA，停止调度。
  3. 读取最近 N 根 K 线 → 计算当前环境快照。
  4. 读取历史交易 → 分析 EA 表现（增量缓存，不每次全量拉取）。
  5. 决策引擎 → 输出每个 EA 的启停 / 权重。
  6. 与上一次决策对比，仅对"变化了"的 EA 下发桥接指令（减少噪音）。
  7. 记录决策日志。
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.analysis import EAPerformanceAnalyzer
from app.bridge.base import TradingBridge
from app.orchestrator.circuit_breaker import CircuitStatus
from app.orchestrator.decision import DecisionEngine, EADecision
from app.orchestrator.state import AccountOrchestratorState, OrchestratorState, SchedulerStatus
from app.regime import RegimeClassifier
from app.schemas import RegimeSnapshot

logger = logging.getLogger(__name__)

_CANDLE_LOOKBACK_DAYS = 30  # 用于计算当前环境的 K 线窗口
_ANALYSIS_LOOKBACK_DAYS = 60  # 用于历史表现分析的回顾窗口


class OrchestratorScheduler:
    def __init__(
        self,
        bridge: TradingBridge,
        state: OrchestratorState,
        interval_seconds: int = 60,  # 每隔多少秒执行一次调度
        decision_engine: Optional[DecisionEngine] = None,
        classifier: Optional[RegimeClassifier] = None,
    ) -> None:
        self.bridge = bridge
        self.state = state
        self.interval = interval_seconds
        self.engine = decision_engine or DecisionEngine()
        self.classifier = classifier or RegimeClassifier()
        self._tasks: dict[str, asyncio.Task] = {}

    def start(
        self,
        account_id: str,
        symbol: str = "XAUUSD",
        timeframe: str = "H1",
    ) -> AccountOrchestratorState:
        acc_state = self.state.get_or_create(account_id, symbol)
        if acc_state.scheduler_status == SchedulerStatus.RUNNING:
            return acc_state  # 已在运行，幂等

        acc_state.scheduler_status = SchedulerStatus.RUNNING
        task = asyncio.create_task(
            self._run_loop(account_id, symbol, timeframe),
            name=f"orch-{account_id}",
        )
        self._tasks[account_id] = task
        logger.info("调度大脑已启动: account=%s symbol=%s", account_id, symbol)
        return acc_state

    def stop(self, account_id: str) -> None:
        acc_state = self.state.get(account_id)
        if acc_state:
            acc_state.scheduler_status = SchedulerStatus.STOPPED
        task = self._tasks.pop(account_id, None)
        if task and not task.done():
            task.cancel()
        logger.info("调度大脑已停止: account=%s", account_id)

    async def _run_loop(self, account_id: str, symbol: str, timeframe: str) -> None:
        acc_state = self.state.get(account_id)
        if not acc_state:
            return
        while acc_state.scheduler_status == SchedulerStatus.RUNNING:
            try:
                await self._tick(acc_state, symbol, timeframe)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("调度 tick 出错 [%s]: %s", account_id, exc, exc_info=True)
            await asyncio.sleep(self.interval)

    async def _tick(
        self, acc_state: AccountOrchestratorState, symbol: str, timeframe: str
    ) -> None:
        account_id = acc_state.account_id

        # ── 步骤1: 读账户信息 → 熔断检查 ──────────────────────────────────
        account_info = await self.bridge.get_account(account_id)
        circuit_status = acc_state.circuit_breaker.update(
            equity=account_info.equity,
            balance=account_info.balance,
        )

        if circuit_status != CircuitStatus.ACTIVE:
            logger.warning(
                "熔断触发 [%s]: %s — %s",
                account_id,
                circuit_status.value,
                acc_state.circuit_breaker.trip_reason,
            )
            await self._disable_all_eas(acc_state)
            acc_state.scheduler_status = SchedulerStatus.STOPPED
            return

        # ── 步骤2: 计算当前市场环境 ────────────────────────────────────────
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        candle_start = now - timedelta(days=_CANDLE_LOOKBACK_DAYS)
        candles = await self.bridge.get_candles(symbol, timeframe, candle_start, now)
        snapshots = self.classifier.classify(candles, symbol)
        if not snapshots:
            logger.warning("K 线不足，跳过本次调度 [%s]", account_id)
            return
        current_regime: RegimeSnapshot = snapshots[-1]

        # ── 步骤3: 历史 EA 表现分析 ────────────────────────────────────────
        analysis_start = now - timedelta(days=_ANALYSIS_LOOKBACK_DAYS)
        analyzer = EAPerformanceAnalyzer(self.bridge, self.classifier)
        analysis = await analyzer.analyze(
            account_id, symbol, analysis_start, now, timeframe=timeframe
        )

        # ── 步骤4: 决策引擎 ────────────────────────────────────────────────
        new_decisions = self.engine.decide(analysis.reports, current_regime)

        # ── 步骤5: 仅对"变化了"的 EA 下发指令（差异执行） ─────────────────
        prev_map: dict[str, bool] = {
            d.ea_name: d.enabled for d in acc_state.active_decisions
        }
        for decision in new_decisions:
            prev_enabled = prev_map.get(decision.ea_name)
            if prev_enabled is None or prev_enabled != decision.enabled:
                try:
                    await self.bridge.set_ea_enabled(
                        account_id, decision.ea_name, decision.enabled
                    )
                    logger.info(
                        "EA指令下发 [%s] %s → enabled=%s | %s",
                        account_id,
                        decision.ea_name,
                        decision.enabled,
                        decision.reason,
                    )
                except NotImplementedError:
                    # MetaApi 骨架尚未实现 set_ea_enabled，跳过但继续记录决策
                    logger.debug("set_ea_enabled 未实现，仅记录决策")
                except Exception as exc:
                    logger.error("下发 EA 指令失败 [%s] %s: %s", account_id, decision.ea_name, exc)

        # ── 步骤6: 记录决策 ────────────────────────────────────────────────
        acc_state.record_decision(new_decisions, current_regime)
        logger.info(
            "调度完成 [%s] 环境=%s 激活EA=%s",
            account_id,
            [l.value for l in current_regime.labels],
            [d.ea_name for d in new_decisions if d.enabled],
        )

    async def _disable_all_eas(self, acc_state: AccountOrchestratorState) -> None:
        for d in acc_state.active_decisions:
            if d.enabled:
                try:
                    await self.bridge.set_ea_enabled(acc_state.account_id, d.ea_name, False)
                except Exception:
                    pass
