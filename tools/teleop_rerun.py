import sys
from .config_loader import get_config_loader 
from lerobot.teleoperators.lelamp_leader import LeLampLeaderConfig, LeLampLeader
from .rerun import ControlMode, set_joints, set_led_intensity

# Load configuration
config_loader = get_config_loader()
leader_config = config_loader.get_leader_config()

if not leader_config:
    print("Error: Leader arm must be configured in config.yaml")
    sys.exit(1)

teleop_config = LeLampLeaderConfig(
    port=leader_config.port,
    id=leader_config.id,
)

teleop_device = LeLampLeader(teleop_config)
teleop_device.connect()

while True:
    try:
        action = teleop_device.get_action()
        print(action)
        action_dict = {}

        for joint_name, joint_value in action.items():
            if joint_name.endswith(".pos"):
                joint_name = joint_name[:-4]
            elif joint_name.endswith(".intensity"):
                joint_name = joint_name[:-10]
                set_led_intensity(joint_value)
                continue  # Skip intensity values

            action_dict[joint_name] = joint_value

            if joint_name == "shoulder_pan":
                action_dict[joint_name] = - joint_value

        set_joints(action_dict, ControlMode.NORMALIZED)
    except KeyboardInterrupt:
        print("Shutting down teleop...")
        break