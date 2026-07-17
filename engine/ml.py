"""ML sidecar (Phase 4) — trains on the labeled decision dataset.

Pipeline is fully built and self-activating: the morning tick calls
maybe_train() daily; below MIN_TRAIN_ROWS it reports "accumulating" and does
nothing. Once enough labeled rows exist it fits a logistic regression
(direction of the post-decision move) with cross-validation, and saves the
model as plain JSON (coefficients + standardization) so inference is pure
Python — no pickle, auditable in git history if ever committed.

The analyst consumes it through the gateway's get_ml_prediction tool; until
trained, that tool says so honestly. The model is ADVISORY until its CV
accuracy earns more (strategist + operator decide when).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .store import Store

MODEL_PATH = REPO_ROOT / "models" / "model.json"
MIN_TRAIN_ROWS = 25          # fit + report metrics from here
ADVISORY_TARGET_ROWS = 50    # the "worth trusting as a feature" bar

NUMERIC_KEYS = (
    "implied_move_pct", "rsi14", "atr14_pct", "realized_vol20_pct",
    "volume_z20", "pct_from_high", "pct_from_low", "rel_strength20_pct",
    "conviction",
    # Prior-reaction gap history (see gap_history_features / the backtest
    # block mapping in extract_features — train and serve share these names).
    "gap_n", "gap_up_rate", "gap_mean_pct", "gap_mean_abs_pct",
    "gap_std_pct", "gap_worst_pct", "gap_best_pct",
)

# Live snapshots embed get_backtest_summary verbatim under "backtest"; its
# gap stats are the same quantities gap_history_features computes for
# reconstructed rows, so map them onto the shared feature names.
GAP_STAT_ALIASES = {
    "n": "gap_n", "up_rate": "gap_up_rate", "mean_pct": "gap_mean_pct",
    "mean_abs_pct": "gap_mean_abs_pct", "std_pct": "gap_std_pct",
    "worst_pct": "gap_worst_pct", "best_pct": "gap_best_pct",
}


def gap_history_features(store: Store, symbol: str, before_date: str) -> dict[str, float]:
    """Prior-reaction gap stats from backtest rows STRICTLY before
    before_date (YYYY-MM-DD). The strict cutoff is the lookahead guard: an
    event's own reaction (report_date == before_date) never feeds its
    features, only earlier quarters do."""
    gaps = [
        (r["post_open"] - r["pre_close"]) / r["pre_close"] * 100
        for r in store.backtest_events(symbol)
        if r["report_date"] < before_date
        and r["pre_close"] and r["post_open"]
        and r["pre_close"] > 0 and r["post_open"] > 0
    ]
    if not gaps:
        return {}
    n = len(gaps)
    mean = sum(gaps) / n
    var = sum((g - mean) ** 2 for g in gaps) / n
    return {
        "gap_n": float(n),
        "gap_up_rate": round(sum(g > 0 for g in gaps) / n, 4),
        "gap_mean_pct": round(mean, 4),
        "gap_mean_abs_pct": round(sum(abs(g) for g in gaps) / n, 4),
        "gap_std_pct": round(var ** 0.5, 4),
        "gap_worst_pct": round(min(gaps), 4),
        "gap_best_pct": round(max(gaps), 4),
    }


def extract_features(features: dict, conviction: float | None = None) -> dict[str, float]:
    """Pull known numeric keys from a feature snapshot (root, 'computed', or
    'indicators' sub-dicts), plus conviction."""
    sources = [features]
    for sub in ("computed", "indicators", "implied_move"):
        if isinstance(features.get(sub), dict):
            sources.append(features[sub])
    bt = features.get("backtest")
    if isinstance(bt, dict) and isinstance(bt.get("gap_t1close_to_postopen"), dict):
        stats = bt["gap_t1close_to_postopen"]
        sources.append({dst: stats[src] for src, dst in GAP_STAT_ALIASES.items()
                        if src in stats})
    out: dict[str, float] = {}
    for key in NUMERIC_KEYS:
        for src in sources:
            v = src.get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[key] = float(v)
                break
    if conviction is not None and "conviction" not in out:
        out["conviction"] = float(conviction)
    return out


def build_dataset(store: Store) -> tuple[list[dict[str, float]], list[int]]:
    X: list[dict[str, float]] = []
    y: list[int] = []
    for row in store.labeled_decisions(limit=100_000):
        move = row.get("outcome_move_pct")
        if move is None:
            continue
        try:
            feats = row["features"]
            feats = json.loads(feats) if isinstance(feats, str) else (feats or {})
        except (json.JSONDecodeError, TypeError):
            continue
        vec = extract_features(feats, row.get("conviction"))
        # Gap history is computed fresh from the backtests table (cutoff =
        # decision date, so only earlier quarters count — later backfills
        # still describe events that predate the decision). The stored
        # snapshot stays untouched and wins where it already has a value.
        cutoff = (row.get("created_at") or "")[:10]
        if cutoff:
            for k, v in gap_history_features(store, row["symbol"], cutoff).items():
                vec.setdefault(k, v)
        if len(vec) < 3:  # too sparse to learn from
            continue
        X.append(vec)
        y.append(1 if move > 0 else 0)
    # Reconstructed historical rows (indicators as-of T-1 + realized gap
    # label). Same target definition as live rows: pre-close -> post-open.
    for row in store.training_rows():
        try:
            feats = json.loads(row["features"])
        except (json.JSONDecodeError, TypeError):
            continue
        vec = extract_features(feats)
        for k, v in gap_history_features(store, row["symbol"], row["report_date"]).items():
            vec.setdefault(k, v)
        if len(vec) < 3:
            continue
        X.append(vec)
        y.append(1 if row["label_move_pct"] > 0 else 0)
    return X, y


def train(store: Store, model_path: Path = MODEL_PATH) -> dict[str, Any]:
    X, y = build_dataset(store)
    n = len(X)
    status: dict[str, Any] = {"rows": n, "min_rows": MIN_TRAIN_ROWS,
                              "advisory_target": ADVISORY_TARGET_ROWS}
    if n < MIN_TRAIN_ROWS or len(set(y)) < 2:
        status.update(trained=False, reason=(
            f"accumulating dataset ({n}/{MIN_TRAIN_ROWS} usable labeled rows"
            + ("" if len(set(y)) >= 2 or n == 0 else ", single-class so far") + ")"))
        store.meta_set("ml_status", json.dumps(status))
        return status

    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    keys = [k for k in NUMERIC_KEYS if sum(k in x for x in X) >= n * 0.5]
    mat = np.array([[x.get(k, math.nan) for k in keys] for x in X])
    col_mean = np.nanmean(mat, axis=0)
    idx = np.where(np.isnan(mat))
    mat[idx] = np.take(col_mean, idx[1])
    col_std = mat.std(axis=0)
    col_std[col_std == 0] = 1.0
    mat = (mat - col_mean) / col_std

    clf = LogisticRegression(max_iter=1000, C=1.0)
    folds = min(5, n // 5) if n >= 10 else 2
    cv = cross_val_score(clf, mat, np.array(y), cv=folds, scoring="accuracy")
    clf.fit(mat, np.array(y))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model = {
        "keys": keys,
        "mean": col_mean.tolist(),
        "std": col_std.tolist(),
        "coef": clf.coef_[0].tolist(),
        "intercept": float(clf.intercept_[0]),
        "rows": n,
        "base_rate_up": round(sum(y) / n, 3),
        "cv_accuracy": round(float(cv.mean()), 3),
        "cv_folds": folds,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    model_path.write_text(json.dumps(model, indent=1))
    status.update(trained=True, cv_accuracy=model["cv_accuracy"],
                  base_rate_up=model["base_rate_up"], keys=keys)
    store.meta_set("ml_status", json.dumps(status))
    return status


def predict(features: dict, conviction: float | None = None,
            model_path: Path = MODEL_PATH) -> dict[str, Any]:
    if not model_path.exists():
        return {"available": False,
                "reason": "model not trained yet — dataset still accumulating"}
    model = json.loads(model_path.read_text())
    vec = extract_features(features, conviction)
    z = model["intercept"]
    used, missing = [], []
    for k, mean, std, w in zip(model["keys"], model["mean"], model["std"], model["coef"]):
        if k in vec:
            z += w * ((vec[k] - mean) / std)
            used.append(k)
        else:
            missing.append(k)  # imputed at the mean → contributes 0
    prob_up = 1.0 / (1.0 + math.exp(-z))
    below_base = model["cv_accuracy"] <= model["base_rate_up"]
    return {
        "available": True,
        "prob_up": round(prob_up, 3),
        "advisory_only": model["rows"] < ADVISORY_TARGET_ROWS or below_base,
        "quality": ("BELOW BASE RATE — the model currently predicts direction "
                    "worse than always guessing the majority class; treat this "
                    "output as noise and give it ZERO weight in your decision"
                    if below_base else "above base rate"),
        "model": {"rows": model["rows"], "cv_accuracy": model["cv_accuracy"],
                  "base_rate_up": model["base_rate_up"],
                  "trained_at": model["trained_at"]},
        "features_used": used,
        "features_missing": missing,
    }


def brief_status(store: Store, model_path: Path = MODEL_PATH) -> str:
    if model_path.exists():
        m = json.loads(model_path.read_text())
        if m["cv_accuracy"] <= m["base_rate_up"]:
            tag = "BELOW BASE RATE — treat as noise"
        elif m["rows"] < ADVISORY_TARGET_ROWS:
            tag = "ADVISORY"
        else:
            tag = "active"
        return (f"trained ({tag}): {m['rows']} rows, CV accuracy "
                f"{m['cv_accuracy']:.0%} vs base rate {m['base_rate_up']:.0%}, "
                f"as of {m['trained_at']}")
    raw = store.meta_get("ml_status", "")
    if raw:
        try:
            s = json.loads(raw)
            return s.get("reason", "accumulating dataset")
        except json.JSONDecodeError:
            pass
    return f"untrained — accumulating dataset (target {MIN_TRAIN_ROWS} labeled rows)"
