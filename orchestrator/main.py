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
    p_scout.add_argument("--model", default=launcher.DEFAULT_MODEL)

    p_an = sub.add_parser("analyze", help="run the analyst for one symbol")
    p_an.add_argument("symbol")
    p_an.add_argument("--model", default=launcher.DEFAULT_MODEL)

    sub.add_parser("status", help="print the current context pack")

    p_close = sub.add_parser("close", help="close an open paper position")
    p_close.add_argument("symbol")
    p_close.add_argument("--price", type=float, required=True)
    p_close.add_argument("--notes", default="")

    args = parser.parse_args(argv)

    if args.cmd == "scout":
        return launcher.run_role("scout", model=args.model)
    if args.cmd == "analyze":
        return launcher.run_role("analyst", symbol=args.symbol.upper(), model=args.model)

    cfg = Config.from_env()
    store = Store(cfg.db_path)
    try:
        if args.cmd == "status":
            print(build_context_pack(cfg, store))
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
