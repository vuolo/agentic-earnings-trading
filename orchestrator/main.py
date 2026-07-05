"""CLI entry point.

    python -m orchestrator.main scout                  # sync earnings calendar
    python -m orchestrator.main analyze NVDA           # analyst run for one symbol
    python -m orchestrator.main status                 # print the context pack
    python -m orchestrator.main close NVDA --price 187.50 [--notes "T+1 open"]
"""

from __future__ import annotations

import argparse
import sys

from engine.config import Config
from engine.context import build_context_pack
from engine.store import Store

from . import launcher


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scout = sub.add_parser("scout", help="sync upcoming earnings into the store")
    p_scout.add_argument("--model", default=None)

    p_an = sub.add_parser("analyze", help="run the analyst for one symbol")
    p_an.add_argument("symbol")
    p_an.add_argument("--model", default=None)

    sub.add_parser("status", help="print the current context pack")

    p_report = sub.add_parser("report", help="print the operator briefing")
    p_report.add_argument("--write", action="store_true",
                          help="also write reports/BRIEFING.md")

    p_close = sub.add_parser("close", help="close an open paper position")
    p_close.add_argument("symbol")
    p_close.add_argument("--price", type=float, required=True)
    p_close.add_argument("--notes", default="")

    p_arm = sub.add_parser(
        "arm-live", help="ARM live trading (REAL MONEY) for a limited window"
    )
    p_arm.add_argument("--per-position", type=float, default=200.0,
                       help="live per-position cap in USD (default 200)")
    p_arm.add_argument("--daily", type=float, default=400.0,
                       help="live daily new-exposure cap in USD (default 400)")
    p_arm.add_argument("--days", type=int, default=7,
                       help="days until the arm auto-expires (default 7)")
    p_arm.add_argument("--confirm", action="store_true",
                       help="required: acknowledge real orders will be placed")

    sub.add_parser("disarm", help="disarm live trading immediately")

    p_bt = sub.add_parser("backtest", help="backfill historical earnings reactions")
    p_bt.add_argument("symbol", nargs="?", default="")
    p_bt.add_argument("--model", default=None)

    sub.add_parser("ml-train", help="(re)train the ML sidecar from the dataset")
    sub.add_parser("monitor", help="run the account monitor/reconciliation agent")

    args = parser.parse_args(argv)

    if args.cmd == "scout":
        return launcher.run_role("scout", model=args.model)
    if args.cmd == "analyze":
        return launcher.run_role("analyst", symbol=args.symbol.upper(), model=args.model)

    if args.cmd == "backtest":
        target = args.symbol.upper() if args.symbol else \
            "every symbol in the universe (see the context pack)"
        return launcher.run_role("backtester", symbol=target, model=args.model)
    if args.cmd == "monitor":
        return launcher.run_role("monitor")
    if args.cmd == "ml-train":
        import json as _json

        from engine import ml
        cfg0 = Config.from_env()
        store0 = Store(cfg0.db_path)
        try:
            print(_json.dumps(ml.train(store0), indent=1))
        finally:
            store0.close()
        return 0

    if args.cmd == "arm-live":
        from engine import arming
        if not args.confirm:
            print(
                "Refusing to arm without --confirm.\n\n"
                "Arming means the daily tick's executor places REAL orders on "
                "your Robinhood account for approved long_equity decisions, "
                f"capped at ${args.per_position:,.2f}/position and "
                f"${args.daily:,.2f}/day of new exposure, auto-expiring in "
                f"{args.days} day(s). Engine caps still apply on top.\n\n"
                "Re-run with --confirm to arm.",
                file=sys.stderr,
            )
            return 1
        a = arming.arm(args.per_position, args.daily, args.days)
        print(f"ARMED live trading until {a.expires} "
              f"(${a.per_position_cap_usd:,.2f}/position, ${a.daily_cap_usd:,.2f}/day). "
              "Disarm anytime: python -m orchestrator.main disarm")
        return 0
    if args.cmd == "disarm":
        from engine import arming
        print("disarmed" if arming.disarm() else "already disarmed")
        return 0

    import dataclasses

    cfg = Config.from_env()
    if "EARNINGS_POLICY_VERSION" not in __import__("os").environ:
        cfg = dataclasses.replace(
            cfg, policy_version=launcher.policy_text_and_version()[1]
        )
    store = Store(cfg.db_path)
    try:
        if args.cmd == "status":
            print(build_context_pack(cfg, store))
            return 0
        if args.cmd == "report":
            from .briefing import build_briefing
            text = build_briefing(cfg, store)
            print(text)
            if args.write:
                out = launcher.REPO_ROOT / "reports" / "BRIEFING.md"
                out.parent.mkdir(exist_ok=True)
                out.write_text(text)
                print(f"[written to {out}]")
            return 0
        if args.cmd == "close":
            result = store.close_position(args.symbol.upper(), args.price, args.notes)
            if result is None:
                print(f"no open paper position for {args.symbol.upper()}", file=sys.stderr)
                return 1
            print(
                f"closed #{result['decision_id']} {result['symbol']} {result['action']}: "
                f"{result['entry_price']} -> {result['exit_price']} "
                f"({result['move_pct']:+.2f}%), P&L ${result['pnl_usd']:+,.2f}"
            )
            return 0
    finally:
        store.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
