import os
import sys
from datetime import datetime, timedelta

# Set test database BEFORE app import
os.environ["DATABASE_URL"] = "sqlite:///./test_telecom.db"

from fastapi.testclient import TestClient  # noqa: E402

# Add backend root to PYTHONPATH
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_rate_voice_call():
    payload = {
        "msisdn": "911234567890",
        "call_type": "voice",
        "duration_secs": 125,
    }
    r = client.post("/cdrs/ingest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["cdr"]["msisdn"] == payload["msisdn"]
    # 125 secs -> 3 minutes at 0.5 per min on Basic plan = 1.5
    assert abs(data["rated"]["charge_amount"] - 1.5) < 1e-6


def test_usage_summary():
    msisdn = "911234567890"
    now = datetime.utcnow()
    params = {
        "from_ts": (now - timedelta(days=1)).isoformat(),
        "to_ts": (now + timedelta(days=1)).isoformat(),
    }
    r = client.get(f"/subscribers/{msisdn}/usage", params=params)
    assert r.status_code == 200
    data = r.json()
    assert data["msisdn"] == msisdn
    assert data["total_charge"] >= 1.5
