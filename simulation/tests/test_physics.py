"""
Unit tests for simulation.core.physics.PhysicsEngine.

Covers:
- Gravity effect on free-falling drone.
- Damping reducing velocity over time.
- Velocity clamping.
- Ground collision / altitude clamping.
- Movement commands (thrust, horizontal acceleration, rotation).
- PhysicsConfig validation (invalid values).
- Multi-step consistency.
- Deterministic repeated updates.
"""

import math

import numpy as np
import numpy.testing as npt
import pytest

from simulation.core.drone_state import DroneState
from simulation.core.physics import PhysicsConfig, PhysicsEngine


# ==================================================================
# PhysicsConfig Validation
# ==================================================================

class TestPhysicsConfigValidation:
    """Ensure invalid config values raise ValueError."""

    def test_negative_gravity_rejected(self):
        with pytest.raises(ValueError, match="gravity"):
            PhysicsConfig(gravity=-1.0)

    def test_damping_below_zero_rejected(self):
        with pytest.raises(ValueError, match="damping"):
            PhysicsConfig(damping=-0.1)

    def test_damping_above_one_rejected(self):
        with pytest.raises(ValueError, match="damping"):
            PhysicsConfig(damping=1.5)

    def test_max_velocity_zero_rejected(self):
        with pytest.raises(ValueError, match="max_velocity"):
            PhysicsConfig(max_velocity=0.0)

    def test_max_velocity_negative_rejected(self):
        with pytest.raises(ValueError, match="max_velocity"):
            PhysicsConfig(max_velocity=-1.0)

    def test_valid_config_accepted(self):
        config = PhysicsConfig(
            gravity=9.81,
            damping=0.5,
            max_velocity=10.0,
            ground_level=-1.0,
        )
        assert config.gravity == 9.81


# ==================================================================
# Gravity
# ==================================================================

class TestGravity:
    """Test that gravity accelerates the drone downward."""

    def test_free_fall_increases_downward_velocity(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 100.0)  # High up.
        # Allow max_velocity >= 10.0 so free fall isn't clipped at default 5.0
        engine = PhysicsEngine(PhysicsConfig(damping=0.0, max_velocity=20.0))

        engine.step(state, dt=1.0)

        # After 1 s of free-fall: vz ≈ −9.81 m/s
        assert state.velocity[2] == pytest.approx(-9.81, abs=0.01)

    def test_free_fall_reduces_altitude(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 100.0)
        engine = PhysicsEngine(PhysicsConfig(damping=0.0, max_velocity=20.0))

        engine.step(state, dt=1.0)

        # Position should have decreased from 100.
        assert state.altitude < 100.0

    def test_zero_gravity_no_fall(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 10.0)
        engine = PhysicsEngine(PhysicsConfig(gravity=0.0, damping=0.0))

        engine.step(state, dt=1.0)

        assert state.altitude == pytest.approx(10.0)
        assert state.velocity[2] == pytest.approx(0.0)


# ==================================================================
# Damping
# ==================================================================

class TestDamping:
    """Test that damping reduces velocity over time."""

    def test_damping_reduces_velocity(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 100.0)
        state.set_velocity(10.0, 0.0, 0.0)
        engine = PhysicsEngine(
            PhysicsConfig(gravity=0.0, damping=0.5, max_velocity=15.0)
        )

        engine.step(state, dt=1.0)

        # After 1 s with damping=0.5: factor = 1 − 0.5*1 = 0.5
        # But velocity is first updated by acceleration (0), then damped.
        assert state.velocity[0] < 10.0
        assert state.velocity[0] > 0.0

    def test_zero_damping_preserves_velocity(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 100.0)
        state.set_velocity(5.0, 0.0, 0.0)
        engine = PhysicsEngine(
            PhysicsConfig(gravity=0.0, damping=0.0)
        )

        engine.step(state, dt=0.1)

        assert state.velocity[0] == pytest.approx(5.0)


# ==================================================================
# Velocity Clamping
# ==================================================================

class TestVelocityClamping:
    """Test hard velocity limits."""

    def test_velocity_clamped_to_max(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 100.0)
        state.set_velocity(0.0, 0.0, 0.0)
        state.set_acceleration(100.0, 0.0, 0.0)
        engine = PhysicsEngine(
            PhysicsConfig(gravity=0.0, damping=0.0, max_velocity=3.0)
        )

        engine.step(state, dt=1.0)

        assert state.velocity[0] == pytest.approx(3.0)

    def test_negative_velocity_clamped(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 100.0)
        state.set_velocity(-100.0, 0.0, 0.0)
        engine = PhysicsEngine(
            PhysicsConfig(gravity=0.0, damping=0.0, max_velocity=2.0)
        )

        engine.step(state, dt=0.01)

        assert state.velocity[0] >= -2.0


# ==================================================================
# Ground Collision
# ==================================================================

