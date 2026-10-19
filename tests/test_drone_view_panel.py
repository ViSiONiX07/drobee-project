"""Visual drone orientation, geometry, layers and simulation lifecycle."""

from types import SimpleNamespace

import pytest

from dashboard.ui.drone_view_panel import DroneCanvas, DroneViewPanel


@pytest.fixture
def panel(widget_factory):
    return widget_factory(DroneViewPanel)


@pytest.mark.parametrize("orientation,point,expected", [
    ((0, 0, 0), (1, 2, 3), (1, 2, 3)),
    ((90, 0, 0), (0, 1, 0), (0, 0, 1)),
    ((0, 90, 0), (1, 0, 0), (0, 0, -1)),
    ((0, 0, 90), (1, 0, 0), (0, 1, 0)),
])
def test_rotation_preserves_basis_vectors(widget_factory, orientation, point, expected):
    canvas = widget_factory(DroneCanvas)
    canvas.set_orientation(*orientation)
    assert canvas._rotate(*point) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("value,expected", [(-1, 0), (0, 0), (123.5, 123.5), (200, 200), (201, 200)])
def test_visual_throttle_clamps_to_zero_through_two_hundred(widget_factory, value, expected):
    canvas = widget_factory(DroneCanvas)
    canvas.set_throttle(value)
    assert canvas.throttle == expected


def test_invalid_camera_mode_leaves_current_camera_unchanged(widget_factory):
    canvas = widget_factory(DroneCanvas)
    canvas.set_camera_mode("TOP (Z)")
    canvas.set_camera_mode("unknown")
    assert canvas.camera_mode == "TOP (Z)"


def test_partial_layer_update_preserves_other_layers(widget_factory):
    canvas = widget_factory(DroneCanvas)
    canvas.set_layers(propellers=False)
    assert canvas.show_propellers is False
    assert canvas.show_thrust_vectors is canvas.show_clearance is canvas.show_grid is True


def test_override_sliders_update_canvas_and_readouts(panel):
    panel.roll_slider.setValue(-30)
    panel.pitch_slider.setValue(15)
    panel.yaw_slider.setValue(270)
    panel.throttle_slider.setValue(150)
    assert (panel.canvas.roll, panel.canvas.pitch, panel.canvas.yaw) == (-30, 15, 270)
    assert panel.roll_value.text() == panel.roll_override_value.text() == "-30.0°"
    assert panel.pitch_value.text() == panel.pitch_override_value.text() == "+15.0°"
    assert panel.yaw_value.text() == "270.0°"
    assert panel.canvas.throttle == 150
    assert panel.throttle_override_value.text() == "150%"


@pytest.mark.parametrize("axis", ["roll", "pitch"])
def test_step_increment_saturates_at_45_degrees(panel, axis):
    slider = getattr(panel, f"{axis}_slider")
    panel.apply_step(axis)
    assert slider.value() == 15
    for _ in range(5):
        panel.apply_step(axis)
    assert slider.value() == 45


def test_layer_checkboxes_update_canvas(panel):
    for checkbox, attribute in [
        (panel.propellers_check, "show_propellers"),
        (panel.thrust_check, "show_thrust_vectors"),
        (panel.clearance_check, "show_clearance"),
        (panel.grid_check, "show_grid"),
    ]:
        for enabled in (False, True):
            checkbox.setChecked(enabled)
            assert getattr(panel.canvas, attribute) is enabled


def test_demo_start_stop_and_reset_are_deterministic(panel):
    panel.toggle_demo()
    assert panel.demo_running is True
    assert panel.demo_timer.isActive()
    assert panel.demo_button.text() == "STOP GIMBAL SWEEP"
    panel.update_demo()
    assert panel.demo_time == pytest.approx(0.04)
    assert panel.canvas.demo_phase == pytest.approx(0.04)
    assert panel.yaw_slider.value() == 1
    panel.toggle_demo()
    assert not panel.demo_running
    assert not panel.demo_timer.isActive()

    panel.toggle_demo()
    panel.roll_slider.setValue(30)
    panel.pitch_slider.setValue(-15)
    panel.throttle_slider.setValue(175)
    panel.reset_orientation()
    assert not panel.demo_running
    assert not panel.demo_timer.isActive()
    assert panel.demo_time == panel.canvas.demo_phase == 0
    assert (panel.canvas.roll, panel.canvas.pitch, panel.canvas.yaw) == (0, 0, 0)
    assert panel.canvas.throttle == panel.throttle_slider.value() == 100
    assert panel.demo_button.text() == "START GIMBAL SWEEP"


def test_battery_packet_updates_badge_without_overriding_visual_attitude(panel, make_packet):
    panel.roll_slider.setValue(25)
    packet = make_packet(battery_v=3.75)
    panel.update_telemetry(packet)
    assert panel.telemetry_packet is packet
    assert panel.battery_badge.text() == "BATT: 3.75 V"
    assert panel.canvas.roll == 25


@pytest.mark.parametrize("packet", [None, SimpleNamespace(), SimpleNamespace(battery_v=None), SimpleNamespace(battery_v="invalid")])
def test_incompatible_battery_packet_preserves_last_display(panel, make_packet, packet):
    panel.update_telemetry(make_packet())
    previous_text = panel.battery_badge.text()
    panel.update_telemetry(packet)
    assert panel.battery_badge.text() == previous_text
