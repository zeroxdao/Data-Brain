"""HTTP 路由。

阶段0：账户与行情读取（验证桥接打通）。
阶段1：交易历史抓取 + 市场环境标签 + EA 表现分析（功能2 分析版）。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.analysis import EAPerformanceAnalyzer
from app.bridge import TradingBridge, get_bridge
from app.config import Settings, get_settings
from app.regime import RegimeClassifier
from app.schemas import AccountInfo, AnalysisResponse, Candle, RegimeSnapshot

router = APIRouter()


def _default_range(days: int) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc).replace(tzinfo=None)
    return end - timedelta(days=days), end


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "bridge": settings.bridge_provider,
    }


@router.get("/accounts/{account_id}", response_model=AccountInfo)
async def get_account(
    account_id: str, bridge: TradingBridge = Depends(get_bridge)
) -> AccountInfo:
    return await bridge.get_account(account_id)


@router.get("/candles", response_model=list[Candle])
async def get_candles(
    symbol: str = Query("XAUUSD"),
    timeframe: str = Query("H1"),
    days: int = Query(30, ge=1, le=365),
    bridge: TradingBridge = Depends(get_bridge),
) -> list[Candle]:
    start, end = _default_range(days)
    return await bridge.get_candles(symbol, timeframe, start, end)


@router.get("/regime", response_model=list[RegimeSnapshot])
async def get_regime(
    symbol: str = Query("XAUUSD"),
    timeframe: str = Query("H1"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=2000),
    bridge: TradingBridge = Depends(get_bridge),
) -> list[RegimeSnapshot]:
    start, end = _default_range(days)
    candles = await bridge.get_candles(symbol, timeframe, start, end)
    snapshots = RegimeClassifier().classify(candles, symbol)
    return snapshots[-limit:]


@router.get("/analysis/{account_id}", response_model=AnalysisResponse)
async def analyze_account(
    account_id: str,
    symbol: str = Query("XAUUSD"),
    timeframe: str = Query("H1"),
    days: int = Query(30, ge=1, le=365),
    bridge: TradingBridge = Depends(get_bridge),
) -> AnalysisResponse:
    start, end = _default_range(days)
    analyzer = EAPerformanceAnalyzer(bridge)
    return await analyzer.analyze(account_id, symbol, start, end, timeframe=timeframe)
