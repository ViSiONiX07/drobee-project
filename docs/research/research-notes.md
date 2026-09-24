# Bee-Brain Research Notes & Algorithm Design

This document details the bio-inspired algorithmic foundation, sensor processing pipeline, and altitude/drift estimation models implemented in Bee-Brain.

## 1. Bio-Inspired Algorithmic Inspirations

Bee-Brain draws algorithmic inspiration from insect visual processing models. These lightweight bio-inspired visual mechanisms enable resource-efficient computation on microcontrollers without requiring heavy deep-learning inference.

> **Clarification**: Bee-Brain utilizes mathematical and algorithmic models inspired by insect vision. It does NOT run a biological connectome simulation or emulate a full 166,700-neuron insect brain on the ESP32-S3.

### 1.1 Elementary Motion Detector (EMD) / Reichardt Detector
- **Biological Basis**: Modeled after motion detection in the insect visual system (Hassenstein-Reichardt detector).
- **Function in Bee-Brain**: Processes spatio-temporal luminance changes from optical flow sensor fields to extract direction-selective optical flow vectors.
- **Application**: Used alongside ADNS3080 displacement readings to filter motion noise and calculate horizontal drift velocity ($\Delta x, \Delta y$).

### 1.2 Lobula Giant Movement Detector (LGMD)
- **Biological Basis**: Modeled after the visual looming-sensitive neuron found in locusts.
- **Function in Bee-Brain**: Computes angular expansion rate ($\theta / \dot{\theta}$) of visual cues and rapid distance changes measured by downward and forward sensors.
- **Application**: Acts as a rapid-trigger collision warning and emergency failsafe metric for proximity detection.

---

## 2. Sensor Processing & Control Architecture

Bee-Brain operates a GPS-free, lightweight sensor suite:

1. **VL53L0X / TOF200C Downward Laser ToF**:
   - Provides absolute altitude distance measurements to the ground ($z$).
   - Feeds directly into altitude-hold PID control loops.

2. **ADNS3080 Downward Optical Flow**:
   - Provides horizontal image motion vectors.
   - Scaled by ground height ($z$) to compute physical lateral drift velocities ($v_x, v_y$).
   - Feeds directly into horizontal drift correction PID control loops.

### Scope & Stability
This dual-sensor architecture is intentionally sufficient for:
- Indoor hovering stability
- Automatic altitude hold
- Active drift correction
- Autonomous level flight

*Note: An Inertial Measurement Unit (IMU) is an optional future enhancement for attitude/yaw awareness and high-frequency disturbance rejection.*

---

## 3. Physical Room Mapping & Bench Rig

- **Flying Micro-Drone**: Focused purely on micro-weight, hover, and drift stabilization.
- **Bench-Mounted Room Scanner**: Utilizes an SG90 servo and ToF sensor mounted on a stationary laboratory bench rig to collect multi-angle range scans.
- **Point-Cloud Processing**: Scanned points are transferred to the PySide6 Dashboard where Open3D handles sensor-based point-cloud acquisition and 3D reconstruction.
