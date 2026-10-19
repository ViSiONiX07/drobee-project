"""Telemetry card boundaries, rolling charts and estimated velocity."""

import pytest

from dashboard.ui.telemetry_panel import BatteryCard, TelemetryPanel
from dashboard.ui.theme import Palette


@pytest.fixture
def panel(widget_factory, monkeypatch):
    monkeypatch.setattr("dashboard.ui.telemetry_panel.random.gauss", lambda *_: 0.0)
    return widget_factory(TelemetryPanel)


@pytest.mark.parametrize("voltage,status,color,fraction", [
    (2.5, "CRITICAL", Palette.ACCENT_CRIMSON, 0.0),
    (3.4, "CRITICAL", Palette.ACCENT_CRIMSON, 1 / 3),
    (3.4001, "WARNING", Palette.ACCENT_AMBER, 0.4001 / 1.2),
    (3.7, "WARNING", Palette.ACCENT_AMBER, 0.7 / 1.2),
    (3.7001, "HEALTHY", Palette.ACCENT_SAGE, 0.7001 / 1.2),
    (5.0, "HEALTHY", Palette.ACCENT_SAGE, 1.0),
])
def test_battery_thresholds_and_visual_fill(widget_factory, voltage, status, color, fraction):
    card = widget_factory(BatteryCard)
    card.bar.resize(122, 7)

    card.update_voltage(voltage)

    assert card.value_label.text() == f"{voltage:.2f}"
    assert card.status_label.text() == status
    assert color in card.status_label.styleSheet()
    assert color in card.fill.styleSheet()
    assert card.fill.width() == pytest.approx(120 * fraction, abs=1)
    assert 0 <= card.fill.width() <= 120


def test_packet_updates_cards_in_display_units(panel, make_packet):
    panel.update_telemetry(make_packet())

    assert panel.altitude_card.value_label.text() == "1.43"
    assert panel.altitude_card.raw_label.text() == "RAW ALTITUDE: 142.8 cm"
    assert "EST." not in panel.altitude_card.velocity_label.text()
    assert panel.altitude_card.setpoint_label.text() == "TARGET: NOT PROVIDED"
    assert panel.drift_card.position_label.text() == "POS DRIFT X / Y\n+0.150 / -0.080"
    assert panel.drift_card.radar.drift_x == 0.15
    assert panel.drift_card.radar.drift_y == -0.08
    assert panel.battery_card.value_label.text() == "3.85"
    assert panel.altitude_chart.series_a == pytest.approx([1.428])
    assert "BUFFER: 1 / 100" in panel.session_label.text()


@pytest.mark.parametrize("dt,expected", [(0.5, "+1.000"), (0.0, "+500.000")])
def test_estimated_velocity_uses_monotonic_interval_with_zero_interval_guard(
    panel, make_packet, monkeypatch, dt, expected,
):
    now = 10.0
    monkeypatch.setattr("time.monotonic", lambda: now)
    panel.update_telemetry(make_packet(altitude_cm=100))
    now += dt

    panel.update_telemetry(make_packet(altitude_cm=150))

    assert panel.altitude_card.velocity_label.text() == (
        f"VERTICAL VELOCITY: {expected} m/s (EST.)"
    )


@pytest.mark.parametrize("x,y,within", [
    (0.2, -0.2, True), (-0.2, 0.2, True),
    (0.2001, 0, False), (0, -0.2001, False),
])
def test_drift_corridor_includes_both_signed_boundaries(panel, make_packet, x, y, within):
    panel.update_telemetry(make_packet(drift_x=x, drift_y=y))
    assert panel.drift_card.status_label.text() == (
        "WITHIN DISPLAY CORRIDOR" if within else "OUTSIDE DISPLAY CORRIDOR"
    )


@pytest.mark.parametrize("link,tof,flow", [
    (True, True, True), (False, False, False), (True, False, True), (False, True, False),
])
def test_link_and_sensor_states_can_recover(panel, make_packet, link, tof, flow):
    # Start with the opposite state so stale text and colors are detectable.
    for link_ok, tof_ok, flow_ok in [(not link, not tof, not flow), (link, tof, flow)]:
        panel.update_telemetry(make_packet(
            link_ok=link_ok,
            sensor_status={"tof": tof_ok, "optical_flow": flow_ok},
        ))
    assert panel.comms_card.status_label.text() == (
        "● CONNECTED" if link else "● DISCONNECTED"
    )
    assert panel.sensor_table.state_labels["tof"].text() == ("NOMINAL" if tof else "ERROR")
    assert panel.sensor_table.state_labels["flow"].text() == ("NOMINAL" if flow else "ERROR")
    color = Palette.ACCENT_SAGE if link else Palette.ACCENT_CRIMSON
    assert color in panel.comms_card.status_label.styleSheet()


@pytest.mark.parametrize("altitude_cm", [0, 100, -10])
def test_flat_altitude_keeps_a_nonzero_chart_range(panel, make_packet, altitude_cm):
    packet = make_packet(altitude_cm=altitude_cm)
    for _ in range(3):
        panel.update_telemetry(packet)
    assert panel.altitude_chart.y_min >= 0
    assert panel.altitude_chart.y_max > panel.altitude_chart.y_min
    if altitude_cm >= 0:
        assert panel.altitude_chart.y_min <= altitude_cm / 100 <= panel.altitude_chart.y_max


def test_charts_roll_over_together_and_keep_latest_samples(panel, make_packet):
    for altitude_cm in range(105):
        panel.update_telemetry(make_packet(altitude_cm=altitude_cm))

    expected = [value / 100 for value in range(5, 105)]
    assert list(panel.altitude_history) == expected
    assert panel.altitude_chart.series_a == expected
    assert panel.sample_count == 105
    assert len(panel.roll_rate_history) == len(panel.pitch_rate_history) == 100
    assert panel.rate_chart.series_a == list(panel.roll_rate_history)
    assert panel.rate_chart.series_b == list(panel.pitch_rate_history)
    assert len(set(panel.rate_chart.series_a)) > 1
    assert "BUFFER: 100 / 100" in panel.session_label.text()
