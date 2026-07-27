from datetime import date, timedelta
from pathlib import Path

import pytest

from engine.store import Store
from orchestrator.daily import analyst_due, next_trading_day, resolve_phase


WED = date(2026, 7, 15)  # Wednesday
FRI = date(2026, 7, 17)  # Friday
SAT = date(2026, 7, 18)


def test_next_trading_day_skips_weekend():
    assert next_trading_day(FRI) == date(2026, 7, 20)  # Monday
    assert next_trading_day(WED) == date(2026, 7, 16)


def test_holidays_are_not_trading_days():
    from orchestrator.daily import is_trading_day
    assert not is_trading_day(date(2026, 9, 7))    # Labor Day
    assert not is_trading_day(date(2026, 7, 3))    # July 4th observed
    assert is_trading_day(date(2026, 11, 27))                       # half day trades...
    assert not is_trading_day(date(2026, 11, 27), full_session=True)  # ...but no entries
    # Friday 9/4 before Labor Day Monday: next trading day is Tuesday 9/8
    assert next_trading_day(date(2026, 9, 4)) == date(2026, 9, 8)
    # A bmo report on Tue 9/8 → entry due Friday 9/4
    assert analyst_due("2026-09-08", "bmo", date(2026, 9, 4))
    # Nothing due on the holiday itself
    assert not analyst_due("2026-09-08", "bmo", date(2026, 9, 7))


def test_bmo_due_prior_trading_day():
    assert analyst_due("2026-07-16", "bmo", WED)       # entry T-1 close
    assert not analyst_due("2026-07-15", "bmo", WED)   # report already imminent
    assert not analyst_due("2026-07-17", "bmo", WED)


def test_bmo_monday_due_on_friday():
    assert analyst_due("2026-07-20", "bmo", FRI)  # Monday bmo → enter Friday close


def test_amc_due_on_report_day_only():
    assert analyst_due("2026-07-15", "amc", WED)
    assert not analyst_due("2026-07-16", "amc", WED)
    assert not analyst_due("2026-07-14", "amc", WED)


def test_unknown_treated_like_bmo():
    assert analyst_due("2026-07-16", "unknown", WED)
    assert not analyst_due("2026-07-15", "unknown", WED)


def test_nothing_due_on_weekends():
    assert not analyst_due("2026-07-20", "bmo", SAT)
    assert not analyst_due("2026-07-18", "amc", SAT)


def test_resolve_phase():
    from datetime import datetime
    assert resolve_phase(datetime(2026, 7, 15, 9, 31)) == "morning"
    assert resolve_phase(datetime(2026, 7, 15, 15, 40)) == "afternoon"
    assert resolve_phase(datetime(2026, 7, 15, 16, 50)) == "evening"


def test_entry_window_gates_late_and_early_fires():
    # A wake-from-sleep replay at 12:30 or 16:10 must never run the entry
    # pipeline (9-day live outage root cause: post-close execution attempts).
    from datetime import time
    from orchestrator.daily import in_entry_window
    assert in_entry_window(time(15, 30))
    assert in_entry_window(time(15, 25))
    assert in_entry_window(time(15, 57, 59))
    assert not in_entry_window(time(15, 58))
    assert not in_entry_window(time(12, 30))
    assert not in_entry_window(time(16, 10))
    assert not in_entry_window(time(9, 24))


def test_entry_clock_ordering():
    # The dispatch deadlines must stay coherent: analysts stop starting
    # before the executor's last launch, which precedes the window close.
    from orchestrator import daily
    assert (daily.ENTRY_PIPELINE_OPEN < daily.BACKFILL_CUTOFF
            < daily.EXEC_NOT_BEFORE < daily.EXEC_VALVE
            <= daily.ANALYST_START_CUTOFF < daily.EXEC_LAST_LAUNCH
            < daily.ENTRY_PIPELINE_CLOSE)


@pytest.fixture()
def store(tmp_path: Path):
    s = Store(tmp_path / "t.sqlite3")
    yield s
    s.close()


def _open_position(store, symbol, report_date, timing="unknown", status="open_paper"):
    event_id = store.upsert_event(symbol, report_date, timing)
    return store.insert_decision(
        symbol=symbol, action="long_equity", policy_version="t",
        risk_verdict="approved", status=status,
        size_usd=100.0, entry_price=100.0, event_id=event_id,
    )


def test_due_closes_past_events_and_bmo_today(store):
    _open_position(store, "NVDA", "2026-07-14")                 # passed → due
    _open_position(store, "TSM", "2026-07-15", timing="bmo")    # bmo today → due
    _open_position(store, "AMD", "2026-07-15", timing="amc")    # amc today → not yet
    _open_position(store, "MU", "2026-07-16")                   # future → no
    due = store.due_closes("2026-07-15")
    assert sorted(r["symbol"] for r in due) == ["NVDA", "TSM"]


