import sqlite3
import json
import time
from pathlib import Path
import os

DB_DIR  = Path(os.getenv("APPDATA", Path.home())) / "DupeClearPro"
DB_PATH = DB_DIR / "dupeclear.db"

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scan_profiles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            folders    TEXT NOT NULL,
            options    TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS scan_history (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name     TEXT,
            folders          TEXT NOT NULL,
            started_at       TIMESTAMP NOT NULL,
            completed_at     TIMESTAMP,
            files_scanned    INTEGER DEFAULT 0,
            duplicate_groups INTEGER DEFAULT 0,
            wasted_bytes     INTEGER DEFAULT 0,
            freed_bytes      INTEGER DEFAULT 0,
            results_json     TEXT
        );

        CREATE TABLE IF NOT EXISTS trash_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path   TEXT NOT NULL,
            trash_path      TEXT NOT NULL,
            file_name       TEXT NOT NULL,
            size_bytes      INTEGER NOT NULL,
            deleted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scan_history_id INTEGER REFERENCES scan_history(id)
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        INSERT OR IGNORE INTO app_settings VALUES ('theme', 'dark');
        INSERT OR IGNORE INTO app_settings VALUES ('auto_empty_bin_days', '30');
        INSERT OR IGNORE INTO app_settings VALUES ('max_bin_size_gb', '5');
        INSERT OR IGNORE INTO app_settings VALUES ('auto_select_rule', 'newest');
        INSERT OR IGNORE INTO app_settings VALUES ('license_key', '');
        INSERT OR IGNORE INTO app_settings VALUES ('license_status', 'free');
        INSERT OR IGNORE INTO app_settings VALUES ('excluded_folders', '["C:\\\\Windows","C:\\\\Program Files","C:\\\\Program Files (x86)"]');
        INSERT OR IGNORE INTO app_settings VALUES ('first_run', 'true');
        INSERT OR IGNORE INTO app_settings VALUES ('window_geometry', '');
    """)
    conn.commit()


def get_setting(key: str, default: str = "") -> str:
    conn = get_conn()
    row = conn.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO app_settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()


def _retry_execute(conn, sql, params=(), retries=3):
    for attempt in range(retries):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < retries - 1:
                time.sleep(0.1)
            else:
                raise


# ---------- scan history ----------

def insert_scan_history(folders, started_at) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO scan_history (folders, started_at) VALUES (?,?)",
        (json.dumps(folders), started_at)
    )
    conn.commit()
    return cur.lastrowid


def update_scan_history(scan_id: int, **kwargs):
    conn = get_conn()
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [scan_id]
    conn.execute(f"UPDATE scan_history SET {fields} WHERE id=?", values)
    conn.commit()


def get_all_history() -> list:
    conn = get_conn()
    return conn.execute(
        "SELECT * FROM scan_history ORDER BY started_at DESC"
    ).fetchall()


def get_lifetime_stats() -> dict:
    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*) as scans,
               SUM(files_scanned) as total_files,
               SUM(freed_bytes)   as total_freed
        FROM scan_history
    """).fetchone()
    return {
        "scans":       row["scans"] or 0,
        "total_files": row["total_files"] or 0,
        "total_freed": row["total_freed"] or 0,
    }


# ---------- trash ----------

def add_trash_item(original_path, trash_path, file_name, size_bytes, scan_history_id=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO trash_items (original_path,trash_path,file_name,size_bytes,scan_history_id) VALUES (?,?,?,?,?)",
        (original_path, trash_path, file_name, size_bytes, scan_history_id)
    )
    conn.commit()


def get_trash_items() -> list:
    conn = get_conn()
    return conn.execute("SELECT * FROM trash_items ORDER BY deleted_at DESC").fetchall()


def delete_trash_item(item_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM trash_items WHERE id=?", (item_id,))
    conn.commit()


# ---------- profiles ----------

def save_profile(name: str, folders: list, options: dict):
    conn = get_conn()
    conn.execute(
        """INSERT INTO scan_profiles (name,folders,options,updated_at)
           VALUES (?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(name) DO UPDATE SET folders=excluded.folders,
           options=excluded.options, updated_at=CURRENT_TIMESTAMP""",
        (name, json.dumps(folders), json.dumps(options))
    )
    conn.commit()


def get_profiles() -> list:
    conn = get_conn()
    return conn.execute("SELECT * FROM scan_profiles ORDER BY name").fetchall()


def delete_profile(name: str):
    conn = get_conn()
    conn.execute("DELETE FROM scan_profiles WHERE name=?", (name,))
    conn.commit()
