"""
Unit tests for simulation.core.simulator.Simulator.

Covers:
- Default construction and initial state.
- Single step execution.
- Multi-step run.
- Tick counter and elapsed time.
- Deterministic simulation with seeded RNG.
- Reset restores initial conditions.
- Thrust command → climb.
- Horizontal movement commands.
- Rotation commands.
- Ground boundary during simulation.
- SimulatorConfig validation.
- Invalid step counts.
"""

import math

import numpy.testing as npt
import pytest

from simulation.core.drone_state import DroneState
from simulation.core.physics import PhysicsConfig
from simulation.core.simulator import Simulator, SimulatorConfig


# ==================================================================
# Default Construction
# ==================================================================

class TestSimulatorDefaults:
    """Verify freshly constructed simulator state."""

    def test_initial_tick_is_zero(self):
        sim = Simulator()
        assert sim.tick == 0

    def test_initial_elapsed_time_is_zero(self):
        sim = Simulator()
        assert sim.elapsed_time == 0.0

    def test_initial_state_at_origin(self):
        sim = Simulator()
        npt.assert_array_equal(sim.state.position, [0.0, 0.0, 0.0])

    def test_initial_velocity_is_zero(self):
        sim = Simulator()
        npt.assert_array_equal(sim.state.velocity, [0.0, 0.0, 0.0])

    def test_initial_orientation_is_level(self):
        sim = Simulator()
        assert sim.state.roll == 0.0
        assert sim.state.pitch == 0.0
        assert sim.state.yaw == 0.0

    def test_rng_is_none_without_seed(self):
        sim = Simulator()
        assert sim.rng is None

    def test_rng_exists_with_seed(self):
        sim = Simulator(SimulatorConfig(seed=42))
        assert sim.rng is not None


# ==================================================================
# Single Step
# ==================================================================

class TestSimulatorStep:
    """Test single-step execution."""

    def test_step_increments_tick(self):
        sim = Simulator()
        sim.step()
        assert sim.tick == 1

    def test_step_advances_elapsed_time(self):
        sim = Simulator(SimulatorConfig(dt=0.01))
        sim.step()
        assert sim.elapsed_time == pytest.approx(0.01)

    def test_step_on_ground_stays_on_ground(self):
        sim = Simulator()
        sim.step()
        assert sim.state.altitude >= 0.0


# ==================================================================
# Multi-Step Run
# ==================================================================

class TestSimulatorRun:
    """Test multi-step execution via run()."""

    def test_run_advances_tick_count(self):
        sim = Simulator()
        sim.run(steps=50)
        assert sim.tick == 50

    def test_run_elapsed_time(self):
        config = SimulatorConfig(dt=0.01)
        sim = Simulator(config)
        sim.run(steps=100)
        assert sim.elapsed_time == pytest.approx(1.0)

    def test_run_zero_steps_rejected(self):
        sim = Simulator()
        with pytest.raises(ValueError, match="steps"):
            sim.run(steps=0)

    def test_run_negative_steps_rejected(self):
        sim = Simulator()
        with pytest.raises(ValueError, match="steps"):
            sim.run(steps=-1)


# ==================================================================
# Reset
# ==================================================================

class TestSimulatorReset:
    """Test state reset."""

    def test_reset_restores_tick(self):
        sim = Simulator()
        sim.run(steps=10)
        sim.reset()
        assert sim.tick == 0

    def test_reset_restores_elapsed_time(self):
        sim = Simulator()
        sim.run(steps=10)
        sim.reset()
        assert sim.elapsed_time == 0.0

    def test_reset_restores_state(self):
        sim = Simulator()
        sim.run(steps=10)
        sim.reset()
        npt.assert_array_equal(sim.state.position, [0.0, 0.0, 0.0])
        npt.assert_array_equal(sim.state.velocity, [0.0, 0.0, 0.0])

    def test_reset_reseeds_rng(self):
        config = SimulatorConfig(seed=99)
        sim = Simulator(config)
        val_before = sim.rng.random()

        sim.reset()
        val_after = sim.rng.random()

        assert val_before == val_after


# ==================================================================
# Thrust / Climb
# ==================================================================

class TestSimulatorThrust:
    """Test vertical thrust commands."""

    def test_thrust_exceeding_gravity_produces_climb(self):
        physics = PhysicsConfig(gravity=9.81, damping=0.0)
        config = SimulatorConfig(dt=0.016, physics=physics)
        sim = Simulator(config)
        sim.state.set_position(0.0, 0.0, 1.0)

        for _ in range(100):
            sim.command_thrust(20.0)
            sim.step()

        assert sim.state.altitude > 1.0
        assert sim.state.velocity[2] > 0.0

    def test_hover_thrust_maintains_altitude(self):
        physics = PhysicsConfig(gravity=9.81, damping=0.0)
        config = SimulatorConfig(dt=0.016, physics=physics)
        sim = Simulator(config)
        sim.state.set_position(0.0, 0.0, 5.0)

        for _ in range(100):
            sim.command_thrust(9.81)  # Exactly cancel gravity.
            sim.step()

        # Should stay very close to 5.0 m.
        assert sim.state.altitude == pytest.approx(5.0, abs=0.1)


