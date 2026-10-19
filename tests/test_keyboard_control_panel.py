"""Keyboard simulation input, focus cleanup, tilt limits and timing metrics."""

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent

from dashboard.ui.keyboard_control_panel import KeyboardControlPanel


@pytest.fixture
def panel(widget_factory):
    return widget_factory(KeyboardControlPanel)


def press(panel, key, repeat=False):
    event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.NoModifier, "", repeat)
    panel.keyPressEvent(event)
    return event


def release(panel, key, repeat=False):
    event = QKeyEvent(QEvent.Type.KeyRelease, key, Qt.NoModifier, "", repeat)
    panel.keyReleaseEvent(event)
    return event


@pytest.mark.parametrize("key,roll,pitch", [
    (Qt.Key_W, 0, 0.16), (Qt.Key_8, 0, 0.16),
    (Qt.Key_S, 0, -0.16), (Qt.Key_5, 0, -0.16),
    (Qt.Key_A, -0.16, 0), (Qt.Key_4, -0.16, 0),
    (Qt.Key_D, 0.16, 0), (Qt.Key_6, 0.16, 0),
])
def test_each_direction_and_numpad_alias_moves_one_tick(panel, key, roll, pitch):
    inactive_style = panel.key_buttons[key].styleSheet()
    assert press(panel, key).isAccepted()
    assert panel.motion_timer.isActive()
    panel.update_motion()
    assert panel.roll == pytest.approx(roll)
    assert panel.pitch == pytest.approx(pitch)
    assert panel.gauge.roll == panel.roll
    assert panel.gauge.pitch == panel.pitch
    assert panel.key_buttons[key].styleSheet() != inactive_style
    assert release(panel, key).isAccepted()
    assert not panel.motion_timer.isActive()
    assert panel.pressed_keys == set()
    assert panel.keystrokes == 2


def test_repeated_presses_and_auto_repeat_do_not_double_count_or_release(panel):
    press(panel, Qt.Key_W, repeat=True)
    assert panel.keystrokes == 0
    assert not panel.motion_timer.isActive()
    press(panel, Qt.Key_W)
    press(panel, Qt.Key_W)
    press(panel, Qt.Key_W, repeat=True)
    release(panel, Qt.Key_W, repeat=True)
    assert panel.keystrokes == 1
    assert panel.pressed_keys == {Qt.Key_W}
    assert panel.motion_timer.isActive()
    release(panel, Qt.Key_W)
    release(panel, Qt.Key_W)
    assert panel.keystrokes == 2


def test_aliases_do_not_double_motion_and_opposites_cancel(panel):
    for key in (Qt.Key_W, Qt.Key_8, Qt.Key_A, Qt.Key_4):
        press(panel, key)
    panel.update_motion()
    assert panel.roll == pytest.approx(-0.16)
    assert panel.pitch == pytest.approx(0.16)
    for key in (Qt.Key_D, Qt.Key_S):
        press(panel, key)
    panel.update_motion()
    assert panel.roll == pytest.approx(-0.16)
    assert panel.pitch == pytest.approx(0.16)


@pytest.mark.parametrize("keys,expected", [
    ((Qt.Key_W, Qt.Key_D), 15.0), ((Qt.Key_S, Qt.Key_A), -15.0),
])
def test_held_keys_clamp_both_axes_at_tilt_limit(panel, keys, expected):
    for key in keys:
        press(panel, key)
    for _ in range(110):
        panel.update_motion()
    assert panel.roll == panel.pitch == expected
    assert panel.margin_value.text() == "0.0°"
    assert panel.gauge.roll == panel.gauge.pitch == expected


def test_releasing_one_key_keeps_other_key_moving(panel):
    press(panel, Qt.Key_W)
    press(panel, Qt.Key_D)
    release(panel, Qt.Key_W)
    assert panel.motion_timer.isActive()
    panel.update_motion()
    assert panel.pitch == 0
    assert panel.roll == pytest.approx(0.16)
    release(panel, Qt.Key_D)
    assert not panel.motion_timer.isActive()
    assert panel.primary_held.text() == "HELD: NONE"


@pytest.mark.parametrize("action", ["escape", "focus_out"])
def test_escape_or_focus_loss_releases_keys_without_leveling(panel, action):
    press(panel, Qt.Key_8)
    panel.update_motion()
    assert panel.numpad_status.text() == "CO-PILOT: ACTIVE"
    if action == "escape":
        press(panel, Qt.Key_Escape)
    else:
        panel.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
    assert not panel.pressed_keys
    assert not panel.motion_timer.isActive()
    assert panel.pitch == pytest.approx(0.16)
    assert panel.numpad_status.text() == "CO-PILOT: READY"


def test_space_levels_attitude_and_clears_held_keys(panel):
    press(panel, Qt.Key_A)
    press(panel, Qt.Key_W)
    panel.update_motion()
    press(panel, Qt.Key_Space)
    assert panel.roll == panel.pitch == panel.yaw == 0
    assert panel.pressed_keys == set()
    assert not panel.motion_timer.isActive()
    assert panel.margin_value.text() == "15.0°"


def test_unmapped_key_has_no_motion_or_diagnostic_effect(panel):
    press(panel, Qt.Key_F1)
    release(panel, Qt.Key_F1)
    assert panel.keystrokes == 0
    assert not panel.pressed_keys
    assert not panel.motion_timer.isActive()


def test_event_intervals_and_jitter_use_controlled_monotonic_time(panel, monkeypatch):
    now = 10.0
    monkeypatch.setattr("dashboard.ui.keyboard_control_panel.time.monotonic", lambda: now)
    panel.register_key_event(Qt.Key_W, "KEY_DOWN")
    now = 10.010
    panel.register_key_event(Qt.Key_W, "KEY_UP")
    assert panel.debounce_value.text() == "10.0 ms"
    now = 10.030
    panel.register_key_event(Qt.Key_A, "KEY_DOWN")
    assert panel.debounce_value.text() == "20.0 ms"
    assert panel.jitter_value.text() == "5.00 ms"
    # Floating point rounding may make the integer progress bar 49 or 50.
    assert 49 <= panel.jitter_bar.value() <= 50
    assert panel.keystrokes_value.text() == "3"


def test_timing_buffers_and_log_are_bounded_and_clear_keeps_counters(panel, monkeypatch):
    now = 0.0
    monkeypatch.setattr("dashboard.ui.keyboard_control_panel.time.monotonic", lambda: now)
    for index in range(105):
        now = index / 100
        panel.register_key_event(Qt.Key_W, "KEY_DOWN")
    assert len(panel.event_times) == 20
    assert len(panel.event_log_lines) == 100
    assert panel.keystrokes == 105
    panel.clear_log()
    assert len(panel.event_log_lines) == 0
    assert panel.event_log.text() == "Event log cleared."
    assert panel.log_count_label.text() == "105 KEY EVENTS"
    assert panel.keystrokes == 105


def test_clock_rolls_seconds_into_minutes(panel, monkeypatch):
    monkeypatch.setattr("dashboard.ui.keyboard_control_panel.time.monotonic", lambda: panel.started_at + 125)
    panel.update_clock()
    assert panel.uptime_label.text() == "UPTIME: 02:05"
