#!/usr/bin/env python3
"""
Barebone calibration script for SO101 Follower and Leader arms.
This script provides basic calibration functionality for both arms.
"""

import sys
import time
from typing import Optional
import os

# Import config loader
from .config_loader import get_config_loader, ArmConfig

# Import follower arm classes
try:
    from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower
    FOLLOWER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import SO101 follower classes: {e}")
    FOLLOWER_AVAILABLE = False

# Import leader arm classes (may not be available)
try:
    from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
    LEADER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import SO101 leader classes: {e}")
    print("Leader arm functionality will be disabled")
    LEADER_AVAILABLE = False

if not FOLLOWER_AVAILABLE and not LEADER_AVAILABLE:
    print("Error: No SO101 arm classes could be imported!")
    print("Make sure lerobot is properly installed with: pip install lerobot[feetech]")
    sys.exit(1)


class ArmCalibrator:
    """Barebone calibrator for SO101 arms."""
    
    def __init__(self):
        self.follower = None
        self.leader = None
        self.config_loader = get_config_loader()
    
    def setup_follower(self, arm_config: ArmConfig) -> bool:
        """Setup follower arm configuration."""
        if not FOLLOWER_AVAILABLE:
            print("✗ Follower arm classes not available")
            return False
            
        try:
            config = SO101FollowerConfig(
                port=arm_config.port,
                id=arm_config.id,
            )
            self.follower = SO101Follower(config)
            print(f"✓ Follower arm configured on port {arm_config.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to configure follower arm: {e}")
            return False
    
    def setup_leader(self, arm_config: ArmConfig) -> bool:
        """Setup leader arm configuration."""
        if not LEADER_AVAILABLE:
            print("✗ Leader arm classes not available")
            return False
            
        try:
            config = SO101LeaderConfig(
                port=arm_config.port,
                id=arm_config.id,
            )
            self.leader = SO101Leader(config)
            print(f"✓ Leader arm configured on port {arm_config.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to configure leader arm: {e}")
            return False
    
    def calibrate_follower(self) -> bool:
        """Calibrate the follower arm."""
        if not self.follower:
            print("✗ Follower arm not configured")
            return False
        
        try:
            print("Connecting to follower arm...")
            self.follower.connect(calibrate=False)
            
            print("Starting follower arm calibration...")
            self.follower.calibrate()
            
            print("✓ Follower arm calibration completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Follower arm calibration failed: {e}")
            return False
        finally:
            if self.follower:
                try:
                    self.follower.disconnect()
                    print("Follower arm disconnected")
                except:
                    pass
    
    def calibrate_leader(self) -> bool:
        """Calibrate the leader arm."""
        if not self.leader:
            print("✗ Leader arm not configured")
            return False
        
        try:
            print("Connecting to leader arm...")
            self.leader.connect(calibrate=False)
            
            print("Starting leader arm calibration...")
            self.leader.calibrate()
            
            print("✓ Leader arm calibration completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Leader arm calibration failed: {e}")
            return False
        finally:
            if self.leader:
                try:
                    self.leader.disconnect()
                    print("Leader arm disconnected")
                except:
                    pass
    
    def calibrate_both(self) -> bool:
        """Calibrate both arms sequentially."""
        print("=== Starting calibration for both arms ===")
        
        # Get configurations from config loader
        follower_config = self.config_loader.get_follower_config()
        leader_config = self.config_loader.get_leader_config()
        
        if not follower_config:
            print("✗ Follower arm not configured in config.yaml")
            return False
        
        if not leader_config:
            print("✗ Leader arm not configured in config.yaml")
            return False
        
        # Setup both arms
        if not self.setup_follower(follower_config):
            return False
        
        if not self.setup_leader(leader_config):
            return False
        
        # Calibrate follower first
        print("\n--- Calibrating Follower Arm ---")
        if not self.calibrate_follower():
            print("Follower calibration failed, stopping...")
            return False
        
        # Wait a moment between calibrations
        time.sleep(2)
        
        # Calibrate leader
        print("\n--- Calibrating Leader Arm ---")
        if not self.calibrate_leader():
            print("Leader calibration failed")
            return False
        
        print("\n=== Both arms calibrated successfully! ===")
        return True


