"""Run configuration: mode, risk limits, universe, policy version.

Everything is env-overridable (EARNINGS_*) so the orchestrator can pass
configuration down to the gateway MCP server process — the same pattern the
launcher uses for role authorization. Defaults are the safe ones.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Starting universe: AI / data-center infrastructure names (POLICY.md mirrors this).
DEFAULT_UNIVERSE = (
    "NVDA", "AMD", "AVGO", "TSM", "MU", "SMCI", "DELL", "HPE",
    "VRT", "ANET", "MRVL", "COHR", "CRDO", "ALAB", "ORCL",
)

# Non-tradeable megacaps whose earnings move the whole AI complex — tracked
# for macro context only (the risk gate blocks trading them regardless).
DEFAULT_MACRO_WATCH = ("MSFT", "GOOGL", "META", "AMZN", "AAPL")

# Market-wide expansion (2026-07-05): names outside the core universe are
# tradeable only when their event passes the liquidity screen the scout
# records (enforced server-side by the risk gate).
SCREEN_MIN_PRICE = 5.0            # no sub-$5 names
SCREEN_MIN_AVG_VOLUME = 500_000   # shares/day


@dataclass(frozen=True)
class RiskLimits:
    max_position_usd: float = 1_000.0
    max_daily_new_exposure_usd: float = 2_500.0
    max_open_positions: int = 5


@dataclass(frozen=True)
class Config:
    mode: str = "paper"  # v1: RiskGate rejects anything but "paper"
    db_path: Path = REPO_ROOT / "datasets" / "earnings.sqlite3"
    policy_version: str = "0.1.0"
    universe: tuple[str, ...] = DEFAULT_UNIVERSE
    macro_watch: tuple[str, ...] = DEFAULT_MACRO_WATCH
    limits: RiskLimits = field(default_factory=RiskLimits)

    @classmethod
    def from_env(cls) -> "Config":
        env = os.environ
        universe = DEFAULT_UNIVERSE
        if env.get("EARNINGS_UNIVERSE"):
            universe = tuple(
                s.strip().upper() for s in env["EARNINGS_UNIVERSE"].split(",") if s.strip()
            )
        macro_watch = DEFAULT_MACRO_WATCH
        if env.get("EARNINGS_MACRO_WATCH"):
            macro_watch = tuple(
                s.strip().upper() for s in env["EARNINGS_MACRO_WATCH"].split(",") if s.strip()
            )
        limits = RiskLimits(
            max_position_usd=float(env.get("EARNINGS_MAX_POSITION_USD", 1_000.0)),
            max_daily_new_exposure_usd=float(env.get("EARNINGS_MAX_DAILY_USD", 2_500.0)),
            max_open_positions=int(env.get("EARNINGS_MAX_OPEN_POSITIONS", 5)),
        )
        mode = env.get("EARNINGS_MODE", "").strip().lower()
        if not mode:
            # Single source of truth for live: the operator's arm switch.
            from . import arming
            mode = "live" if arming.arm_status()[0] else "paper"
        return cls(
            mode=mode,
            db_path=Path(env.get("EARNINGS_DB", str(cls.db_path))),
            policy_version=env.get("EARNINGS_POLICY_VERSION", "0.1.0"),
            universe=universe,
            macro_watch=macro_watch,
            limits=limits,
        )
