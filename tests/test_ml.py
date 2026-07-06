import json
from pathlib import Path

import pytest

from engine import ml
from engine.store import Store


@pytest.fixture()
def store(tmp_path: Path):
    s = Store(tmp_path / "t.sqlite3")
    yield s
    s.close()


def _labeled_row(store, i, up: bool):
    """Synthetic labeled decision: rsi cleanly separates up from down."""
    feats = {
        "computed": {"rsi14": 70.0 + i % 5 if up else 30.0 - i % 5,
                     "atr14_pct": 3.0, "realized_vol20_pct": 40.0,
                     "pct_from_high": -2.0, "pct_from_low": 20.0},
        "implied_move": {"implied_move_pct": 8.0},
    }
    did = store.insert_decision(
        symbol="NVDA", action="long_equity", policy_version="t",
        risk_verdict="approved", status="open_paper",
        size_usd=100.0, entry_price=100.0, conviction=0.7,
        features=json.dumps(feats),
    )
    store.close_position("NVDA", 105.0 if up else 95.0)
    return did


def test_untrained_below_threshold(store, tmp_path):
    for i in range(5):
        _labeled_row(store, i, up=(i % 2 == 0))
    status = ml.train(store, model_path=tmp_path / "m.json")
    assert status["trained"] is False
    assert "accumulating" in status["reason"]
    pred = ml.predict({}, model_path=tmp_path / "m.json")
    assert pred["available"] is False


def test_trains_and_predicts_direction(store, tmp_path):
    for i in range(ml.MIN_TRAIN_ROWS + 5):
        _labeled_row(store, i, up=(i % 2 == 0))
    mp = tmp_path / "m.json"
    status = ml.train(store, model_path=mp)
    assert status["trained"] is True
    assert status["cv_accuracy"] > 0.8  # rsi separates classes by design

    hot = {"computed": {"rsi14": 72.0, "atr14_pct": 3.0, "realized_vol20_pct": 40.0,
                        "pct_from_high": -2.0, "pct_from_low": 20.0},
           "implied_move": {"implied_move_pct": 8.0}}
    cold = {"computed": {"rsi14": 28.0, "atr14_pct": 3.0, "realized_vol20_pct": 40.0,
                         "pct_from_high": -2.0, "pct_from_low": 20.0},
            "implied_move": {"implied_move_pct": 8.0}}
    p_hot = ml.predict(hot, conviction=0.7, model_path=mp)
    p_cold = ml.predict(cold, conviction=0.7, model_path=mp)
    assert p_hot["available"] and p_cold["available"]
    assert p_hot["prob_up"] > 0.6 > 0.4 > p_cold["prob_up"]
    assert p_hot["advisory_only"] is True  # below ADVISORY_TARGET_ROWS


def test_extract_features_nested():
    feats = {"implied_move": {"implied_move_pct": 9.6},
             "computed": {"rsi14": 55.0}, "volume_z20": 1.2}
    vec = ml.extract_features(feats, conviction=0.65)
    assert vec == {"implied_move_pct": 9.6, "rsi14": 55.0,
                   "volume_z20": 1.2, "conviction": 0.65}


def test_training_rows_join_dataset(store, tmp_path):
    import json as _json
    for i in range(30):
        up = i % 2 == 0
        store.upsert_training_row(
            f"SYM{i}", "2026-01-05",
            _json.dumps({"computed": {"rsi14": 70.0 if up else 30.0,
                                      "atr14_pct": 3.0, "pct_from_high": -2.0}}),
            2.5 if up else -2.5,
        )
    X, y = ml.build_dataset(store)
    assert len(X) == 30 and sum(y) == 15
    status = ml.train(store, model_path=tmp_path / "m.json")
    assert status["trained"] is True
