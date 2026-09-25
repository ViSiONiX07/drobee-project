# Bee-Brain Webots Simulation

This directory contains the Webots simulation environment, 3D worlds, and Python controllers for Bee-Brain.

## Features

- **Indoor Environment**: `worlds/lab_room.wbt` provides a bounded indoor test arena.
- **Drone Controller**: `controllers/drone_controller/drone_controller.py` implements virtual sensor reading and JSON telemetry generation.
- **Telemetry Contract**: Uses the identical JSON format as physical ESP32-S3 firmware.

## How to Run

1. Open Webots simulator.
2. Load `simulation/worlds/lab_room.wbt`.
3. Select `drone_controller` for the drone node.
4. Press Play to start simulation and telemetry streaming.
