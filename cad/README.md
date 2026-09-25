# Bee-Brain CAD & Physical Frame Architecture

This directory contains FreeCAD Python parametric generator scripts, exported STEP models, and 3D-printable STL files for the Bee-Brain frame.

## Directory Layout

- `scripts/bee_brain_frame_generator.py`: FreeCAD Python script for parametric frame generation.
- `step/frame_v1.step`: STEP neutral CAD exchange geometry.
- `stl/frame_v1.stl`: STL mesh file formatted for FDM / SLA 3D printing.

## Design Constraints & Specifications

1. **Mass Budget**: Frame weight is a critical flight constraint. Target printed frame weight must remain under **8.0 grams** to preserve lift capacity with 8520 coreless motors and a 1S LiPo battery.
2. **Electronics Mounting**: Seeed XIAO ESP32-S3 micro-controller is mounted using standard female header sockets on a perfboard carrier to enable rapid component replacement and vibration isolation.
3. **Downward Sensor Suite**: Brackets on the frame bottom hold the VL53L0X ToF sensor and ADNS3080 optical flow sensor rigidly perpendicular to the floor.
4. **Bench-Mounted Room Scanner**: The SG90 pan-tilt servo scanner rig is **bench-mounted** on a laboratory fixture and is NOT part of the flying drone frame.
5. **Dimensions**: Geometry dimensions in `scripts/bee_brain_frame_generator.py` are parameterized placeholders to be finalized upon physical caliper measurement of motor cans and PCB tolerances.
