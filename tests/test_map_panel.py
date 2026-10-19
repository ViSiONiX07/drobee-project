"""Mapping data, scan controls, camera state and actual export file contents."""

import math
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent

from dashboard.ui.map_panel import MapPanel, PointCloudView


@pytest.fixture
def panel(widget_factory):
    return widget_factory(MapPanel)


def test_point_input_normalizes_xyz_and_preserves_categories(widget_factory):
    view = widget_factory(PointCloudView)
    view.set_points([(1, "2", 3), (-1, 0.25, 0, "wall"), (1, 2)])
    assert view.points == [(1.0, 2.0, 3.0, "sensor"), (-1.0, 0.25, 0.0, "wall")]
    assert view.demo_mode is False
    view.set_points([])
    assert view.points == []
    assert view.demo_mode is False


def test_external_cloud_replaces_current_count_and_preserves_total(panel):
    panel.set_point_cloud([(0, 0, 0), (1, 2, 3)])
    assert panel.point_count == panel.total_point_count == 2
    assert panel.point_count_label.text() == "2"
    assert panel.bottom_count_label.text() == "BUFFER: 2 PTS"
    panel.set_point_cloud([(4, 5, 6)])
    assert panel.point_count == 1
    assert panel.total_point_count == 2
    assert panel.point_cloud.points == [(4.0, 5.0, 6.0, "sensor")]


def test_count_updates_ignore_negative_counts_and_cap_display_statistics(panel):
    panel.add_points(-5)
    assert panel.point_count == panel.total_point_count == 0
    panel.add_points(200_000)
    assert panel.point_count_label.text() == "200,000"
    assert panel.coverage_value[1].text() == "16.0 m²"
    assert panel.coverage_value[2].text() == "100.0% Chamber"
    assert panel.memory_bar.value() == 100
    assert panel.memory_label.text() == "64.0 MB / 64.0 MB"


def test_scan_lifecycle_is_idempotent_and_ticks_only_while_active(panel, monkeypatch):
    now = 100.0
    monkeypatch.setattr("dashboard.ui.map_panel.time.monotonic", lambda: now)
    monkeypatch.setattr("dashboard.ui.map_panel.random.randint", lambda *_: 100)
    panel._scan_tick()
    assert panel.point_count == 0

    panel.toggle_scan()
    assert panel.scanning is True
    assert panel.scan_timer.isActive()
    assert panel.controller_state.text() == "STATE: ACTIVE"
    log_count = len(panel.logs)
    now = 101.0
    panel.start_scan()
    assert len(panel.logs) == log_count
    assert panel.scan_started_at == 100.0

    now = 165.0
    panel._scan_tick()
    assert panel.point_count == panel.total_point_count == 100
    assert panel.elapsed_seconds == 65
    assert panel.scan_elapsed_label.text() == "SCAN DURATION: 01:05"
    assert panel.scan_progress.value() == 65

    panel.toggle_scan()
    assert not panel.scanning
    assert not panel.scan_timer.isActive()
    assert panel.controller_state.text() == "STATE: IDLE"
    panel._scan_tick()
    assert panel.point_count == 100


def test_clear_map_stops_scan_resets_counters_and_restores_marked_demo_cloud(panel):
    panel.set_point_cloud([(1, 2, 3)])
    panel.start_scan()
    panel.elapsed_seconds = 65
    panel.scan_progress.setValue(65)
    panel.clear_map()

    assert not panel.scanning
    assert not panel.scan_timer.isActive()
    assert panel.point_count == panel.total_point_count == panel.elapsed_seconds == 0
    assert panel.scan_progress.value() == 0
    assert panel.scan_elapsed_label.text() == "SCAN DURATION: 00:00"
    assert panel.point_cloud.demo_mode is True
    assert len(panel.point_cloud.points) > 0
    assert panel.bottom_count_label.text() == "BUFFER: 0 PTS"


@pytest.mark.parametrize("mode,label", [
    ("Isometric", "Cam: Iso 45° / Elev 30°"), ("Top (Z)", "Cam: Top / Z Axis"),
    ("Side (X)", "Cam: Side / X Axis"), ("First-Person", "Cam: First-Person"),
])
def test_camera_buttons_select_one_mode(panel, mode, label):
    panel.camera_buttons[mode].click()
    assert panel.point_cloud.camera_mode == mode
    assert panel.camera_info.text() == label
    assert [name for name, button in panel.camera_buttons.items() if button.isChecked()] == [mode]


def test_reset_camera_restores_zoom_and_orbit_and_trail_button_updates_view(panel):
    panel.set_camera_mode("Top (Z)")
    panel.point_cloud.yaw = 1.5
    panel.point_cloud.zoom = 2.0
    panel.reset_view()
    assert panel.point_cloud.camera_mode == "Isometric"
    assert panel.point_cloud.yaw == 0
    assert panel.point_cloud.zoom == 1
    panel.trail_button.click()
    assert panel.point_cloud.show_trail is False
    assert panel.trail_button.text() == "Trail: OFF"
    panel.trail_button.click()
    assert panel.point_cloud.show_trail is True


