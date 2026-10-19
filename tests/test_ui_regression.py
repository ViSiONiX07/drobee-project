"""
Automated Pytest UI Regression Suite for Bee-Brain PySide6 Ground Station.
Tests six-page navigation, active button states, and telemetry dispatch.
Executes headlessly using the Qt offscreen platform.
"""

import json

import pytest
from PySide6.QtGui import QPalette

from dashboard.ui.theme import Palette


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
        window.show_page(page_idx, expected_title.lower(), active_btn)

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


def test_telemetry_packet_ingestion_and_dispatch(window, telemetry_data):
    """Verify telemetry packet parsing, label formatting, and multi-panel dispatch."""
    raw_json = json.dumps(telemetry_data)
    window.handle_telemetry(raw_json)

    # Telemetry Panel assertions
    assert window.telemetry_panel.altitude_card.value_label.text() == "1.43"
    assert window.telemetry_panel.battery_card.value_label.text() == "3.85"
    assert window.telemetry_panel.comms_card.status_label.text() == "● CONNECTED"
    assert window.control_panel.altitude_value.text() == "142.8 cm"
    assert window.control_panel.motor_values[1][1].text() == "PWM: 64 / 255"
    assert window.drone_view_panel.battery_badge.text() == "BATT: 3.85 V"
    packet = window.telemetry_service.get_latest()
    assert window.control_panel.last_packet is packet
    assert window.drone_view_panel.telemetry_packet is packet
    assert window.diagnostics_panel.packet_count.text() == "1"

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
    assert window.telemetry_service.get_history() == []
    assert window.telemetry_service.get_stats()["validation_errors"] == 1


def test_shell_readouts_and_theme_follow_failure_and_recovery(window, telemetry_data):
    for healthy in (False, True):
        window.handle_telemetry(json.dumps({
            **telemetry_data,
            "link_ok": healthy,
            "sensor_status": {"tof": healthy, "optical_flow": healthy},
        }))
        assert window.header_link_status.text() == (
            "● LINK: CONNECTED" if healthy else "● LINK: DISCONNECTED"
        )
        assert window.header_link_status.property("state") == ("nominal" if healthy else "fault")
        # Exercise the new QSS selectors through the widget's resolved color.
        window.header_link_status.ensurePolished()
        assert window.header_link_status.palette().color(QPalette.ColorRole.WindowText).name() == (
            Palette.ACCENT_SAGE if healthy else Palette.ACCENT_CRIMSON
        ).lower()
        assert window.status_battery.text() == "BATT: 3.85 V"
        assert window.status_tof.text() == (
            "TOF: LOCK  |  FLOW: TRACKING" if healthy else "TOF: ERROR  |  FLOW: ERROR"
        )
        assert window.header_rate_status.text() == "RATE: 10 Hz"
    assert window.telemetry_service.get_stats()["received_count"] == 2


@pytest.mark.parametrize("tof,flow,expected", [
    (True, False, "TOF: LOCK  |  FLOW: ERROR"),
    (False, True, "TOF: ERROR  |  FLOW: TRACKING"),
])
def test_shell_distinguishes_independent_sensor_failures(window, telemetry_data, tof, flow, expected):
    window.handle_telemetry(json.dumps({
        **telemetry_data, "sensor_status": {"tof": tof, "optical_flow": flow},
    }))
    assert window.status_tof.text() == expected


def test_selecting_keyboard_page_activates_keyboard_controls(window):
    window.keyboard_test_button.click()
    assert window.pages.currentWidget() is window.keyboard_control_panel
    assert window.keyboard_test_button.property("active") is True
    assert window.keyboard_control_panel.footer_status.text() == "●  KEYBOARD ACTIVE"
