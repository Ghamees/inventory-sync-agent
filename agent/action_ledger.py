import hashlib
import json
import sqlite3
from pathlib import Path


DB_PATH = Path("data/agent.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialise_ledger():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflict_id TEXT UNIQUE NOT NULL,
                sku TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def create_conflict_id(conflict: dict) -> str:
    canonical_conflict = json.dumps(conflict, sort_keys=True)
    return hashlib.sha256(canonical_conflict.encode()).hexdigest()


def has_been_handled(conflict_id: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM actions
            WHERE conflict_id = ? AND status = 'completed'
            """,
            (conflict_id,),
        ).fetchone()

    return row is not None


def record_action(
    conflict_id: str,
    sku: str,
    action: str,
    details: dict,
    status: str = "completed",
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO actions
            (conflict_id, sku, action, details, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conflict_id,
                sku,
                action,
                json.dumps(details, sort_keys=True),
                status,
            ),
        )