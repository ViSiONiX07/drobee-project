"""
Unit tests for simulation.core.drone_state.DroneState.

Covers:
- Default initialisation values.
- Position, velocity, acceleration setters.
- Orientation setters and degree conversion.
- Altitude and speed convenience properties.
- State reset.
- Snapshot to_dict() serialisation.
- Deep copy independence.
"""

import math

import numpy as np
import numpy.testing as npt
import pytest

from simulation.core.drone_state import DroneState


# ==================================================================
# Default Initialisation
# ==================================================================

class TestDroneStateDefaults:
    """Verify that a freshly constructed DroneState has correct defaults."""

    def test_default_position_is_origin(self):
        state = DroneState()
        npt.assert_array_equal(state.position, [0.0, 0.0, 0.0])

    def test_default_velocity_is_zero(self):
        state = DroneState()
        npt.assert_array_equal(state.velocity, [0.0, 0.0, 0.0])

    def test_default_acceleration_is_zero(self):
        state = DroneState()
        npt.assert_array_equal(state.acceleration, [0.0, 0.0, 0.0])

    def test_default_orientation_is_level(self):
        state = DroneState()
        assert state.roll == 0.0
        assert state.pitch == 0.0
        assert state.yaw == 0.0

    def test_default_altitude_is_zero(self):
        state = DroneState()
        assert state.altitude == 0.0

    def test_default_speed_is_zero(self):
        state = DroneState()
        assert state.speed == 0.0


# ==================================================================
# Position
# ==================================================================

class TestDroneStatePosition:
    """Tests for position manipulation."""

    def test_set_position(self):
        state = DroneState()
        state.set_position(1.0, 2.0, 3.0)
        npt.assert_array_almost_equal(state.position, [1.0, 2.0, 3.0])

    def test_altitude_reflects_z(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 5.5)
        assert state.altitude == pytest.approx(5.5)

    def test_position_direct_assignment(self):
        state = DroneState()
        state.position[:] = [10.0, 20.0, 30.0]
        assert state.altitude == pytest.approx(30.0)


# ==================================================================
# Velocity
# ==================================================================

class TestDroneStateVelocity:
    """Tests for velocity manipulation."""

    def test_set_velocity(self):
        state = DroneState()
        state.set_velocity(1.0, -1.0, 0.5)
        npt.assert_array_almost_equal(state.velocity, [1.0, -1.0, 0.5])

    def test_speed_magnitude(self):
        state = DroneState()
        state.set_velocity(3.0, 4.0, 0.0)
        assert state.speed == pytest.approx(5.0)


# ==================================================================
# Acceleration
# ==================================================================

class TestDroneStateAcceleration:
    """Tests for acceleration manipulation."""

    def test_set_acceleration(self):
        state = DroneState()
        state.set_acceleration(0.0, 0.0, 9.81)
        npt.assert_array_almost_equal(
            state.acceleration, [0.0, 0.0, 9.81]
        )


# ==================================================================
# Orientation
# ==================================================================

class TestDroneStateOrientation:
    """Tests for orientation manipulation and unit conversion."""

    def test_set_orientation(self):
        state = DroneState()
        state.set_orientation(0.1, 0.2, 0.3)
        assert state.roll == pytest.approx(0.1)
        assert state.pitch == pytest.approx(0.2)
        assert state.yaw == pytest.approx(0.3)

    def test_orientation_tuple(self):
        state = DroneState()
        state.set_orientation(0.1, 0.2, 0.3)
        assert state.orientation == pytest.approx((0.1, 0.2, 0.3))

    def test_orientation_degrees(self):
        state = DroneState()
        state.set_orientation(
            math.radians(45.0),
            math.radians(-30.0),
            math.radians(90.0),
        )
        deg = state.orientation_degrees
        assert deg[0] == pytest.approx(45.0)
        assert deg[1] == pytest.approx(-30.0)
        assert deg[2] == pytest.approx(90.0)


# ==================================================================
# Reset
# ==================================================================

class TestDroneStateReset:
    """Tests for state reset."""

    def test_reset_clears_all(self):
        state = DroneState()
        state.set_position(5.0, 5.0, 5.0)
        state.set_velocity(1.0, 1.0, 1.0)
        state.set_acceleration(2.0, 2.0, 2.0)
        state.set_orientation(0.5, 0.5, 0.5)

        state.reset()

        npt.assert_array_equal(state.position, [0.0, 0.0, 0.0])
        npt.assert_array_equal(state.velocity, [0.0, 0.0, 0.0])
        npt.assert_array_equal(state.acceleration, [0.0, 0.0, 0.0])
        assert state.roll == 0.0
        assert state.pitch == 0.0
        assert state.yaw == 0.0


# ==================================================================
# Serialisation
# ==================================================================

class TestDroneStateSerialization:
    """Tests for to_dict() snapshot."""

    def test_to_dict_structure(self):
        state = DroneState()
        state.set_position(1.0, 2.0, 3.0)
        state.set_velocity(0.1, 0.2, 0.3)
        state.set_orientation(0.01, 0.02, 0.03)

        d = state.to_dict()

        assert d["position"] == pytest.approx([1.0, 2.0, 3.0])
        assert d["velocity"] == pytest.approx([0.1, 0.2, 0.3])
        assert d["roll"] == pytest.approx(0.01)
        assert d["pitch"] == pytest.approx(0.02)
        assert d["yaw"] == pytest.approx(0.03)

    def test_to_dict_returns_plain_lists(self):
        state = DroneState()
        d = state.to_dict()
        assert isinstance(d["position"], list)
        assert isinstance(d["velocity"], list)


# ==================================================================
# Copy Independence
# ==================================================================

class TestDroneStateCopy:
    """Tests that copy() produces an independent clone."""

    def test_copy_is_independent(self):
        original = DroneState()
        original.set_position(1.0, 2.0, 3.0)

        clone = original.copy()
        clone.set_position(10.0, 20.0, 30.0)

        # Original must be unchanged.
        npt.assert_array_almost_equal(
            original.position, [1.0, 2.0, 3.0]
        )


# ==================================================================
# Instance Independence (default_factory)
# ==================================================================

class TestDroneStateIndependence:
    """Ensure each DroneState instance has its own arrays."""

    def test_two_instances_are_independent(self):
        a = DroneState()
        b = DroneState()
        a.set_position(1.0, 2.0, 3.0)

        npt.assert_array_equal(b.position, [0.0, 0.0, 0.0])
