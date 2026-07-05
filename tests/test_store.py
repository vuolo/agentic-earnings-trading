from datetime import date, timedelta
from pathlib import Path

import pytest

from engine.store import Store


@pytest.fixture()
def store(tmp_path: Path):
    s = Store(tmp_path / "t.sqlite3")
    yield s
    s.close()


def test_event_upsert_is_idempotent(store):
    d = (date.today() + timedelta(days=3)).isoformat()
    id1 = store.upsert_event("nvda", d, "unknown")
    id2 = store.upsert_event("NVDA", d, "amc", raw='{"src": "fresher"}')
    assert id1 == id2
    row = store.get_event("NVDA", d)
    assert row["timing"] == "amc"
    assert row["raw"] == '{"src": "fresher"}'


def test_upsert_rejects_bad_date(store):
    with pytest.raises(ValueError):
        store.upsert_event("NVDA", "next tuesday")


def test_upcoming_events_window(store):
    today = date.today()
    store.upsert_event("NVDA", (today + timedelta(days=2)).isoformat())
    store.upsert_event("AMD", (today + timedelta(days=30)).isoformat())
    store.upsert_event("MU", (today - timedelta(days=2)).isoformat())
    symbols = [e["symbol"] for e in store.upcoming_events(days=14)]
    assert symbols == ["NVDA"]


def test_long_close_pnl(store):
    store.insert_decision(
        symbol="NVDA", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=1_000.0, entry_price=100.0,
    )
    result = store.close_position("NVDA", 110.0, "T+1")
    assert result["pnl_usd"] == pytest.approx(100.0)
    assert result["move_pct"] == pytest.approx(10.0)
    assert store.open_position_for("NVDA") is None


def test_bearish_close_pnl_inverse(store):
    store.insert_decision(
        symbol="AMD", action="bearish_option", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=1_000.0, entry_price=100.0,
    )
    result = store.close_position("AMD", 90.0)
    assert result["pnl_usd"] == pytest.approx(100.0)  # underlying fell, bearish gains
    assert result["move_pct"] == pytest.approx(-10.0)


def test_close_without_position_returns_none(store):
    assert store.close_position("NVDA", 100.0) is None


def test_today_new_exposure_counts_open_and_closed(store):
    store.insert_decision(
        symbol="NVDA", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=400.0, entry_price=100.0,
    )
    store.insert_decision(
        symbol="AMD", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=600.0, entry_price=100.0,
    )
    store.close_position("AMD", 105.0)
    # rejected and pass rows don't consume budget
    store.insert_decision(
        symbol="MU", action="long_equity", policy_version="t",
        risk_verdict="rejected: x", status="rejected", size_usd=999.0,
    )
    store.insert_decision(
        symbol="MU", action="pass", policy_version="t",
        risk_verdict="n/a (pass)", status="pass",
    )
    assert store.today_new_exposure() == pytest.approx(1_000.0)
