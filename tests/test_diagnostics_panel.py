"""Packet-driven diagnostics, demo isolation and bounded event filtering."""

import pytest

from dashboard.ui.diagnostics_panel import DiagnosticsPanel


@pytest.fixture
def panel(widget_factory):
    return widget_factory(DiagnosticsPanel)


@pytest.mark.parametrize("as_dict", [False, True], ids=["model", "dict"])
@pytest.mark.parametrize("link,tof,flow", [
    (True, True, True), (False, True, True), (True, False, True), (True, True, False),
])
def test_packet_drives_health_battery_and_motors(panel, make_packet, as_dict, link, tof, flow):
    packet = make_packet(
        link_ok=link, sensor_status={"tof": tof, "optical_flow": flow},
    )
    panel.demo_timer.start()
    panel.update_telemetry(packet.model_dump() if as_dict else packet)

    assert not panel.demo_timer.isActive()
    assert panel.link_badge.text() == ("● LINK: CONNECTED" if link else "● LINK: LOST")
    assert panel.tof_status.text() == ("OK" if tof else "UNAVAILABLE")
    assert panel.optical_flow_status.text() == ("OK" if flow else "UNAVAILABLE")
    assert panel.integrity_value.text() == (
        "■ PACKET HEALTHY" if link and tof and flow else "■ CHECK REQUIRED"
    )
    assert panel.battery_number.text() == "3.85"
    assert panel.battery_status.text() == "3.85 V"
    assert panel.footer_battery.text() == "BATT: 3.85 V"
    assert [label.text() for label in panel.motor_values] == [
        "0 PWM*", "64 PWM*", "128 PWM*", "255 PWM*",
    ]

    # Even a queued demo callback must not overwrite the received values.
    panel._update_demo_values()
    assert panel.battery_number.text() == "3.85"
    assert panel.footer_battery.text() == "BATT: 3.85 V"
    assert panel.motor_values[-1].text() == "255 PWM*"


def test_partial_dictionary_defaults_missing_health_to_unavailable(panel):
    battery_before = panel.battery_number.text()
    panel.update_telemetry({"motor_pwm": (1, 2, 3, 4, 5)})
    assert panel.link_badge.text() == "● LINK: LOST"
    assert panel.tof_status.text() == panel.optical_flow_status.text() == "UNAVAILABLE"
    assert panel.battery_number.text() == battery_before
    assert [label.text() for label in panel.motor_values] == ["1 PWM*", "2 PWM*", "3 PWM*", "4 PWM*"]


@pytest.mark.parametrize("distance,tone", [
    (209, "heatHot"), (210, "heatNormal"), (349, "heatNormal"), (350, "heatFar"),
])
def test_tof_heatmap_thresholds(panel, distance, tone):
    assert panel._tof_tone(distance) == tone


def test_log_buttons_filter_entries_and_show_empty_filter(panel):
    panel.clear_status()
    panel._append_event("INFO", "info-only-marker")
    panel._append_event("ERROR", "error-only-marker")
    panel.log_filter_buttons["ERROR"].click()
    assert "error-only-marker" in panel.event_log.text()
    assert "info-only-marker" not in panel.event_log.text()
    assert [name for name, button in panel.log_filter_buttons.items()
            if button.objectName() == "logFilterActive"] == ["ERROR"]
    panel.log_filter_buttons["WARN"].click()
    assert panel.event_log.text() == "No events for this filter."
    assert panel.log_buffer_label.text() == "BUFFER: 2 / 1000 LINES"
    panel.log_filter_buttons["ALL"].click()
    assert "info-only-marker" in panel.event_log.text()
    assert "error-only-marker" in panel.event_log.text()


def test_event_storage_and_visible_tail_have_separate_bounds(panel):
    panel.clear_status()
    for index in range(1005):
        panel._append_event("INFO", f"entry-{index:04d}")
    assert len(panel._log_entries) == 1000
    assert panel._log_entries[0][2] == "entry-0005"
    lines = panel.event_log.text().splitlines()
    assert len(lines) == 80
    assert lines[0].endswith("entry-0925")
    assert lines[-1].endswith("entry-1004")
    assert panel.log_buffer_label.text() == "BUFFER: 1000 / 1000 LINES"
    panel.clear_status()
    assert panel._log_entries == []
    assert panel.event_log.text() == "No events for this filter."
    assert panel.log_buffer_label.text() == "BUFFER: 0 / 1000 LINES"


def test_self_check_identifies_simulation_and_can_be_cleared(panel):
    panel.run_system_check()
    assert panel.daemon_status.text() == "DEMO CHECK COMPLETE · HARDWARE NOT VERIFIED"
    assert "physical hardware not tested" in panel.event_log.text()
    panel.clear_status()
    assert panel.daemon_status.text() == "Log buffer cleared."
