"""Deterministic indicator math (Phase 2) — pure functions over OHLCV bars.

Agents fetch raw bars via the Robinhood MCP and pass them to the gateway's
compute_indicators tool, which calls this module. The model never does the
arithmetic; these outputs go verbatim into feature snapshots (and therefore
into the ML training set), so they must stay deterministic and versioned.
"""

from __future__ import annotations

import json
import math
from typing import Any

FEATURE_VERSION = 1


def _get(bar: dict, *names: str) -> float | None:
    for n in names:
        v = bar.get(n)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


def parse_bars(bars_json: str | list) -> list[dict[str, float]]:
    """Accept whatever bar shape the MCP returns and normalize to OHLCV."""
    data = json.loads(bars_json) if isinstance(bars_json, str) else bars_json
    if isinstance(data, dict):
        for key in ("bars", "historicals", "results", "data_points", "candles", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError("could not find a list of bars in the input")
    out = []
    for b in data:
        if not isinstance(b, dict):
            continue
        close = _get(b, "close", "close_price", "c", "adjusted_close", "adj_close")
        if close is None or close <= 0:
            continue
        out.append({
            "open": _get(b, "open", "open_price", "o") or close,
            "high": _get(b, "high", "high_price", "h") or close,
            "low": _get(b, "low", "low_price", "l") or close,
            "close": close,
            "volume": _get(b, "volume", "v") or 0.0,
        })
    if len(out) < 30:
        raise ValueError(f"need at least 30 usable bars, got {len(out)}")
    return out


def sma(values: list[float], n: int) -> float:
    return sum(values[-n:]) / min(n, len(values))


def rsi(closes: list[float], n: int = 14) -> float | None:
    if len(closes) < n + 1:
        return None
    gains, losses = [], []
    for prev, cur in zip(closes[:-1], closes[1:]):
        change = cur - prev
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[:n]) / n
    avg_loss = sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):  # Wilder smoothing
        avg_gain = (avg_gain * (n - 1) + g) / n
        avg_loss = (avg_loss * (n - 1) + l) / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def atr_pct(bars: list[dict], n: int = 14) -> float | None:
    if len(bars) < n + 1:
        return None
    trs = []
    for prev, cur in zip(bars[:-1], bars[1:]):
        trs.append(max(
            cur["high"] - cur["low"],
            abs(cur["high"] - prev["close"]),
            abs(cur["low"] - prev["close"]),
        ))
    atr = sum(trs[:n]) / n
    for tr in trs[n:]:
        atr = (atr * (n - 1) + tr) / n
    return atr / bars[-1]["close"] * 100.0


def realized_vol_pct(closes: list[float], n: int = 20) -> float | None:
    if len(closes) < n + 1:
        return None
    rets = [math.log(c / p) for p, c in zip(closes[-n - 1:-1], closes[-n:])]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / len(rets)
    return math.sqrt(var) * math.sqrt(252) * 100.0


def volume_zscore(volumes: list[float], n: int = 20) -> float | None:
    if len(volumes) < n + 1 or not any(volumes[-n - 1:-1]):
        return None
    window = volumes[-n - 1:-1]
    mean = sum(window) / n
    var = sum((v - mean) ** 2 for v in window) / n
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (volumes[-1] - mean) / std


def compute(bars: list[dict], benchmark: list[dict] | None = None) -> dict[str, Any]:
    closes = [b["close"] for b in bars]
    volumes = [b["volume"] for b in bars]
    s20, s50 = sma(closes, 20), sma(closes, 50)
    if s20 > s50 * 1.005:
        trend = "rising"
    elif s20 < s50 * 0.995:
        trend = "falling"
    else:
        trend = "flat"
    hi, lo = max(closes), min(closes)
    out: dict[str, Any] = {
        "feature_version": FEATURE_VERSION,
        "bars_used": len(bars),
        "close": closes[-1],
        "sma20": round(s20, 4),
        "sma50": round(s50, 4),
        "trend": trend,
        "rsi14": None if (v := rsi(closes)) is None else round(v, 2),
        "atr14_pct": None if (v := atr_pct(bars)) is None else round(v, 2),
        "realized_vol20_pct": None if (v := realized_vol_pct(closes)) is None else round(v, 2),
        "volume_z20": None if (v := volume_zscore(volumes)) is None else round(v, 2),
        "pct_from_high": round((closes[-1] - hi) / hi * 100.0, 2),
        "pct_from_low": round((closes[-1] - lo) / lo * 100.0, 2),
    }
    if benchmark and len(benchmark) >= 21 and len(closes) >= 21:
        bench = [b["close"] for b in benchmark]
        stock_ret = (closes[-1] - closes[-21]) / closes[-21] * 100.0
        bench_ret = (bench[-1] - bench[-21]) / bench[-21] * 100.0
        out["rel_strength20_pct"] = round(stock_ret - bench_ret, 2)
    return out


def implied_move(underlying_price: float, call_mid: float, put_mid: float) -> dict[str, Any]:
    if underlying_price <= 0 or call_mid < 0 or put_mid < 0 or (call_mid + put_mid) == 0:
        raise ValueError("need positive underlying and non-zero straddle legs")
    straddle = call_mid + put_mid
    return {
        "straddle_mid": round(straddle, 4),
        "implied_move_pct": round(straddle / underlying_price * 100.0, 2),
        "implied_move_usd": round(straddle, 2),
        "underlying_price": underlying_price,
    }