def test_due_amc_same_day_closes(store):
    _open_position(store, "AMD", "2026-07-15", timing="amc", status="open_live")
    _open_position(store, "NVDA", "2026-07-15", timing="bmo", status="open_live")
    due = store.due_amc_same_day_closes("2026-07-15")
    assert [r["symbol"] for r in due] == ["AMD"]


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


def test_day_trades_counter(store):
    did = _open_position(store, "AMD", "2026-07-01", timing="amc", status="open_live")
    assert store.day_trades_last_5d() == 0
    assert store.live_closes_today() == 0
    store.close_live(did, 105.0)  # same-day round trip (created + labeled now)
    assert store.day_trades_last_5d() == 1
    assert store.live_closes_today() == 1  # GFV guard input


def test_edge_rank_prefers_gap_history_over_volume(store):
    from orchestrator.daily import edge_rank
    import json as _json
    # Mover: small volume but big historical reactions.
    store.upsert_backtest("MOVR", "2026-01-15", "amc", pre_close=100.0, post_open=112.0)
    store.upsert_backtest("MOVR", "2026-04-16", "amc", pre_close=100.0, post_open=91.0)
    # Sleeper: huge volume, tiny historical gaps.
    store.upsert_backtest("SLPR", "2026-01-15", "bmo", pre_close=100.0, post_open=100.5)
    mover = {"symbol": "MOVR", "screen": _json.dumps({"avg_volume": 600_000})}
    sleeper = {"symbol": "SLPR", "screen": _json.dumps({"avg_volume": 90_000_000})}
    fresh = {"symbol": "NEWB", "screen": _json.dumps({"avg_volume": 2_000_000})}
    ranked = sorted([sleeper, mover, fresh], key=lambda e: edge_rank(store, e, False))
    assert [e["symbol"] for e in ranked] == ["MOVR", "SLPR", "NEWB"]
    # Core always outranks non-core, whatever the history says.
    assert edge_rank(store, {"symbol": "NVDA", "screen": None}, True) < \
        edge_rank(store, mover, False)


def test_backtest_upsert_and_summary(store):
    store.upsert_backtest("NVDA", "2026-02-25", "amc",
                          pre_close=100.0, post_open=104.0, post_close=106.0)
    store.upsert_backtest("NVDA", "2025-11-20", "amc",
                          pre_close=100.0, post_open=98.0, post_close=97.0)
    # idempotent + never downgrades timing / clobbers prices with nulls
    store.upsert_backtest("NVDA", "2026-02-25", "unknown")
    s = store.backtest_summary("NVDA")
    assert s["events"] == 2
    gap = s["gap_t1close_to_postopen"]
    assert gap["n"] == 2
    assert gap["mean_pct"] == pytest.approx(1.0)
    assert gap["up_rate"] == pytest.approx(0.5)
    assert gap["worst_pct"] == pytest.approx(-2.0)
    assert store.backtest_events("NVDA")[0]["timing"] == "amc"


def test_monday_backtest_refresh_is_scoped_to_decided_symbols(store):
    # Regression: the unscoped query returned every calendar name (295 on
    # 2026-07-27), blowing the 22-min agent timeout so nothing refreshed.
    # Only symbols we decided on feed training/playbook, so only those matter.
    from datetime import date, timedelta
    from orchestrator.daily import BACKTEST_REFRESH_MAX
    today = date(2026, 7, 27)          # a Monday
    last_week = (today - timedelta(days=3)).isoformat()

    decided = store.upsert_event("HOPE", last_week, "bmo")
    store.insert_decision(symbol="HOPE", action="long_equity", policy_version="t",
                          risk_verdict="approved", status="closed_live",
                          size_usd=27.0, entry_price=13.5, event_id=decided)
    for i in range(50):                # calendar noise, never decided on
        store.upsert_event(f"NOI{i}", last_week, "bmo")

    rows = store._db.execute(
        """SELECT DISTINCT e.symbol FROM events e
           JOIN decisions d ON d.event_id = e.id
           WHERE e.report_date >= ? AND e.report_date < ?
           ORDER BY e.symbol""",
        ((today - timedelta(days=7)).isoformat(), today.isoformat()),
    ).fetchall()
    syms = [r["symbol"] for r in rows][:BACKTEST_REFRESH_MAX]

    assert syms == ["HOPE"]                 # the 50 undecided names are excluded
    assert len(syms) <= BACKTEST_REFRESH_MAX
