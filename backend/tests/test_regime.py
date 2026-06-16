from datetime import datetime, timedelta

from app.regime import RegimeClassifier
from app.schemas import Candle, RegimeLabel


def _trending_candles(n: int = 100) -> list[Candle]:
    base = datetime(2024, 1, 1)
    candles = []
    price = 100.0
    for i in range(n):
        price *= 1.01  # 稳定上涨 → 应识别为趋势
        candles.append(
            Candle(
                time=base + timedelta(hours=i),
                open=price / 1.01,
                high=price * 1.002,
                low=price / 1.01 * 0.999,
                close=price,
                volume=100,
            )
        )
    return candles


def test_indicators_computed():
    clf = RegimeClassifier()
    df = clf.compute_indicators(_trending_candles())
    assert {"adx", "atr", "plus_di", "minus_di", "realized_vol"}.issubset(df.columns)
    assert df["adx"].iloc[-1] >= 0


def test_strong_uptrend_classified_as_trend_up():
    clf = RegimeClassifier()
    snaps = clf.classify(_trending_candles(), "TEST")
    assert snaps
    # 末段应被识别为上涨趋势
    assert snaps[-1].trend_label == RegimeLabel.TREND_UP
    assert snaps[-1].adx >= 25


def test_label_at_returns_latest_before_time():
    clf = RegimeClassifier()
    snaps = clf.classify(_trending_candles(), "TEST")
    target = snaps[10].time
    found = RegimeClassifier.label_at(snaps, target)
    assert found is not None and found.time == target