@pytest.mark.parametrize("size", [10, 20, 50])
def test_density_presets_and_slider_stay_synchronized(panel, size):
    panel.density_buttons[size].click()
    assert panel.voxel_mm == panel.voxel_slider.value() == size
    assert panel.voxel_label.text() == f"{size} mm"
    assert [value for value, button in panel.density_buttons.items() if button.isChecked()] == [size]
    panel.voxel_slider.setValue(17)
    assert panel.voxel_mm == 17
    assert panel.voxel_top_label.text() == "Voxel Grid: 17mm Isotropic"
    assert not any(button.isChecked() for button in panel.density_buttons.values())


def test_sensor_state_and_signed_velocity_updates(panel):
    for healthy in (False, True):
        panel.set_sensor_status(healthy)
        panel.set_optical_flow_status(healthy)
        assert panel.tof_badge.text() == ("● READY" if healthy else "● ERROR")
        assert panel.flow_badge.text() == ("● GROUND LOCK" if healthy else "● NO LOCK")
    panel.set_velocity(-0.125, 0.5)
    assert panel.velocity_x_label.text() == "-0.12 m/s"
    assert panel.velocity_y_label.text() == "+0.50 m/s"


@pytest.mark.parametrize("mode,expected", [
    ("Top (Z)", (288, 396)), ("Side (X)", (376, -44)),
    ("First-Person", (301.2, 8.8)), ("Isometric", (136.64, 48.4)),
])
def test_known_point_projection_for_each_camera(widget_factory, mode, expected):
    view = widget_factory(PointCloudView)
    view.resize(400, 400)
    view.set_camera_mode(mode)
    point = view._project(1, 2, 3)
    assert (point.x(), point.y()) == pytest.approx(expected)
    view.yaw = math.pi / 2
    view.set_camera_mode("Top (Z)")
    rotated = view._project(1, 0, 0)
    assert (rotated.x(), rotated.y()) == pytest.approx((200, 308))


def test_wheel_zoom_is_bounded_and_left_drag_changes_orbit(widget_factory):
    view = widget_factory(PointCloudView)
    def wheel(delta):
        return QWheelEvent(QPointF(), QPointF(), QPoint(), QPoint(0, delta),
                           Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)

    for _ in range(30):
        view.wheelEvent(wheel(120))
    assert view.zoom == 2.5
    for _ in range(50):
        view.wheelEvent(wheel(-120))
    assert view.zoom == 0.45

    def mouse(kind, x, button, buttons):
        return QMouseEvent(kind, QPointF(x, 10), QPointF(x, 10), button, buttons, Qt.NoModifier)

    view.mousePressEvent(mouse(QMouseEvent.Type.MouseButtonPress, 10, Qt.LeftButton, Qt.LeftButton))
    view.mouseMoveEvent(mouse(QMouseEvent.Type.MouseMove, 30, Qt.NoButton, Qt.LeftButton))
    assert view.yaw == pytest.approx(0.16)
    view.mouseReleaseEvent(mouse(QMouseEvent.Type.MouseButtonRelease, 30, Qt.LeftButton, Qt.NoButton))
    view.mouseMoveEvent(mouse(QMouseEvent.Type.MouseMove, 80, Qt.NoButton, Qt.NoButton))
    assert view.yaw == pytest.approx(0.16)
    assert not view.dragging
    assert view.last_mouse is None


@pytest.mark.parametrize("format_index,extension", [(0, ".ply"), (1, ".xyz")])
@pytest.mark.parametrize("point_count", [0, 2])
@pytest.mark.parametrize("existing_extension", [False, True])
def test_export_writes_header_count_and_six_decimal_coordinates(
    panel, monkeypatch, tmp_path, format_index, extension, point_count, existing_extension,
):
    points = [(1.25, -2.5, 0, "floor"), (-0.125, 3, 4.5, "wall")][:point_count]
    panel.set_point_cloud(points)
    panel.format_combo.setCurrentIndex(format_index)
    filename = "cloud" + (extension.upper() if existing_extension else "")
    destination = tmp_path / filename
    dialog = Mock(return_value=(str(destination), ""))
    monkeypatch.setattr("dashboard.ui.map_panel.QFileDialog.getSaveFileName", dialog)

    panel.export_ply()

    output = destination if existing_extension else tmp_path / (filename + extension)
    lines = output.read_text().splitlines()
    coordinates = ["1.250000 -2.500000 0.000000", "-0.125000 3.000000 4.500000"][:point_count]
    if format_index == 0:
        assert lines[:7] == [
            "ply", "format ascii 1.0", f"element vertex {point_count}",
            "property float x", "property float y", "property float z", "end_header",
        ]
        assert lines[7:] == coordinates
    else:
        assert lines == coordinates
    assert list(tmp_path.iterdir()) == [output]
    assert f"Exported {point_count:,} points" in panel.logs[-1]
    assert dialog.call_args.args[2] == "bee_brain_map" + extension


def test_cancel_export_does_not_write_or_log(panel, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dashboard.ui.map_panel.QFileDialog.getSaveFileName", lambda *_: ("", ""))
    previous_logs = list(panel.logs)
    panel.export_ply()
    assert list(tmp_path.iterdir()) == []
    assert panel.logs == previous_logs


def test_export_os_error_is_logged_without_crashing(panel, monkeypatch, tmp_path):
    missing_parent = tmp_path / "missing" / "cloud.ply"
    monkeypatch.setattr("dashboard.ui.map_panel.QFileDialog.getSaveFileName", lambda *_: (str(missing_parent), ""))
    panel.export_ply()
    assert "ERROR: Export failed:" in panel.logs[-1]
    assert not missing_parent.exists()
