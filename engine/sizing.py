"""Dynamic position sizing — the account breathes with equity and conviction.

Server-computed (gateway tool `compute_position_size`) so the number the
analyst trades is deterministic and auditable; the RiskGate still enforces
every cap independently at submit time — this module recommends, the gate
rules (capital rules live in engine/, never in prompts).

The risk budget is a fraction of CURRENT equity placed against the adverse
move, scaled continuously by conviction:

    risk_pct = RISK_FLOOR_PCT + RISK_SLOPE_PCT * max(0, conviction - 0.5)
               (capped at RISK_CEIL_PCT)
    size_usd = equity * risk_pct/100 / (adverse_move_pct/100)

so a $500 account at conviction 0.55 against a 5% adverse move risks ~$5.6
and sizes ~$112; the same setup on a $1,000 account sizes ~$225 — growth
raises sizes automatically, drawdowns cut them. Wilder names (bigger adverse
move) size smaller for the same conviction; quiet names size up to the caps.

Haircuts (multiplicative): non-core screened names x0.75, overnight-through-
the-print entries x0.8.

Clamps, applied after haircuts and reported as the binding constraint:
per-position cap (engine, tightened by the arm file in live mode), 50% of
equity, buying power minus a $5 buffer, and the remaining daily new-exposure
budget. If the clamped size lands under MIN_SIZE_USD the tool recommends a
pass — a fill that small is fee-free but risk-noise, and "size floor
unreachable" is an explicit policy disqualifier.
"""

from __future__ import annotations

from typing import Any

RISK_FLOOR_PCT = 1.0   # % of equity at risk at conviction <= 0.5
RISK_SLOPE_PCT = 5.0   # additional % of equity per 1.0 of conviction above 0.5
RISK_CEIL_PCT = 3.0    # hard ceiling on % of equity at risk per trade
NONCORE_HAIRCUT = 0.75
OVERNIGHT_HAIRCUT = 0.8
BUYING_POWER_BUFFER_USD = 5.0
MAX_EQUITY_FRACTION = 0.5
MIN_SIZE_USD = 20.0  # fractional orders execute fine this small; below this
                     # the label is more rounding than signal


def dynamic_size(
    *,
    equity_usd: float,
    buying_power_usd: float,
    conviction: float,
    adverse_move_pct: float,
    pos_cap_usd: float,
    daily_remaining_usd: float,
    core: bool = True,
    overnight: bool = False,
) -> dict[str, Any]:
    """Compute the recommended size. Returns a dict meant to be embedded
    verbatim in features_json under "sizing"."""
    if not (0.0 <= conviction <= 1.0):
        return {"error": "conviction must be within [0, 1]"}
    if adverse_move_pct <= 0:
        return {"error": "adverse_move_pct must be positive — use "
                         "max(implied_move_pct, |historical gap tail|)"}
    if equity_usd <= 0 or buying_power_usd < 0:
        return {"error": "equity/buying power unavailable or non-positive"}

    risk_pct = min(RISK_FLOOR_PCT + RISK_SLOPE_PCT * max(0.0, conviction - 0.5),
                   RISK_CEIL_PCT)
    risk_usd = equity_usd * risk_pct / 100.0
    raw = risk_usd / (adverse_move_pct / 100.0)

    haircuts: list[str] = []
    if not core:
        raw *= NONCORE_HAIRCUT
        haircuts.append(f"non-core x{NONCORE_HAIRCUT}")
    if overnight:
        raw *= OVERNIGHT_HAIRCUT
        haircuts.append(f"overnight x{OVERNIGHT_HAIRCUT}")

    clamps = {
        "per_position_cap": pos_cap_usd,
        "half_equity": equity_usd * MAX_EQUITY_FRACTION,
        "buying_power": max(buying_power_usd - BUYING_POWER_BUFFER_USD, 0.0),
        "daily_budget_remaining": daily_remaining_usd,
    }
    binding = min(clamps, key=lambda k: clamps[k]) if clamps and min(clamps.values()) < raw else None
    size = min(raw, *clamps.values())

    out: dict[str, Any] = {
        "size_usd": round(max(size, 0.0), 2),
        "risk_pct_of_equity": round(risk_pct, 3),
        "risk_usd": round(risk_usd, 2),
        "adverse_move_pct": adverse_move_pct,
        "conviction": conviction,
        "raw_size_usd": round(raw, 2),
        "haircuts": haircuts,
        "binding_constraint": binding,
        "inputs": {
            "equity_usd": equity_usd,
            "buying_power_usd": buying_power_usd,
            "pos_cap_usd": pos_cap_usd,
            "daily_remaining_usd": round(daily_remaining_usd, 2),
            "core": core,
            "overnight": overnight,
        },
    }
    if out["size_usd"] < MIN_SIZE_USD:
        out["recommendation"] = "pass_below_floor"
        out["note"] = (f"clamped size ${out['size_usd']:.2f} is under the "
                       f"${MIN_SIZE_USD:.0f} floor — policy disqualifier (c); "
                       "submit a pass citing this sizing output")
    else:
        out["recommendation"] = "trade"
        out["max_loss_estimate_usd"] = round(out["size_usd"] * adverse_move_pct / 100.0, 2)
    return out