# ==================================================================
# Horizontal Movement
# ==================================================================

class TestSimulatorMovement:
    """Test horizontal movement commands."""

    def test_forward_movement(self):
        physics = PhysicsConfig(gravity=0.0, damping=0.0)
        config = SimulatorConfig(dt=0.016, physics=physics)
        sim = Simulator(config)

        for _ in range(100):
            sim.command_move(5.0, 0.0)
            sim.step()

        assert sim.state.position[0] > 0.0

    def test_lateral_movement(self):
        physics = PhysicsConfig(gravity=0.0, damping=0.0)
        config = SimulatorConfig(dt=0.016, physics=physics)
        sim = Simulator(config)

        for _ in range(100):
            sim.command_move(0.0, 3.0)
            sim.step()

        assert sim.state.position[1] > 0.0

    def test_backward_movement(self):
        physics = PhysicsConfig(gravity=0.0, damping=0.0)
        config = SimulatorConfig(dt=0.016, physics=physics)
        sim = Simulator(config)

        for _ in range(100):
            sim.command_move(-5.0, 0.0)
            sim.step()

        assert sim.state.position[0] < 0.0


# ==================================================================
# Rotation
# ==================================================================

class TestSimulatorRotation:
    """Test rotation commands."""

    def test_yaw_rotation(self):
        sim = Simulator()
        sim.command_rotate(dyaw=math.radians(45.0))
        assert sim.state.yaw == pytest.approx(math.radians(45.0))

    def test_roll_rotation(self):
        sim = Simulator()
        sim.command_rotate(droll=math.radians(10.0))
        assert sim.state.roll == pytest.approx(math.radians(10.0))

    def test_pitch_rotation(self):
        sim = Simulator()
        sim.command_rotate(dpitch=math.radians(-5.0))
        assert sim.state.pitch == pytest.approx(math.radians(-5.0))


# ==================================================================
# Ground Boundary During Simulation
# ==================================================================

class TestSimulatorGround:
    """Ensure ground boundary is enforced during simulation."""

    def test_free_fall_stops_at_ground(self):
        sim = Simulator(SimulatorConfig(
            dt=0.01,
            physics=PhysicsConfig(damping=0.0),
        ))
        sim.state.set_position(0.0, 0.0, 1.0)

        sim.run(steps=1000)  # Let it fall.

        assert sim.state.altitude >= 0.0
        assert sim.state.velocity[2] >= 0.0


# ==================================================================
# Config Validation
# ==================================================================

class TestSimulatorConfigValidation:
    """Ensure invalid config raises ValueError."""

    def test_zero_dt_rejected(self):
        with pytest.raises(ValueError, match="dt"):
            SimulatorConfig(dt=0.0)

    def test_negative_dt_rejected(self):
        with pytest.raises(ValueError, match="dt"):
            SimulatorConfig(dt=-0.01)


# ==================================================================
# Determinism
# ==================================================================

class TestSimulatorDeterminism:
    """Verify that identical configs produce identical results."""

    def test_identical_runs_produce_identical_states(self):
        def run():
            config = SimulatorConfig(
                dt=0.016,
                physics=PhysicsConfig(damping=0.05),
                seed=123,
            )
            sim = Simulator(config)
            sim.state.set_position(0.0, 0.0, 10.0)

            for i in range(200):
                sim.command_thrust(9.81 + 0.5)
                sim.step()

            return sim.state.to_dict()

        a = run()
        b = run()

        npt.assert_array_almost_equal(a["position"], b["position"])
        npt.assert_array_almost_equal(a["velocity"], b["velocity"])
        assert a["roll"] == b["roll"]
        assert a["pitch"] == b["pitch"]
        assert a["yaw"] == b["yaw"]

    def test_reset_replays_identically(self):
        config = SimulatorConfig(
            dt=0.016,
            physics=PhysicsConfig(damping=0.05),
            seed=42,
        )
        sim = Simulator(config)
        sim.state.set_position(0.0, 0.0, 10.0)

        for _ in range(50):
            sim.command_thrust(10.0)
            sim.step()

        first_run = sim.state.to_dict()

        sim.reset()
        sim.state.set_position(0.0, 0.0, 10.0)

        for _ in range(50):
            sim.command_thrust(10.0)
            sim.step()

        second_run = sim.state.to_dict()

        npt.assert_array_almost_equal(
            first_run["position"], second_run["position"]
        )
