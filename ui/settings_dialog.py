"""Settings dialog for the Pomodoro app."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from database import Database
from ui.theme import get_stylesheet

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

ALARMS_DIR = Path(__file__).resolve().parent.parent / "alarms"
AUDIO_EXTENSIONS = {".wav", ".mp3"}

def _scan_alarms() -> list[str]:
    """Return sorted list of alarm files in the alarms/ directory."""
    if not ALARMS_DIR.is_dir():
        return []
    files: list[str] = []
    for entry in sorted(ALARMS_DIR.iterdir()):
        if entry.is_file() and entry.suffix.lower() in AUDIO_EXTENSIONS:
            files.append(entry.name)
    return files


class SettingsDialog(QDialog):
    """Modal dialog for configuring timer settings."""

    def __init__(self, db: Database, scheme: str = "dark", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db

        self.setStyleSheet(get_stylesheet(scheme))

        self.setWindowTitle("settings")
        self.setModal(True)
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # --- Duration spinners ---
        self._work_spin = QSpinBox()
        self._work_spin.setRange(1, 120)
        self._work_spin.setSuffix(" min")
        self._work_spin.setFixedWidth(100)
        form.addRow("work_duration:", self._work_spin)

        self._rest_spin = QSpinBox()
        self._rest_spin.setRange(1, 60)
        self._rest_spin.setSuffix(" min")
        self._rest_spin.setFixedWidth(100)
        form.addRow("rest_duration:", self._rest_spin)

        self._long_rest_spin = QSpinBox()
        self._long_rest_spin.setRange(1, 60)
        self._long_rest_spin.setSuffix(" min")
        self._long_rest_spin.setFixedWidth(100)
        form.addRow("long_rest_duration:", self._long_rest_spin)

        # --- Long rest settings ---
        self._long_rest_enabled_cb = QCheckBox()
        form.addRow("long_rest:", self._long_rest_enabled_cb)

        self._periods_before_spin = QSpinBox()
        self._periods_before_spin.setRange(1, 10)
        self._periods_before_spin.setFixedWidth(100)
        form.addRow("work_periods_before_long_rest:", self._periods_before_spin)

        # --- Goal ---
        self._goal_spin = QSpinBox()
        self._goal_spin.setRange(1, 99)
        self._goal_spin.setFixedWidth(100)
        form.addRow("goal:", self._goal_spin)

        # --- Work days ---
        self._day_checks: list[QCheckBox] = []
        days_widget = QWidget()
        days_layout = QHBoxLayout(days_widget)
        days_layout.setContentsMargins(0, 0, 0, 0)
        for i, name in enumerate(DAY_NAMES):
            cb = QCheckBox(name)
            self._day_checks.append(cb)
            days_layout.addWidget(cb)
        form.addRow("work_days:", days_widget)

        # --- Color scheme ---
        self._scheme_combo = QComboBox()
        self._scheme_combo.addItems(["dark", "light"])
        self._scheme_combo.setFixedWidth(100)
        form.addRow("colour_scheme:", self._scheme_combo)

        # --- Always on top ---
        self._always_on_top_cb = QCheckBox()
        form.addRow("always_on_top:", self._always_on_top_cb)

        # --- Alarm sound ---
        self._alarm_combo = QComboBox()
        self._alarm_combo.addItem("Default")
        for fname in _scan_alarms():
            self._alarm_combo.addItem(fname)
        self._alarm_combo.setFixedWidth(140)
        form.addRow("alarm_sound:", self._alarm_combo)

        layout.addLayout(form)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_settings()

    def _load_settings(self) -> None:
        s = self._db.get_all_settings()

        self._work_spin.setValue(int(s.get("work_duration", 25)))
        self._rest_spin.setValue(int(s.get("rest_duration", 5)))
        self._long_rest_spin.setValue(int(s.get("long_rest_duration", 15)))
        self._long_rest_enabled_cb.setChecked(
            s.get("long_rest_enabled", "1") == "1"
        )
        self._periods_before_spin.setValue(
            int(s.get("work_periods_before_long_rest", 4))
        )
        self._goal_spin.setValue(int(s.get("goal", 14)))

        work_days_str = s.get("work_days", "1,2,3,4,5")
        work_days = {int(d.strip()) for d in work_days_str.split(",") if d.strip()}
        for i, cb in enumerate(self._day_checks):
            cb.setChecked((i + 1) in work_days)

        scheme = s.get("color_scheme", "dark")
        self._scheme_combo.setCurrentIndex(0 if scheme == "dark" else 1)

        self._always_on_top_cb.setChecked(s.get("always_on_top", "0") == "1")

        alarm = s.get("alarm_sound", "")
        idx = self._alarm_combo.findText(alarm) if alarm else 0
        self._alarm_combo.setCurrentIndex(max(idx, 0))

    def _on_save(self) -> None:
        work_days = ",".join(
            str(i + 1) for i, cb in enumerate(self._day_checks) if cb.isChecked()
        )
        # Ensure at least one day is selected
        if not work_days:
            work_days = "1,2,3,4,5"

        self._db.set_settings(
            {
                "work_duration": str(self._work_spin.value()),
                "rest_duration": str(self._rest_spin.value()),
                "long_rest_duration": str(self._long_rest_spin.value()),
                "long_rest_enabled": "1" if self._long_rest_enabled_cb.isChecked() else "0",
                "work_periods_before_long_rest": str(self._periods_before_spin.value()),
                "goal": str(self._goal_spin.value()),
                "work_days": work_days,
                "color_scheme": "dark" if self._scheme_combo.currentIndex() == 0 else "light",
                "always_on_top": "1" if self._always_on_top_cb.isChecked() else "0",
                "alarm_sound": ""
                if self._alarm_combo.currentIndex() <= 0
                else self._alarm_combo.currentText(),
            }
        )
        self.accept()
