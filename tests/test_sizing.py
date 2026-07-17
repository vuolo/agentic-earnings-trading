import pytest

from engine.sizing import dynamic_size


BASE = dict(equity_usd=500.0, buying_power_usd=500.0, pos_cap_usd=250.0,
            daily_remaining_usd=450.0)


def test_conviction_scales_risk_continuously():
    lo = dynamic_size(conviction=0.5, adverse_move_pct=5.0, **BASE)
    mid = dynamic_size(conviction=0.7, adverse_move_pct=5.0, **BASE)
    hi = dynamic_size(conviction=0.9, adverse_move_pct=5.0, **BASE)
    assert lo["size_usd"] == pytest.approx(100.0)          # 1% of 500 / 5%
    assert mid["size_usd"] == pytest.approx(200.0)         # 2% of 500 / 5%
    assert hi["size_usd"] == 250.0                         # 3% clamped by cap
    assert hi["binding_constraint"] == "per_position_cap"
    assert lo["size_usd"] < mid["size_usd"] <= hi["size_usd"]


def test_account_breathes_with_equity():
    small = dynamic_size(conviction=0.6, adverse_move_pct=5.0, **BASE)
    grown = dynamic_size(conviction=0.6, adverse_move_pct=5.0,
                         equity_usd=1000.0, buying_power_usd=1000.0,
                         pos_cap_usd=250.0, daily_remaining_usd=450.0)
    assert grown["risk_usd"] == pytest.approx(2 * small["risk_usd"])
    assert grown["raw_size_usd"] == pytest.approx(2 * small["raw_size_usd"])


def test_wilder_names_size_smaller():
    quiet = dynamic_size(conviction=0.6, adverse_move_pct=3.0, **BASE)
    wild = dynamic_size(conviction=0.6, adverse_move_pct=15.0, **BASE)
    assert wild["raw_size_usd"] < quiet["raw_size_usd"]
    assert wild["max_loss_estimate_usd"] <= quiet["risk_usd"] + 0.01


def test_haircuts_multiply():
    plain = dynamic_size(conviction=0.6, adverse_move_pct=5.0, **BASE)
    cut = dynamic_size(conviction=0.6, adverse_move_pct=5.0, core=False,
                       overnight=True, **BASE)
    assert cut["raw_size_usd"] == pytest.approx(plain["raw_size_usd"] * 0.75 * 0.8)
    assert cut["haircuts"] == ["non-core x0.75", "overnight x0.8"]


def test_buying_power_binds_with_buffer():
    out = dynamic_size(conviction=0.9, adverse_move_pct=2.0,
                       equity_usd=500.0, buying_power_usd=120.0,
                       pos_cap_usd=250.0, daily_remaining_usd=450.0)
    assert out["size_usd"] == pytest.approx(115.0)  # 120 - $5 buffer
    assert out["binding_constraint"] == "buying_power"


def test_below_floor_recommends_pass():
    out = dynamic_size(conviction=0.5, adverse_move_pct=5.0,
                       equity_usd=500.0, buying_power_usd=20.0,
                       pos_cap_usd=250.0, daily_remaining_usd=450.0)
    assert out["recommendation"] == "pass_below_floor"
    out2 = dynamic_size(conviction=0.5, adverse_move_pct=20.0,
                        equity_usd=200.0, buying_power_usd=200.0,
                        pos_cap_usd=250.0, daily_remaining_usd=450.0)
    assert out2["size_usd"] == pytest.approx(10.0)  # 1% of 200 / 20%
    assert out2["recommendation"] == "pass_below_floor"


def test_wild_name_small_but_tradeable():
    # SMPL-type event: 17% adverse move, low conviction, non-core overnight.
    # The old tiers traded $75 (max loss ~$13); the dynamic model trades
    # small instead of passing - participation with proportional risk.
    out = dynamic_size(conviction=0.55, adverse_move_pct=17.0,
                       equity_usd=485.63, buying_power_usd=485.63,
                       pos_cap_usd=250.0, daily_remaining_usd=450.0,
                       core=False, overnight=True)
    assert out["recommendation"] == "trade"
    assert 20.0 <= out["size_usd"] < 40.0
    assert out["max_loss_estimate_usd"] < 7.0


def test_input_validation():
    assert "error" in dynamic_size(conviction=1.2, adverse_move_pct=5.0, **BASE)
    assert "error" in dynamic_size(conviction=0.6, adverse_move_pct=0.0, **BASE)
    assert "error" in dynamic_size(conviction=0.6, adverse_move_pct=5.0,
                                   equity_usd=0.0, buying_power_usd=100.0,
                                   pos_cap_usd=250.0, daily_remaining_usd=450.0)


def test_effective_caps_paper_mode(tmp_path):
    from engine.config import Config
    from engine.risk import effective_caps
    cfg = Config(db_path=tmp_path / "t.sqlite3")
    pos, daily = effective_caps(cfg)
    assert pos == cfg.limits.max_position_usd
    assert daily == cfg.limits.max_daily_new_exposure_usd
