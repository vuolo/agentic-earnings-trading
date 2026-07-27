from pathlib import Path

import pytest

from engine.store import Store


@pytest.fixture()
def store(tmp_path: Path):
    s = Store(tmp_path / "t.sqlite3")
    yield s
    s.close()


def _pending(store, symbol="NVDA", report_date="2026-08-26"):
    event_id = store.upsert_event(symbol, report_date)
    return store.insert_decision(
        symbol=symbol, action="long_equity", policy_version="t",
        risk_verdict="approved", status="pending_live",
        size_usd=200.0, entry_price=100.0, event_id=event_id,
    )


def test_execution_fill_flow(store):
    did = _pending(store)
    assert [r["id"] for r in store.pending_executions()] == [did]
    row = store.mark_execution(did, filled=True, fill_price=100.5, detail="limit filled")
    assert row["status"] == "open_live"
    assert row["entry_price"] == pytest.approx(100.5)
    assert store.pending_executions() == []


def test_execution_failure_flow(store):
    did = _pending(store)
    row = store.mark_execution(did, filled=False, detail="unfilled, cancelled")
    assert row["status"] == "exec_failed"
    assert row["exec_detail"] == "unfilled, cancelled"


def test_mark_execution_guards(store):
    did = _pending(store)
    assert store.mark_execution(did, filled=True, fill_price=None) is None  # needs price
    store.mark_execution(did, filled=True, fill_price=100.0)
    assert store.mark_execution(did, filled=True, fill_price=101.0) is None  # not pending
    assert store.mark_execution(9999, filled=False) is None


def test_whole_share_fill_corrects_size(store):
    # Whole-share entry: decided $200 notional, but only 1 share @ $150 filled.
    # size_usd must drop to the real $150 so P&L and budget aren't inflated.
    did = _pending(store)  # size_usd=200, entry 100
    row = store.mark_execution(did, filled=True, fill_price=150.0,
                               filled_notional=150.0, detail="1 whole share")
    assert row["size_usd"] == pytest.approx(150.0)
    assert row["entry_price"] == pytest.approx(150.0)
    # P&L now computed off the corrected notional: 1 share * (165-150) = $15.
    result = store.close_live(did, 165.0)
    assert result["pnl_usd"] == pytest.approx(15.0)


def test_fractional_fill_keeps_size(store):
    # No filled_notional (fractional/dollar order) leaves size_usd untouched.
    did = _pending(store)  # size_usd=200
    row = store.mark_execution(did, filled=True, fill_price=100.0)
    assert row["size_usd"] == pytest.approx(200.0)


def test_live_close_records_real_pnl(store):
    did = _pending(store, report_date="2026-07-10")
    store.mark_execution(did, filled=True, fill_price=100.0)
    due = store.due_live_closes("2026-07-11")
    assert [r["id"] for r in due] == [did]
    result = store.close_live(did, 108.0, "T+1 sell fill")
    assert result["pnl_usd"] == pytest.approx(16.0)  # $200 @ 100 -> 108
    assert store.get_decision(did)["status"] == "closed_live"
    assert store.due_live_closes("2026-07-11") == []


def test_short_close_pnl_inverse(store):
    event_id = store.upsert_event("MU", "2026-07-10", "amc")
    did = store.insert_decision(
        symbol="MU", action="short_equity", policy_version="t",
        risk_verdict="approved", status="pending_live",
        size_usd=120.0, entry_price=120.0, event_id=event_id,
    )
    store.mark_execution(did, filled=True, fill_price=120.0)
    result = store.close_live(did, 108.0, "buy-to-cover at open")
    assert result["pnl_usd"] == pytest.approx(12.0)   # stock fell 10%, short gains
    assert result["move_pct"] == pytest.approx(-10.0)
    assert store.get_decision(did)["status"] == "closed_live"


def test_pass_counterfactual_labeling(store):
    event_id = store.upsert_event("TSM", "2026-07-16")
    did = store.insert_decision(
        symbol="TSM", action="pass", policy_version="t",
        risk_verdict="n/a (pass)", status="pass",
        entry_price=434.45, event_id=event_id,
    )
    assert [r["id"] for r in store.due_pass_labels("2026-07-17")] == [did]
    result = store.label_pass(did, 447.5, "moved +3% — pass was right vs 9.6% implied")
    assert result["pnl_usd"] == 0.0
    assert result["move_pct"] == pytest.approx(3.004, abs=0.01)
    assert store.get_decision(did)["status"] == "pass"  # status unchanged
    assert store.label_pass(did, 450.0) is None  # already labeled
    assert store.due_pass_labels("2026-07-17") == []


