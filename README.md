# agentic-earnings-trading

Claude-orchestrated, real-money trading around earnings events, market-wide,
via the [Robinhood MCP server](https://agent.robinhood.com/mcp/trading).
Agent analysts build server-computed feature snapshots (indicators, implied
move, backtest gap stats, web sentiment, ML advisory, per-symbol playbook);
a **server-side risk gate** has the final word; an executor trades only while
the operator's time-boxed **arm switch** is on.

The system **breathes**: four launchd ticks a day (09:24 auction exits →
15:40 entries → 16:20/16:50 exit-queueing + disaster valve) run scout /
analyst / executor / labeler / monitor agents; every decision, pass
counterfactual, and realized event feeds SQLite; the **ML sidecar retrains
daily** (plus reconstructed historical rows); a **strategist** revises the
trading policy and playbook itself — validated, version-bumped,
git-committed. The operator reads `reports/BRIEFING.md` (auto-committed
daily) and steers via `DIRECTIVES.md`.

Strategy (evidence-locked — see `reports/research/`): enter 15:45–15:58 ET
before the print (AMC same day, BMO the prior day), hold through the
overnight reaction, exit in the next 9:30 **opening auction** (pre-queued at
the broker, crash-proof). Core AI/data-center names at full sizing; any other
earnings name only through a gate-enforced liquidity screen.

See `ARCHITECTURE.md` for the full design and dated findings; `CLAUDE.md`
for working rules and the command list; **`SETUP.md` to bring the system up
on a new machine** (state in `datasets/` is gitignored — migration matters).

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q                       # 63 tests

python -m orchestrator.main status        # context pack
python -m orchestrator.main report        # operator briefing
python -m orchestrator.schedule install   # launchd ticks + caffeinate
python -m orchestrator.main arm-live --per-position 250 --daily 450 --days 30 --confirm
```

Agent runs use headless Claude Code (`claude -p`) on the operator's login —
Robinhood MCP OAuth must be completed once via `/mcp` in Claude Code.
