"""
Bee-Brain Simulation Orchestrator.

Owns the simulation loop, fixed timestep, and deterministic update cycle.
Coordinates :class:`DroneState` and :class:`PhysicsEngine` without
depending on any UI framework, Webots, or hardware.

Determinism
-----------
When a ``seed`` is provided, the simulator initialises a dedicated
:class:`numpy.random.Generator` that can be used for any stochastic
elements (e.g. future sensor noise).  The simulation loop itself
(physics updates) is fully deterministic regardless of seed because
no randomness is currently injected into the physics step.

Limitations
-----------
- Uses a fixed-timestep Euler integrator.  No sub-stepping or
  Runge-Kutta integration is implemented.
- No motor model — thrust/acceleration is set directly.
- No sensor model — state is read directly.
- No telemetry emission — the caller is responsible for reading
  state and converting to the project's ``TelemetryPacket`` format.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.core.drone_state import DroneState
from simulation.core.physics import PhysicsConfig, PhysicsEngine


@dataclass
class SimulatorConfig:
    """Top-level configuration for the simulator.

    Parameters
    ----------
    dt : float
        Fixed simulation timestep in seconds (default 0.016 ≈ 60 Hz,
        matching the existing Webots ``TIME_STEP = 16`` ms).
    physics : PhysicsConfig | None
        Physics constants.  Uses defaults when *None*.
    seed : int | None
        Random seed for deterministic stochastic elements.
        *None* means no dedicated RNG is created.
    """

    dt: float = 0.016
    physics: PhysicsConfig | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.dt <= 0.0:
            raise ValueError(
                f"dt must be positive, got {self.dt}"
            )


class Simulator:
    """Fixed-timestep simulation orchestrator.

    Usage
    -----
    >>> from simulation.core import Simulator
    >>> sim = Simulator()
    >>> sim.step()                       # advance one tick
    >>> print(sim.state)                 # inspect drone state
    >>> sim.run(steps=100)               # advance 100 ticks
    >>> print(sim.elapsed_time)          # total simulated time

    Parameters
    ----------
    config : SimulatorConfig | None
        Top-level configuration.  Uses defaults when *None*.
    """

    def __init__(self, config: SimulatorConfig | None = None) -> None:
        self.config = config or SimulatorConfig()

        self.state = DroneState()
        self.physics = PhysicsEngine(self.config.physics)

        self._tick: int = 0
        self._rng: np.random.Generator | None = None

        if self.config.seed is not None:
            self._rng = np.random.default_rng(self.config.seed)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def tick(self) -> int:
        """Number of simulation ticks completed."""
        return self._tick

    @property
    def elapsed_time(self) -> float:
        """Total simulated time in seconds."""
        return self._tick * self.config.dt

    @property
    def rng(self) -> np.random.Generator | None:
        """Seeded random generator, or *None* if no seed was set."""
        return self._rng

    # ------------------------------------------------------------------
    # Simulation control
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance the simulation by one fixed timestep.

        Resets the acceleration vector after the physics step so that
        forces must be re-applied each tick (explicit force model).
        Commands set via ``command_thrust`` / ``command_move`` between
        calls to ``step()`` are consumed exactly once.
        """
        # Run physics with whatever acceleration was set since last step.
        self.physics.step(self.state, self.config.dt)

        # Clear acceleration — forces must be re-applied next tick.
        self.state.acceleration[:] = 0.0

        self._tick += 1

    def run(self, steps: int) -> None:
        """Advance the simulation by *steps* ticks.

        Parameters
        ----------
        steps : int
            Number of timesteps to execute.  Must be ≥ 1.
        """
        if steps < 1:
            raise ValueError(f"steps must be >= 1, got {steps}")
        for _ in range(steps):
            self.step()

    def reset(self) -> None:
        """Reset state and tick counter to initial conditions.

        Re-seeds the RNG if a seed was originally provided, ensuring
        deterministic replay.
        """
        self.state.reset()
        self._tick = 0
        if self.config.seed is not None:
            self._rng = np.random.default_rng(self.config.seed)

    # ------------------------------------------------------------------
    # Command helpers (delegate to physics engine)
    # ------------------------------------------------------------------

    def command_thrust(self, force_z: float) -> None:
        """Set vertical thrust acceleration for the next step.

        Parameters
        ----------
        force_z : float
            Upward acceleration in m/s² (must exceed gravity ≈ 9.81
            to climb).
        """
        self.physics.apply_thrust(self.state, force_z)

    def command_move(self, ax: float, ay: float) -> None:
        """Set horizontal acceleration for the next step.

        Parameters
        ----------
        ax : float
            Forward (+X) acceleration in m/s².
        ay : float
            Leftward (+Y) acceleration in m/s².
        """
        self.physics.apply_horizontal_acceleration(self.state, ax, ay)

    def command_rotate(
        self,
        droll: float = 0.0,
        dpitch: float = 0.0,
        dyaw: float = 0.0,
    ) -> None:
        """Apply an instantaneous orientation change.

        Parameters
        ----------
        droll, dpitch, dyaw : float
            Orientation increments in radians.
        """
        self.physics.apply_rotation(
            self.state, droll, dpitch, dyaw,
        )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Simulator(tick={self._tick}, "
            f"t={self.elapsed_time:.3f}s, "
            f"dt={self.config.dt}, "
            f"state={self.state})"
        )
