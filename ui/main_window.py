"""Main timer window for the Pomodoro app."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from database import Database
from timer_controller import PERIOD_NAMES, Period, PomodoroTimer
from sound import play_alert, stop_alert, set_alarm
from ui.end_dialog import EndOfPeriodDialog
from ui.settings_dialog import SettingsDialog
from ui.stats_dialog import StatsDialog

from ui.theme import get_stylesheet

FONT_FAMILY = "Menlo, Monaco, Courier New, monospace"

PLAY_SYMBOL = "▶"
PAUSE_SYMBOL = "⏸"
PLAY_PAUSE_SYMBOL = "⏯"

DEFAULT_WINDOW_W = 360
DEFAULT_WINDOW_H = 400


class MainWindow(QMainWindow):
    """The main Pomodoro timer window."""

    def __init__(self, db: Database, timer: PomodoroTimer) -> None:
        super().__init__()
        self._db = db
        self._timer = timer

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_visible = True

        self.setWindowTitle("work_timer")
        self.setMinimumSize(320, 280)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(12)

        # ---- Top bar: icons left, period info right ----
        top_bar = QHBoxLayout()
        top_bar.setSpacing(2)

        gear_btn = QPushButton("⚙")  # ⚙
        gear_btn.setToolTip("settings")
        gear_btn.setFixedSize(40, 36)
        gear_btn.setStyleSheet("QPushButton { font-size: 18px; border: none; background: transparent; padding: 0px; }")
        gear_btn.clicked.connect(self._open_settings)

        graph_btn = QPushButton("\U0001F4C8")  # 📈
        graph_btn.setToolTip("history")
        graph_btn.setFixedSize(40, 36)
        graph_btn.setStyleSheet("QPushButton { font-size: 18px; border: none; background: transparent; padding: 0px; }")
        graph_btn.clicked.connect(self._open_stats)

        top_bar.addWidget(gear_btn)
        top_bar.addWidget(graph_btn)
        top_bar.addStretch()

        self._period_label = QLabel("work")
        self._period_label.setFont(QFont(FONT_FAMILY, 12))
        self._period_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._period_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._long_rest_progress_label = QLabel("")
        self._long_rest_progress_label.setFont(QFont(FONT_FAMILY, 11))
        self._long_rest_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._long_rest_progress_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # Wrap labels in a widget so they expand to fill the top bar
        period_widget = QWidget()
        period_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        period_col = QVBoxLayout(period_widget)
        period_col.setContentsMargins(0, 0, 0, 0)
        period_col.setSpacing(2)
        period_col.addWidget(self._period_label)
        period_col.addWidget(self._long_rest_progress_label)
        top_bar.addWidget(period_widget)

        root.addLayout(top_bar)

        # ---- Timer display ----
        root.addStretch()
        self._time_label = QLabel("25:00")
        self._time_label.setFont(QFont(FONT_FAMILY, 56, QFont.Weight.Bold))
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setObjectName("timer")
        self._time_label.mousePressEvent = lambda e: self._on_play_pause()
        root.addWidget(self._time_label)

        # ---- Daily counter ----
        self._daily_label = QLabel("0/14")
        self._daily_label.setFont(QFont(FONT_FAMILY, 16))
        self._daily_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._daily_label.setObjectName("daily")
        root.addWidget(self._daily_label)

        root.addStretch()

        # ---- Control buttons ----
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._play_btn = QPushButton(PLAY_PAUSE_SYMBOL)
        self._play_btn.setToolTip("play/pause (space)")
        self._play_btn.setFixedSize(52, 40)
        self._play_btn.clicked.connect(self._on_play_pause)

        stop_btn = QPushButton("■")  # ■
        stop_btn.setToolTip("stop (esc)")
        stop_btn.setFixedSize(52, 40)
        stop_btn.clicked.connect(self._on_stop)

        ff_btn = QPushButton("⏭")  # ⏭
        ff_btn.setToolTip("fast_forward (→)")
        ff_btn.setFixedSize(52, 40)
        ff_btn.clicked.connect(self._on_fast_forward)

        btn_layout.addWidget(self._play_btn)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(stop_btn)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(ff_btn)
        btn_layout.addStretch()
        root.addLayout(btn_layout)

        # ---- Connections ----
        self._timer.tick.connect(self._on_tick)
        self._timer.state_changed.connect(self._on_state_changed)
        self._timer.period_finished.connect(self._on_period_finished)
        self._timer.daily_count_changed.connect(self._on_daily_count_changed)
        self._timer.long_rest_progress_changed.connect(self._on_long_rest_progress_changed)

        # ---- Keyboard shortcuts ----
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self._on_play_pause)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self._on_stop)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=self._on_fast_forward)

        # ---- Restore window state ----
        self._restore_window_state()

        # ---- Apply theme ----
        self._apply_theme()

        # ---- Always on top ----
        self._apply_always_on_top()

        # ---- Initial display ----
        self._apply_alarm()
        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    # ---- Slots ----

    def _on_tick(self, remaining: int) -> None:
        self._update_time_display()

    def _on_state_changed(self, state: Period) -> None:
        self._update_period_label()

    def _on_period_finished(self, period: Period) -> None:
        """Show modal, play sound, start blinking."""
        # Save completed work period to DB
        if period == Period.WORK:
            self._db.increment_daily_record(date.today().isoformat())

        play_alert()
        self._start_blinking()
        self._show_end_dialog(period)

    def _on_daily_count_changed(self, count: int, goal: int) -> None:
        self._update_daily_label()

    def _on_long_rest_progress_changed(self, current: int, total: int) -> None:
        if current > 0 and total > 0:
            self._long_rest_progress_label.setText(f"{current}/{total}")
            self._long_rest_progress_label.setVisible(True)
        else:
            self._long_rest_progress_label.setVisible(False)

    # ---- Button handlers ----

    def _on_play_pause(self) -> None:
        if self._timer.is_paused:
            self._timer.start()
            self._play_btn.setText(PAUSE_SYMBOL)
        else:
            self._timer.pause()
            self._play_btn.setText(PLAY_SYMBOL)

    def _on_stop(self) -> None:
        self._timer.stop()
        self._play_btn.setText(PLAY_SYMBOL)
        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    def _on_fast_forward(self) -> None:
        self._timer.fast_forward()
        self._play_btn.setText(PLAY_SYMBOL)
        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    # ---- Settings / Stats ----

    def _open_settings(self) -> None:
        scheme = self._db.get_setting("color_scheme") or "dark"
        dlg = SettingsDialog(self._db, scheme, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._apply_settings_from_db()
            self._apply_theme()
            self._apply_always_on_top()
            self._apply_alarm()

    def _open_stats(self) -> None:
        scheme = self._db.get_setting("color_scheme") or "dark"
        dlg = StatsDialog(
            self._db, self._timer.work_periods_completed_today, scheme, self
        )
        dlg.exec()

    def _apply_settings_from_db(self) -> None:
        self._timer.configure(**self._db.get_typed_settings())
        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    # ---- End-of-period dialog ----

    def _show_end_dialog(self, period: Period) -> None:
        dlg = EndOfPeriodDialog(period, self)
        dlg.exec()

        # Stop sound and blinking regardless of outcome
        stop_alert()
        self._stop_blinking()

        if dlg.outcome == "continue":
            self._timer.fast_forward()
            self._timer.start()
            self._play_btn.setText(PAUSE_SYMBOL)
        elif dlg.outcome == "finish":
            self._timer.stop()
            self._play_btn.setText(PLAY_SYMBOL)
        else:  # timeout — advance but stay paused
            self._timer.fast_forward()
            self._play_btn.setText(PLAY_SYMBOL)

        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    # ---- Blinking ----

    def _start_blinking(self) -> None:
        self._blink_visible = True
        self._blink_timer.start(500)

    def _stop_blinking(self) -> None:
        self._blink_timer.stop()
        self._time_label.setVisible(True)

    def _toggle_blink(self) -> None:
        self._blink_visible = not self._blink_visible
        self._time_label.setVisible(self._blink_visible)

    # ---- Display updates ----

    def _update_time_display(self) -> None:
        secs = self._timer.remaining_seconds
        mins = secs // 60
        secs = secs % 60
        self._time_label.setText(f"{mins}:{secs:02d}")

    def _update_period_label(self) -> None:
        self._period_label.setText(
            PERIOD_NAMES.get(self._timer.state, "")
        )

    def _update_daily_label(self) -> None:
        self._daily_label.setText(
            f"{self._timer.work_periods_completed_today}/{self._timer.display_goal}"
        )

    # ---- Theming ----

    def _apply_theme(self) -> None:
        scheme = self._db.get_setting("color_scheme") or "dark"
        self.setStyleSheet(get_stylesheet(scheme))

    def _apply_alarm(self) -> None:
        alarm = self._db.get_setting("alarm_sound") or ""
        alarm_path: str | None = None
        if alarm:
            full = Path(__file__).resolve().parent.parent / "alarms" / alarm
            if full.is_file():
                alarm_path = str(full)
        set_alarm(alarm_path)

    def _apply_always_on_top(self) -> None:
        enabled = self._db.get_setting("always_on_top") == "1"
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if self.isVisible():
            self.show()

    # ---- Window state ----

    def _restore_window_state(self) -> None:
        state = self._db.get_window_state()
        if state:
            x = state.get("x", 100)
            y = state.get("y", 100)
            w = state.get("width", DEFAULT_WINDOW_W)
            h = state.get("height", DEFAULT_WINDOW_H)
            self.setGeometry(x, y, w, h)
        else:
            self.resize(DEFAULT_WINDOW_W, DEFAULT_WINDOW_H)

    def _save_window_state(self) -> None:
        geo = self.geometry()
        self._db.save_window_state(geo.x(), geo.y(), geo.width(), geo.height())

    def closeEvent(self, event) -> None:
        self._save_window_state()
        stop_alert()
        super().closeEvent(event)