def test_pass_label_without_reference_price(store):
    event_id = store.upsert_event("MU", "2026-07-01")
    did = store.insert_decision(
        symbol="MU", action="pass", policy_version="t",
        risk_verdict="n/a (pass)", status="pass", event_id=event_id,
    )
    result = store.label_pass(did, 120.0, "no ref price recorded")
    assert result["move_pct"] is None
    assert result["pnl_usd"] == 0.0


def test_meta_and_outcome_count(store):
    assert store.outcome_count() == 0
    assert store.meta_get("strategist_outcome_count", "0") == "0"
    store.meta_set("strategist_outcome_count", "5")
    assert store.meta_get("strategist_outcome_count") == "5"
    store.meta_set("strategist_outcome_count", "7")
    assert store.meta_get("strategist_outcome_count") == "7"


def test_performance_summary_shapes(store):
    did = _pending(store, report_date="2026-07-10")
    store.mark_execution(did, filled=True, fill_price=100.0)
    store.close_live(did, 110.0)
    summary = store.performance_summary()
    assert summary["closed_trades"] == 1
    assert summary["wins"] == 1
    assert summary["total_pnl_usd"] == pytest.approx(20.0)


# -- morning fill reconciliation (regression: phantom-open positions) --------
# Twice now the pre-open executor left filled exits unreported (VZ/NEM/EW
# 2026-07-24, HOPE/AZN 2026-07-27), because a `claude -p` run cannot block
# until the 9:30 cross. The orchestrator now owns that timing via a late
# reconcile pass. These pin the seam.

def _open_live(store, symbol, report_date, timing="bmo"):
    event_id = store.upsert_event(symbol, report_date, timing)
    did = store.insert_decision(
        symbol=symbol, action="long_equity", policy_version="t",
        risk_verdict="approved", status="pending_live",
        size_usd=100.0, entry_price=50.0, event_id=event_id)
    store.mark_execution(did, filled=True, fill_price=50.0)
    return did


def test_reconcile_reports_fills_and_clears_flag(store, monkeypatch):
    from datetime import date
    from orchestrator import daily
    did = _open_live(store, "HOPE", "2026-07-27")
    today = date(2026, 7, 27)
    assert [r["id"] for r in store.due_live_closes(today.isoformat())] == [did]

    # Simulate the reconcile executor doing its job: recording the real fill.
    def fake_run(store_, role, *, symbol=None, model=None):
        store_.close_live(did, 55.0, "auction fill")
        return 0
    monkeypatch.setattr(daily, "_run_with_evidence", fake_run)
    notes = []
    monkeypatch.setattr(daily, "_notify", lambda m: notes.append(m))

    arm = type("A", (), {"expires": "2026-08-04"})()
    daily._reconcile_live_fills(store, arm=arm, arm_why="", today=today, model=None)

    assert store.get_decision(did)["status"] == "closed_live"
    assert store.meta_get("exit_reconcile_needed") == ""
    assert notes == []  # healthy path must not notify


def test_reconcile_flags_and_notifies_when_still_unreported(store, monkeypatch):
    from datetime import date
    from orchestrator import daily
    did = _open_live(store, "AZN", "2026-07-27")
    today = date(2026, 7, 27)

    # The reconcile run fails to record anything (unfilled exit / broken run).
    monkeypatch.setattr(daily, "_run_with_evidence",
                        lambda store_, role, **kw: 0)
    notes = []
    monkeypatch.setattr(daily, "_notify", lambda m: notes.append(m))

    arm = type("A", (), {"expires": "2026-08-04"})()
    daily._reconcile_live_fills(store, arm=arm, arm_why="", today=today, model=None)

    assert store.get_decision(did)["status"] == "open_live"
    flag = store.meta_get("exit_reconcile_needed")
    assert f"#{did}" in flag and "AZN" in flag
    assert len(notes) == 1 and "unreported" in notes[0]


def test_reconcile_disarmed_flags_without_running_executor(store, monkeypatch):
    from datetime import date
    from orchestrator import daily
    did = _open_live(store, "NEM", "2026-07-27")
    ran = []
    monkeypatch.setattr(daily, "_run_with_evidence",
                        lambda *a, **k: ran.append(1) or 0)
    notes = []
    monkeypatch.setattr(daily, "_notify", lambda m: notes.append(m))

    daily._reconcile_live_fills(store, arm=None, arm_why="not armed",
                                today=date(2026, 7, 27), model=None)

    assert ran == []  # never launch an order-capable role while disarmed
    assert f"#{did}" in store.meta_get("exit_reconcile_needed")
    assert len(notes) == 1
