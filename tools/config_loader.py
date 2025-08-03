#!/usr/bin/env python3
"""
Configuration loader for SO101 arm settings.
Loads configuration from config.yaml file.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ArmConfig:
    """Configuration for a single arm."""
    port: str
    id: str
    enabled: bool = True


@dataclass
class Settings:
    """General settings."""
    calibration_timeout: int = 30
    connection_timeout: int = 10
    retry_attempts: int = 3


class ConfigLoader:
    """Loads and manages configuration from YAML file."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config loader.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config.yaml in project root
            self.config_path = Path(__file__).parent.parent / "config.yaml"
        else:
            self.config_path = Path(config_path)
        
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                print(f"Warning: Config file not found at {self.config_path}")
                print("Using default configuration...")
                self._config = self._get_default_config()
                return
            
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
                
            print(f"✓ Configuration loaded from {self.config_path}")
            
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")
            print("Using default configuration...")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration...")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "arms": {
                "follower": {
                    "port": "/dev/tty.usbmodem5A7A0178351",
                    "id": "le_lamp",
                    "enabled": True
                },
                "leader": {
                    "port": "/dev/tty.usbmodem5A7A0170321",
                    "id": "le_lamp",
                    "enabled": True
                }
            },
            "settings": {
                "calibration_timeout": 30,
                "connection_timeout": 10,
                "retry_attempts": 3
            }
        }
    
    def get_arm_config(self, arm_type: str) -> Optional[ArmConfig]:
        """Get configuration for a specific arm type.
        
        Args:
            arm_type: Either 'follower' or 'leader'
            
        Returns:
            ArmConfig object or None if not found/disabled
        """
        if not self._config:
            return None
        
        arm_config = self._config.get("arms", {}).get(arm_type)
        if not arm_config:
            return None
        
        if not arm_config.get("enabled", True):
            return None
        
        return ArmConfig(
            port=arm_config.get("port", ""),
            id=arm_config.get("id", "le_lamp"),
            enabled=arm_config.get("enabled", True)
        )
    
    def get_settings(self) -> Settings:
        """Get general settings.
        
        Returns:
            Settings object
        """
        if not self._config:
            return Settings()
        
        settings = self._config.get("settings", {})
        return Settings(
            calibration_timeout=settings.get("calibration_timeout", 30),
            connection_timeout=settings.get("connection_timeout", 10),
            retry_attempts=settings.get("retry_attempts", 3)
        )
    
    def get_follower_config(self) -> Optional[ArmConfig]:
        """Get follower arm configuration."""
        return self.get_arm_config("follower")
    
    def get_leader_config(self) -> Optional[ArmConfig]:
        """Get leader arm configuration."""
        return self.get_arm_config("leader")
    
    def get_all_arms(self) -> Dict[str, ArmConfig]:
        """Get configuration for all enabled arms.
        
        Returns:
            Dictionary mapping arm type to ArmConfig
        """
        arms = {}
        
        follower_config = self.get_follower_config()
        if follower_config:
            arms["follower"] = follower_config
        
        leader_config = self.get_leader_config()
        if leader_config:
            arms["leader"] = leader_config
        
        return arms
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_config_path(self) -> Path:
        """Get the path to the config file."""
        return self.config_path
    
    def create_default_config(self) -> bool:
        """Create a default config file if it doesn't exist.
        
        Returns:
            True if created successfully, False otherwise
        """
        if self.config_path.exists():
            print(f"Config file already exists at {self.config_path}")
            return True
        
        try:
            default_config = self._get_default_config()
            
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            print(f"✓ Created default config file at {self.config_path}")
            return True
            
        except Exception as e:
            print(f"Error creating config file: {e}")
            return False


# Global config loader instance
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """Get the global config loader instance.
    
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def reload_config() -> None:
    """Reload the global configuration."""
    global _config_loader
    if _config_loader:
        _config_loader.reload()


if __name__ == "__main__":
    # Test the config loader
    loader = ConfigLoader()
    
    print("Configuration Test:")
    print("=" * 20)
    
    print(f"Config file: {loader.get_config_path()}")
    print()
    
    follower = loader.get_follower_config()
    if follower:
        print(f"Follower: {follower.port} (ID: {follower.id})")
    else:
        print("Follower: Not configured or disabled")
    
    leader = loader.get_leader_config()
    if leader:
        print(f"Leader: {leader.port} (ID: {leader.id})")
    else:
        print("Leader: Not configured or disabled")
    
    settings = loader.get_settings()
    print(f"\nSettings:")
    print(f"  Calibration timeout: {settings.calibration_timeout}s")
    print(f"  Connection timeout: {settings.connection_timeout}s")
    print(f"  Retry attempts: {settings.retry_attempts}") 