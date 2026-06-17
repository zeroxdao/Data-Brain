from datetime import datetime, timedelta

import pytest

from app.analysis import EAPerformanceAnalyzer
from app.bridge.mock import MockBridge


@pytest.mark.asyncio
async def test_analysis_produces_reports():
    bridge = MockBridge()
    analyzer = EAPerformanceAnalyzer(bridge)
    end = datetime(2024, 3, 1)
    start = end - timedelta(days=40)
    resp = await analyzer.analyze("acc-1", "XAUUSD", start, end)

    assert resp.analyzed_deals > 0
    assert resp.reports
    names = {r.ea_name for r in resp.reports}
    assert {"TrendRider", "RangeScalper"} & names

    for report in resp.reports:
        assert report.total_trades > 0
        assert report.by_regime  # 每个 EA 都应有按环境的拆分
        assert report.insight
