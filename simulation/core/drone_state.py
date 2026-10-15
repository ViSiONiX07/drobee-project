"""
Bee-Brain Drone State Module.

Maintains the complete kinematic state of a simulated drone:
position, velocity, acceleration, and orientation (roll, pitch, yaw).

Coordinate System
-----------------
Right-handed, Z-up:
    +X  → forward
    +Y  → left
    +Z  → up (altitude)

This matches the existing Webots controller convention where
``altitude = position[2]``.

Units
-----
- Position:     metres (m)
- Velocity:     metres per second (m/s)
- Acceleration: metres per second squared (m/s²)
- Orientation:  radians (rad)

Limitations
-----------
- Orientation is stored as Euler angles (roll, pitch, yaw).  Gimbal lock
  is possible at ±90° pitch but is acceptable for the gentle manoeuvres
  expected in Phase 1 indoor hover scenarios.
- No quaternion representation is provided yet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np


def _zero_vec() -> np.ndarray:
    """Return a zero 3-vector (float64)."""
    return np.zeros(3, dtype=np.float64)


@dataclass
class DroneState:
    """Complete kinematic state of the simulated drone.

    All vector attributes are 3-element NumPy arrays ordered ``[x, y, z]``.
    Orientation is stored as individual Euler angles in radians.

    Parameters
    ----------
    position : np.ndarray
        World-frame position ``[x, y, z]`` in metres.
    velocity : np.ndarray
        World-frame velocity ``[vx, vy, vz]`` in m/s.
    acceleration : np.ndarray
        World-frame acceleration ``[ax, ay, az]`` in m/s².
    roll : float
        Roll angle in radians (rotation about X axis).
    pitch : float
        Pitch angle in radians (rotation about Y axis).
    yaw : float
        Yaw angle in radians (rotation about Z axis).
    """

    position: np.ndarray = field(default_factory=_zero_vec)
    velocity: np.ndarray = field(default_factory=_zero_vec)
    acceleration: np.ndarray = field(default_factory=_zero_vec)

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def altitude(self) -> float:
        """Current altitude (Z component of position) in metres."""
        return float(self.position[2])

    @property
    def speed(self) -> float:
        """Magnitude of the velocity vector in m/s."""
        return float(np.linalg.norm(self.velocity))

    @property
    def orientation(self) -> tuple[float, float, float]:
        """Orientation as ``(roll, pitch, yaw)`` in radians."""
        return (self.roll, self.pitch, self.yaw)

    @property
    def orientation_degrees(self) -> tuple[float, float, float]:
        """Orientation as ``(roll, pitch, yaw)`` in degrees."""
        return (
            math.degrees(self.roll),
            math.degrees(self.pitch),
            math.degrees(self.yaw),
        )

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def set_position(self, x: float, y: float, z: float) -> None:
        """Set world-frame position."""
        self.position[:] = [x, y, z]

    def set_velocity(self, vx: float, vy: float, vz: float) -> None:
        """Set world-frame velocity."""
        self.velocity[:] = [vx, vy, vz]

    def set_acceleration(self, ax: float, ay: float, az: float) -> None:
        """Set world-frame acceleration."""
        self.acceleration[:] = [ax, ay, az]

    def set_orientation(
        self,
        roll: float,
        pitch: float,
        yaw: float,
    ) -> None:
        """Set orientation in radians."""
        self.roll = float(roll)
        self.pitch = float(pitch)
        self.yaw = float(yaw)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all state variables to their defaults (origin, zero velocity, level)."""
        self.position[:] = 0.0
        self.velocity[:] = 0.0
        self.acceleration[:] = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

    # ------------------------------------------------------------------
    # Snapshot / serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-dict snapshot of the current state.

        Useful for logging, telemetry bridging, or test assertions.
        """
        return {
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "acceleration": self.acceleration.tolist(),
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
        }

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(self) -> DroneState:
        """Return a deep copy of this state."""
        return DroneState(
            position=self.position.copy(),
            velocity=self.velocity.copy(),
            acceleration=self.acceleration.copy(),
            roll=self.roll,
            pitch=self.pitch,
            yaw=self.yaw,
        )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        pos = self.position
        vel = self.velocity
        deg = self.orientation_degrees
        return (
            f"DroneState("
            f"pos=[{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}], "
            f"vel=[{vel[0]:.3f}, {vel[1]:.3f}, {vel[2]:.3f}], "
            f"rpy_deg=[{deg[0]:.1f}, {deg[1]:.1f}, {deg[2]:.1f}])"
        )
