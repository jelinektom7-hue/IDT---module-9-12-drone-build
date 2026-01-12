# IDT modules 9-12: quadrotor build and autonomous GNSS waypoint flight (Team 2)

![Completed quadrotor on the bench](assets/figure_04.jpg)

This repository documents our module 9-12 project for **Introduction to Drone Technology (IDT)** at the **University of Southern Denmark**.

We built a wooden H-frame quadrotor, configured a **Pixhawk 4c** flight controller via **QGroundControl**, and validated:

- Indoor assisted flight for stability and calibration sanity checks
- Outdoor GNSS based position hold flights (manual stick input, controller holds position)
- Autonomous waypoint missions using GNSS navigation

## Contents

- [Project goals](#project-goals)
- [Hardware and build choices](#hardware-and-build-choices)
- [System architecture](#system-architecture)
- [QGroundControl configuration](#qgroundcontrol-configuration)
- [Autonomy workflow](#autonomy-workflow)
- [Flight testing](#flight-testing)
- [Trajectory data and plots](#trajectory-data-and-plots)
- [Lessons learned](#lessons-learned)
- [Safety notes](#safety-notes)
- [Repo layout suggestion](#repo-layout-suggestion)
- [Team](#team)

## Project goals

We aimed for a platform that is:

- Fast to assemble and easy to repair
- Mechanically robust for iterative testing
- Capable of stable hover and outdoor GNSS assisted flight
- Able to execute autonomous waypoint missions with repeatable behavior

## Hardware and build choices

### Airframe

We chose a **quadrotor H-frame** built from wood (planks, sticks, and plywood). The H-frame made it easy to:

- Keep motor spacing clear and symmetric
- Place electronics on a flat central plate
- Mount landing legs near the motors

We placed the **4S 5000 mAh LiPo** (the heaviest component) at the **geometric center** and secured it with Velcro straps to keep the center of mass close to the body origin.

![Top view of the frame and electronics](assets/figure_05.jpeg)

### Propulsion and power

- 4x brushless motors
- 4x ESCs
- CW and CCW propellers in a diagonal pairing to cancel net torque
- Power distribution board fed directly from the LiPo

### Flight control and sensors

- Pixhawk 4c flight controller
- IMU (onboard)
- Barometer (onboard)
- GNSS receiver + antenna
- Radio receiver for manual control
- Telemetry link for ground station connection

## System architecture

At a high level:

1. **Battery** feeds the **power distribution board**.
2. The distribution board powers the **ESCs** and the **flight controller**.
3. The Pixhawk sends control signals to each ESC (one ESC per motor).
4. The Pixhawk estimates attitude and position using onboard sensors (IMU, barometer, GNSS) and runs closed loop controllers for roll, pitch, yaw, altitude, and (when enabled) horizontal position.

We relied on flight controller safety features (arming checks, RC loss handling, emergency shutdown behavior). We did not add a custom hardware kill switch, so correct configuration and pre flight checks mattered a lot.

## QGroundControl configuration

We used QGroundControl to complete the standard setup flow:

- Select the airframe type (quadcopter)
- Calibrate: gyroscope, accelerometer, compass, and level horizon
- Calibrate the radio (move each stick and switch through the full range)
- Map flight modes to a switch (for example: Stabilized, Position, Mission)
- Assign and verify a kill switch channel

**Important:** we observed that an incorrect horizon or IMU calibration can look like unexplained drift while hovering. Recalibrating on a truly level surface improved hover stability.

## Autonomy workflow

We developed autonomy incrementally:

1. **Manual flight** to verify motor order, prop direction, and basic stability.
2. **Stabilized mode** testing for indoor hover and pilot assisted control.
3. **Position hold** outdoors (GNSS enabled) to evaluate drift, wind sensitivity, and convergence.
4. **Waypoint missions** designed in QGroundControl to test autonomous execution.

Challenges we had to manage:

- GNSS noise and drift
- Parameter tuning for position control and altitude hold
- Waypoint transitions, especially at sharp corners

## Flight testing

### Indoor testing (safety cage)

We began indoors (without GNSS) using a stabilized mode:

- The pilot controlled thrust and yaw inputs
- The flight controller stabilized roll and pitch

Issues found and fixed:

- **Horizon calibration**: calibrating while the drone was not level caused consistent drift during hover. Recalibration fixed it.
- **Telemetry antenna placement**: an antenna mounted too close to a propeller was struck during a hard landing and broke. We replaced and repositioned it away from moving parts.

![Indoor test setup](assets/figure_01.jpeg)

### Outdoor manual flights (Position mode)

We then flew outdoors in a GNSS assisted mode where the pilot commands movement and the controller holds position:

- Straight line out and back along the landing strip
- Rectangular pattern with corner holds and transitions

The GNSS trajectory was generally close to the intended shape. Small lateral deviations were expected due to GNSS noise and wind.

### Autonomous missions (Mission mode)

Before enabling autonomous flight, we did a short manual Position flight to confirm the system behaved as expected.

We executed two mission types:

1. **Simple mission** covering a predefined area
2. **More complex mission** with altitude changes, waits at waypoints, and tighter turns

Observed behavior:

- The drone followed the overall waypoint structure and completed missions.
- Deviations were most visible at sharper turns and transitions.
- A waypoint acceptance radius can cause the vehicle to start turning toward the next waypoint before it fully converges to the exact setpoint.

![Autonomous trajectory overlay](assets/figure_02.png)

## Trajectory data and plots

We visualized GNSS tracks and converted them to UTM for plotting and comparison.

We also tried trajectory simplification using tolerance values around **0.4 m to 0.5 m**. The goal was to reduce point density while preserving the overall geometry for easier visualization and post processing.

![Example UTM trajectory (simplified)](assets/figure_03.png)

For the more complex mission, we compared:

- Commanded setpoints
- Estimated vehicle position
- GNSS projected position

![Setpoints vs estimated vs GNSS position](assets/figure_06.png)

## Lessons learned

What worked well:

- The H-frame layout and central battery placement made the platform predictable and easier to tune.
- Once calibrated properly, the Pixhawk 4c provided reliable stabilization and sensor fusion for both manual and autonomous modes.

What bit us:

- Calibration errors can masquerade as controller problems.
- GNSS noise and wind can dominate small scale position errors.
- Mechanical placement matters, especially antennas and anything near propellers.

## Safety notes

- Always remove propellers for bench testing and calibration.
- Double check motor order and prop direction before the first flight.
- Keep antennas and wires clear of propellers, even during hard landings.
- Use a safety cage for early indoor tests.
- Do not skip arming checks, sensor calibration, and failsafe verification.

## Repo layout suggestion

If you want to turn this into a fully reproducible repo, a practical structure is:

