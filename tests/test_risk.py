from pathlib import Path

import pytest

from engine.config import Config, RiskLimits
from engine.risk import DecisionRequest, RiskGate
from engine.store import Store


@pytest.fixture()
def setup(tmp_path: Path):
    cfg = Config(
        db_path=tmp_path / "t.sqlite3",
        universe=("NVDA", "AMD", "MU"),
        limits=RiskLimits(
            max_position_usd=1_000.0,
            max_daily_new_exposure_usd=2_500.0,
            max_open_positions=2,
        ),
    )
    store = Store(cfg.db_path)
    yield cfg, store, RiskGate(cfg, store)
    store.close()


def _open_position(store: Store, symbol: str, size: float = 500.0) -> int:
    return store.insert_decision(
        symbol=symbol, action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=size, entry_price=100.0,
    )


def req(symbol="NVDA", action="long_equity", size=500.0, conviction=0.7):
    return DecisionRequest(symbol=symbol, action=action, size_usd=size, conviction=conviction)


def test_approves_within_limits(setup):
    _, _, gate = setup
    verdict = gate.evaluate(req())
    assert verdict.approved
    assert str(verdict) == "approved"


def test_rejects_oversized_position(setup):
    _, _, gate = setup
    verdict = gate.evaluate(req(size=1_500.0))
    assert not verdict.approved
    assert any("per-position cap" in r for r in verdict.reasons)


def test_rejects_nonpositive_size(setup):
    _, _, gate = setup
    assert not gate.evaluate(req(size=0)).approved


def test_rejects_noncore_without_screened_event(setup):
    _, store, gate = setup
    verdict = gate.evaluate(req(symbol="GME"))
    assert not verdict.approved
    assert any("no recorded upcoming event" in r for r in verdict.reasons)
    from datetime import date, timedelta
    eid = store.upsert_event("GME", (date.today() + timedelta(days=2)).isoformat())
    verdict = gate.evaluate(req(symbol="GME"))
    assert not verdict.approved
    assert any("liquidity screen" in r for r in verdict.reasons)
    store.set_event_screen(eid, True, '{"price": 25.0, "avg_volume": 5000000}')
    assert gate.evaluate(req(symbol="GME")).approved


def test_rejects_invalid_action(setup):
    _, _, gate = setup
    assert not gate.evaluate(req(action="sell_naked_calls")).approved
    assert not gate.evaluate(req(action="pass")).approved


def test_short_requires_operator_enable(setup):
    _, store, gate = setup
    verdict = gate.evaluate(req(action="short_equity"))
    assert not verdict.approved
    assert any("operator-verified shorting" in r for r in verdict.reasons)
    store.meta_set("short_capable", "1")
    assert gate.evaluate(req(action="short_equity")).approved
    store.meta_set("short_capable", "")
    assert not gate.evaluate(req(action="short_equity")).approved


def test_rejects_duplicate_open_position(setup):
    _, store, gate = setup
    _open_position(store, "NVDA")
    verdict = gate.evaluate(req(symbol="NVDA"))
    assert not verdict.approved
    assert any("already exists" in r for r in verdict.reasons)


def test_rejects_at_max_open_positions(setup):
    _, store, gate = setup
    _open_position(store, "NVDA")
    _open_position(store, "AMD")
    verdict = gate.evaluate(req(symbol="MU"))
    assert not verdict.approved
    assert any("max open positions" in r for r in verdict.reasons)


def test_rejects_when_daily_budget_exhausted(setup):
    _, store, gate = setup
    _open_position(store, "NVDA", size=1_000.0)
    _open_position(store, "AMD", size=1_000.0)
    store.close_position("AMD", 110.0)  # closed same day still counts toward budget
    verdict = gate.evaluate(req(symbol="MU", size=1_000.0))
    assert not verdict.approved
    assert any("daily new-exposure budget" in r for r in verdict.reasons)


def test_rejects_live_mode_when_disarmed(setup, tmp_path, monkeypatch):
    from engine import arming
    monkeypatch.setattr(arming, "ARM_PATH", tmp_path / "no-arm.json")
    cfg, store, _ = setup
    live_cfg = Config(mode="live", db_path=cfg.db_path, universe=cfg.universe, limits=cfg.limits)
    verdict = RiskGate(live_cfg, store).evaluate(req())
    assert not verdict.approved
    assert any("not armed" in r for r in verdict.reasons)


def test_rejects_bad_conviction(setup):
    _, _, gate = setup
    assert not gate.evaluate(req(conviction=1.5)).approved


def _armed_live_gate(setup, monkeypatch):
    """Live-mode gate with a faked active arm (caps match the test limits)."""
    from engine import arming
    cfg, store, _ = setup
    fake = arming.Arm(per_position_cap_usd=1_000.0, daily_cap_usd=2_500.0,
                      expires="2999-01-01", armed_at="2026-01-01T00:00:00")
    monkeypatch.setattr(arming, "arm_status", lambda: (fake, ""))
    live_cfg = Config(mode="live", db_path=cfg.db_path, universe=cfg.universe,
                      limits=cfg.limits)
    return store, RiskGate(live_cfg, store)


def test_live_entry_not_starved_by_paper_legs(setup, monkeypatch):
    # Proven live 2026-07-20 (HAL): $0-capital paper dataset legs filled every
    # open-position slot and the daily budget, rejecting an armed live long.
    store, gate = _armed_live_gate(setup, monkeypatch)
    for sym in ("NVDA", "AMD"):  # max_open_positions=2, all paper
        store.insert_decision(
            symbol=sym, action="bearish_option", policy_version="t",
            risk_verdict="approved", status="open_paper",
            size_usd=1_000.0, entry_price=100.0)
    verdict = gate.evaluate(req(symbol="MU"))
    assert verdict.approved, verdict.reasons


def test_live_caps_still_bind_on_live_positions(setup, monkeypatch):
    store, gate = _armed_live_gate(setup, monkeypatch)
    for sym, status in (("NVDA", "pending_live"), ("AMD", "open_live")):
        store.insert_decision(
            symbol=sym, action="long_equity", policy_version="t",
            risk_verdict="approved", status=status,
            size_usd=500.0, entry_price=100.0)
    verdict = gate.evaluate(req(symbol="MU"))
    assert not verdict.approved
    assert any("max open positions" in r for r in verdict.reasons)


def test_live_daily_budget_ignores_paper_but_counts_live(setup, monkeypatch):
    store, gate = _armed_live_gate(setup, monkeypatch)
    store.insert_decision(  # paper leg: must not consume the live budget
        symbol="NVDA", action="bearish_option", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=2_400.0, entry_price=100.0)
    assert gate.evaluate(req(symbol="MU", size=1_000.0)).approved
    store.insert_decision(  # live entry today: does consume it
        symbol="AMD", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_live",
        size_usd=2_000.0, entry_price=100.0)
    verdict = gate.evaluate(req(symbol="MU", size=1_000.0))
    assert not verdict.approved
    assert any("daily new-exposure budget" in r for r in verdict.reasons)


def test_paper_mode_still_counts_everything(setup):
    # Paper mode simulates the caps faithfully: paper legs fill slots.
    _, store, gate = setup
    _open_position(store, "NVDA")
    _open_position(store, "AMD")
    assert not gate.evaluate(req(symbol="MU")).approved
