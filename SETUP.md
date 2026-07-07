# SETUP.md — bringing this system up on a (new) Mac

Everything needed to run agentic-earnings-trading from scratch or migrate it
to another MacBook. The repo travels via git; **the state does not** — see §5.

## 1. Prerequisites

- macOS 13+ (launchd + ScreenCaptureKit-era; Apple Silicon or Intel fine)
- Python 3.12 — `brew install python@3.12`
- git + the `gh` CLI (`brew install gh`, then `gh auth login`)
- **Claude Code CLI** installed and logged in (Max plan; `claude` once,
  interactively). The launcher shells `claude -p` — no API key is used.
- A Robinhood account with a brokerage account that is
  **agentic-enabled for this Claude login** (`agentic_allowed=true` in
  `get_accounts`) — currently ••••8223 "Agentic" (cash).

## 2. Repo + Python environment

```bash
mkdir -p ~/code && cd ~/code
gh repo clone vuolo/agentic-earnings-trading agentic-trading
cd agentic-trading
python3.12 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -e ".[dev]"   # [dev] matters: pytest lives there
python -m pytest -q        # all tests must pass before anything else
```

⚠️ Keep the repo OUT of iCloud-synced paths (~/Documents, ~/Desktop):
iCloud can evict files to dataless stubs, which kills launchd jobs with
errno 11. Our plists set `MaterializeDatalessFiles` to survive this, but a
non-synced location is calmer - since 2026-07-07 the canonical home is
`~/code/agentic-trading` (symlink left at the old ~/Documents/GitHub path).
If you must run synced, consider `brctl download .venv` after big installs.
After ANY relocation: rebuild the venv with `[dev]`, reinstall the plists
(`python -m orchestrator.schedule install`), migrate the Claude project
memory dir (keyed by absolute path under ~/.claude/projects/), and run the
§6 defanged validation.

## 3. Robinhood MCP OAuth

1. Open Claude Code in the repo — it will offer the project-scoped
   `robinhood-trading` server from `.mcp.json`; approve it.
2. Run `/mcp` → complete the Robinhood OAuth login.
3. Headless runs (`claude -p`) reuse this OAuth automatically (verified
   2026-07-05). Re-login here if agents ever start failing auth.

## 4. Account designation + broker prerequisites

```bash
python -m orchestrator.main set-account 758818223   # the agentic account
```

Broker-side requirements on that account (each one has burned us / would):
- `agentic_allowed=true` for THIS Claude login (per-agent flag).
- **Investor profile completed** — Robinhood blocks the account's second
  trade until the questionnaire is done. If you see *"answer some questions
  about your investing goals"*, finish it at:
  `https://applink.robinhood.com/investment_profile?account_number=<ACCT>`
- Cash in the account (buying power = settled cash only; T+1 settlement —
  see POLICY.md's capital-cycle note).

## 5. State migration (old Mac → new Mac) — gitignored, must be copied

| Path | What it is | If lost |
|---|---|---|
| `datasets/earnings.sqlite3` | **THE dataset**: events, decisions, outcomes, backtests, training rows, meta (account, gates, health) | Irreplaceable history; decisions/outcomes cannot be reconstructed. Copy it. |
| `models/model.json` | current ML model | Regenerates on next morning tick — losing it is fine |
| `.arm-live.json` | live-trading arm switch | Re-arm deliberately (see §7); do NOT copy casually |
| `logs/` | run history | optional |

```bash
# on the old Mac
rsync -a datasets models user@newmac:~/…/agentic-earnings-trading/
```

Fresh start instead (no migration): the store self-creates; then bootstrap
with `scout`, `backtest` (universe), and `ml-backfill` runs — expect an
evening of agent time and an empty decision history.

## 6. Scheduling (launchd) — with mandatory validation

```bash
python -m orchestrator.schedule install    # com.earnings.daily (09:24/15:40/16:20/16:50 ET)
                                           # + com.earnings.caffeinate (06:57/06:58 weekdays)
pmset -g sched                             # check existing wake events first!
sudo pmset repeat wakeorpoweron MTWRFSU 06:50:00   # only if nothing already wakes the Mac
# ⚠ the caffeinate agent's fire times must land ~2min AFTER the wake event —
# if the wake time changes, update _caffeinate_plist() and reinstall
# (2026-07-06: wake moved 07:55→06:55; caffeinate re-anchored to 06:57/06:58)
```

Machine conditions at fire times: **awake** (caffeinate handles 06:57–~17:14
once the morning wake happens), **logged in** (lock screen is fine; logout is
not), **plugged in**, auto-restart for OS updates disabled. Timezone must be
US/Eastern (fire times are local).

**Rule (ARCHITECTURE §8, learned the hard way): validate under REAL launchd,
never just a shell test.** With the system disarmed (or on a weekend):

```bash
launchctl kickstart -k gui/$(id -u)/com.earnings.daily
tail -f ~/Library/Logs/earnings/launchd_stdout.log            # expect a clean phase run,
grep -E "errno=11|not found" ~/Library/Logs/earnings/launchd_stderr.log   # …and nothing here
```

**If the system is ARMED and it's a weekday** (validated 2026-07-07): defang
by temporarily appending `--phase evening --dry-run` to the plist's
ProgramArguments (plistlib, not hand-editing), `launchctl bootout` +
`bootstrap` to reload, kickstart, confirm a clean "DRY RUN ... tick complete"
in stdout and an empty stderr, then restore with
`python -m orchestrator.schedule install` and verify the args are canonical
again. Do it outside tick windows; never disarm/re-arm just to validate
(re-arming is an operator act).

The first interactive-shell-passing, launchd-failing bug here was a PATH
symlink issue that only a real fire exposed. Repeat this check after ANY
schedule/plist/PATH change.

## 7. Arming live trading (operator decision, every time)

```bash
python -m orchestrator.main status                     # review state first
python -m orchestrator.main arm-live --per-position 250 --daily 450 --days 30 --confirm
python -m orchestrator.main disarm                     # instant kill, anytime
```

⚠️ **Never run the schedule armed on two machines at once** — two morning
ticks means duplicate real orders. Migrating: `python -m orchestrator.schedule
uninstall` + `disarm` on the OLD machine BEFORE installing on the new one.

## 8. Verify end-to-end

```bash
python -m orchestrator.main status    # context pack: mode, account, ML, events
python -m orchestrator.main report    # operator briefing
python -m orchestrator.daily --phase morning --dry-run    # tick plan, no agents
python -m orchestrator.main monitor   # 1 cheap agent: snapshot + RECONCILE: OK
```

If `monitor` returns exit 0 with a real balance and `RECONCILE: OK`, the full
chain works: launchd context → claude CLI → Robinhood OAuth → gateway → store.

## 9. Ongoing operation

- Read `reports/BRIEFING.md` (auto-committed every morning tick).
- Steer via `DIRECTIVES.md` (agents read it every run).
- Arm expiry: the briefing warns 7 days out; re-arming is always manual.
- Commands reference: `CLAUDE.md`. Design + dated findings: `ARCHITECTURE.md`.
