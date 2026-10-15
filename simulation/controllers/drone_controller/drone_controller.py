from controllers import Supervisor, Keyboard
import math


# ============================================================
# BEE-BRAIN WEBOTS DRONE CONTROLLER
# ============================================================

robot = Supervisor()
TIME_STEP = 16

keyboard = Keyboard()
keyboard.enable(TIME_STEP)


# ============================================================
# ROBOT NODE
# ============================================================

drone_node = robot.getFromDef("bee_brain_drone")

if drone_node is None:
    print("ERROR: Could not find DEF bee_brain_drone")
    print("Make sure the Robot has: DEF bee_brain_drone Robot { ... }")
    robot.step(TIME_STEP)
    raise SystemExit

translation_field = drone_node.getField("translation")


# ============================================================
# PHYSICS
# ============================================================

MASS = 0.12
GRAVITY = 9.81

WEIGHT = MASS * GRAVITY

MIN_TOTAL_THRUST = WEIGHT * 0.45
MAX_TOTAL_THRUST = WEIGHT * 1.35


# ============================================================
# ALTITUDE
# ============================================================

TARGET_ALTITUDE = 1.0

ALTITUDE_KP = 0.45
ALTITUDE_KD = 0.80

TAKEOFF_THRUST_MULTIPLIER = 1.12
TAKEOFF_RELEASE_ALTITUDE = 0.70

ALTITUDE_TOLERANCE = 0.05
VERTICAL_SPEED_TOLERANCE = 0.15


# ============================================================
# ATTITUDE
# ============================================================

ROLL_KP = 0.055
PITCH_KP = 0.055

ROLL_KD = 0.045
PITCH_KD = 0.045

YAW_KP = 0.025
YAW_KD = 0.020

MAX_TORQUE = 0.018

MAX_SAFE_ROLL = math.radians(25.0)
MAX_SAFE_PITCH = math.radians(25.0)


# ============================================================
# MOVEMENT
# ============================================================

MAX_COMMAND_ANGLE = math.radians(5.0)

COMMAND_DURATION = 0.18

VELOCITY_BRAKE_GAIN = 0.035
MAX_BRAKE_ANGLE = math.radians(3.0)


# ============================================================
# YAW
# ============================================================

YAW_RATE = math.radians(35.0)


# ============================================================
# STATE
# ============================================================

armed = False
takeoff_complete = False

target_roll = 0.0
target_pitch = 0.0
target_yaw = 0.0

command_timer = 0.0
current_command = "NONE"

previous_roll = 0.0
previous_pitch = 0.0
previous_yaw = 0.0


# ============================================================
# MOTORS
# ============================================================

motor_names = [
    "m1_motor",
    "m2_motor",
    "m3_motor",
    "m4_motor",
]

motors = []

for name in motor_names:

    try:
        motor = robot.getDevice(name)

        if motor:
            motors.append(motor)

            try:
                motor.setPosition(float("inf"))
                motor.setVelocity(0.0)
            except Exception:
                pass

    except Exception:
        pass


# ============================================================
# SENSORS
# ============================================================

tof = None
camera = None

try:
    tof = robot.getDevice("tof_sensor")

    if tof:
        tof.enable(TIME_STEP)

except Exception:
    tof = None


try:
    camera = robot.getDevice("optical_flow_camera")

    if camera:
        camera.enable(TIME_STEP)

except Exception:
    camera = None


# ============================================================
# UTILITY
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def wrap_angle(angle):

    while angle > math.pi:
        angle -= 2.0 * math.pi

    while angle < -math.pi:
        angle += 2.0 * math.pi

    return angle


def get_position():

    return translation_field.getSFVec3f()


def get_velocity():

    return drone_node.getVelocity()


def get_angular_velocity():

    return drone_node.getVelocity()[3:]


# ============================================================
# ORIENTATION
# ============================================================

def get_orientation():

    return drone_node.getOrientation()


def get_euler_angles():

    m = get_orientation()

    m00 = m[0]
    m10 = m[3]
    m20 = m[6]

    m21 = m[7]
    m22 = m[8]

    pitch = math.asin(
        clamp(-m20, -1.0, 1.0)
    )

    roll = math.atan2(
        m21,
        m22
    )

    yaw = math.atan2(
        m10,
        m00
    )

    return roll, pitch, yaw


