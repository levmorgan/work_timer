"""Unit tests for database.py"""

import sqlite3
from pathlib import Path

import pytest

from database import DEFAULT_SETTINGS, Database


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Create a Database backed by a temporary file."""
    return Database(db_path=tmp_path / "test.db")


class TestInitialization:
    def test_creates_tables(self, db: Database) -> None:
        tables = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {row[0] for row in tables}
        assert table_names == {"settings", "daily_records", "window_state"}

    def test_inserts_default_settings(self, db: Database) -> None:
        for key, expected in DEFAULT_SETTINGS.items():
            assert db.get_setting(key) == expected

    def test_defaults_dont_overwrite_existing(self, tmp_path: Path) -> None:
        db1 = Database(db_path=tmp_path / "test.db")
        db1.set_setting("goal", "10")
        db1.close()

        db2 = Database(db_path=tmp_path / "test.db")
        assert db2.get_setting("goal") == "10"  # not overridden to 14
        db2.close()


class TestSettings:
    def test_get_setting_missing(self, db: Database) -> None:
        assert db.get_setting("nonexistent") is None

    def test_get_all_settings(self, db: Database) -> None:
        settings = db.get_all_settings()
        for key, expected in DEFAULT_SETTINGS.items():
            assert settings[key] == expected

    def test_set_setting(self, db: Database) -> None:
        db.set_setting("goal", "20")
        assert db.get_setting("goal") == "20"

    def test_set_settings_batch(self, db: Database) -> None:
        db.set_settings({"goal": "8", "work_duration": "30"})
        assert db.get_setting("goal") == "8"
        assert db.get_setting("work_duration") == "30"
        # others unchanged
        assert db.get_setting("rest_duration") == "5"


class TestDailyRecords:
    def test_get_record_missing(self, db: Database) -> None:
        assert db.get_daily_record("2025-01-01") is None

    def test_increment_creates_and_increments(self, db: Database) -> None:
        db.increment_daily_record("2025-01-01")
        assert db.get_daily_record("2025-01-01") == 1

        db.increment_daily_record("2025-01-01")
        assert db.get_daily_record("2025-01-01") == 2

    def test_set_daily_record(self, db: Database) -> None:
        db.set_daily_record("2025-01-01", 5)
        assert db.get_daily_record("2025-01-01") == 5

        db.set_daily_record("2025-01-01", 3)
        assert db.get_daily_record("2025-01-01") == 3

    def test_get_all_daily_records(self, db: Database) -> None:
        db.set_daily_record("2025-01-01", 3)
        db.set_daily_record("2025-01-02", 5)
        db.set_daily_record("2025-01-03", 2)

        all_records = db.get_all_daily_records()
        assert all_records == [
            ("2025-01-01", 3),
            ("2025-01-02", 5),
            ("2025-01-03", 2),
        ]

    def test_get_all_daily_records_since(self, db: Database) -> None:
        db.set_daily_record("2025-01-01", 3)
        db.set_daily_record("2025-01-02", 5)
        db.set_daily_record("2025-01-03", 2)

        since = db.get_all_daily_records(since="2025-01-02")
        assert since == [("2025-01-02", 5), ("2025-01-03", 2)]

    def test_get_all_daily_records_empty(self, db: Database) -> None:
        assert db.get_all_daily_records() == []


class TestWindowState:
    def test_initial_state_empty(self, db: Database) -> None:
        assert db.get_window_state() == {}

    def test_save_and_restore(self, db: Database) -> None:
        db.save_window_state(100, 200, 400, 300)
        state = db.get_window_state()
        assert state == {"x": 100, "y": 200, "width": 400, "height": 300}

    def test_update_state(self, db: Database) -> None:
        db.save_window_state(10, 20, 30, 40)
        db.save_window_state(50, 60, 70, 80)
        state = db.get_window_state()
        assert state == {"x": 50, "y": 60, "width": 70, "height": 80}


class TestClose:
    def test_close(self, db: Database) -> None:
        db.close()
        with pytest.raises(sqlite3.ProgrammingError):
            db._conn.execute("SELECT 1")
