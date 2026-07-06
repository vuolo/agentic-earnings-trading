"""RiskGate — the enforced capital rules (ARCHITECTURE §1.1).

Runs server-side inside the gateway MCP process. The agent cannot argue with,
soften, or bypass these checks; a rejection is recorded and final for that
submission. Prompts may *repeat* the policy for quality, but this is where it
is enforced.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .store import Store

VALID_ACTIONS = ("long_equity", "short_equity", "bearish_option", "pass")
TRADE_ACTIONS = ("long_equity", "short_equity", "bearish_option")


@dataclass(frozen=True)
class DecisionRequest:
    symbol: str
    action: str
    size_usd: float
    conviction: float | None = None


@dataclass(frozen=True)
class Verdict:
    approved: bool
    reasons: tuple[str, ...] = ()

    def __str__(self) -> str:
        return "approved" if self.approved else "rejected: " + "; ".join(self.reasons)


class RiskGate:
    def __init__(self, cfg: Config, store: Store):
        self.cfg = cfg
        self.store = store

    def evaluate(self, req: DecisionRequest) -> Verdict:
        reasons: list[str] = []
        limits = self.cfg.limits
        symbol = req.symbol.strip().upper()

        # Effective caps: engine caps, tightened by the arm file in live mode.
        pos_cap = limits.max_position_usd
        daily_cap = limits.max_daily_new_exposure_usd
        if self.cfg.mode == "live":
            from . import arming
            arm, why = arming.arm_status()
            if arm is None:
                reasons.append(
                    f"live mode requested but {why} — the operator must run "
                    "`python -m orchestrator.main arm-live --confirm`"
                )
            else:
                pos_cap = min(pos_cap, arm.per_position_cap_usd)
                daily_cap = min(daily_cap, arm.daily_cap_usd)
        elif self.cfg.mode != "paper":
            reasons.append(f"unknown mode '{self.cfg.mode}'")
        if req.action not in TRADE_ACTIONS:
            reasons.append(f"action '{req.action}' is not a tradeable action")
        if req.action == "short_equity" and self.store.meta_get("short_capable", "") != "1":
            reasons.append(
                "short_equity requires operator-verified shorting "
                "(`enable-shorting` after a successful broker probe) — "
                "margin/broker support is unconfirmed"
            )
        if self.cfg.universe and symbol not in self.cfg.universe:
            # Market-wide expansion: non-core names are tradeable ONLY when
            # their upcoming event passed the scout's liquidity screen.
            event = self.store.upcoming_event_for(symbol)
            if event is None:
                reasons.append(
                    f"{symbol} is outside the core universe and has no "
                    "recorded upcoming event"
                )
            elif not event["screened"]:
                reasons.append(
                    f"{symbol} is outside the core universe and its event "
                    "has not passed the liquidity screen (price/volume/"
                    "tradability recorded by the scout)"
                )
        if req.size_usd <= 0:
            reasons.append("size_usd must be positive")
        elif req.size_usd > pos_cap:
            reasons.append(
                f"size ${req.size_usd:,.2f} exceeds per-position cap ${pos_cap:,.2f}"
            )
        if req.conviction is not None and not (0.0 <= req.conviction <= 1.0):
            reasons.append("conviction must be within [0, 1]")

        if self.store.open_position_for(symbol) is not None:
            reasons.append(f"an open paper position already exists for {symbol}")
        if len(self.store.open_positions()) >= limits.max_open_positions:
            reasons.append(f"max open positions ({limits.max_open_positions}) reached")

        used = self.store.today_new_exposure()
        if req.size_usd > 0 and used + req.size_usd > daily_cap:
            reasons.append(
                f"daily new-exposure budget exceeded: ${used:,.2f} used + "
                f"${req.size_usd:,.2f} > ${daily_cap:,.2f}"
            )

        return Verdict(approved=not reasons, reasons=tuple(reasons))