# ============================================================
# BODY VELOCITY
# ============================================================

def get_body_velocity():

    velocity = get_velocity()

    vx_world = velocity[0]
    vy_world = velocity[1]
    vz_world = velocity[2]

    m = get_orientation()

    body_x_world = (
        m[0],
        m[3],
        m[6],
    )

    body_y_world = (
        m[1],
        m[4],
        m[7],
    )

    body_z_world = (
        m[2],
        m[5],
        m[8],
    )

    vx_body = (
        vx_world * body_x_world[0]
        + vy_world * body_x_world[1]
        + vz_world * body_x_world[2]
    )

    vy_body = (
        vx_world * body_y_world[0]
        + vy_world * body_y_world[1]
        + vz_world * body_y_world[2]
    )

    vz_body = (
        vx_world * body_z_world[0]
        + vy_world * body_z_world[1]
        + vz_world * body_z_world[2]
    )

    return vx_body, vy_body, vz_body


# ============================================================
# MOTOR VISUALS
# ============================================================

def update_motor_visuals(thrust_ratio):

    thrust_ratio = clamp(
        thrust_ratio,
        0.0,
        1.0
    )

    speed = 150.0 + (
        850.0 * thrust_ratio
    )

    for motor in motors:

        try:
            motor.setVelocity(speed)
        except Exception:
            pass


def stop_motors():

    for motor in motors:

        try:
            motor.setVelocity(0.0)
        except Exception:
            pass


# ============================================================
# KEYBOARD
# ============================================================

def process_keyboard(dt):

    global armed
    global target_roll
    global target_pitch
    global target_yaw
    global command_timer
    global current_command

    key = keyboard.getKey()

    # --------------------------------------------------------
    # ARM / DISARM
    # --------------------------------------------------------

    if key == ord(" "):

        armed = not armed

        if armed:

            print("")
            print("========================================")
            print("ARMED")
            print("========================================")

        else:

            target_roll = 0.0
            target_pitch = 0.0

            print("")
            print("========================================")
            print("DISARMED")
            print("========================================")

    # --------------------------------------------------------
    # MOVEMENT
    # --------------------------------------------------------

    if armed:

        # W
        if key == ord("W") or key == ord("w"):

            target_pitch = -MAX_COMMAND_ANGLE
            target_roll = 0.0

            command_timer = COMMAND_DURATION
            current_command = "FORWARD"

        # S
        elif key == ord("S") or key == ord("s"):

            target_pitch = MAX_COMMAND_ANGLE
            target_roll = 0.0

            command_timer = COMMAND_DURATION
            current_command = "BACKWARD"

        # A
        elif key == ord("A") or key == ord("a"):

            target_roll = MAX_COMMAND_ANGLE
            target_pitch = 0.0

            command_timer = COMMAND_DURATION
            current_command = "LEFT"

        # D
        elif key == ord("D") or key == ord("d"):

            target_roll = -MAX_COMMAND_ANGLE
            target_pitch = 0.0

            command_timer = COMMAND_DURATION
            current_command = "RIGHT"

        # Q
        elif key == ord("Q") or key == ord("q"):

            target_yaw += YAW_RATE * dt

            command_timer = COMMAND_DURATION
            current_command = "YAW LEFT"

        # E
        elif key == ord("E") or key == ord("e"):

            target_yaw -= YAW_RATE * dt

            command_timer = COMMAND_DURATION
            current_command = "YAW RIGHT"

    # --------------------------------------------------------
    # COMMAND TIMEOUT
    # --------------------------------------------------------

    if command_timer > 0.0:

        command_timer -= dt

        if command_timer <= 0.0:

            command_timer = 0.0

            target_roll = 0.0
            target_pitch = 0.0

            current_command = "NONE"


# ============================================================
# VELOCITY BRAKING
# ============================================================

