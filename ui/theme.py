"""Shared stylesheets for the Pomodoro app — dark and light greyscale themes."""

DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1a1a1a;
    color: #e0e0e0;
}
QLabel {
    color: #e0e0e0;
}
QLabel#timer {
    color: #e0e0e0;
    font-size: 56px;
}
QLabel#daily {
    color: #888888;
    font-size: 16px;
}
QPushButton {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #3a3a3a;
}
QPushButton:pressed {
    background-color: #444444;
}
QPushButton:checked {
    background-color: #444444;
}
QSpinBox, QComboBox, QCheckBox {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: none;
    border-bottom: 1px solid #3a3a3a;
    border-radius: 0px;
    padding: 4px 6px;
}
QSpinBox, QComboBox {
    min-width: 70px;
}
QToolTip {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #555555;
    border-radius: 2px;
    background-color: #2a2a2a;
}
QCheckBox::indicator:checked {
    background-color: #888888;
}
QComboBox QAbstractItemView {
    background-color: #2a2a2a;
    color: #e0e0e0;
    selection-background-color: #444444;
    border: 1px solid #555555;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f5f5f5;
    color: #222222;
}
QLabel {
    color: #222222;
}
QLabel#timer {
    color: #222222;
    font-size: 56px;
}
QLabel#daily {
    color: #666666;
    font-size: 16px;
}
QPushButton {
    background-color: #e0e0e0;
    color: #222222;
    border: 1px solid #999999;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QPushButton:pressed {
    background-color: #c0c0c0;
}
QPushButton:checked {
    background-color: #c0c0c0;
}
QSpinBox, QComboBox, QCheckBox {
    background-color: #f5f5f5;
    color: #222222;
    border: none;
    border-bottom: 1px solid #c0c0c0;
    border-radius: 0px;
    padding: 4px 6px;
}
QSpinBox, QComboBox {
    min-width: 70px;
}
QToolTip {
    background-color: #e0e0e0;
    color: #222222;
    border: 1px solid #999999;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #999999;
    border-radius: 2px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #666666;
}
QComboBox QAbstractItemView {
    background-color: #f5f5f5;
    color: #222222;
    selection-background-color: #d0d0d0;
    border: 1px solid #999999;
}
"""


def get_stylesheet(scheme: str) -> str:
    """Return the stylesheet for the given colour scheme ('dark' or 'light')."""
    if scheme == "light":
        return LIGHT_STYLESHEET
    return DARK_STYLESHEET
