# experiment/db.py
# SQLite persistence layer for experiment runs.
# JSON files are fine for single runs, but once you have 50+ experiments
# you want to query across them — hence the DB.
# Schema is intentionally simple: runs + results, no ORM.

import sqlite3
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "experiments/sentinel.db"


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Create tables if they don't exist. Safe to call multiple times."""
    conn = _connect(db_path)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT NOT NULL UNIQUE,
                model       TEXT,
                provider    TEXT,
                created_at  TEXT NOT NULL,
                metadata    TEXT,   -- JSON blob
                summary     TEXT    -- JSON blob
            );

            CREATE TABLE IF NOT EXISTS results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          TEXT NOT NULL,
                prompt          TEXT,
                response        TEXT,
                category        TEXT,
                severity        INTEGER,
                safety_score    REAL,
                is_unsafe       INTEGER,  -- 0 or 1
                helpfulness     REAL,
                trustworthiness REAL,
                composite       REAL,
                latency_s       REAL,
                error           TEXT,
                raw             TEXT,     -- full JSON blob
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE INDEX IF NOT EXISTS idx_results_run_id ON results(run_id);
            CREATE INDEX IF NOT EXISTS idx_results_category ON results(category);
            CREATE INDEX IF NOT EXISTS idx_results_is_unsafe ON results(is_unsafe);
        """)
    conn.close()
    logger.debug(f"DB initialized at {db_path}")


class ExperimentDB:
    """
    Simple interface for storing and querying experiment data.

    Usage:
        db = ExperimentDB("experiments/sentinel.db")
        db.save_run(run_id, metadata, results, summary)
        rows = db.get_unsafe_results(run_id)
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def _conn(self) -> sqlite3.Connection:
        return _connect(self.db_path)

    def save_run(self, run_id: str, metadata: dict, results: list[dict], summary: dict):
        """Persist a complete experiment run."""
        conn = self._conn()
        try:
            with conn:
                conn.execute(
                    """INSERT OR REPLACE INTO runs
                       (run_id, model, provider, created_at, metadata, summary)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        metadata.get("model"),
                        metadata.get("provider", "openai"),
                        datetime.utcnow().isoformat(),
                        json.dumps(metadata),
                        json.dumps(summary),
                    ),
                )
                for r in results:
                    se = r.get("safety_eval", {})
                    ae = r.get("alignment_eval", {})
                    conn.execute(
                        """INSERT INTO results
                           (run_id, prompt, response, category, severity,
                            safety_score, is_unsafe, helpfulness, trustworthiness,
                            composite, latency_s, error, raw)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            run_id,
                            r.get("prompt", ""),
                            r.get("response", ""),
                            r.get("category", ""),
                            r.get("severity", 0),
                            se.get("safety_score"),
                            int(se.get("is_unsafe", False)),
                            ae.get("helpfulness"),
                            ae.get("trustworthiness"),
                            ae.get("composite_alignment"),
                            r.get("latency_s"),
                            r.get("error"),
                            json.dumps(r),
                        ),
                    )
        finally:
            conn.close()
        logger.info(f"Saved run {run_id} with {len(results)} results to DB.")

    def list_runs(self) -> list[dict]:
        """Return all runs ordered by creation time."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT run_id, model, provider, created_at FROM runs ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_summary(self, run_id: str) -> dict:
        conn = self._conn()
        row = conn.execute("SELECT summary FROM runs WHERE run_id=?", (run_id,)).fetchone()
        conn.close()
        return json.loads(row["summary"]) if row else {}

    def get_unsafe_results(self, run_id: str) -> list[dict]:
        """Fetch results flagged as unsafe for a given run."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM results WHERE run_id=? AND is_unsafe=1",
            (run_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def compare_runs(self, run_id_a: str, run_id_b: str) -> dict:
        """Quick stat comparison between two runs."""
        def stats(run_id):
            conn = self._conn()
            row = conn.execute(
                """SELECT COUNT(*) total,
                          SUM(is_unsafe) unsafe,
                          AVG(safety_score) avg_safety,
                          AVG(composite) avg_composite
                   FROM results WHERE run_id=?""",
                (run_id,),
            ).fetchone()
            conn.close()
            return dict(row) if row else {}

        return {"run_a": stats(run_id_a), "run_b": stats(run_id_b)}
