import json

import pytest

from engine import indicators


def bars(closes, volumes=None):
    volumes = volumes or [1000.0] * len(closes)
    return [{"open": c, "high": c * 1.01, "low": c * 0.99, "close": c, "volume": v}
            for c, v in zip(closes, volumes)]


def test_parse_bars_shapes():
    raw = [{"close_price": "100.5", "open_price": "99", "volume": 10}] * 35
    parsed = indicators.parse_bars(json.dumps(raw))
    assert len(parsed) == 35 and parsed[0]["close"] == 100.5
    wrapped = json.dumps({"historicals": raw})
    assert len(indicators.parse_bars(wrapped)) == 35
    with pytest.raises(ValueError):
        indicators.parse_bars(json.dumps(raw[:5]))  # too few


def test_rsi_extremes():
    rising = [100 + i for i in range(40)]
    falling = [140 - i for i in range(40)]
    assert indicators.rsi(rising) == 100.0
    assert indicators.rsi(falling) == pytest.approx(0.0, abs=0.01)


def test_compute_features_shape():
    closes = [100 + (i % 7) - 3 + i * 0.1 for i in range(60)]
    feats = indicators.compute(bars(closes))
    for key in ("rsi14", "atr14_pct", "realized_vol20_pct", "volume_z20",
                "sma20", "sma50", "trend", "pct_from_high", "pct_from_low"):
        assert key in feats, key
    assert feats["trend"] in ("rising", "falling", "flat")
    assert feats["pct_from_high"] <= 0 <= feats["pct_from_low"]


def test_relative_strength():
    stock = [100 * (1.01 ** i) for i in range(40)]   # strong
    bench = [100.0] * 40                              # flat
    feats = indicators.compute(bars(stock), bars(bench))
    assert feats["rel_strength20_pct"] > 15


def test_implied_move():
    r = indicators.implied_move(434.45, 20.95, 20.675)
    assert r["implied_move_pct"] == pytest.approx(9.58, abs=0.01)
    with pytest.raises(ValueError):
        indicators.implied_move(0, 1, 1)
