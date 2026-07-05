# agentic-earnings-trading

Claude-orchestrated trading around earnings events (BMO/AMC), starting with an
AI / data-center stock universe. Agent analysts gather statistics, indicators,
and sentiment through the [Robinhood MCP server](https://agent.robinhood.com/mcp/trading);
a **server-side risk gate** decides whether proposed trades are accepted; every
decision is recorded with its full feature snapshot so the dataset can train an
ML sidecar that eventually becomes the primary signal source.

The system is a **breathing loop**: a daily tick (launchd) runs scout →
labeler → analyst → executor → strategist. It labels its own outcomes
(including pass counterfactuals) and the strategist revises the versioned
trading policy from the evidence — git-committed, audit-trailed. **Live
trading is disarmed by default**: real orders happen only while the operator's
time-boxed arm switch (`arm-live --confirm`) is active, under caps enforced in
code that no agent or policy text can change. See `ARCHITECTURE.md` for the
full design; `CLAUDE.md` for the working rules.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q                      # engine tests

python -m orchestrator.main status       # current context pack (no agent)
python -m orchestrator.main scout        # agent: sync earnings calendar
python -m orchestrator.main analyze NVDA # agent: analyze one event, submit decision
python -m orchestrator.main close NVDA --price 187.50   # label a paper outcome
```

Agent runs use headless Claude Code (`claude -p`) on your existing login, and
require the Robinhood MCP OAuth to have been completed once via `/mcp` in
Claude Code.

## Layout

- `engine/` — deterministic core: config, risk gate, SQLite store, context pack
- `gateway/` — local MCP server agents submit through (risk gate lives here)
- `orchestrator/` — role launcher (`claude -p`) + CLI
- `prompts/` — versioned trading policy + role missions
- `datasets/` — decisions/outcomes SQLite (gitignored; the future training set)