def apply_velocity_braking():

    global target_roll
    global target_pitch

    vx_body, vy_body, _ = get_body_velocity()

    vx_body = clamp(
        vx_body,
        -2.0,
        2.0
    )

    vy_body = clamp(
        vy_body,
        -2.0,
        2.0
    )

    if command_timer <= 0.0:

        brake_pitch = clamp(
            vx_body * VELOCITY_BRAKE_GAIN,
            -MAX_BRAKE_ANGLE,
            MAX_BRAKE_ANGLE
        )

        brake_roll = clamp(
            vy_body * VELOCITY_BRAKE_GAIN,
            -MAX_BRAKE_ANGLE,
            MAX_BRAKE_ANGLE
        )

        target_pitch += brake_pitch
        target_roll -= brake_roll

        target_pitch = clamp(
            target_pitch,
            -MAX_BRAKE_ANGLE,
            MAX_BRAKE_ANGLE
        )

        target_roll = clamp(
            target_roll,
            -MAX_BRAKE_ANGLE,
            MAX_BRAKE_ANGLE
        )


# ============================================================
# ALTITUDE CONTROLLER
# ============================================================

def calculate_thrust(
    altitude,
    vertical_velocity
):

    global takeoff_complete

    # --------------------------------------------------------
    # TAKEOFF
    # --------------------------------------------------------

    if not takeoff_complete:

        if altitude < TAKEOFF_RELEASE_ALTITUDE:

            thrust = (
                WEIGHT *
                TAKEOFF_THRUST_MULTIPLIER
            )

            return clamp(
                thrust,
                MIN_TOTAL_THRUST,
                MAX_TOTAL_THRUST
            )

        altitude_error = (
            TARGET_ALTITUDE -
            altitude
        )

        correction = (
            ALTITUDE_KP *
            altitude_error
            -
            ALTITUDE_KD *
            vertical_velocity
        )

        thrust = WEIGHT + correction

        thrust = clamp(
            thrust,
            MIN_TOTAL_THRUST,
            MAX_TOTAL_THRUST
        )

        if (
            abs(altitude_error)
            <= 0.08
            and
            abs(vertical_velocity)
            <= 0.20
        ):

            takeoff_complete = True

            print(
                "Takeoff complete -> "
                f"alt={altitude:.3f} m"
            )

        return thrust

    # --------------------------------------------------------
    # NORMAL HOLD
    # --------------------------------------------------------

    altitude_error = (
        TARGET_ALTITUDE -
        altitude
    )

    correction = (
        ALTITUDE_KP *
        altitude_error
        -
        ALTITUDE_KD *
        vertical_velocity
    )

    thrust = WEIGHT + correction

    return clamp(
        thrust,
        MIN_TOTAL_THRUST,
        MAX_TOTAL_THRUST
    )


# ============================================================
# ATTITUDE CONTROLLER
# ============================================================

def calculate_torque(
    roll,
    pitch,
    yaw,
    roll_rate,
    pitch_rate,
    yaw_rate
):

    roll_error = wrap_angle(
        target_roll - roll
    )

    pitch_error = wrap_angle(
        target_pitch - pitch
    )

    yaw_error = wrap_angle(
        target_yaw - yaw
    )

    roll_torque = (
        ROLL_KP * roll_error
        -
        ROLL_KD * roll_rate
    )

    pitch_torque = (
        PITCH_KP * pitch_error
        -
        PITCH_KD * pitch_rate
    )

    yaw_torque = (
        YAW_KP * yaw_error
        -
        YAW_KD * yaw_rate
    )

    roll_torque = clamp(
        roll_torque,
        -MAX_TORQUE,
        MAX_TORQUE
    )

    pitch_torque = clamp(
        pitch_torque,
        -MAX_TORQUE,
        MAX_TORQUE
    )

    yaw_torque = clamp(
        yaw_torque,
        -MAX_TORQUE,
        MAX_TORQUE
    )

    return (
        roll_torque,
        pitch_torque,
        yaw_torque
    )


# ============================================================
# SAFETY
# ============================================================

def safety_check(
    roll,
    pitch
):

    if abs(roll) > MAX_SAFE_ROLL:

        print(
            "SAFETY DISARM: "
            f"roll={math.degrees(roll):.1f} deg"
        )

        return False

    if abs(pitch) > MAX_SAFE_PITCH:

        print(
            "SAFETY DISARM: "
            f"pitch={math.degrees(pitch):.1f} deg"
        )

        return False

    return True


# ============================================================
# STARTUP
# ============================================================

