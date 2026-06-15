"""Smoke tests — verify the full widget tree builds without crashing."""

import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from database import Database
from timer_controller import Period, PomodoroTimer


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(db_path=tmp_path / "smoke.db")


@pytest.fixture
def timer(db: Database) -> PomodoroTimer:
    t = PomodoroTimer()
    t.configure(**db.get_typed_settings())
    return t


class TestMainWindow:
    def test_constructs_without_crashing(
        self, qapp: QApplication, db: Database, timer: PomodoroTimer
    ) -> None:
        from ui.main_window import MainWindow

        w = MainWindow(db, timer)
        assert w.windowTitle() == "work_timer"
        assert w.isVisible() is False

    def test_initial_state(
        self, qapp: QApplication, db: Database, timer: PomodoroTimer
    ) -> None:
        from ui.main_window import MainWindow

        w = MainWindow(db, timer)
        assert timer.state == Period.WORK
        assert timer.is_paused is True
        assert timer.remaining_seconds == 25 * 60

    def test_play_pause_stop_ff(
        self, qapp: QApplication, db: Database, timer: PomodoroTimer
    ) -> None:
        from ui.main_window import MainWindow

        w = MainWindow(db, timer)
        # Play
        timer.start()
        assert timer.is_paused is False
        # Pause
        timer.pause()
        assert timer.is_paused is True
        # Fast-forward
        timer.fast_forward()
        assert timer.state == Period.REST
        # Stop
        timer.stop()
        assert timer.state == Period.WORK
        assert timer.is_paused is True

    def test_settings_dialog_constructs(
        self, qapp: QApplication, db: Database, timer: PomodoroTimer
    ) -> None:
        from ui.main_window import MainWindow
        from ui.settings_dialog import SettingsDialog

        w = MainWindow(db, timer)
        dlg = SettingsDialog(db, "dark", w)
        assert dlg.windowTitle() == "settings"
        dlg.close()

    def test_stats_dialog_constructs(
        self, qapp: QApplication, db: Database, timer: PomodoroTimer
    ) -> None:
        from ui.main_window import MainWindow
        from ui.stats_dialog import StatsDialog

        w = MainWindow(db, timer)
        dlg = StatsDialog(db, 0, "dark", w)
        assert dlg.windowTitle() == "history"
        dlg.close()

    def test_apply_saved_state(
        self, qapp: QApplication, db: Database, timer: PomodoroTimer
    ) -> None:
        from ui.main_window import MainWindow

        w = MainWindow(db, timer)
        w.show()
        w.apply_saved_state()
        assert w.isVisible() is True
        w.hide()
