"""Flight control telemetry readouts and explicitly simulated controls."""

import pytest
from PySide6.QtWidgets import QHBoxLayout

from dashboard.ui.control_panel import ControlPanel


@pytest.fixture
def panel(widget_factory):
    return widget_factory(ControlPanel)


def test_telemetry_updates_motor_percentages_and_average_throttle(panel, make_packet):
    packet = make_packet()
    panel.update_telemetry(packet)

    assert panel.last_packet is packet
    assert panel.altitude_value.text() == "142.8 cm"
    assert panel.drift_x_value.text() == "+0.15"
    assert panel.drift_y_value.text() == "-0.08"
    assert panel.battery_value.text() == "3.850 V"
    assert [bar.value() for bar in panel.motor_bars] == [0, 64, 128, 255]
    assert [labels[0].text() for labels in panel.motor_values] == ["0%", "25%", "50%", "100%"]
    assert [labels[1].text() for labels in panel.motor_values] == [
        "PWM: 0 / 255", "PWM: 64 / 255", "PWM: 128 / 255", "PWM: 255 / 255",
    ]
    assert panel.throttle_bar.value() == 112
    assert panel.throttle_value.text() == "44%"
    assert "Altitude: 142.8 cm" in panel.command_status.text()


def test_16_bit_pwm_is_clamped_to_legacy_motor_display(panel, make_packet):
    panel.update_telemetry(make_packet(motor_pwm=[0, 255, 256, 65535]))
    assert [bar.value() for bar in panel.motor_bars] == [0, 255, 255, 255]
    assert [labels[0].text() for labels in panel.motor_values] == ["0%", "100%", "100%", "100%"]


@pytest.mark.parametrize("voltage,color", [(3.4, ControlPanel.RED), (3.7, ControlPanel.AMBER), (3.71, ControlPanel.GREEN)])
def test_battery_warning_boundaries(panel, make_packet, voltage, color):
    panel.update_telemetry(make_packet(battery_v=voltage))
    assert color in panel.battery_value.styleSheet()


def test_link_and_sensor_failure_then_recovery(panel, make_packet):
    for healthy in (False, True):
        panel.update_telemetry(make_packet(
            link_ok=healthy,
            sensor_status={"tof": healthy, "optical_flow": healthy},
        ))
        assert panel.link_badge.text() == ("● LINK: CONNECTED" if healthy else "● LINK: LOST")
        assert panel.failsafe_status.text() == ("READY" if healthy else "LINK LOST")
        assert panel.tof_status.text() == ("OK" if healthy else "ERROR")
        assert panel.flow_status.text() == ("TRACKING" if healthy else "ERROR")
        assert (panel.GREEN if healthy else panel.RED) in panel.link_badge.styleSheet()


def test_arm_button_toggles_simulation_and_leaves_cutoff_disabled(panel):
    assert panel.is_armed is False
    assert not panel.kill_button.isEnabled()

    panel.arm_button.click()
    assert panel.is_armed is True
    assert panel.arm_status.text() == "ARMED (SIM)"
    assert panel.state_label.text() == "ARMED — SIMULATION ONLY"
    assert panel.arm_button.text() == "DISARM SIMULATION"

    panel.arm_button.click()
    assert panel.is_armed is False
    assert panel.state_label.text() == "DISARMED"
    assert panel.arm_button.text() == "ARM SIMULATION"
    assert not panel.kill_button.isEnabled()


@pytest.mark.parametrize("mode", ["ALTITUDE HOLD", "POSITION HOLD", "AUTONOMOUS", "STABILIZE"])
def test_dropdown_selects_local_mode_used_in_telemetry_summary(panel, make_packet, mode):
    # Force an actual transition even when testing the initial STABILIZE item.
    panel.flight_mode.setCurrentText("AUTONOMOUS" if mode == "STABILIZE" else "STABILIZE")
    panel.flight_mode.setCurrentText(mode)
    assert panel.current_mode == mode
    assert panel.command_status.text() == f"Mode selected: {mode} — UI only"
    panel.update_telemetry(make_packet())
    assert f"Mode: {mode}" in panel.command_status.text()


def test_trim_sliders_display_tenths_and_reset_both_axes(panel):
    panel.pitch_slider.setValue(-50)
    panel.roll_slider.setValue(50)
    assert panel.pitch_trim_value.text() == "-5.0°"
    assert panel.roll_trim_value.text() == "5.0°"
    panel.show_mock_saved()
    assert panel.command_status.text() == "Trim values saved in the UI session only."
    panel.reset_trims()
    assert panel.pitch_slider.value() == panel.roll_slider.value() == 0
    assert panel.pitch_trim_value.text() == panel.roll_trim_value.text() == "0.0°"


@pytest.mark.parametrize("value,expected,percentage", [(-1, 0, "0%"), (128, 128, "50%"), (999, 255, "100%")])
def test_compatibility_throttle_clamps_to_display_range(panel, value, expected, percentage):
    panel.set_throttle(value)
    assert panel.throttle_bar.value() == expected
    assert panel.throttle_value.text() == percentage


def test_compatibility_attitude_and_failsafe_readouts(panel):
    panel.set_attitude(-2.5, 3.25, 180)
    assert [panel.roll_value.text(), panel.pitch_value.text(), panel.yaw_value.text()] == [
        "-2.50°", "3.25°", "180.00°",
    ]
    for active in (True, False):
        panel.set_failsafe(active)
        assert panel.failsafe_active is active
        assert panel.failsafe_status.text() == ("ACTIVE" if active else "READY")


@pytest.mark.parametrize("width,mode,count,direction", [
    (779, "one", 3, QHBoxLayout.TopToBottom),
    (780, "two", 2, QHBoxLayout.TopToBottom),
    (1179, "two", 2, QHBoxLayout.TopToBottom),
    (1180, "three", 3, QHBoxLayout.LeftToRight),
])
def test_responsive_column_breakpoints(panel, width, mode, count, direction):
    panel.scroll.viewport().resize(width, 600)
    panel.update_responsive_layout()
    assert panel._layout_mode == mode
    assert panel.columns_layout.count() == count
    assert panel.columns_layout.direction() == direction
    # Repeated layout updates must not duplicate the columns.
    panel.update_responsive_layout()
    assert panel.columns_layout.count() == count
