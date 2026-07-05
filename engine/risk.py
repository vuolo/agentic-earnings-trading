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

VALID_ACTIONS = ("long_equity", "bearish_option", "pass")
TRADE_ACTIONS = ("long_equity", "bearish_option")


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

        if self.cfg.mode != "paper":
            reasons.append(
                f"mode '{self.cfg.mode}' is not permitted — v1 is paper-only (Phase 5 gates live)"
            )
        if req.action not in TRADE_ACTIONS:
            reasons.append(f"action '{req.action}' is not a tradeable action")
        if self.cfg.universe and symbol not in self.cfg.universe:
            reasons.append(f"{symbol} is outside the configured universe")
        if req.size_usd <= 0:
            reasons.append("size_usd must be positive")
        elif req.size_usd > limits.max_position_usd:
            reasons.append(
                f"size ${req.size_usd:,.2f} exceeds per-position cap ${limits.max_position_usd:,.2f}"
            )
        if req.conviction is not None and not (0.0 <= req.conviction <= 1.0):
            reasons.append("conviction must be within [0, 1]")

        if self.store.open_position_for(symbol) is not None:
            reasons.append(f"an open paper position already exists for {symbol}")
        if len(self.store.open_positions()) >= limits.max_open_positions:
            reasons.append(f"max open positions ({limits.max_open_positions}) reached")

        used = self.store.today_new_exposure()
        if req.size_usd > 0 and used + req.size_usd > limits.max_daily_new_exposure_usd:
            reasons.append(
                f"daily new-exposure budget exceeded: ${used:,.2f} used + "
                f"${req.size_usd:,.2f} > ${limits.max_daily_new_exposure_usd:,.2f}"
            )

        return Verdict(approved=not reasons, reasons=tuple(reasons))
