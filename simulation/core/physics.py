"""
Bee-Brain Physics Engine Module.

Applies Newtonian kinematics, gravity, damping, ground collision,
and velocity limiting to a :class:`DroneState`.

Model Assumptions & Limitations
--------------------------------
- This is a **simplified point-mass model**, not a validated aerodynamic
  quadcopter simulation.  There is no rotor-disc aerodynamics, no air
  resistance proportional to area/drag-coefficient, and no gyroscopic
  precession.
- Gravity acts as a constant downward acceleration (−Z).
- Linear damping is applied as a fraction of velocity removed per second.
  This is a first-order approximation of air resistance.
- Ground collision is handled by clamping altitude to ≥ 0 and zeroing
  downward velocity.  No bounce or ground-effect modelling.
- Velocity is hard-clamped per axis to configurable limits.
- Orientation changes are applied as simple additive Euler angle
  increments, not through a torque/inertia model.  This is adequate for
  Phase 1 but does not model realistic attitude dynamics.

Coordinate System & Units
--------------------------
See :mod:`simulation.core.drone_state` for the coordinate convention.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from simulation.core.drone_state import DroneState


@dataclass
class PhysicsConfig:
    """Configuration constants for the physics engine.

    Parameters
    ----------
    gravity : float
        Gravitational acceleration magnitude in m/s² (default 9.81).
    damping : float
        Linear velocity damping coefficient in the range [0, 1].
        A value of 0.1 removes 10 % of velocity per second.
    max_velocity : float
        Per-axis velocity clamp in m/s.
    ground_level : float
        Altitude floor in metres (default 0.0).
    """

    gravity: float = 9.81
    damping: float = 0.1
    max_velocity: float = 5.0
    ground_level: float = 0.0

    def __post_init__(self) -> None:
        if self.gravity < 0.0:
            raise ValueError(
                f"gravity must be non-negative, got {self.gravity}"
            )
        if not 0.0 <= self.damping <= 1.0:
            raise ValueError(
                f"damping must be in [0, 1], got {self.damping}"
            )
        if self.max_velocity <= 0.0:
            raise ValueError(
                f"max_velocity must be positive, got {self.max_velocity}"
            )


class PhysicsEngine:
    """Applies physics rules to a :class:`DroneState`.

    The engine is **stateless** — it reads from and writes to the
    ``DroneState`` that is passed in.  This keeps the physics layer
    fully decoupled from the simulation orchestrator and UI.

    Parameters
    ----------
    config : PhysicsConfig | None
        Physics constants.  Uses defaults when *None*.
    """

    def __init__(self, config: PhysicsConfig | None = None) -> None:
        self.config = config or PhysicsConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(self, state: DroneState, dt: float) -> None:
        """Advance *state* by one physics tick of duration *dt* seconds.

        Order of operations:
        1. Apply gravity to acceleration.
        2. Integrate acceleration → velocity (Euler).
        3. Apply linear damping.
        4. Clamp velocity.
        5. Integrate velocity → position (Euler).
        6. Enforce ground boundary.

        Parameters
        ----------
        state : DroneState
            Mutable drone state — modified in-place.
        dt : float
            Timestep duration in seconds.  Must be > 0.
        """
        if dt <= 0.0:
            raise ValueError(f"dt must be positive, got {dt}")

        self._apply_gravity(state)
        self._integrate_velocity(state, dt)
        self._apply_damping(state, dt)
        self._clamp_velocity(state)
        self._integrate_position(state, dt)
        self._enforce_ground(state)

    # ------------------------------------------------------------------
    # Movement commands (world-frame impulse accelerations)
    # ------------------------------------------------------------------

    def apply_thrust(self, state: DroneState, force_z: float) -> None:
        """Set the vertical (Z) acceleration component.

        Parameters
        ----------
        state : DroneState
            Target state.
        force_z : float
            Desired upward acceleration in m/s².
        """
        state.acceleration[2] = force_z

    def apply_horizontal_acceleration(
        self,
        state: DroneState,
        ax: float,
        ay: float,
    ) -> None:
        """Set horizontal (X, Y) acceleration components.

        Parameters
        ----------
        state : DroneState
            Target state.
        ax : float
            Forward (+X) acceleration in m/s².
        ay : float
            Leftward (+Y) acceleration in m/s².
        """
        state.acceleration[0] = ax
        state.acceleration[1] = ay

    def apply_rotation(
        self,
        state: DroneState,
        droll: float,
        dpitch: float,
        dyaw: float,
    ) -> None:
        """Increment orientation by the given Euler-angle deltas.

        Parameters
        ----------
        state : DroneState
            Target state.
        droll, dpitch, dyaw : float
            Orientation increments in radians.
        """
        state.roll += droll
        state.pitch += dpitch
        state.yaw += dyaw

        # Normalise angles to (−π, π]
        state.roll = self._wrap_angle(state.roll)
        state.pitch = self._wrap_angle(state.pitch)
        state.yaw = self._wrap_angle(state.yaw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_gravity(self, state: DroneState) -> None:
        """Add gravitational acceleration (negative Z)."""
        state.acceleration[2] -= self.config.gravity

    def _integrate_velocity(self, state: DroneState, dt: float) -> None:
        """Euler integration: v += a * dt."""
        state.velocity += state.acceleration * dt

    def _apply_damping(self, state: DroneState, dt: float) -> None:
        """Reduce velocity by a fraction proportional to *dt*.

        ``v *= (1 − damping * dt)``

        The factor is clamped so it never reverses direction.
        """
        factor = max(0.0, 1.0 - self.config.damping * dt)
        state.velocity *= factor

    def _clamp_velocity(self, state: DroneState) -> None:
        """Hard-clamp each velocity component to ±max_velocity."""
        limit = self.config.max_velocity
        np.clip(state.velocity, -limit, limit, out=state.velocity)

    def _integrate_position(self, state: DroneState, dt: float) -> None:
        """Euler integration: p += v * dt."""
        state.position += state.velocity * dt

    def _enforce_ground(self, state: DroneState) -> None:
        """Clamp altitude to ≥ ground_level and zero downward velocity on contact."""
        gl = self.config.ground_level
        if state.position[2] < gl:
            state.position[2] = gl
            if state.velocity[2] < 0.0:
                state.velocity[2] = 0.0

    @staticmethod
    def _wrap_angle(angle: float) -> float:
        """Normalise *angle* to the range (−π, π]."""
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle <= -math.pi:
            angle += 2.0 * math.pi
        return angle
