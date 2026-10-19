"""Deterministic telemetry fixtures and headless Qt widget lifecycle helpers."""

import os

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def telemetry_data():
    """A fresh packet using only the original, required protocol fields."""
    return {
        "altitude_cm": 142.8,
        "drift_x": 0.15,
        "drift_y": -0.08,
        "battery_v": 3.85,
        "motor_pwm": [0, 64, 128, 255],
        "link_ok": True,
        "sensor_status": {"tof": True, "optical_flow": True},
    }


@pytest.fixture
def make_packet(telemetry_data):
    from dashboard.services.telemetry import TelemetryPacket

    def make(**overrides):
        return TelemetryPacket.model_validate({**telemetry_data, **overrides})

    return make


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    from dashboard.ui.main_window import apply_dark_style

    app = QApplication.instance() or QApplication([])
    apply_dark_style(app)
    return app


@pytest.fixture
def widget_factory(qapp):
    """Stop demo timers immediately and dispose every widget after each test."""
    from PySide6.QtCore import QCoreApplication, QEvent, QTimer

    widgets = []

    def make(widget_type):
        widget = widget_type()
        widgets.append(widget)
        for timer in widget.findChildren(QTimer):
            timer.stop()
        return widget

    yield make

    for widget in reversed(widgets):
        for timer in widget.findChildren(QTimer):
            timer.stop()
        widget.close()
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture
def window(widget_factory):
    from dashboard.ui.main_window import MainWindow

    return widget_factory(MainWindow)
