#!/usr/bin/env python3
"""
WorldWideCoin Configuration Management
Handles application settings and peer management
"""

import json
import os
from typing import List, Dict, Any


class Config:
    """Configuration manager for WorldWideCoin"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Warning: Could not load config file {self.config_file}")
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "peers": [
                {"host": "localhost", "port": 5001},
                {"host": "localhost", "port": 5002},
                {"host": "localhost", "port": 5003}
            ],
            "api": {
                "host": "0.0.0.0",
                "port": 5000
            },
            "mining": {
                "enabled": False,
                "threads": 1
            },
            "network": {
                "max_peers": 10,
                "timeout": 30
            }
        }

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError:
            print(f"Warning: Could not save config file {self.config_file}")

    def get_peers(self) -> List[Dict[str, Any]]:
        """Get list of known peers"""
        return self.config.get("peers", [])

    def add_peer(self, host: str, port: int):
        """Add a new peer to the configuration"""
        peer = {"host": host, "port": port}
        if peer not in self.config["peers"]:
            self.config["peers"].append(peer)
            self.save_config()

    def remove_peer(self, host: str, port: int):
        """Remove a peer from the configuration"""
        peer = {"host": host, "port": port}
        if peer in self.config["peers"]:
            self.config["peers"].remove(peer)
            self.save_config()

    def get(self, key: str, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value"""
        self.config[key] = value
        self.save_config()
