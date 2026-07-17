from pathlib import Path

import pytest

from engine import context
from engine.config import Config
from engine.context import build_context_pack
from engine.store import Store
from orchestrator.briefing import build_briefing


@pytest.fixture()
def setup(tmp_path: Path):
    cfg = Config(db_path=tmp_path / "t.sqlite3", universe=("NVDA", "TSM"))
    store = Store(cfg.db_path)
    yield cfg, store
    store.close()


def test_briefing_sections_present(setup):
    cfg, store = setup
    event_id = store.upsert_event("TSM", "2099-01-05", "bmo")  # far-future Monday
    did = store.insert_decision(
        symbol="NVDA", action="long_equity", policy_version="0.2.0",
        risk_verdict="approved", status="open_paper",
        size_usd=100.0, entry_price=50.0, event_id=event_id, conviction=0.7,
    )
    text = build_briefing(cfg, store)
    for section in ("## Account & risk", "## Open positions",
                    "## Trade history & dataset", "## Plan - next 14 days",
                    "## Longer-term roadmap status", "## Steering"):
        assert section in text
    assert f"#{did} NVDA" in text


def test_briefing_shows_closed_pnl(setup):
    cfg, store = setup
    store.insert_decision(
        symbol="NVDA", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=100.0, entry_price=100.0,
        event_id=store.upsert_event("NVDA", "2026-01-02"),
    )
    store.close_position("NVDA", 110.0)
    text = build_briefing(cfg, store)
    assert "wins 1/1" in text
    assert "$10.00" in text


def test_trade_history_includes_outcomes(setup):
    _, store = setup
    store.insert_decision(
        symbol="NVDA", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=100.0, entry_price=100.0,
    )
    store.close_position("NVDA", 90.0)
    h = store.trade_history()
    assert h[0]["pnl_usd"] == pytest.approx(-10.0)
    assert h[0]["status"] == "closed_paper"


def test_directives_injected_into_context_pack(setup, tmp_path, monkeypatch):
    cfg, store = setup
    d = tmp_path / "DIRECTIVES.md"
    d.write_text("Hold cash unless the stats are excellent.")
    monkeypatch.setattr(context, "DIRECTIVES_PATH", d)
    pack = build_context_pack(cfg, store)
    assert "operator_directives" in pack
    assert "Hold cash unless the stats are excellent." in pack


def test_pack_lists_screened_noncore_events(setup):
    """Regression (2026-07-16): the pack filtered upcoming_earnings to the
    core universe, so screened non-core events were invisible — analysts hit
    their step-1 'no recorded event' stop and benched whole slates."""
    from datetime import datetime, timedelta, timezone
    cfg, store = setup
    d1 = (datetime.now(timezone.utc).date() + timedelta(days=3)).isoformat()
    d2 = (datetime.now(timezone.utc).date() + timedelta(days=4)).isoformat()
    store.upsert_event("TSM", d1, "bmo")  # core
    eid = store.upsert_event("NFLX", d1, "amc")  # non-core, screened
    store.set_event_screen(eid, True, '{"avg_volume": 39000000}')
    store.upsert_event("PENNY", d2, "bmo")  # non-core, unscreened
    eid_macro = store.upsert_event("MSFT", d2, "amc")  # macro watch
    store.set_event_screen(eid_macro, True, '{"avg_volume": 20000000}')
    pack = build_context_pack(cfg, store)
    upcoming = pack.split("upcoming_earnings")[1].split("macro_events")[0]
    assert f"TSM {d1} bmo (core)" in upcoming
    assert f"NFLX {d1} amc (screened)" in upcoming
    assert "PENNY" not in upcoming
    assert "MSFT" not in upcoming  # macro names are context, never tradeable
    assert f"MSFT {d2} amc" in pack.split("macro_events")[1]


def test_missing_directives_is_fine(setup, tmp_path, monkeypatch):
    cfg, store = setup
    monkeypatch.setattr(context, "DIRECTIVES_PATH", tmp_path / "nope.md")
    assert "operator_directives" not in build_context_pack(cfg, store)