class TestGroundCollision:
    """Test altitude floor enforcement."""

    def test_altitude_clamped_at_ground(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 0.5)
        state.set_velocity(0.0, 0.0, -10.0)
        engine = PhysicsEngine(PhysicsConfig(damping=0.0, max_velocity=15.0))

        engine.step(state, dt=1.0)

        assert state.altitude >= 0.0

    def test_downward_velocity_zeroed_on_ground_contact(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 0.01)
        state.set_velocity(0.0, 0.0, -5.0)
        engine = PhysicsEngine(PhysicsConfig(damping=0.0))

        engine.step(state, dt=1.0)

        assert state.velocity[2] >= 0.0

    def test_custom_ground_level(self):
        state = DroneState()
        state.set_position(0.0, 0.0, -0.5)
        state.set_velocity(0.0, 0.0, -1.0)
        engine = PhysicsEngine(
            PhysicsConfig(ground_level=-1.0, damping=0.0, gravity=0.0)
        )

        engine.step(state, dt=0.1)

        # Position should remain above −1.0 after step.
        assert state.altitude >= -1.0

    def test_on_ground_no_penetration(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 0.0)
        engine = PhysicsEngine(PhysicsConfig(damping=0.0))

        engine.step(state, dt=0.016)

        # Should stay at ground, not go negative.
        assert state.altitude >= 0.0


# ==================================================================
# Movement Commands
# ==================================================================

class TestMovementCommands:
    """Test thrust and horizontal acceleration commands."""

    def test_thrust_exceeding_gravity_climbs(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 1.0)
        engine = PhysicsEngine(PhysicsConfig(damping=0.0, max_velocity=20.0))

        # Apply upward thrust > gravity.
        engine.apply_thrust(state, 20.0)
        engine.step(state, dt=0.1)

        # Net upward acceleration = 20.0 − 9.81 = 10.19 m/s²
        assert state.velocity[2] > 0.0
        assert state.altitude > 1.0

    def test_forward_acceleration(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 10.0)
        engine = PhysicsEngine(
            PhysicsConfig(gravity=0.0, damping=0.0)
        )

        engine.apply_horizontal_acceleration(state, 5.0, 0.0)
        engine.step(state, dt=0.1)

        assert state.velocity[0] > 0.0
        assert state.position[0] > 0.0

    def test_lateral_acceleration(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 10.0)
        engine = PhysicsEngine(
            PhysicsConfig(gravity=0.0, damping=0.0)
        )

        engine.apply_horizontal_acceleration(state, 0.0, 3.0)
        engine.step(state, dt=0.1)

        assert state.velocity[1] > 0.0
        assert state.position[1] > 0.0


# ==================================================================
# Rotation Commands
# ==================================================================

class TestRotationCommands:
    """Test orientation increment commands."""

    def test_yaw_rotation(self):
        state = DroneState()
        engine = PhysicsEngine()

        engine.apply_rotation(state, 0.0, 0.0, math.radians(45.0))

        assert state.yaw == pytest.approx(math.radians(45.0))

    def test_roll_rotation(self):
        state = DroneState()
        engine = PhysicsEngine()

        engine.apply_rotation(state, math.radians(10.0), 0.0, 0.0)

        assert state.roll == pytest.approx(math.radians(10.0))

    def test_angle_wrapping(self):
        state = DroneState()
        engine = PhysicsEngine()

        # Rotate past π → should wrap.
        engine.apply_rotation(state, 0.0, 0.0, math.pi + 0.5)

        assert -math.pi < state.yaw <= math.pi


# ==================================================================
# dt Validation
# ==================================================================

class TestDtValidation:
    """Ensure invalid dt raises ValueError."""

    def test_zero_dt_rejected(self):
        state = DroneState()
        engine = PhysicsEngine()
        with pytest.raises(ValueError, match="dt"):
            engine.step(state, dt=0.0)

    def test_negative_dt_rejected(self):
        state = DroneState()
        engine = PhysicsEngine()
        with pytest.raises(ValueError, match="dt"):
            engine.step(state, dt=-0.01)


# ==================================================================
# Multi-Step Consistency
# ==================================================================

class TestMultiStepConsistency:
    """Verify that repeated steps produce consistent, accumulating results."""

    def test_repeated_gravity_steps(self):
        state = DroneState()
        state.set_position(0.0, 0.0, 500.0)
        engine = PhysicsEngine(PhysicsConfig(damping=0.0, max_velocity=20.0))

        for _ in range(100):
            engine.step(state, dt=0.01)

        # After 1 s of free-fall from 500 m, altitude should be < 500.
        assert state.altitude < 500.0
        assert state.velocity[2] < 0.0

    def test_deterministic_repeated_runs(self):
        """Two identical sequences must produce identical results."""
        def run_sim():
            state = DroneState()
            state.set_position(0.0, 0.0, 10.0)
            engine = PhysicsEngine(PhysicsConfig(damping=0.05))
            for _ in range(200):
                engine.step(state, dt=0.016)
            return state.to_dict()

        result_a = run_sim()
        result_b = run_sim()

        npt.assert_array_almost_equal(
            result_a["position"],
            result_b["position"],
        )
        npt.assert_array_almost_equal(
            result_a["velocity"],
            result_b["velocity"],
        )