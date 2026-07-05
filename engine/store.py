"""SQLite store: earnings events, agent decisions (+feature snapshots), outcomes.

This is the dataset the ML sidecar will train on — decisions join outcomes on
decision_id. All timestamps are UTC ISO-8601; the daily risk budget uses the
UTC day.

Decision lifecycle:
    pass          → labeled later with a counterfactual outcome (pnl 0)
    rejected      → terminal (risk gate said no)
    open_paper    → closed_paper  (paper broker; also bearish legs in live mode)
    pending_live  → open_live → closed_live   (executor agent, armed only)
    pending_live  → exec_failed                (execution failed; detail kept)
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = (
    "pass", "rejected", "open_paper", "closed_paper",
    "pending_live", "open_live", "closed_live", "exec_failed",
)

_DECISIONS_SQL = """
CREATE TABLE IF NOT EXISTS decisions (
    id             INTEGER PRIMARY KEY,
    event_id       INTEGER REFERENCES events(id),
    symbol         TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    action         TEXT NOT NULL CHECK (action IN ('long_equity', 'bearish_option', 'pass')),
    size_usd       REAL NOT NULL DEFAULT 0,
    entry_price    REAL,
    conviction     REAL,
    thesis         TEXT,
    features       TEXT,
    risk_verdict   TEXT NOT NULL,
    status         TEXT NOT NULL,
    exec_detail    TEXT,
    created_at     TEXT NOT NULL
);
"""

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY,
    symbol      TEXT NOT NULL,
    report_date TEXT NOT NULL,
    timing      TEXT NOT NULL DEFAULT 'unknown' CHECK (timing IN ('bmo', 'amc', 'unknown')),
    source      TEXT NOT NULL DEFAULT 'robinhood',
    raw         TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE (symbol, report_date)
);

{_DECISIONS_SQL}

CREATE TABLE IF NOT EXISTS outcomes (
    id          INTEGER PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES decisions(id),
    exit_price  REAL,
    move_pct    REAL,
    pnl_usd     REAL,
    notes       TEXT,
    labeled_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Exposure counts everything that consumed (or is consuming) capital budget.
_BUDGET_STATUSES = "('open_paper', 'closed_paper', 'pending_live', 'open_live', 'closed_live')"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class Store:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(self.db_path))
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._migrate_v1_decisions()
        self._db.executescript(_SCHEMA)
        self._db.commit()

    def _migrate_v1_decisions(self) -> None:
        """v1 decisions had a status CHECK limited to the paper lifecycle;
        rebuild the table (v2 validates status in code) preserving rows."""
        row = self._db.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'decisions'"
        ).fetchone()
        if row is None or "status IN" not in row["sql"]:
            return
        cols = ("id, event_id, symbol, policy_version, action, size_usd, "
                "entry_price, conviction, thesis, features, risk_verdict, "
                "status, created_at")
        self._db.execute("ALTER TABLE decisions RENAME TO decisions_v1")
        self._db.executescript(_DECISIONS_SQL)
        self._db.execute(
            f"INSERT INTO decisions ({cols}) SELECT {cols} FROM decisions_v1"
        )
        self._db.execute("DROP TABLE decisions_v1")
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    # -- events ------------------------------------------------------------

    def upsert_event(
        self,
        symbol: str,
        report_date: str,
        timing: str = "unknown",
        source: str = "robinhood",
        raw: str | None = None,
    ) -> int:
        symbol = symbol.strip().upper()
        date.fromisoformat(report_date)  # validate YYYY-MM-DD
        if timing not in ("bmo", "amc", "unknown"):
            timing = "unknown"
        now = _now()
        self._db.execute(
            """INSERT INTO events (symbol, report_date, timing, source, raw, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (symbol, report_date) DO UPDATE SET
                   timing = CASE WHEN excluded.timing = 'unknown'
                                 THEN events.timing ELSE excluded.timing END,
                   source = excluded.source,
                   raw = COALESCE(excluded.raw, events.raw),
                   updated_at = excluded.updated_at""",
            (symbol, report_date, timing, source, raw, now, now),
        )
        self._db.commit()
        row = self._db.execute(
            "SELECT id FROM events WHERE symbol = ? AND report_date = ?",
            (symbol, report_date),
        ).fetchone()
        return int(row["id"])

    def upcoming_events(self, days: int = 14) -> list[sqlite3.Row]:
        start = _today()
        end = (date.fromisoformat(start) + timedelta(days=days)).isoformat()
        return self._db.execute(
            """SELECT * FROM events WHERE report_date BETWEEN ? AND ?
               ORDER BY report_date, symbol""",
            (start, end),
        ).fetchall()

    def get_event(self, symbol: str, report_date: str) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT * FROM events WHERE symbol = ? AND report_date = ?",
            (symbol.strip().upper(), report_date),
        ).fetchone()

    # -- decisions -----------------------------------------------------------

    def insert_decision(
        self,
        *,
        symbol: str,
        action: str,
        policy_version: str,
        risk_verdict: str,
        status: str,
        size_usd: float = 0.0,
        entry_price: float | None = None,
        conviction: float | None = None,
        thesis: str | None = None,
        features: str | None = None,
        event_id: int | None = None,
    ) -> int:
        if status not in VALID_STATUSES:
            raise ValueError(f"invalid status {status!r}")
        cur = self._db.execute(
            """INSERT INTO decisions
               (event_id, symbol, policy_version, action, size_usd, entry_price,
                conviction, thesis, features, risk_verdict, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, symbol.strip().upper(), policy_version, action, size_usd,
             entry_price, conviction, thesis, features, risk_verdict, status, _now()),
        )
        self._db.commit()
        return int(cur.lastrowid)

    def get_decision(self, decision_id: int) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT * FROM decisions WHERE id = ?", (decision_id,)
        ).fetchone()

    def open_positions(self) -> list[sqlite3.Row]:
        return self._db.execute(
            """SELECT * FROM decisions
               WHERE status IN ('open_paper', 'pending_live', 'open_live')
               ORDER BY created_at"""
        ).fetchall()

    def open_position_for(self, symbol: str) -> sqlite3.Row | None:
        return self._db.execute(
            """SELECT * FROM decisions
               WHERE status IN ('open_paper', 'pending_live', 'open_live')
                 AND symbol = ?""",
            (symbol.strip().upper(),),
        ).fetchone()

    def today_new_exposure(self) -> float:
        row = self._db.execute(
            f"""SELECT COALESCE(SUM(size_usd), 0) AS total FROM decisions
                WHERE status IN {_BUDGET_STATUSES}
                  AND substr(created_at, 1, 10) = ?""",
            (_today(),),
        ).fetchone()
        return float(row["total"])

    def decisions_for_event(self, event_id: int) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM decisions WHERE event_id = ?", (event_id,)
        ).fetchall()

    def recent_decisions(self, limit: int = 5) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    # -- close / outcome labeling ---------------------------------------------

    def due_closes(self, today: str) -> list[sqlite3.Row]:
        """Open paper positions whose event report date has passed — due for
        T+1 close-out and outcome labeling."""
        return self._db.execute(
            """SELECT d.*, e.report_date, e.timing FROM decisions d
               JOIN events e ON e.id = d.event_id
               WHERE d.status = 'open_paper' AND e.report_date < ?
               ORDER BY e.report_date, d.symbol""",
            (today,),
        ).fetchall()

    def due_live_closes(self, today: str) -> list[sqlite3.Row]:
        """Open LIVE positions whose event report date has passed — the
        executor must sell and report the real fill."""
        return self._db.execute(
            """SELECT d.*, e.report_date, e.timing FROM decisions d
               JOIN events e ON e.id = d.event_id
               WHERE d.status = 'open_live' AND e.report_date < ?
               ORDER BY e.report_date, d.symbol""",
            (today,),
        ).fetchall()

    def due_pass_labels(self, today: str) -> list[sqlite3.Row]:
        """Pass decisions whose event has passed and that have no outcome yet —
        due for counterfactual labeling (what would the trade have done)."""
        return self._db.execute(
            """SELECT d.*, e.report_date, e.timing FROM decisions d
               JOIN events e ON e.id = d.event_id
               LEFT JOIN outcomes o ON o.decision_id = d.id
               WHERE d.status = 'pass' AND e.report_date < ? AND o.id IS NULL
               ORDER BY e.report_date, d.symbol""",
            (today,),
        ).fetchall()

    def _record_outcome(
        self, decision: sqlite3.Row, exit_price: float, notes: str, new_status: str | None
    ) -> dict[str, Any]:
        entry = float(decision["entry_price"] or 0)
        move_pct = (exit_price - entry) / entry * 100.0 if entry > 0 else None
        if decision["action"] == "pass" or entry <= 0:
            pnl = 0.0
        else:
            sign = 1.0 if decision["action"] == "long_equity" else -1.0
            pnl = sign * (float(decision["size_usd"]) / entry) * (exit_price - entry)
        self._db.execute(
            """INSERT INTO outcomes (decision_id, exit_price, move_pct, pnl_usd, notes, labeled_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (decision["id"], exit_price, move_pct, pnl, notes, _now()),
        )
        if new_status is not None:
            self._db.execute(
                "UPDATE decisions SET status = ? WHERE id = ?",
                (new_status, decision["id"]),
            )
        self._db.commit()
        return {
            "decision_id": int(decision["id"]),
            "symbol": decision["symbol"],
            "action": decision["action"],
            "entry_price": entry if entry > 0 else None,
            "exit_price": exit_price,
            "move_pct": move_pct,
            "pnl_usd": pnl,
        }

    def close_position(
        self, symbol: str, exit_price: float, notes: str = ""
    ) -> dict[str, Any] | None:
        """Close the open PAPER position for `symbol`. P&L uses a delta-one
        proxy on the underlying (ARCHITECTURE §4)."""
        pos = self._db.execute(
            "SELECT * FROM decisions WHERE status = 'open_paper' AND symbol = ?",
            (symbol.strip().upper(),),
        ).fetchone()
        if pos is None or float(pos["entry_price"] or 0) <= 0 or exit_price <= 0:
            return None
        return self._record_outcome(pos, exit_price, notes, "closed_paper")

    def close_live(
        self, decision_id: int, exit_price: float, notes: str = ""
    ) -> dict[str, Any] | None:
        """Record the real exit fill for an open LIVE position."""
        pos = self.get_decision(decision_id)
        if pos is None or pos["status"] != "open_live" or exit_price <= 0:
            return None
        return self._record_outcome(pos, exit_price, notes, "closed_live")

    def label_pass(
        self, decision_id: int, exit_price: float, notes: str = ""
    ) -> dict[str, Any] | None:
        """Counterfactual outcome for a pass decision (pnl 0; move_pct only if
        the pass recorded a reference entry_price). Status stays 'pass'."""
        d = self.get_decision(decision_id)
        if d is None or d["status"] != "pass" or exit_price <= 0:
            return None
        if self._db.execute(
            "SELECT id FROM outcomes WHERE decision_id = ?", (decision_id,)
        ).fetchone():
            return None
        return self._record_outcome(d, exit_price, notes, None)

    # -- live execution -------------------------------------------------------

    def pending_executions(self) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM decisions WHERE status = 'pending_live' ORDER BY id"
        ).fetchall()

    def mark_execution(
        self, decision_id: int, *, filled: bool,
        fill_price: float | None = None, detail: str = "",
    ) -> sqlite3.Row | None:
        d = self.get_decision(decision_id)
        if d is None or d["status"] != "pending_live":
            return None
        if filled:
            if not fill_price or fill_price <= 0:
                return None
            self._db.execute(
                """UPDATE decisions SET status = 'open_live', entry_price = ?,
                   exec_detail = ? WHERE id = ?""",
                (fill_price, detail, decision_id),
            )
        else:
            self._db.execute(
                "UPDATE decisions SET status = 'exec_failed', exec_detail = ? WHERE id = ?",
                (detail, decision_id),
            )
        self._db.commit()
        return self.get_decision(decision_id)

    # -- meta / aggregates ------------------------------------------------------

    def meta_get(self, key: str, default: str = "") -> str:
        row = self._db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def meta_set(self, key: str, value: str) -> None:
        self._db.execute(
            """INSERT INTO meta (key, value) VALUES (?, ?)
               ON CONFLICT (key) DO UPDATE SET value = excluded.value""",
            (key, value),
        )
        self._db.commit()

    def outcome_count(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) AS n FROM outcomes").fetchone()["n"])

    def labeled_decisions(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._db.execute(
            """SELECT d.*, o.exit_price, o.move_pct AS outcome_move_pct,
                      o.pnl_usd, o.notes AS outcome_notes, o.labeled_at
               FROM decisions d JOIN outcomes o ON o.decision_id = d.id
               ORDER BY o.labeled_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def performance_summary(self) -> dict[str, Any]:
        db = self._db
        by_action = {
            r["action"]: r["n"]
            for r in db.execute(
                "SELECT action, COUNT(*) AS n FROM decisions GROUP BY action"
            )
        }
        trades = db.execute(
            """SELECT COUNT(*) AS n,
                      COALESCE(SUM(o.pnl_usd), 0) AS pnl,
                      COALESCE(SUM(o.pnl_usd > 0), 0) AS wins,
                      AVG(ABS(o.move_pct)) AS avg_abs_move
               FROM decisions d JOIN outcomes o ON o.decision_id = d.id
               WHERE d.status IN ('closed_paper', 'closed_live')"""
        ).fetchone()
        passes = db.execute(
            """SELECT COUNT(*) AS n, AVG(ABS(o.move_pct)) AS avg_abs_move
               FROM decisions d JOIN outcomes o ON o.decision_id = d.id
               WHERE d.action = 'pass'"""
        ).fetchone()
        return {
            "decisions_by_action": by_action,
            "closed_trades": int(trades["n"]),
            "wins": int(trades["wins"]),
            "total_pnl_usd": round(float(trades["pnl"]), 2),
            "avg_abs_move_pct_trades": trades["avg_abs_move"],
            "labeled_passes": int(passes["n"]),
            "avg_abs_move_pct_passes": passes["avg_abs_move"],
            "rejected": int(db.execute(
                "SELECT COUNT(*) AS n FROM decisions WHERE status = 'rejected'"
            ).fetchone()["n"]),
            "exec_failed": int(db.execute(
                "SELECT COUNT(*) AS n FROM decisions WHERE status = 'exec_failed'"
            ).fetchone()["n"]),
        }
