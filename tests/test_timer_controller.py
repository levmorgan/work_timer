"""Unit tests for timer_controller.py"""

from datetime import date, timedelta

import pytest

from timer_controller import Period, PomodoroTimer


# ---- helpers ----

def _make_timer(**overrides) -> PomodoroTimer:
    """Create a timer with default settings for testing.
    Pass keyword args to override specific settings.
    """
    t = PomodoroTimer()
    settings: dict = dict(
        work_duration_mins=25,
        rest_duration_mins=5,
        long_rest_duration_mins=15,
        long_rest_enabled=True,
        work_periods_before_long_rest=4,
        goal=14,
        work_days={1, 2, 3, 4, 5},
    )
    settings.update(overrides)
    t.configure(**settings)
    return t


# ---- Initialization ----

class TestInitialState:
    def test_initial_state_is_work(self) -> None:
        t = PomodoroTimer()
        assert t.state == Period.WORK

    def test_initial_remaining_is_work_duration(self) -> None:
        t = PomodoroTimer()
        assert t.remaining_seconds == 25 * 60

    def test_initial_paused(self) -> None:
        t = PomodoroTimer()
        assert t.is_paused is True

    def test_initial_counters_zero(self) -> None:
        t = PomodoroTimer()
        assert t.work_sessions_since_long_rest == 0
        assert t.work_periods_completed_today == 0


# ---- Start / Pause ----

class TestStartPause:
    def test_start_unpauses(self) -> None:
        t = _make_timer()
        t.start()
        assert t.is_paused is False

    def test_pause_stops_ticking(self) -> None:
        t = _make_timer()
        t.start()
        t.pause()
        assert t.is_paused is True

    def test_start_resumes_from_paused(self) -> None:
        t = _make_timer()
        t.start()
        # Simulate a few ticks
        t._remaining = 1200
        t.pause()
        assert t.remaining_seconds == 1200
        t.start()
        assert t.is_paused is False
        assert t.remaining_seconds == 1200

    def test_start_when_running_is_noop(self) -> None:
        t = _make_timer()
        t.start()
        t._remaining = 1000
        t.start()  # second start should be no-op
        assert t.remaining_seconds == 1000


# ---- Tick / Countdown ----

class TestTick:
    def test_tick_decrements_remaining(self) -> None:
        t = _make_timer()
        t.start()
        initial = t.remaining_seconds
        t._on_tick()
        assert t.remaining_seconds == initial - 1

    def test_tick_emits_tick_signal(self) -> None:
        t = _make_timer()
        signals: list[int] = []
        t.tick.connect(signals.append)
        t.start()
        t._on_tick()
        t._on_tick()
        assert len(signals) >= 2

    def test_work_period_end_increments_daily_count(self) -> None:
        t = _make_timer()
        t.start()
        # Set up: at the end of a work period
        t._state = Period.WORK
        t._remaining = 1
        t._on_tick()  # reaches 0 → work period ends
        assert t.work_periods_completed_today == 1

    def test_period_end_emits_period_finished(self) -> None:
        t = _make_timer()
        finished: list[Period] = []
        t.period_finished.connect(finished.append)
        t.start()
        t._state = Period.WORK
        t._remaining = 1
        t._on_tick()
        assert finished == [Period.WORK]

    def test_period_end_stops_timer(self) -> None:
        t = _make_timer()
        t.start()
        t._state = Period.WORK
        t._remaining = 1
        t._on_tick()
        assert t.is_paused is True

    def test_rest_period_end_does_not_increment_daily_count(self) -> None:
        t = _make_timer()
        t.start()
        t._state = Period.REST
        t._remaining = 1
        t._on_tick()
        assert t.work_periods_completed_today == 0


# ---- State Transitions (tested via _advance_period) ----

