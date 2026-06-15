"""Entry point for the Pomodoro timer application."""

import signal
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from database import Database
from timer_controller import PomodoroTimer


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("work_timer")

    # Ctrl+C in the terminal quits the app cleanly.
    # SIGINT works on all platforms but on Windows the handler fires
    # in a separate thread — app.quit() is thread-safe, so this is fine.
    try:
        signal.signal(signal.SIGINT, lambda *_: app.quit())
    except (AttributeError, ValueError):
        pass  # running without a console (e.g. double-clicked .exe)

    db = Database()

    # Create and configure the timer from saved settings
    timer = PomodoroTimer()
    timer.configure(**db.get_typed_settings())

    from ui.main_window import MainWindow

    window = MainWindow(db, timer)

    # Cmd+Q works even when a modal is displayed
    quit_sc = QShortcut(QKeySequence(QKeySequence.StandardKey.Quit), window)
    quit_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
    quit_sc.activated.connect(app.quit)

    # Periodic midnight check — ensures daily counter resets even when idle
    midnight_timer = QTimer(window)
    midnight_timer.timeout.connect(timer.check_date_change)
    midnight_timer.start(30_000)  # every 30 seconds

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
