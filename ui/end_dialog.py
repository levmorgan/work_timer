"""End-of-period modal dialog with Continue / Finish buttons."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from timer_controller import PERIOD_NAMES, Period


class EndOfPeriodDialog(QDialog):
    """Modal shown when a period ends. Offers Continue / Finish with a
    5-minute countdown that auto-advances if the user doesn't interact."""

    def __init__(
        self,
        period: Period,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._result: str = "timeout"  # "continue" | "finish" | "timeout"
        self._countdown: int = 300  # 5 minutes in seconds
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_countdown)

        name = PERIOD_NAMES.get(period, "period")
        self.setWindowTitle(f"{name}_complete")
        self.setModal(True)
        self.setFixedSize(320, 160)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        message = QLabel(
            f"{name}_period_finished\n"
            "auto_advancing in 5:00..."
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        self._message_label = message

        button_layout = QHBoxLayout()
        continue_btn = QPushButton("continue")
        continue_btn.clicked.connect(self._on_continue)
        finish_btn = QPushButton("finish")
        finish_btn.clicked.connect(self._on_finish)

        button_layout.addStretch()
        button_layout.addWidget(continue_btn)
        button_layout.addWidget(finish_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self._countdown_timer.start(1000)

    def _tick_countdown(self) -> None:
        self._countdown -= 1
        if self._countdown <= 0:
            self._countdown_timer.stop()
            self._result = "timeout"
            self.accept()
        else:
            mins = self._countdown // 60
            secs = self._countdown % 60
            self._message_label.setText(
                "period_finished\n"
                f"auto_advancing in {mins}:{secs:02d}..."
            )

    def _on_continue(self) -> None:
        self._countdown_timer.stop()
        self._result = "continue"
        self.accept()

    def _on_finish(self) -> None:
        self._countdown_timer.stop()
        self._result = "finish"
        self.reject()

    @property
    def outcome(self) -> str:
        return self._result
