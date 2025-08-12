# LeLamp

![LeLamp Banner](./images/Banner.png)

An open source robot lamp based on [Apple's Elegnt](https://machinelearning.apple.com/research/elegnt-expressive-functional-movement), made by [[Human Computer Lab]](https://www.humancomputerlab.com/)

**This repository is an early work in progress.** We published our progress early on as we believe early feedback leads to better design iteration. To contribute ideas, you're welcome to join our [Discord](https://discord.gg/wVF99EtRzg).

## Project Overview

LeLamp is being developed on two parallel tracks:

### **1. Modified SO101 Arm**

![Modified SO101](./images/ModifiedSo.jpeg)

This version is for those who already own an SO-101 or SO-100 arm from The Robot Studio. We built it for quick prototyping.

3D files for modifications can be found in `prints/modifications_for_so101/`. You'll need a SO101 or SO100 for this modification or any STS3215 based robot. The modification is a replacement for the gripper on these arms, effectively reducing the arm DOF from 6 to 5.

Biggest thanks to Jennie and Lily for sponsoring the SO101 arms in this project. If you want to buy a kit at a discounted price, check out [Seeed Studio](https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html?sensecap_affiliate=3gToNR2&referring_service=link)

### **2. From Scratch Design**

![LeLamp](./images/LeLamp.png)

Currently in development. This version will be our main model in the future, where we'll build new interactive paradigms and even imitation learning or general policies for real world deployment.

You can view the live CAD model on [OnShape](https://cad.onshape.com/documents/7ff6d1fd85a1383ea9f71557/w/b399d2ceb47c6775362882dc/e/14b04feff73ad1eb6f6b1f57?renderMode=0&uiState=688fc0a88a82666976c1a86f)

## Set-up for LeLamp on SO10x

If you're using the SO10x arms, follow this to get LeLamp up and running.

### Initial Set-up

If you're setting up the SO10x arms for the first time, best practice is to follow [this tutorial first](https://huggingface.co/docs/lerobot/en/so101). There are 3 checkpoints you need to do:

- Motor Set Up
- Motor Calibration
- Teleoperation

### 3D Printing and Modifications

After initial testing that the SO101 works. you can unscrew the gripper on the arm and start fitting the 3D printed lamp head. The 3D printed files are inside `prints/modifications_for_so101/`. You'll need to print all these files:

- **MotorMount**: We designed a twist snap mechanism to quickly iterate on different lamp head designs. This will be attached to the motor horn on the robot arm.
- **LampHead**: This is the lamp head to be attached to the motor mount through twist snap mechanism.
- **CameraMount**: Camera mount for global shutter usb cameras. **If you don't have a camera, you don't need to print this**.

### Calibration

To calibrate the arms, here is what you'll need to run. The process is similiar to how you'd set up the SO101 arm:

```bash
# For uv init
uv sync

# For finding usb port
uv run -m lerobot.find_port

# For LeLampFollower
uv run -m lerobot.calibrate \
    --robot.type=lelamp_follower \
    --robot.port=/dev/tty.usbmodem58760431551 \ # <- The port of your robot
    --robot.id=lelamp # <- Give the robot a unique name

# For LeLampLeader
uv run -m lerobot.calibrate \
    --teleop.type=lelamp_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \ # <- The port of your robot
    --teleop.id=lelamp # <- Give the robot a unique name
```

### Teleoperation

To teleop the lamp, there are 2 methods.

#### Method 1: Use LeRobot's Script

LeLamp is compatible with LeRobot's teleoperate module.

```bash
uv run -m lerobot.teleoperate \
    --robot.type=lelamp_follower \
    --robot.port=/dev/tty.usbmodem58760431541 \
    --robot.id=lelamp \
    --teleop.type=lelamp_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=lelamp
```

#### Method 2: Use LeLamp's teleop module

To use LeLamp, we provide a quick and easy to remember teleop method. First, you'll need to edit the `config.json` file in this repository to have your lamp's id and port.

```yaml
# SO101 Arm Configuration
# Configuration file for leader and follower arm ports

arms:
  follower:
    port: "/dev/tty.usbmodem5A7A0178351" <- edit here
    id: "lelamp" <- edit here
    enabled: true

  leader:
    port: "/dev/tty.usbmodem5A7A0170321" <- edit here
    id: "lelamp" <- edit here
    enabled: true

# General settings
settings:
  calibration_timeout: 30 # seconds
  connection_timeout: 10 # seconds
  retry_attempts: 3
```

Then you only need to run our teleop module.

```bash
uv run -m tools.teleop
```

## Demo

`main.py` contains a hand tracking demo that uses a PID loop to control the shoulder pan and wrist flex of the arm.

### Running the Demo

1. Install uv: `pip install uv`
2. Run: `uv run main.py`

Note: If you have trouble installing with GitLFS, try running `export GIT_LFS_SKIP_SMUDGE=1`

## Status

This project is actively being developed. Upcoming tasks:

- [ ] Redesign lamp to fit ST3215 servos
- [ ] Test Mujoco environment
- [ ] Train lamp to jump
- [ ] Add voice and mic capabilities

More updates coming in the upcoming weeks!

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
