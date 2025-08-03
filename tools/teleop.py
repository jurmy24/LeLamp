import sys
from .config_loader import get_config_loader 

from lerobot.robots.lelamp_follower import LeLampFollowerConfig, LeLampFollower
from lerobot.teleoperators.lelamp_leader import LeLampLeaderConfig, LeLampLeader
# Load configuration
config_loader = get_config_loader()
follower_config = config_loader.get_follower_config()
leader_config = config_loader.get_leader_config()

if not follower_config or not leader_config:
    print("Error: Both follower and leader arms must be configured in config.yaml")
    sys.exit(1)

robot_config = LeLampFollowerConfig(
    port=follower_config.port,
    id=follower_config.id,
)

teleop_config = LeLampLeaderConfig(
    port=leader_config.port,
    id=leader_config.id,
)

robot = LeLampFollower(robot_config)
teleop_device = LeLampLeader(teleop_config)
robot.connect(calibrate=False)
teleop_device.connect(calibrate=False)

while True:
    try:
        action = teleop_device.get_action()
        print(action)
        robot.send_action(action)
    except KeyboardInterrupt:
        print("Shutting down teleop...")
        break