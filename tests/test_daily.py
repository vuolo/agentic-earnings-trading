from datetime import date, timedelta
from pathlib import Path

import pytest

from engine.store import Store
from orchestrator.daily import analyst_due


TODAY = date(2026, 7, 15)


def test_bmo_due_only_day_before():
    assert analyst_due("2026-07-16", "bmo", TODAY)
    assert not analyst_due("2026-07-15", "bmo", TODAY)
    assert not analyst_due("2026-07-17", "bmo", TODAY)


def test_amc_due_day_before_and_report_day():
    assert analyst_due("2026-07-15", "amc", TODAY)
    assert analyst_due("2026-07-16", "amc", TODAY)
    assert not analyst_due("2026-07-17", "amc", TODAY)
    assert not analyst_due("2026-07-14", "amc", TODAY)


def test_unknown_treated_like_bmo():
    assert analyst_due("2026-07-16", "unknown", TODAY)
    assert not analyst_due("2026-07-15", "unknown", TODAY)


@pytest.fixture()
def store(tmp_path: Path):
    s = Store(tmp_path / "t.sqlite3")
    yield s
    s.close()


def _open_position(store, symbol, report_date):
    event_id = store.upsert_event(symbol, report_date)
    return store.insert_decision(
        symbol=symbol, action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=500.0, entry_price=100.0, event_id=event_id,
    )


def test_due_closes_only_past_events(store):
    today = date(2026, 7, 15)
    _open_position(store, "NVDA", "2026-07-14")   # passed → due
    _open_position(store, "AMD", "2026-07-15")    # today → not yet
    _open_position(store, "MU", "2026-07-16")     # future → no
    due = store.due_closes(today.isoformat())
    assert [r["symbol"] for r in due] == ["NVDA"]


def test_due_closes_ignores_closed_and_unlinked(store):
    _open_position(store, "NVDA", "2026-07-14")
    store.close_position("NVDA", 105.0)
    store.insert_decision(  # open but no event link → manual territory
        symbol="AMD", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=500.0, entry_price=100.0,
    )
    assert store.due_closes("2026-07-15") == []


def test_decisions_for_event(store):
    event_id = store.upsert_event("TSM", "2026-07-16")
    assert store.decisions_for_event(event_id) == []
    store.insert_decision(
        symbol="TSM", action="pass", policy_version="t",
        risk_verdict="n/a (pass)", status="pass", event_id=event_id,
    )
    assert len(store.decisions_for_event(event_id)) == 1
