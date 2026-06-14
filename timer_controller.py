"""Pomodoro timer state machine.

Manages WORK → REST → LONG_REST transitions, countdown, and daily tracking.
Emits Qt signals so the UI layer stays decoupled from timer logic.
"""

from __future__ import annotations

from datetime import date
from enum import Enum, auto

from PySide6.QtCore import QObject, QTimer, Signal


class Period(Enum):
    WORK = auto()
    REST = auto()
    LONG_REST = auto()


PERIOD_NAMES: dict[Period, str] = {
    Period.WORK: "work",
    Period.REST: "rest",
    Period.LONG_REST: "long_rest",
}

# These match Python's datetime.isoweekday() — Monday=1, Sunday=7
DAY_NAMES: dict[int, str] = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}


class PomodoroTimer(QObject):
    """Core timer logic for the Pomodoro app."""

    tick = Signal(int)  # remaining_seconds
    state_changed = Signal(Period)  # new state
    period_finished = Signal(Period)  # which period just ended
    daily_count_changed = Signal(int, int)  # count, goal
    long_rest_progress_changed = Signal(int, int)  # current work sessions, total needed

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._qtimer = QTimer(self)
        self._qtimer.timeout.connect(self._on_tick)

        # Configurable values (set via configure())
        self._work_secs: int = 25 * 60
        self._rest_secs: int = 5 * 60
        self._long_rest_secs: int = 15 * 60
        self._long_rest_enabled: bool = True
        self._periods_before_long_rest: int = 4
        self._goal: int = 14
        self._work_days: set[int] = {1, 2, 3, 4, 5}

        # Current state
        self._state: Period = Period.WORK
        self._remaining: int = self._work_secs
        self._paused: bool = True

        # Counters
        self._work_sessions_since_long_rest: int = 0
        self._work_periods_completed_today: int = 0
        self._last_date: date = date.today()

    # ---- public API ----

    def configure(
        self,
        *,
        work_duration_mins: int = 25,
        rest_duration_mins: int = 5,
        long_rest_duration_mins: int = 15,
        long_rest_enabled: bool = True,
        work_periods_before_long_rest: int = 4,
        goal: int = 14,
        work_days: set[int] | None = None,
    ) -> None:
        """Apply settings. Duration changes take effect immediately if the
        timer is paused; otherwise on the next period start.
        """
        self._work_secs = work_duration_mins * 60
        self._rest_secs = rest_duration_mins * 60
        self._long_rest_secs = long_rest_duration_mins * 60
        self._long_rest_enabled = long_rest_enabled
        self._periods_before_long_rest = work_periods_before_long_rest
        self._goal = goal
        if work_days is not None:
            self._work_days = work_days

        # Sync remaining to new duration if paused (startup, settings
        # changes while idle). Running timers keep their remaining time.
        if self._paused:
            self._remaining = self._duration_for(self._state)

        self._emit_daily_count()
        self._emit_long_rest_progress()

    def start(self) -> None:
        if not self._paused:
            return
        self._paused = False
        self._check_midnight()
        self._qtimer.start(1000)

    def pause(self) -> None:
        self._paused = True
        self._qtimer.stop()

    def stop(self) -> None:
        """Reset to start of WORK period, paused.
        No-op if already at start of WORK and paused.
        """
        was_paused = self._paused
        was_work = self._state == Period.WORK
        at_start = self._remaining == self._work_secs

        if was_paused and was_work and at_start:
            return  # no-op

        self._qtimer.stop()
        self._paused = True
        self._state = Period.WORK
        self._remaining = self._work_secs
        self.state_changed.emit(self._state)
        self.tick.emit(self._remaining)
        self._emit_long_rest_progress()

    def fast_forward(self) -> None:
        """Skip to the next period in sequence, leave paused."""
        self._qtimer.stop()
        self._paused = True
        self._advance_period()
        self.tick.emit(self._remaining)
        self.state_changed.emit(self._state)
        self._emit_long_rest_progress()

    # ---- properties ----

    @property
    def state(self) -> Period:
        return self._state

    @property
    def remaining_seconds(self) -> int:
        return self._remaining

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def work_sessions_since_long_rest(self) -> int:
        return self._work_sessions_since_long_rest

    @property
    def work_periods_completed_today(self) -> int:
        return self._work_periods_completed_today

    @property
    def is_today_work_day(self) -> bool:
        return date.today().isoweekday() in self._work_days

    @property
    def display_goal(self) -> int:
        return self._goal if self.is_today_work_day else 0

    @property
    def long_rest_progress_max(self) -> int:
        return self._periods_before_long_rest

    def check_date_change(self) -> None:
        """Public method — call periodically to catch midnight while idle."""
        self._check_midnight()

    # ---- internal ----

    def _duration_for(self, state: Period) -> int:
        if state == Period.WORK:
            return self._work_secs
        elif state == Period.LONG_REST:
            return self._long_rest_secs
        else:
            return self._rest_secs

    def _on_tick(self) -> None:
        self._check_midnight()
        self._remaining = max(0, self._remaining - 1)
        self.tick.emit(self._remaining)

        if self._remaining <= 0:
            self._qtimer.stop()
            self._paused = True

            period_that_ended = self._state

            if self._state == Period.WORK:
                self._work_periods_completed_today += 1
                self._emit_daily_count()

            self.period_finished.emit(period_that_ended)

    def _advance_period(self) -> None:
        """Move to the next period in the sequence and reset the countdown."""
        if self._state == Period.WORK:
            # WORK completed → check if long rest is due
            if (
                self._long_rest_enabled
                and self._work_sessions_since_long_rest
                >= self._periods_before_long_rest
            ):
                self._state = Period.LONG_REST
                self._remaining = self._long_rest_secs
            else:
                self._state = Period.REST
                self._remaining = self._rest_secs
        elif self._state == Period.REST:
            self._state = Period.WORK
            self._remaining = self._work_secs
            self._work_sessions_since_long_rest += 1
        elif self._state == Period.LONG_REST:
            self._state = Period.WORK
            self._remaining = self._work_secs
            self._work_sessions_since_long_rest = 1

    def _check_midnight(self) -> None:
        """Reset daily count if the date has changed."""
        today = date.today()
        if today != self._last_date:
            self._work_periods_completed_today = 0
            self._last_date = today
            self._emit_daily_count()

    def _emit_daily_count(self) -> None:
        self.daily_count_changed.emit(
            self._work_periods_completed_today, self.display_goal
        )

    def _emit_long_rest_progress(self) -> None:
        if self._state != Period.LONG_REST and self._long_rest_enabled:
            self.long_rest_progress_changed.emit(
                self._work_sessions_since_long_rest,
                self._periods_before_long_rest,
            )
        else:
            self.long_rest_progress_changed.emit(0, 0)
