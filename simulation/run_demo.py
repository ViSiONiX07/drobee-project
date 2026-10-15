#!/usr/bin/env python3
"""
Bee-Brain Simulation — Standalone Demo.

Demonstrates the Phase 1 simulation engine running independently
without Webots, PySide6, or any hardware.

Usage
-----
    python -m simulation.run_demo          # from repository root
    python simulation/run_demo.py          # alternative

The demo:
1. Creates a simulator with default physics.
2. Lifts the drone from the ground using thrust.
3. Hovers for a short period.
4. Applies forward movement.
5. Applies a yaw rotation.
6. Releases thrust and lets the drone descend.
7. Prints state snapshots at each phase.
"""

from __future__ import annotations

import math
import sys

from simulation.core.drone_state import DroneState
from simulation.core.physics import PhysicsConfig
from simulation.core.simulator import Simulator, SimulatorConfig


def print_state(label: str, sim: Simulator) -> None:
    """Print a labelled snapshot of the current simulation state."""
    s = sim.state
    print(
        f"  [{label:>14s}]  "
        f"t={sim.elapsed_time:6.3f}s  "
        f"tick={sim.tick:5d}  "
        f"pos=({s.position[0]:+7.3f}, {s.position[1]:+7.3f}, {s.position[2]:+7.3f})  "
        f"vel=({s.velocity[0]:+6.3f}, {s.velocity[1]:+6.3f}, {s.velocity[2]:+6.3f})  "
        f"rpy=({math.degrees(s.roll):+6.1f}°, "
        f"{math.degrees(s.pitch):+6.1f}°, "
        f"{math.degrees(s.yaw):+6.1f}°)"
    )


def main() -> None:
    """Run the standalone simulation demo."""

    print()
    print("=" * 72)
    print("  BEE-BRAIN PHASE 1 SIMULATION DEMO")
    print("=" * 72)
    print()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    physics_config = PhysicsConfig(
        gravity=9.81,
        damping=0.1,
        max_velocity=5.0,
        ground_level=0.0,
    )

    sim_config = SimulatorConfig(
        dt=0.016,           # ~60 Hz, matching Webots TIME_STEP=16 ms
        physics=physics_config,
        seed=42,            # Deterministic
    )

    sim = Simulator(sim_config)

    print(f"  Timestep:       {sim_config.dt} s")
    print(f"  Gravity:        {physics_config.gravity} m/s²")
    print(f"  Damping:        {physics_config.damping}")
    print(f"  Max velocity:   {physics_config.max_velocity} m/s")
    print(f"  Seed:           {sim_config.seed}")
    print()

    # ------------------------------------------------------------------
    # Phase 1: Takeoff
    # ------------------------------------------------------------------

    print("--- Phase: TAKEOFF ---")
    print_state("start", sim)

    HOVER_THRUST = physics_config.gravity + 2.0  # Slight upward bias.

    for _ in range(200):  # ~3.2 s
        sim.command_thrust(HOVER_THRUST)
        sim.step()

    print_state("after takeoff", sim)
    print()

    # ------------------------------------------------------------------
    # Phase 2: Hover
    # ------------------------------------------------------------------

    print("--- Phase: HOVER ---")

    for _ in range(100):  # ~1.6 s
        sim.command_thrust(physics_config.gravity)  # Exactly cancel gravity.
        sim.step()

    print_state("after hover", sim)
    print()

    # ------------------------------------------------------------------
    # Phase 3: Forward flight
    # ------------------------------------------------------------------

    print("--- Phase: FORWARD FLIGHT ---")

    for _ in range(150):  # ~2.4 s
        sim.command_thrust(physics_config.gravity)
        sim.command_move(3.0, 0.0)  # 3 m/s² forward.
        sim.step()

    print_state("after forward", sim)
    print()

    # ------------------------------------------------------------------
    # Phase 4: Yaw rotation
    # ------------------------------------------------------------------

    print("--- Phase: YAW ROTATION ---")

    sim.command_rotate(dyaw=math.radians(45.0))
    print_state("after yaw +45°", sim)
    print()

    # ------------------------------------------------------------------
    # Phase 5: Descent (release thrust)
    # ------------------------------------------------------------------

    print("--- Phase: DESCENT ---")

    for _ in range(500):  # ~8 s
        sim.step()  # No thrust → gravity pulls down.

    print_state("after descent", sim)
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    print("=" * 72)
    print(f"  Total ticks:    {sim.tick}")
    print(f"  Total time:     {sim.elapsed_time:.3f} s")
    print(f"  Final altitude: {sim.state.altitude:.3f} m")
    print(f"  Final speed:    {sim.state.speed:.3f} m/s")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
