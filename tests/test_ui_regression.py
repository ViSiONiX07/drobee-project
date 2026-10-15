"""
Automated Pytest UI Regression Suite for Bee-Brain PySide6 Ground Station.
Tests six-page navigation, active button states, and telemetry dispatch.
Executes headlessly using the Qt offscreen platform.
"""

import json
import os

import pytest

# Enforce headless offscreen rendering prior to importing PySide6 GUI modules
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from dashboard.ui.main_window import MainWindow, apply_dark_style


@pytest.fixture(scope="session")
def qapp():
    """Ensure a singleton QApplication instance exists for offscreen tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    apply_dark_style(app)
    return app


@pytest.fixture
def window(qapp):
    """Create a MainWindow instance with the background fake telemetry timer stopped for deterministic testing."""
    win = MainWindow()
    # Stop background timer so tests control packet delivery deterministically
    win.fake_telemetry.stop()
    yield win
    win.fake_telemetry.stop()
    win.close()


def test_window_initialization(window):
    """Verify window title, structure, and 6-page widget stack."""
    assert window.windowTitle() == "Bee-Brain"
    assert window.pages.count() == 6
    assert window.telemetry_panel is not None
    assert window.control_panel is not None
    assert window.map_panel is not None
    assert window.diagnostics_panel is not None
    assert window.drone_view_panel is not None
    assert window.keyboard_control_panel is not None


def test_six_page_navigation_and_active_button_state(window):
    """Verify that navigating to each of the 6 pages updates the active button state and page title."""
    pages_to_test = [
        (0, "TELEMETRY", window.telemetry_button),
        (1, "FLIGHT CONTROL", window.control_button),
        (2, "3D MAPPING", window.map_button),
        (3, "DIAGNOSTICS", window.diagnostics_button),
        (4, "3D DRONE VIEW", window.drone_view_button),
        (5, "KEYBOARD CONTROL TEST", window.keyboard_test_button),
    ]

    all_buttons = [btn for _, _, btn in pages_to_test]

    for page_idx, expected_title, active_btn in pages_to_test:
        window.show_page(page_idx, expected_title, active_btn)

        # 1. Verify stacked widget is displaying the correct page index
        assert window.pages.currentIndex() == page_idx

        # 2. Verify page header title matches
        assert window.page_title.text() == expected_title

        # 3. Verify target button is active, and ALL other 5 buttons are inactive
        for btn in all_buttons:
            if btn is active_btn:
                assert btn.property("active") is True, f"Button {btn.text()} should be active for page {page_idx}"
            else:
                assert btn.property("active") is False, f"Button {btn.text()} should be inactive for page {page_idx}"


def test_telemetry_packet_ingestion_and_dispatch(window):
    """Verify telemetry packet parsing, label formatting, and multi-panel dispatch."""
    packet_data = {
        "altitude_cm": 142.8,
        "drift_x": 0.15,
        "drift_y": -0.08,
        "battery_v": 3.85,
        "motor_pwm": [130, 135, 132, 138],
        "link_ok": True,
        "sensor_status": {
            "tof": True,
            "optical_flow": True
        }
    }

    raw_json = json.dumps(packet_data)
    window.handle_telemetry(raw_json)

    # Telemetry Panel assertions
    assert "142.80 cm" in window.telemetry_panel.alt_label.text()
    assert "3.85 V" in window.telemetry_panel.bat_label.text()
    assert "CONNECTED" in window.telemetry_panel.link_label.text()
    assert "130" in window.telemetry_panel.motors_label.text()

    # Diagnostics Panel assertions
    assert window.diagnostics_panel.link_status.text() == "● CONNECTED"
    assert window.diagnostics_panel.tof_status.text() == "● OK"
    assert window.diagnostics_panel.optical_flow_status.text() == "● OK"
    assert window.diagnostics_panel.battery_status.text() == "3.85 V"
    assert window.diagnostics_panel.power_status.text() == "HEALTHY"


def test_invalid_telemetry_packet_handling(window):
    """Verify that malformed telemetry triggers error status without crashing the dashboard."""
    corrupted_json = "NOT_A_VALID_JSON_STRING"
    window.handle_telemetry(corrupted_json)

    assert window.system_status.text() == "● SYSTEM ERROR"
    assert window.diagnostics_panel.system_status.text() == "ERROR"