def main():
    """Main calibration function."""
    print("SO101 Arm Calibration Script")
    print("=" * 40)
    
    # Load configuration
    config_loader = get_config_loader()
    print(f"Configuration loaded from: {config_loader.get_config_path()}")
    
    # Show available functionality
    print(f"\nAvailable arms:")
    print(f"  - Follower: {'✓' if FOLLOWER_AVAILABLE else '✗'}")
    print(f"  - Leader: {'✓' if LEADER_AVAILABLE else '✗'}")
    print()
    
    # Show current configuration
    follower_config = config_loader.get_follower_config()
    leader_config = config_loader.get_leader_config()
    
    if follower_config:
        print(f"Follower config: {follower_config.port} (ID: {follower_config.id})")
    else:
        print("Follower: Not configured or disabled")
    
    if leader_config:
        print(f"Leader config: {leader_config.port} (ID: {leader_config.id})")
    else:
        print("Leader: Not configured or disabled")
    print()
    
    calibrator = ArmCalibrator()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "follower":
            if not FOLLOWER_AVAILABLE:
                print("✗ Follower arm not available")
                return
            if not follower_config:
                print("✗ Follower arm not configured in config.yaml")
                return
            print("Calibrating follower arm only...")
            if calibrator.setup_follower(follower_config):
                calibrator.calibrate_follower()
            return
        
        elif command == "leader":
            if not LEADER_AVAILABLE:
                print("✗ Leader arm not available")
                return
            if not leader_config:
                print("✗ Leader arm not configured in config.yaml")
                return
            print("Calibrating leader arm only...")
            if calibrator.setup_leader(leader_config):
                calibrator.calibrate_leader()
            return
        
        elif command == "both":
            if not FOLLOWER_AVAILABLE or not LEADER_AVAILABLE:
                print("✗ Both arms not available")
                return
            print("Calibrating both arms...")
            calibrator.calibrate_both()
            return
        
        else:
            print(f"Unknown command: {command}")
            print_usage()
            return
    
    # Interactive mode
    print("Choose calibration mode:")
    if FOLLOWER_AVAILABLE and follower_config:
        print("1. Follower arm only")
    if LEADER_AVAILABLE and leader_config:
        print("2. Leader arm only") 
    if FOLLOWER_AVAILABLE and LEADER_AVAILABLE and follower_config and leader_config:
        print("3. Both arms")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1" and FOLLOWER_AVAILABLE and follower_config:
            print("Calibrating follower arm only...")
            if calibrator.setup_follower(follower_config):
                calibrator.calibrate_follower()
        
        elif choice == "2" and LEADER_AVAILABLE and leader_config:
            print("Calibrating leader arm only...")
            if calibrator.setup_leader(leader_config):
                calibrator.calibrate_leader()
        
        elif choice == "3" and FOLLOWER_AVAILABLE and LEADER_AVAILABLE and follower_config and leader_config:
            print("Calibrating both arms...")
            calibrator.calibrate_both()
        
        elif choice == "4":
            print("Exiting...")
            return
        
        else:
            print("Invalid choice or arm not available/configured. Exiting...")
    
    except KeyboardInterrupt:
        print("\nCalibration interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")


def print_usage():
    """Print usage information."""
    print("\nUsage:")
    print("  python calibrate.py [follower|leader|both]")
    print("\nExamples:")
    print("  python calibrate.py follower  # Calibrate follower arm only")
    print("  python calibrate.py leader    # Calibrate leader arm only")
    print("  python calibrate.py both      # Calibrate both arms")
    print("  python calibrate.py           # Interactive mode")
    print("\nNote: Arm configurations are loaded from config.yaml")


if __name__ == "__main__":
    main()