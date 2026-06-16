from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_account():
    r = client.get("/api/accounts/acc-1")
    assert r.status_code == 200
    assert r.json()["account_id"] == "acc-1"


def test_candles():
    r = client.get("/api/candles", params={"symbol": "XAUUSD", "days": 10})
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_regime():
    r = client.get("/api/regime", params={"symbol": "XAUUSD", "days": 30, "limit": 20})
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 20
    if data:
        assert "trend_label" in data[0]


def test_analysis():
    r = client.get("/api/analysis/acc-1", params={"symbol": "XAUUSD", "days": 40})
    assert r.status_code == 200
    body = r.json()
    assert body["analyzed_deals"] > 0
    assert body["reports"]
