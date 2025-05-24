# ai/PAIA_CONFIG.py
import os
import json
from .singleton import PAIASingleton

DEFAULT_CONFIG = {
    "server": {"host": "localhost", "port": 8000},
    "ui": {"directory": "ui","host":"localhost","port":8080,"autostart":False},
    "logging": {"level": "DEBUG", "dir": ".", "file_name":"app.log"},
    "services": {
        "translate": {"enabled": True, "streamable": False, "parameters": []},
        "text-generator": {"enabled": True, "streamable": False, "parameters": []}
    }
}

class PAIAConfig(PAIASingleton):
    config = {}
    host = "localhost"
    port = 8000
    ui_dir = "ui"
    logging_level = "DEBUG"
    logging_dir = "."
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", "config.json")

    def __init__(self):
        self.configLoaded = False
        self.config = self.loadConfig()

    def default(self):
        return DEFAULT_CONFIG
    
    def get(self):
        return self.config

    def loadConfig(self):          
        if self.configLoaded:
            return self.config
        
        res = False
        try:
            print(f"Attempting to load config from: {self.config_path}")
            if not os.path.exists(self.config_path):
                print(f"Config file does not exist at: {self.config_path}")
                raise FileNotFoundError
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            res = True
        except FileNotFoundError:
            print(f"PAIA_CONFIG.json not found at {self.config_path}, using defaults")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Invalid PAIA_CONFIG.json at {self.config_path}: {str(e)}, using defaults")
        except PermissionError as e:
            print(f"Permission denied for PAIA_CONFIG.json at {self.config_path}: {str(e)}, using defaults")
        
        if not res:
            self.config = self.default()
            print("Loading default config ( file not found or error )")
                
        print(f"Loaded config: host={self.host}, port={self.port}, ui_dir={self.ui_dir}, logging_level={self.logging_level}, logging_dir={self.logging_dir}")

        self.host = self.config["server"]["host"]
        self.port = int(self.config["server"]["port"])
        self.ui_dir = self.config["ui"]["directory"]
        self.ui_host = self.config["ui"]["host"]
        self.ui_port = int(self.config["ui"]["port"])
        self.logging_level = self.config.get("logging", {}).get("level", "DEBUG")
        self.logging_dir = self.config.get("logging", {}).get("dir", ".")

        # Load service-specific configs, overriding matching nodes
        service_dir = os.path.join(self.base_dir, "microservice")
        for service_name in self.config.get("services", {}):
            service_config_path = os.path.join(service_dir, f"{service_name.replace('-', '_')}.json")
            try:
                print(f"Attempting to load service config from: {service_config_path}")
                if os.path.exists(service_config_path):
                    with open(service_config_path, "r") as f:
                        service_config = json.load(f)
                        # Update global config with service-specific values
                        self._merge_service_config(self.config["services"][service_name], service_config)
                        print(f"Updated service config for {service_name}: {self.config['services'][service_name]}")
                else:
                    print(f"No service config found for {service_name} at {service_config_path}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Invalid service config at {service_config_path}: {str(e)}")
            except PermissionError as e:
                print(f"Permission denied for service config at {service_config_path}: {str(e)}")
        
        self.configLoaded = True
        return self.config

    def _merge_service_config(self, global_config, service_config):
        """Recursively update global_config with service_config values."""
        for key, value in service_config.items():
            if isinstance(value, dict) and key in global_config and isinstance(global_config[key], dict):
                self._merge_service_config(global_config[key], value)
            else:
                global_config[key] = value

PAIA_CONFIG = PAIAConfig()