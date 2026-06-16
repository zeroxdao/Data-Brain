"""离线 Mock 桥接：用确定性合成数据，让平台无需任何凭证即可运行与测试。

合成数据特意构造出"环境相关"的盈亏模式：
- TrendRider（趋势跟随）在趋势段更赚钱，在震荡段亏钱；
- RangeScalper（震荡剥头皮）相反。
这样功能2 的分析能产出有意义的洞察，便于演示与测试。
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

from app.bridge.base import TradingBridge
from app.schemas import AccountInfo, Candle, Deal, DealType

_TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


class MockBridge(TradingBridge):
    """确定性合成数据桥接。"""

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed

    async def get_account(self, account_id: str) -> AccountInfo:
        return AccountInfo(
            account_id=account_id,
            broker="MockBroker",
            currency="USD",
            balance=10_000.0,
            equity=10_250.0,
            leverage=100,
        )

    def _generate_series(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> list[Candle]:
        step = _TIMEFRAME_MINUTES.get(timeframe.upper(), 60)
        rng = random.Random(f"{self._seed}-{symbol}-{timeframe}")
        candles: list[Candle] = []
        price = 2000.0 if symbol.upper().startswith("XAU") else 1.10
        t = start
        i = 0
        while t <= end:
            # 交替的趋势段与震荡段，制造可识别的市场环境
            phase = (i // 50) % 2  # 每 50 根切换一次
            drift = (0.0008 if (i // 50) % 4 < 2 else -0.0008) if phase == 0 else 0.0
            vol = 0.0015 if phase == 0 else 0.0006
            ret = drift + rng.gauss(0, vol)
            open_p = price
            close_p = max(0.0001, price * (1 + ret))
            high_p = max(open_p, close_p) * (1 + abs(rng.gauss(0, vol / 2)))
            low_p = min(open_p, close_p) * (1 - abs(rng.gauss(0, vol / 2)))
            candles.append(
                Candle(
                    time=t,
                    open=round(open_p, 5),
                    high=round(high_p, 5),
                    low=round(low_p, 5),
                    close=round(close_p, 5),
                    volume=rng.randint(100, 1000),
                )
            )
            price = close_p
            t += timedelta(minutes=step)
            i += 1
        return candles

    async def get_candles(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> list[Candle]:
        return self._generate_series(symbol, timeframe, start, end)

    async def get_deals(
        self,
        account_id: str,
        start: datetime,
        end: datetime,
        symbol: str | None = None,
    ) -> list[Deal]:
        sym = symbol or "XAUUSD"
        candles = self._generate_series(sym, "H1", start, end)
        if len(candles) < 10:
            return []
        rng = random.Random(f"{self._seed}-deals-{account_id}-{sym}")
        deals: list[Deal] = []
        eas = ["TrendRider", "RangeScalper"]
        deal_no = 0
        # 每隔几根 K 线产生一笔交易，盈亏与"持仓窗口内的趋势强度"相关
        window = 6
        for idx in range(0, len(candles) - window, 4):
            c_open = candles[idx]
            c_close = candles[idx + window]
            move = (c_close.close - c_open.open) / c_open.open
            # 趋势强度：窗口内方向一致性
            ups = sum(
                1
                for j in range(idx, idx + window)
                if candles[j + 1].close > candles[j].close
            )
            trendiness = abs(ups / window - 0.5) * 2  # 0=纯震荡, 1=单边
            ea = eas[deal_no % len(eas)]
            if ea == "TrendRider":
                # 趋势越强越赚；震荡时亏
                base = move * 10000 * trendiness - 5 * (1 - trendiness)
            else:  # RangeScalper
                # 震荡时小赚；趋势强时被打损
                base = 8 * (1 - trendiness) - move * 10000 * trendiness * 0.5
            profit = round(base + rng.gauss(0, 3), 2)
            d_type = DealType.BUY if move >= 0 else DealType.SELL
            deals.append(
                Deal(
                    deal_id=f"D{deal_no}",
                    symbol=sym,
                    ea_name=ea,
                    type=d_type,
                    volume=0.1,
                    open_time=c_open.time,
                    close_time=c_close.time,
                    open_price=c_open.open,
                    close_price=c_close.close,
                    profit=profit,
                    commission=-0.7,
                    swap=round(rng.uniform(-0.5, 0.1), 2),
                )
            )
            deal_no += 1
        return deals

    async def set_ea_enabled(self, account_id: str, ea_name: str, enabled: bool) -> bool:
        # Mock：仅记录意图，真实实现会下发指令到桥接 EA
        return True
