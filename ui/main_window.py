"""Main timer window for the Pomodoro app."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QFont, QKeySequence, QMouseEvent, QShortcut
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
from sound import play_alert, set_alarm, set_volume, stop_alert
from ui.settings_dialog import SettingsDialog, alarms_dir
from ui.theme import get_stylesheet

FONT_FAMILY = "Menlo, Monaco, Consolas, Courier New, monospace"

# noqa — Font Awesome Private Use Area codepoints
PLAY_SYMBOL = ""       # fa-play
PAUSE_SYMBOL = ""      # fa-pause
STOP_SYMBOL = ""       # fa-stop
FF_SYMBOL = ""         # fa-forward
GEAR_SYMBOL = ""       # fa-gear
CHART_SYMBOL = ""      # fa-chart-bar

DEFAULT_WINDOW_W = 360
DEFAULT_WINDOW_H = 400

TIMER_FONT_SIZE = 56
DAILY_FONT_SIZE = 16
PERIOD_FONT_SIZE = 12
PROGRESS_FONT_SIZE = 11
MIN_SCALE = 0.5
MIN_SCALE_TIMER = 0.65 if sys.platform == "win32" else 0.75
MAX_SCALE = 1.0


BTN_W = 52
BTN_H = 40
BTN_SPACING = 8
ICON_BTN_W = 28
ICON_BTN_H = 28

# Button colors matching the global stylesheet (dark / light handled in resize)
BTN_BG_DARK = "#2a2a2a"
BTN_BG_LIGHT = "#e0e0e0"
BTN_BORDER_DARK = "#555555"
BTN_BORDER_LIGHT = "#999999"
BTN_TEXT_DARK = "#e0e0e0"
BTN_TEXT_LIGHT = "#222222"


class _LoadingDialog(QDialog):
    """Shown briefly while matplotlib loads."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("work_timer")
        self.setModal(True)
        self.setFixedSize(200, 60)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        layout = QVBoxLayout(self)
        label = QLabel("loading_history...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class MainWindow(QMainWindow):
    """The main Pomodoro timer window."""

    def __init__(self, db: Database, timer: PomodoroTimer) -> None:
        super().__init__()
        self._db = db
        self._timer = timer

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_visible = True

        self._drag_start: QPoint | None = None

        self.setWindowTitle("work_timer")
        self.setMinimumSize(160, 140)

        central = QWidget()
        self.setCentralWidget(central)
        self._root = QVBoxLayout(central)
        self._root.setContentsMargins(20, 16, 20, 20)
        self._root.setSpacing(12)

        # ---- Top bar: icons left, period info centred ----
        top_bar = QHBoxLayout()
        top_bar.setSpacing(2)

        self._gear_btn = QPushButton(GEAR_SYMBOL)
        self._gear_btn.setToolTip("settings")
        self._gear_btn.setFixedSize(ICON_BTN_W, ICON_BTN_H)
        self._gear_btn.setStyleSheet(
            "QPushButton { font-family: 'Font Awesome 7 Free'; font-weight: 900; font-size: 18px; border: none; background: transparent; padding: 0px; }"
        )
        self._gear_btn.clicked.connect(self._open_settings)

        self._graph_btn = QPushButton(CHART_SYMBOL)
        self._graph_btn.setToolTip("history")
        self._graph_btn.setFixedSize(ICON_BTN_W, ICON_BTN_H)
        self._graph_btn.setStyleSheet(
            "QPushButton { font-family: 'Font Awesome 7 Free'; font-weight: 900; font-size: 18px; border: none; background: transparent; padding: 0px; }"
        )
        self._graph_btn.clicked.connect(self._open_stats)

        top_bar.addWidget(self._gear_btn)
        top_bar.addWidget(self._graph_btn)
        top_bar.addStretch()

        self._period_label = QLabel("work")
        self._period_font = QFont(FONT_FAMILY, PERIOD_FONT_SIZE)
        self._period_label.setFont(self._period_font)
        self._period_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._period_label.setWordWrap(False)
        top_bar.addWidget(self._period_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._long_rest_progress_label = QLabel("")
        self._progress_font = QFont(FONT_FAMILY, PROGRESS_FONT_SIZE)
        self._long_rest_progress_label.setFont(self._progress_font)
        self._long_rest_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        top_bar.addWidget(self._long_rest_progress_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._root.addLayout(top_bar)

        # ---- Timer display ----
        self._root.addStretch()
        self._time_label = QLabel("25:00")
        self._timer_font = QFont(FONT_FAMILY, TIMER_FONT_SIZE, QFont.Weight.Bold)
        self._time_label.setFont(self._timer_font)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setObjectName("timer")
        self._time_label.mousePressEvent = lambda e: self._on_play_pause()
        self._root.addWidget(self._time_label)

        # ---- Daily counter ----
        self._daily_label = QLabel("0/14")
        self._daily_font = QFont(FONT_FAMILY, DAILY_FONT_SIZE)
        self._daily_label.setFont(self._daily_font)
        self._daily_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._daily_label.setObjectName("daily")
        self._root.addWidget(self._daily_label)

        self._root.addStretch()

        # ---- Control buttons ----
        self._btn_layout = QHBoxLayout()
        self._btn_layout.addStretch()

        _icon_font = QFont("Font Awesome 7 Free", 14, QFont.Weight.Black)
        self._play_btn = QPushButton(PLAY_SYMBOL)
        self._play_btn.setToolTip("play/pause (space)")
        self._play_btn.setFixedSize(BTN_W, BTN_H)
        self._play_btn.setFont(_icon_font)
        self._play_btn.clicked.connect(self._on_play_pause)

        self._stop_btn = QPushButton(STOP_SYMBOL)
        self._stop_btn.setToolTip("stop (esc)")
        self._stop_btn.setFixedSize(BTN_W, BTN_H)
        self._stop_btn.setFont(_icon_font)
        self._stop_btn.clicked.connect(self._on_stop)

        self._ff_btn = QPushButton(FF_SYMBOL)
        self._ff_btn.setToolTip("fast_forward (→)")
        self._ff_btn.setFixedSize(BTN_W, BTN_H)
        self._ff_btn.setFont(_icon_font)
        self._ff_btn.clicked.connect(self._on_fast_forward)

        self._btn_layout.addWidget(self._play_btn)
        self._btn_layout.addWidget(self._stop_btn)
        self._btn_layout.addWidget(self._ff_btn)
        self._btn_layout.addStretch()
        self._root.addLayout(self._btn_layout)

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

        # ---- Always on top (must run before show()) ----
        self._apply_always_on_top()

        # ---- Initial display ----
        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    # Called by main.py after show() — applies persisted state without
    # delaying the initial paint.
    def apply_saved_state(self) -> None:
        self._apply_theme()
        self._restore_window_state()
        self._apply_alarm()
        self._apply_volume()
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
            self._apply_volume()

    def _open_stats(self) -> None:
        loading = _LoadingDialog(self)
        loading.show()
        QTimer.singleShot(0, lambda: self._finish_open_stats(loading))

    def _finish_open_stats(self, loading: _LoadingDialog) -> None:
        from ui.stats_dialog import StatsDialog
        scheme = self._db.get_setting("color_scheme") or "dark"
        dlg = StatsDialog(
            self._db, self._timer.work_periods_completed_today, scheme, self
        )
        loading.close()
        dlg.exec()

    def _apply_settings_from_db(self) -> None:
        self._timer.configure(**self._db.get_typed_settings())
        self._update_time_display()
        self._update_period_label()
        self._update_daily_label()

    # ---- End-of-period dialog ----

    def _show_end_dialog(self, period: Period) -> None:
        from ui.end_dialog import EndOfPeriodDialog
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

    def _apply_volume(self) -> None:
        vol = int(self._db.get_setting("alarm_volume") or "100") / 100.0
        set_volume(vol)

    def _apply_alarm(self) -> None:
        alarm = self._db.get_setting("alarm_sound") or ""
        alarm_path: str | None = None
        if alarm:
            full = alarms_dir() / alarm
            if full.is_file():
                alarm_path = str(full)
        set_alarm(alarm_path)

    def _apply_always_on_top(self) -> None:
        enabled = self._db.get_setting("always_on_top") == "1"
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if was_visible:
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

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        scale_w = w / DEFAULT_WINDOW_W
        scale_h = h / DEFAULT_WINDOW_H
        full_scale = max(min(scale_w, scale_h, MAX_SCALE), MIN_SCALE)
        timer_scale = max(min(scale_w, scale_h, MAX_SCALE), MIN_SCALE_TIMER)

        # Scale fonts — timer shrinks less aggressively
        self._timer_font.setPointSizeF(TIMER_FONT_SIZE * timer_scale)
        self._time_label.setFont(self._timer_font)
        self._daily_font.setPointSizeF(DAILY_FONT_SIZE * full_scale)
        self._daily_label.setFont(self._daily_font)

        # Scale control button sizes, shrink padding so icons still fit
        bw = max(int(BTN_W * full_scale), 40)
        bh = max(int(BTN_H * full_scale), 28)
        pad_v = max(int(6 * full_scale), 2)
        pad_h = max(int(14 * full_scale), 6)
        scheme = self._db.get_setting("color_scheme") or "dark"
        if scheme == "light":
            bg, border, text = BTN_BG_LIGHT, BTN_BORDER_LIGHT, BTN_TEXT_LIGHT
        else:
            bg, border, text = BTN_BG_DARK, BTN_BORDER_DARK, BTN_TEXT_DARK
        _btn_style = (
            "QPushButton {"
            " font-family: 'Font Awesome 7 Free'; font-weight: 900;"
            f" background-color: {bg}; color: {text};"
            f" border: 1px solid {border}; border-radius: 4px;"
            " font-size: 14px;"
            f" padding: {pad_v}px {pad_h}px; }}"
        )
        for btn in (self._play_btn, self._stop_btn, self._ff_btn):
            btn.setFixedSize(bw, bh)
            btn.setStyleSheet(_btn_style)

        # Shrink margins and spacing at small sizes
        top_margin = max(int(16 * full_scale), 4)
        bottom_margin = max(int(20 * full_scale), 6)
        side_margin = max(int(20 * full_scale), 8)
        self._root.setContentsMargins(side_margin, top_margin, side_margin, bottom_margin)
        self._root.setSpacing(max(int(12 * full_scale), 4))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._drag_start = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None:
            delta = event.globalPosition().toPoint() - self._drag_start
            if delta.manhattanLength() > 4:
                self._drag_start = None
                self.windowHandle().startSystemMove()

    def closeEvent(self, event) -> None:
        self._save_window_state()
        stop_alert()
        super().closeEvent(event)
