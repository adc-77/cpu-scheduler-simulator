"""
database.py
-----------
All SQLite code lives here, so the rest of the app never writes SQL.

Two tables:
  processes -> the process list the user has entered
  runs      -> history of simulation runs (results stored as JSON text)

The database file (scheduler.db) is created automatically next to this file.
"""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler.db")


def get_connection():
    """Open a connection. Rows can be read like dicts (row["pid"])."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tables if they do not exist yet. Safe to call every start."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            pid      TEXT    NOT NULL UNIQUE,
            arrival  INTEGER NOT NULL,
            burst    INTEGER NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm      TEXT NOT NULL,
            quantum        INTEGER,
            avg_waiting    REAL NOT NULL,
            avg_turnaround REAL NOT NULL,
            result_json    TEXT NOT NULL,
            created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# PROCESSES
# ---------------------------------------------------------------
def add_process(pid, arrival, burst, priority=0):
    """Insert a process. Raises ValueError if the PID already exists."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO processes (pid, arrival, burst, priority) VALUES (?, ?, ?, ?)",
            (pid, arrival, burst, priority))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("PID already exists: " + pid)
    finally:
        conn.close()


def get_processes():
    """Return all processes as a list of dicts (oldest first)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT pid, arrival, burst, priority FROM processes ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_process(pid, arrival, burst, priority):
    """Change a process. Returns True if it existed."""
    conn = get_connection()
    cur = conn.execute(
        "UPDATE processes SET arrival = ?, burst = ?, priority = ? WHERE pid = ?",
        (arrival, burst, priority, pid))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed


def delete_process(pid):
    """Delete one process. Returns True if it existed."""
    conn = get_connection()
    cur = conn.execute("DELETE FROM processes WHERE pid = ?", (pid,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def clear_processes():
    """Delete every process."""
    conn = get_connection()
    conn.execute("DELETE FROM processes")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# SIMULATION RUNS (history)
# ---------------------------------------------------------------
def save_run(result, quantum=None):
    """Save one scheduler result (the dict from schedulers.py). Returns the new run id."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO runs (algorithm, quantum, avg_waiting, avg_turnaround, result_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (result["algorithm"], quantum, result["avg_waiting"],
         result["avg_turnaround"], json.dumps(result)))
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def get_runs():
    """Return a short summary of every saved run, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, algorithm, quantum, avg_waiting, avg_turnaround, created_at "
        "FROM runs ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_run(run_id):
    """Return the full saved result (with Gantt chart) of one run, or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "quantum": row["quantum"],
            "created_at": row["created_at"],
            "result": json.loads(row["result_json"])}


def clear_runs():
    """Delete the whole run history."""
    conn = get_connection()
    conn.execute("DELETE FROM runs")
    conn.commit()
    conn.close()
