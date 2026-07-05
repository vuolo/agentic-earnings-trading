import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from engine import arming
from engine.config import Config, RiskLimits
from engine.risk import DecisionRequest, RiskGate
from engine.store import Store


@pytest.fixture()
def arm_path(tmp_path: Path, monkeypatch):
    p = tmp_path / ".arm-live.json"
    monkeypatch.setattr(arming, "ARM_PATH", p)
    return p


@pytest.fixture()
def live_setup(tmp_path: Path):
    cfg = Config(
        mode="live", db_path=tmp_path / "t.sqlite3", universe=("NVDA",),
        limits=RiskLimits(max_position_usd=1_000.0,
                          max_daily_new_exposure_usd=2_500.0,
                          max_open_positions=5),
    )
    store = Store(cfg.db_path)
    yield RiskGate(cfg, store)
    store.close()


def req(size=150.0, action="long_equity"):
    return DecisionRequest(symbol="NVDA", action=action, size_usd=size, conviction=0.7)


def test_live_without_arm_rejected(arm_path, live_setup):
    verdict = live_setup.evaluate(req())
    assert not verdict.approved
    assert any("not armed" in r for r in verdict.reasons)


def test_live_with_arm_approved_within_caps(arm_path, live_setup):
    arming.arm(200.0, 400.0, days=7)
    assert live_setup.evaluate(req(size=150.0)).approved


def test_arm_cap_tightens_engine_cap(arm_path, live_setup):
    arming.arm(200.0, 400.0, days=7)
    verdict = live_setup.evaluate(req(size=500.0))  # under engine cap, over arm cap
    assert not verdict.approved
    assert any("per-position cap $200.00" in r for r in verdict.reasons)


def test_expired_arm_rejected(arm_path, live_setup):
    a = arming.arm(200.0, 400.0, days=7)
    data = json.loads(arm_path.read_text())
    data["expires"] = (date.today() - timedelta(days=1)).isoformat()
    arm_path.write_text(json.dumps(data))
    verdict = live_setup.evaluate(req())
    assert not verdict.approved
    assert any("expired" in r for r in verdict.reasons)
    assert arming.arm_status()[0] is None
    assert a.per_position_cap_usd == 200.0


def test_invalid_arm_file_rejected(arm_path, live_setup):
    arm_path.write_text("{not json")
    assert not live_setup.evaluate(req()).approved


def test_disarm(arm_path):
    arming.arm(200.0, 400.0, days=7)
    assert arming.arm_status()[0] is not None
    assert arming.disarm() is True
    assert arming.arm_status() == (None, "not armed")
    assert arming.disarm() is False


def test_paper_mode_ignores_arm(arm_path, tmp_path):
    cfg = Config(db_path=tmp_path / "p.sqlite3", universe=("NVDA",))
    store = Store(cfg.db_path)
    try:
        assert RiskGate(cfg, store).evaluate(req(size=500.0)).approved
    finally:
        store.close()