print("")
print("========================================")
print("       BEE-BRAIN DRONE CONTROLLER")
print("========================================")
print(f"Mass:       {MASS:.3f} kg")
print(f"Weight:     {WEIGHT:.3f} N")
print(f"Hover:      {WEIGHT:.3f} N")
print(f"Target Alt: {TARGET_ALTITUDE:.2f} m")
print("")


# ============================================================
# INITIAL STATE
# ============================================================

position = get_position()

previous_altitude = position[2]

previous_roll = 0.0
previous_pitch = 0.0
previous_yaw = 0.0


# ============================================================
# MAIN LOOP
# ============================================================

while robot.step(TIME_STEP) != -1:

    dt = TIME_STEP / 1000.0

    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    position = get_position()

    altitude = position[2]

    # --------------------------------------------------------
    # VELOCITY
    # --------------------------------------------------------

    velocity = get_velocity()

    vx_world = velocity[0]
    vy_world = velocity[1]
    vz_world = velocity[2]

    # --------------------------------------------------------
    # ORIENTATION
    # --------------------------------------------------------

    roll, pitch, yaw = get_euler_angles()

    # --------------------------------------------------------
    # ANGULAR VELOCITY
    # --------------------------------------------------------

    angular_velocity = get_angular_velocity()

    roll_rate = angular_velocity[0]
    pitch_rate = angular_velocity[1]
    yaw_rate = angular_velocity[2]

    # --------------------------------------------------------
    # KEYBOARD
    # --------------------------------------------------------

    process_keyboard(dt)

    # --------------------------------------------------------
    # DISARMED
    # --------------------------------------------------------

    if not armed:

        target_roll = 0.0
        target_pitch = 0.0

        takeoff_complete = False

        stop_motors()

        try:

            drone_node.addForce(
                [0.0, 0.0, 0.0],
                True
            )

            drone_node.addTorque(
                [0.0, 0.0, 0.0],
                True
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # ARMED
    # --------------------------------------------------------

    else:

        if not safety_check(
            roll,
            pitch
        ):

            armed = False

            target_roll = 0.0
            target_pitch = 0.0

            stop_motors()

            try:

                drone_node.addForce(
                    [0.0, 0.0, 0.0],
                    True
                )

                drone_node.addTorque(
                    [0.0, 0.0, 0.0],
                    True
                )

            except Exception:
                pass

        else:

            # ----------------------------------------------
            # Horizontal velocity braking
            # ----------------------------------------------

            apply_velocity_braking()

            # ----------------------------------------------
            # Thrust
            # ----------------------------------------------

            total_thrust = calculate_thrust(
                altitude,
                vz_world
            )

            # ----------------------------------------------
            # Torque
            # ----------------------------------------------

            (
                tau_roll,
                tau_pitch,
                tau_yaw
            ) = calculate_torque(
                roll,
                pitch,
                yaw,
                roll_rate,
                pitch_rate,
                yaw_rate
            )

            # ----------------------------------------------
            # Apply lift
            # ----------------------------------------------

            drone_node.addForce(
                [
                    0.0,
                    0.0,
                    total_thrust
                ],
                True
            )

            # ----------------------------------------------
            # Apply attitude torque
            # ----------------------------------------------

            drone_node.addTorque(
                [
                    tau_roll,
                    tau_pitch,
                    tau_yaw
                ],
                True
            )

            # ----------------------------------------------
            # Motor visuals
            # ----------------------------------------------

            thrust_ratio = (
                total_thrust /
                MAX_TOTAL_THRUST
            )

            update_motor_visuals(
                thrust_ratio
            )

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    print(
        f"Alt: {altitude:5.3f} m | "
        f"Vx: {vx_world:6.2f} | "
        f"Vy: {vy_world:6.2f} | "
        f"Vz: {vz_world:6.2f} | "
        f"Roll: {math.degrees(roll):6.2f} | "
        f"Pitch: {math.degrees(pitch):6.2f} | "
        f"Yaw: {math.degrees(yaw):6.2f} | "
        f"Cmd: {current_command}"
    )

    # --------------------------------------------------------
    # SAVE STATE
    # --------------------------------------------------------

    previous_altitude = altitude
    previous_roll = roll
    previous_pitch = pitch
    previous_yaw = yaw