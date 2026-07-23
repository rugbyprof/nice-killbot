# IoT Robotics Project

# Checkpoint Assignments

At this point in the semester, you should have enough hardware assembled that we can begin connecting the individual pieces into a complete robotic system. The goal of these checkpoints is **progress**, not perfection. Engineering is an iterative process, and demonstrating working components is more important than having a flawless robot.

---

# Checkpoint 1 — IR Remote Controlled Robot

**Due:** During lab (or by this evening if additional time is granted)

## Objective

Build a simple remote-controlled robot consisting of two independent systems that communicate using infrared (IR).

Your project should demonstrate:

1. A handheld ESP32-based controller.
2. A Raspberry Pi robot capable of driving.
3. IR communication between the two devices.

---

## System Requirements

### Part 1 — ESP32 Remote Controller

Your ESP32 controller should include:

- ESP32
- OLED display
- Joystick
- IR transmitter

The controller should:

- Read joystick movement.
- Display useful information on the OLED (direction, command, status, etc.).
- Transmit movement commands over the IR transmitter.

The exact command format is up to you.

---

### Part 2 — Raspberry Pi Robot

Your robot should include:

- Raspberry Pi
- Motor driver(s)
- Four motors
- IR receiver

The Raspberry Pi should:

- Receive IR commands.
- Decode the commands.
- Drive the motors appropriately.

Examples include:

- Forward
- Reverse
- Left
- Right
- Stop

---

### Part 3 — Communication

The ESP32 and Raspberry Pi must communicate using infrared.

At this checkpoint:

- Commands may occasionally be missed.
- Communication does **not** need to be perfect.
- Small delays are acceptable.
- Occasional dropped packets are acceptable.

The important part is demonstrating that commands successfully travel from one device to the other and cause the robot to respond.

---

# Demonstration Checklist

During grading you should be prepared to demonstrate:

### ESP32 Controller

- ☐ OLED powers on
- ☐ Joystick is functional
- ☐ IR transmitter sends commands
- ☐ OLED displays useful status information

### Raspberry Pi Robot

- ☐ Raspberry Pi boots correctly
- ☐ IR receiver detects commands
- ☐ Motors respond to received commands
- ☐ Robot can perform basic movement

### System Integration

- ☐ Controller communicates with robot
- ☐ Robot responds to transmitted commands
- ☐ Overall system demonstrates remote control

---

## Grading Notes

I will primarily be checking whether the three major pieces are working together:

- Remote controller
- Robot chassis
- IR communication

This checkpoint is **not** about perfection.

If your robot occasionally misses commands or requires multiple button presses, that's acceptable for now. I will also be making notes about where each team is in the development process so we can focus on improvements over the next few weeks.

Be sure to bring everything required to operate your robot, including batteries, cables, transmitters, and any other necessary hardware.

I've been genuinely impressed with everyone's progress so far—keep it up!
