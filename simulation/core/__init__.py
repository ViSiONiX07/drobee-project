"""
Bee-Brain Simulation Core Package.

Provides a standalone, physics-based drone simulation engine
independent of Webots, PySide6, and hardware.
"""

from simulation.core.drone_state import DroneState
from simulation.core.physics import PhysicsEngine
from simulation.core.simulator import Simulator

__all__ = [
    "DroneState",
    "PhysicsEngine",
    "Simulator",
]
