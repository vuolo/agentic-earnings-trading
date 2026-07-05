"""The arm switch — the single release lever for live trading.

Live mode exists only while a valid, unexpired `.arm-live.json` sits at the
repo root. It is written exclusively by the operator via
`python -m orchestrator.main arm-live --confirm` and is gitignored. No agent
has any tool that can create or modify it; the strategist can rewrite trading
policy but can never touch this file or the engine caps.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARM_PATH = REPO_ROOT / ".arm-live.json"

_FIELDS = ("per_position_cap_usd", "daily_cap_usd", "expires", "armed_at")


@dataclass(frozen=True)
class Arm:
    per_position_cap_usd: float
    daily_cap_usd: float
    expires: str  # YYYY-MM-DD, inclusive
    armed_at: str


def arm_status() -> tuple[Arm | None, str]:
    """Return (arm, "armed") when live trading is armed, else (None, why)."""
    if not ARM_PATH.exists():
        return None, "not armed"
    try:
        data = json.loads(ARM_PATH.read_text())
        arm = Arm(**{k: data[k] for k in _FIELDS})
        expires = date.fromisoformat(arm.expires)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
        return None, f"arm file invalid ({e})"
    if expires < date.today():
        return None, f"arm expired {arm.expires}"
    return arm, "armed"


def arm(per_position_cap_usd: float, daily_cap_usd: float, days: int) -> Arm:
    a = Arm(
        per_position_cap_usd=float(per_position_cap_usd),
        daily_cap_usd=float(daily_cap_usd),
        expires=(date.today() + timedelta(days=days)).isoformat(),
        armed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    ARM_PATH.write_text(json.dumps(asdict(a), indent=2) + "\n")
    return a


def disarm() -> bool:
    if ARM_PATH.exists():
        ARM_PATH.unlink()
        return True
    return False
