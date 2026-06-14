"""Stats dialog showing a line graph of completed work periods per day."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from database import Database
from ui.theme import get_stylesheet


class StatsDialog(QDialog):
    """Modal dialog displaying historical work period completion data."""

    def __init__(
        self,
        db: Database,
        today_count: int,
        scheme: str = "dark",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = db
        self._today_count = today_count
        self._current_range: str = "30d"
        self._cached_data: list[tuple[str, int]] | None = None

        if scheme == "light":
            self._bg = "#f5f5f5"
            self._fg = "#222222"
            self._accent = "#444444"
            self._line = "#444444"
        else:
            self._bg = "#1a1a1a"
            self._fg = "#e0e0e0"
            self._accent = "#888888"
            self._line = "#cccccc"

        self.setStyleSheet(get_stylesheet(scheme))
        self.setWindowTitle("history")
        self.setModal(True)
        self.resize(600, 420)

        layout = QVBoxLayout(self)

        # Matplotlib figure
        self._figure = Figure(figsize=(5, 3.5), dpi=100)
        self._figure.set_facecolor(self._bg)
        self._canvas = FigureCanvasQTAgg(self._figure)
        layout.addWidget(self._canvas)

        # Range buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ranges = ["7d", "30d", "90d", "All"]
        self._range_buttons: dict[str, QPushButton] = {}
        for r in ranges:
            btn = QPushButton(r)
            btn.setCheckable(True)
            btn.setFixedSize(56, 30)
            btn.clicked.connect(lambda checked, r=r: self._on_range_changed(r))
            btn_layout.addWidget(btn)
            self._range_buttons[r] = btn

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Hover label
        self._hover_label = QLabel("")
        self._hover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hover_label.setStyleSheet(f"color: {self._accent}; font-size: 12px;")
        layout.addWidget(self._hover_label)

        # Initial draw
        self._range_buttons["30d"].setChecked(True)
        self._draw()

        # Connect hover
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    # ---- Data ----

    def _get_work_days(self) -> set[int]:
        raw = self._db.get_setting("work_days") or "1,2,3,4,5"
        return {int(d.strip()) for d in raw.split(",") if d.strip()}

    def _get_plot_data(self) -> list[tuple[str, int]]:
        """Return (date_str, count) for work days only, with today merged in."""
        if self._cached_data is not None:
            return self._cached_data

        today_str = date.today().isoformat()
        work_days = self._get_work_days()

        # Get date range based on filter
        if self._current_range == "7d":
            since = (date.today() - timedelta(days=7)).isoformat()
        elif self._current_range == "30d":
            since = (date.today() - timedelta(days=30)).isoformat()
        elif self._current_range == "90d":
            since = (date.today() - timedelta(days=90)).isoformat()
        else:
            since = None  # All

        records = self._db.get_all_daily_records(since=since)

        # Convert to dict and filter work days
        data: dict[str, int] = {}
        for date_str, count in records:
            try:
                d = date.fromisoformat(date_str)
            except ValueError:
                continue
            if d.isoweekday() in work_days:
                data[date_str] = count

        # Merge today's count (may not be in DB yet, or may be stale)
        data[today_str] = self._today_count

        # Ensure today is included even with no records
        if today_str not in data:
            today_iso = date.today().isoweekday()
            if today_iso in work_days:
                data[today_str] = self._today_count

        # Sort by date
        sorted_items = sorted(data.items())
        self._cached_data = sorted_items
        return sorted_items

    # ---- Drawing ----

    def _draw(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(self._bg)

        data = self._get_plot_data()

        if not data:
            ax.text(
                0.5, 0.5, "no_data_yet",
                ha="center", va="center", color=self._accent,
                fontsize=14, transform=ax.transAxes,
            )
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            dates = [item[0] for item in data]
            counts = [item[1] for item in data]
            x = list(range(len(dates)))

            ax.plot(x, counts, color=self._line, linewidth=2, marker="o", markersize=5)
            ax.fill_between(x, 0, counts, color=self._line, alpha=0.15)

            # Labels
            ax.set_xticks(x)
            ax.set_xticklabels(
                [self._format_date(d) for d in dates],
                rotation=45, ha="right", fontsize=8, color=self._accent,
            )
            ax.set_ylabel("work_periods", color=self._accent, fontsize=10)

            # Styling
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(self._accent)
            ax.spines["bottom"].set_color(self._accent)
            ax.tick_params(colors=self._accent, labelsize=9)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.set_ylim(bottom=0)

        self._figure.tight_layout()
        self._canvas.draw()

    @staticmethod
    def _format_date(date_str: str) -> str:
        try:
            d = date.fromisoformat(date_str)
            return d.strftime("%b %d")
        except ValueError:
            return date_str

    # ---- Interactivity ----

    def _on_range_changed(self, range_key: str) -> None:
        self._current_range = range_key
        self._cached_data = None  # invalidate cache
        # Update button states
        for key, btn in self._range_buttons.items():
            btn.setChecked(key == range_key)
        self._hover_label.setText("")
        self._draw()

    def _on_hover(self, event) -> None:
        if event.inaxes is None:
            self._hover_label.setText("")
            return

        data = self._get_plot_data()
        if not data:
            return

        dates = [item[0] for item in data]
        counts = [item[1] for item in data]

        # Find the nearest data point
        x_data = list(range(len(dates)))
        if not x_data:
            return

        # Find closest x
        x_mouse = event.xdata
        if x_mouse is None:
            return

        closest_idx = min(
            range(len(x_data)),
            key=lambda i: abs(x_data[i] - x_mouse),
        )
        if 0 <= closest_idx < len(dates):
            self._hover_label.setText(
                f"{dates[closest_idx]}  —  {counts[closest_idx]} work_periods"
            )
