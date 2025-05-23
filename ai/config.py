# ai/config.py

import os
import json

from .singleton import PAIASingleton
from .logger import PAIALogger


DEFAULT_CONFIG = {
    "server": {"host": "localhost", "port": 8000},
    "ui": {"directory": "ui"},
    "services": {
        "translate": {"enabled": True, "streamable": False, "parameters": []},
        "text-generator": {"enabled": True, "streamable": False, "parameters": []}
    }
}

class PAIAConfig(PAIASingleton):
    config = {}
    host = "localhost"
    port = 8000
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", "config.json")
    root_path = os.path.join(base_dir, "..")
    ui_dir = os.path.join(root_path, "ui")

    def __init__(self):
        self.configLoaded = False
        self.logger = PAIALogger().get()
        self.get()
        pass

    def default(self):
        # Default config
        return DEFAULT_CONFIG
    
    def get(self):
        # Cached 
        if self.configLoaded:
            return self.config
        
        res = False
        try:
            self.logger.debug(f"Attempting to load config from: {self.config_path}")
            if not os.path.exists(self.config_path):
                self.logger.error(f"Config file does not exist at: {self.config_path}")
                raise FileNotFoundError
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            self.host = self.config["server"]["host"]
            self.port = int(self.config["server"]["port"])
            self.ui_dir = os.path.join(self.root_path, self.config["ui"]["directory"])
            self.logger.info(f"Loaded config: host={self.host}, port={self.port}, ui_dir={self.ui_dir}")
            self.configLoaded = True
            res = True
        except FileNotFoundError as e:
            self.logger.error(f"config.json not found at {self.config_path}, using defaults")
        except (KeyError, json.JSONDecodeError) as e:
            self.logger.error(f"Invalid config.json at {self.config_path}: {str(e)}, using defaults")
        except PermissionError as e:
            self.logger.error(f"Permission denied for config.json at {self.config_path}: {str(e)}, using defaults")
        if not res:
            self.config = self.default()
            self.host = self.config["server"]["host"]
            self.port = int(self.config["server"]["port"])
            self.ui_dir = os.path.join(self.root_path, self.config["ui"]["directory"])
            self.configLoaded = True
        
        return self.config
