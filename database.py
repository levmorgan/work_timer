"""SQLite database for the Pomodoro timer app.

Stores user settings, daily completion records, and window state.
"""

import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_SETTINGS: dict[str, str] = {
    "work_duration": "25",
    "rest_duration": "5",
    "long_rest_duration": "15",
    "long_rest_enabled": "1",
    "work_periods_before_long_rest": "4",
    "goal": "14",
    "work_days": "1,2,3,4,5",
    "color_scheme": "dark",
    "always_on_top": "0",
    "alarm_sound": "",
    "alarm_volume": "100",
}


class Database:
    """Manages the SQLite database for the Pomodoro timer."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            db_path = Path.home() / ".pomodoro" / "pomodoro.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
        self._insert_defaults()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_records (
                date TEXT PRIMARY KEY,
                work_periods_completed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS window_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _insert_defaults(self) -> None:
        for key, value in DEFAULT_SETTINGS.items():
            self._conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        self._conn.commit()

    # ---- Settings ----

    def get_setting(self, key: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def get_all_settings(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key, value FROM settings").fetchall()
        return {row[0]: row[1] for row in rows}

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    def set_settings(self, settings: dict[str, str]) -> None:
        with self._conn:
            for key, value in settings.items():
                self._conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, value),
                )

    # ---- Daily Records ----

    def get_daily_record(self, date_str: str) -> Optional[int]:
        row = self._conn.execute(
            "SELECT work_periods_completed FROM daily_records WHERE date = ?",
            (date_str,),
        ).fetchone()
        return row[0] if row else None

    def get_all_daily_records(
        self, since: Optional[str] = None
    ) -> list[tuple[str, int]]:
        if since:
            rows = self._conn.execute(
                "SELECT date, work_periods_completed FROM daily_records "
                "WHERE date >= ? ORDER BY date",
                (since,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT date, work_periods_completed FROM daily_records "
                "ORDER BY date"
            ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def increment_daily_record(self, date_str: str) -> None:
        """Increment the work periods completed for a given date."""
        self._conn.execute(
            "INSERT INTO daily_records (date, work_periods_completed) "
            "VALUES (?, 1) "
            "ON CONFLICT(date) DO UPDATE SET "
            "work_periods_completed = work_periods_completed + 1",
            (date_str,),
        )
        self._conn.commit()

    def set_daily_record(self, date_str: str, count: int) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO daily_records (date, work_periods_completed) "
            "VALUES (?, ?)",
            (date_str, count),
        )
        self._conn.commit()

    # ---- Window State ----

    def get_window_state(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT key, value FROM window_state"
        ).fetchall()
        state: dict[str, int] = {}
        for key, value in rows:
            try:
                state[key] = int(value)
            except (ValueError, TypeError):
                pass
        return state

    def save_window_state(self, x: int, y: int, width: int, height: int) -> None:
        with self._conn:
            for key, value in [("x", x), ("y", y), ("width", width), ("height", height)]:
                self._conn.execute(
                    "INSERT OR REPLACE INTO window_state (key, value) VALUES (?, ?)",
                    (key, str(value)),
                )

    def get_typed_settings(self) -> dict:
        """Return all settings as a dict with proper Python types,
        suitable for passing directly to PomodoroTimer.configure().
        """
        s = self.get_all_settings()
        return {
            "work_duration_mins": int(s.get("work_duration", 25)),
            "rest_duration_mins": int(s.get("rest_duration", 5)),
            "long_rest_duration_mins": int(s.get("long_rest_duration", 15)),
            "long_rest_enabled": s.get("long_rest_enabled", "1") == "1",
            "work_periods_before_long_rest": int(
                s.get("work_periods_before_long_rest", 4)
            ),
            "goal": int(s.get("goal", 14)),
            "work_days": {
                int(d)
                for d in s.get("work_days", "1,2,3,4,5").split(",")
                if d.strip()
            },
        }

    def close(self) -> None:
        self._conn.close()
