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
    limits: RiskLimits = field(default_factory=RiskLimits)

    @classmethod
    def from_env(cls) -> "Config":
        env = os.environ
        universe = DEFAULT_UNIVERSE
        if env.get("EARNINGS_UNIVERSE"):
            universe = tuple(
                s.strip().upper() for s in env["EARNINGS_UNIVERSE"].split(",") if s.strip()
            )
        limits = RiskLimits(
            max_position_usd=float(env.get("EARNINGS_MAX_POSITION_USD", 1_000.0)),
            max_daily_new_exposure_usd=float(env.get("EARNINGS_MAX_DAILY_USD", 2_500.0)),
            max_open_positions=int(env.get("EARNINGS_MAX_OPEN_POSITIONS", 5)),
        )
        return cls(
            mode=env.get("EARNINGS_MODE", "paper").strip().lower(),
            db_path=Path(env.get("EARNINGS_DB", str(cls.db_path))),
            policy_version=env.get("EARNINGS_POLICY_VERSION", "0.1.0"),
            universe=universe,
            limits=limits,
        )