class TestAdvanceFromWork:
    def test_work_to_rest_when_long_rest_not_due(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 2  # < 4
        t._advance_period()
        assert t.state == Period.REST

    def test_work_to_long_rest_when_threshold_reached(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 4  # >= 4
        t._advance_period()
        assert t.state == Period.LONG_REST
        assert t.remaining_seconds == 15 * 60

    def test_work_to_rest_when_long_rest_disabled(self) -> None:
        t = _make_timer(long_rest_enabled=False)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 10
        t._advance_period()
        assert t.state == Period.REST

    def test_remaining_reset_to_rest_duration(self) -> None:
        t = _make_timer(rest_duration_mins=5)
        t._state = Period.WORK
        t._remaining = 100
        t._work_sessions_since_long_rest = 2
        t._advance_period()
        assert t.remaining_seconds == 5 * 60


class TestAdvanceFromRest:
    def test_rest_to_work(self) -> None:
        t = _make_timer()
        t._state = Period.REST
        t._work_sessions_since_long_rest = 2
        t._advance_period()
        assert t.state == Period.WORK
        # Counter incremented on entering work
        assert t.work_sessions_since_long_rest == 3
        assert t.remaining_seconds == 25 * 60


class TestAdvanceFromLongRest:
    def test_long_rest_to_work_resets_counter(self) -> None:
        t = _make_timer()
        t._state = Period.LONG_REST
        t._work_sessions_since_long_rest = 4
        t._advance_period()
        assert t.state == Period.WORK
        assert t.work_sessions_since_long_rest == 1  # reset, then incremented for new work
        assert t.remaining_seconds == 25 * 60


# ---- Stop ----

class TestStop:
    def test_stop_at_beginning_of_work_paused_is_noop(self) -> None:
        t = _make_timer()
        # Already at beginning of work, paused
        t.stop()
        assert t.state == Period.WORK
        assert t.remaining_seconds == 25 * 60
        assert t.is_paused is True

    def test_stop_during_running_resets_to_work(self) -> None:
        t = _make_timer()
        t.start()
        t._remaining = 500
        t.stop()
        assert t.state == Period.WORK
        assert t.remaining_seconds == 25 * 60
        assert t.is_paused is True

    def test_stop_during_rest_resets_to_work(self) -> None:
        t = _make_timer()
        t._state = Period.REST
        t._remaining = 100
        t._paused = True
        t.stop()
        assert t.state == Period.WORK
        assert t.remaining_seconds == 25 * 60
        assert t.is_paused is True

    def test_stop_from_long_rest_resets_to_work(self) -> None:
        t = _make_timer()
        t._state = Period.LONG_REST
        t._remaining = 200
        t.stop()
        assert t.state == Period.WORK
        assert t.is_paused is True


# ---- Fast-Forward ----

class TestFastForward:
    def test_fast_forward_from_work_to_rest(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 1
        t.fast_forward()
        assert t.state == Period.REST
        assert t.is_paused is True
        assert t.remaining_seconds == 5 * 60

    def test_fast_forward_stays_paused(self) -> None:
        t = _make_timer()
        t.start()
        t.fast_forward()
        assert t.is_paused is True

    def test_fast_forward_leaves_timer_at_start_of_next_period(self) -> None:
        t = _make_timer(rest_duration_mins=5)
        t._state = Period.WORK
        t._remaining = 300  # mid-period
        t._work_sessions_since_long_rest = 1
        t.fast_forward()
        assert t.remaining_seconds == 5 * 60  # full rest duration

    def test_fast_forward_emits_state_changed(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 1
        states: list[Period] = []
        t.state_changed.connect(states.append)
        t.fast_forward()
        assert states == [Period.REST]


# ---- Midnight Reset ----

class TestMidnightReset:
    def test_check_midnight_resets_count(self) -> None:
        t = _make_timer()
        t._work_periods_completed_today = 5
        # Simulate date change
        t._last_date = date.today() - timedelta(days=1)
        t._check_midnight()
        assert t.work_periods_completed_today == 0

    def test_check_midnight_updates_last_date(self) -> None:
        t = _make_timer()
        yesterday = date.today() - timedelta(days=1)
        t._last_date = yesterday
        t._check_midnight()
        assert t._last_date == date.today()

    def test_check_midnight_same_day_does_nothing(self) -> None:
        t = _make_timer()
        t._work_periods_completed_today = 5
        t._last_date = date.today()
        t._check_midnight()
        assert t.work_periods_completed_today == 5


# ---- Work Day Detection ----

class TestWorkDays:
    def test_is_today_work_day(self) -> None:
        t = _make_timer(work_days={1, 2, 3, 4, 5, 6, 7})
        assert t.is_today_work_day is True

    def test_non_work_day_shows_zero_goal(self) -> None:
        today_iso = date.today().isoweekday()
        # Pick a day that is NOT today
        non_today = {d for d in range(1, 8) if d != today_iso}
        t = _make_timer(work_days=non_today)
        assert t.display_goal == 0

    def test_work_day_shows_configured_goal(self) -> None:
        today_iso = date.today().isoweekday()
        t = _make_timer(work_days={today_iso}, goal=8)
        assert t.display_goal == 8


# ---- Long Rest Progress Signal ----

class TestLongRestProgress:
    def test_progress_during_work(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 3
        signals: list[tuple[int, int]] = []
        t.long_rest_progress_changed.connect(
            lambda c, m: signals.append((c, m))
        )
        t._emit_long_rest_progress()
        assert signals == [(3, 4)]

    def test_progress_visible_during_rest(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.REST
        t._work_sessions_since_long_rest = 2
        signals: list[tuple[int, int]] = []
        t.long_rest_progress_changed.connect(
            lambda c, m: signals.append((c, m))
        )
        t._emit_long_rest_progress()
        assert signals == [(2, 4)]

    def test_progress_hidden_during_long_rest(self) -> None:
        t = _make_timer(work_periods_before_long_rest=4)
        t._state = Period.LONG_REST
        t._work_sessions_since_long_rest = 4
        signals: list[tuple[int, int]] = []
        t.long_rest_progress_changed.connect(
            lambda c, m: signals.append((c, m))
        )
        t._emit_long_rest_progress()
        assert signals == [(0, 0)]

    def test_progress_hidden_when_long_rest_disabled(self) -> None:
        t = _make_timer(long_rest_enabled=False)
        t._state = Period.WORK
        t._work_sessions_since_long_rest = 3
        signals: list[tuple[int, int]] = []
        t.long_rest_progress_changed.connect(
            lambda c, m: signals.append((c, m))
        )
        t._emit_long_rest_progress()
        assert signals == [(0, 0)]


# ---- Configure ----

class TestConfigure:
    def test_configure_updates_durations(self) -> None:
        t = _make_timer()
        t.configure(work_duration_mins=30, rest_duration_mins=10, long_rest_duration_mins=20)
        assert t._work_secs == 30 * 60
        assert t._rest_secs == 10 * 60
        assert t._long_rest_secs == 20 * 60

    def test_configure_emits_daily_count(self) -> None:
        t = _make_timer(goal=5, work_days={1, 2, 3, 4, 5, 6, 7})
        signals: list[tuple[int, int]] = []
        t.daily_count_changed.connect(lambda c, g: signals.append((c, g)))
        t._work_periods_completed_today = 2
        t.configure(goal=10, work_days={1, 2, 3, 4, 5, 6, 7})
        assert (2, 10) in signals
