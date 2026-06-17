"""把 K 线序列转成"市场环境"标签。

特征（全部可量化、可解释）：
- ADX：趋势强度。ADX > 阈值 → 趋势市；否则 → 震荡市。
- +DI / -DI：趋势方向，区分 trend_up / trend_down。
- ATR / 已实现波动率：波动水平，按分位划分高/低波动。
- 交易时段：根据 UTC 小时划分 亚/欧/美/盘后。

这一层是功能2 的核心：给每个时刻打上可学习的环境标签。
后续可平滑升级到 HMM / 聚类，而接口保持不变。
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from app.config import Settings, get_settings
from app.schemas import Candle, RegimeLabel, RegimeSnapshot, TradingSession


def _session_for_hour(hour_utc: int) -> TradingSession:
    # 粗略时段划分（UTC）。亚盘 0-7, 欧盘 7-13, 美盘 13-21, 其余盘后。
    if 0 <= hour_utc < 7:
        return TradingSession.ASIA
    if 7 <= hour_utc < 13:
        return TradingSession.EUROPE
    if 13 <= hour_utc < 21:
        return TradingSession.US
    return TradingSession.OFF_HOURS


class RegimeClassifier:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _to_frame(self, candles: list[Candle]) -> pd.DataFrame:
        df = pd.DataFrame([c.model_dump() for c in candles])
        df = df.sort_values("time").reset_index(drop=True)
        return df

    def compute_indicators(self, candles: list[Candle]) -> pd.DataFrame:
        """计算 ADX / +DI / -DI / ATR / 已实现波动率。"""
        df = self._to_frame(candles)
        n = self.settings.adx_period
        atr_n = self.settings.atr_period

        high, low, close = df["high"], df["low"], df["close"]
        prev_close = close.shift(1)

        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)

        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        # Wilder 平滑（用 EMA 近似）
        atr = tr.ewm(alpha=1 / atr_n, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
            alpha=1 / n, adjust=False
        ).mean() / atr.replace(0, np.nan)
        minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
            alpha=1 / n, adjust=False
        ).mean() / atr.replace(0, np.nan)

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1 / n, adjust=False).mean()

        # 已实现波动率：对数收益的滚动标准差（年化无关，仅作相对比较）
        log_ret = np.log(close / prev_close)
        realized_vol = log_ret.rolling(atr_n, min_periods=2).std()

        df["atr"] = atr.fillna(0.0)
        df["adx"] = adx.fillna(0.0)
        df["plus_di"] = plus_di.fillna(0.0)
        df["minus_di"] = minus_di.fillna(0.0)
        df["realized_vol"] = realized_vol.fillna(0.0)
        return df

    def classify(self, candles: list[Candle], symbol: str) -> list[RegimeSnapshot]:
        """对整段 K 线逐根打环境标签。"""
        if len(candles) < self.settings.adx_period + 2:
            return []
        df = self.compute_indicators(candles)

        # 波动分位阈值（基于本段数据，相对划分高/低波动）
        vol_series = df["realized_vol"].replace(0, np.nan).dropna()
        if len(vol_series) == 0:
            hi_thr = lo_thr = 0.0
        else:
            hi_thr = float(vol_series.quantile(self.settings.high_vol_quantile))
            lo_thr = float(vol_series.quantile(self.settings.low_vol_quantile))

        adx_thr = self.settings.adx_trend_threshold
        snapshots: list[RegimeSnapshot] = []
        for _, row in df.iterrows():
            t: datetime = row["time"]
            adx = float(row["adx"])
            if adx >= adx_thr:
                trend = (
                    RegimeLabel.TREND_UP
                    if row["plus_di"] >= row["minus_di"]
                    else RegimeLabel.TREND_DOWN
                )
            else:
                trend = RegimeLabel.RANGE

            rv = float(row["realized_vol"])
            if rv >= hi_thr and hi_thr > 0:
                vol = RegimeLabel.HIGH_VOL
            elif rv <= lo_thr:
                vol = RegimeLabel.LOW_VOL
            else:
                vol = RegimeLabel.LOW_VOL if rv < (hi_thr + lo_thr) / 2 else RegimeLabel.HIGH_VOL

            session = _session_for_hour(t.hour)
            snapshots.append(
                RegimeSnapshot(
                    time=t,
                    symbol=symbol,
                    adx=round(adx, 2),
                    atr=round(float(row["atr"]), 6),
                    realized_vol=round(rv, 6),
                    session=session,
                    trend_label=trend,
                    vol_label=vol,
                    labels=[trend, vol],
                )
            )
        return snapshots

    @staticmethod
    def label_at(snapshots: list[RegimeSnapshot], when: datetime) -> RegimeSnapshot | None:
        """找到不晚于给定时间的最近一个环境快照（用于给某笔交易归因）。"""
        chosen: RegimeSnapshot | None = None
        for s in snapshots:
            if s.time <= when:
                chosen = s
            else:
                break
        return chosen
