"""SQLite store: earnings events, agent decisions (+feature snapshots), outcomes.

This is the dataset the ML sidecar will train on — decisions join outcomes on
decision_id. All timestamps are UTC ISO-8601; the daily risk budget uses the
UTC day.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
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
    status         TEXT NOT NULL CHECK (status IN ('pass', 'rejected', 'open_paper', 'closed_paper')),
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    id          INTEGER PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES decisions(id),
    exit_price  REAL,
    move_pct    REAL,
    pnl_usd     REAL,
    notes       TEXT,
    labeled_at  TEXT NOT NULL
);
"""


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
        self._db.executescript(_SCHEMA)
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
                   timing = excluded.timing,
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

    def open_positions(self) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM decisions WHERE status = 'open_paper' ORDER BY created_at"
        ).fetchall()

    def open_position_for(self, symbol: str) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT * FROM decisions WHERE status = 'open_paper' AND symbol = ?",
            (symbol.strip().upper(),),
        ).fetchone()

    def today_new_exposure(self) -> float:
        row = self._db.execute(
            """SELECT COALESCE(SUM(size_usd), 0) AS total FROM decisions
               WHERE status IN ('open_paper', 'closed_paper')
                 AND substr(created_at, 1, 10) = ?""",
            (_today(),),
        ).fetchone()
        return float(row["total"])

    def decisions_for_event(self, event_id: int) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM decisions WHERE event_id = ?", (event_id,)
        ).fetchall()

    def due_closes(self, today: str) -> list[sqlite3.Row]:
        """Open paper positions whose event report date has passed — the
        reaction day is over (bmo: report day itself; amc: the day after), so
        they are due for T+1 close-out and outcome labeling."""
        return self._db.execute(
            """SELECT d.*, e.report_date, e.timing FROM decisions d
               JOIN events e ON e.id = d.event_id
               WHERE d.status = 'open_paper' AND e.report_date < ?
               ORDER BY e.report_date, d.symbol""",
            (today,),
        ).fetchall()

    def recent_decisions(self, limit: int = 5) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    # -- paper close / outcome labeling --------------------------------------

    def close_position(
        self, symbol: str, exit_price: float, notes: str = ""
    ) -> dict[str, Any] | None:
        """Close the open paper position for `symbol` and record its outcome.

        P&L uses a delta-one proxy on the underlying (ARCHITECTURE §4):
        long_equity is +1x notional, bearish_option is -1x notional.
        """
        pos = self.open_position_for(symbol)
        if pos is None:
            return None
        entry = float(pos["entry_price"] or 0)
        if entry <= 0 or exit_price <= 0:
            return None
        sign = 1.0 if pos["action"] == "long_equity" else -1.0
        qty = float(pos["size_usd"]) / entry
        pnl = sign * qty * (exit_price - entry)
        move_pct = (exit_price - entry) / entry * 100.0
        self._db.execute(
            """INSERT INTO outcomes (decision_id, exit_price, move_pct, pnl_usd, notes, labeled_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (pos["id"], exit_price, move_pct, pnl, notes, _now()),
        )
        self._db.execute(
            "UPDATE decisions SET status = 'closed_paper' WHERE id = ?", (pos["id"],)
        )
        self._db.commit()
        return {
            "decision_id": int(pos["id"]),
            "symbol": pos["symbol"],
            "action": pos["action"],
            "entry_price": entry,
            "exit_price": exit_price,
            "move_pct": move_pct,
            "pnl_usd": pnl,
        }
