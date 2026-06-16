"""数据模型 (Pydantic schemas)。

这些是桥接层、环境引擎、分析层之间传递的统一数据结构。
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Candle(BaseModel):
    """单根 K 线 (OHLCV)。"""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class DealType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Deal(BaseModel):
    """一笔已平仓交易记录。

    简化模型：以"开仓-平仓"配对后的完整交易为单位，便于按盈亏归因。
    """

    deal_id: str
    symbol: str
    ea_name: str | None = None  # 由用户标注或从 magic/comment 推断
    type: DealType
    volume: float
    open_time: datetime
    close_time: datetime
    open_price: float
    close_price: float
    profit: float  # 含佣金/swap 的净盈亏
    commission: float = 0.0
    swap: float = 0.0


class AccountInfo(BaseModel):
    account_id: str
    broker: str | None = None
    currency: str = "USD"
    balance: float
    equity: float
    leverage: int = 100


class RegimeLabel(str, Enum):
    """市场环境标签。"""

    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    HIGH_VOL = "high_volatility"
    LOW_VOL = "low_volatility"


class TradingSession(str, Enum):
    ASIA = "asia"
    EUROPE = "europe"
    US = "us"
    OFF_HOURS = "off_hours"


class RegimeSnapshot(BaseModel):
    """某一时刻的市场环境快照（可量化特征 + 标签）。"""

    time: datetime
    symbol: str
    adx: float
    atr: float
    realized_vol: float
    session: TradingSession
    trend_label: RegimeLabel  # trend_up / trend_down / range
    vol_label: RegimeLabel  # high_volatility / low_volatility
    labels: list[RegimeLabel]


class EARegimePerformance(BaseModel):
    """某个 EA 在某个环境标签下的表现统计。"""

    ea_name: str
    regime: RegimeLabel
    trades: int
    win_rate: float
    total_profit: float
    avg_profit: float
    profit_factor: float


class EAReport(BaseModel):
    """单个 EA 的环境表现报告 + 调度建议。"""

    ea_name: str
    total_trades: int
    total_profit: float
    overall_win_rate: float
    by_regime: list[EARegimePerformance]
    best_regimes: list[RegimeLabel]
    worst_regimes: list[RegimeLabel]
    insight: str


class AnalysisResponse(BaseModel):
    account_id: str
    symbol: str
    analyzed_deals: int
    reports: list[EAReport]
