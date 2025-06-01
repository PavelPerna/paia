# ai/PAIAConfig().py
import os
import json
from .singleton import PAIASingleton

class PAIAConfig(metaclass=PAIASingleton):
    DEFAULT_CONFIG =  {
    "server": {"host": "localhost", "port": 8000},
    "ui": {"directory": "ui","host":"localhost","port":8080,"autostart":True},
    "logging": {"level": "DEBUG", "dir": ".", "file_name":"app.log"},
    "services": {
        "translate": {"enabled": True, "streamable": False, "parameters": []},
        "text-generator": {"enabled": True, "streamable": False, "parameters": []}
        },
    "is_default": True
    }
    config = DEFAULT_CONFIG
    host = "localhost"
    port = 8000
    ui_dir = "ui"
    logging_level = "DEBUG"
    logging_dir = "."
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir,".."))
    config_file = os.path.abspath(os.path.join(base_dir,"..","config.json"))
    

    def __init__(self, config_file: str = None):
        self.configLoaded = False
        self.__loadConfig(config_file)
       
    def getDefault(self):
        return self.DEFAULT_CONFIG
    
    def getConfig(self):
        self.__loadConfig()
        return self.config

    def update(self, config_file: str = None):
        self.__loadConfig(config_file)
        return self.config

    def getUIDirectory(self ,ui_dir :str = None) -> str:
        return os.path.join(self.root_dir,ui_dir if ui_dir else self.ui_dir)
    
    def getUIAddress(self,ui_dir :str = None) -> str:
        return f"http://{self.ui_host}:{self.ui_port}"


    def __loadConfig(self, config_file: str = None, force_reload : bool = False) -> bool:  
        # File changed - force reload automatically 
        if config_file and config_file != self.config_file:
            self.configLoaded = False
            self.config_file = config_file
        # Force reload from file 
        if force_reload:
            self.configLoaded = False
        
        # If actual , return
        if self.configLoaded:
            return self.config
        
        # Load config from file
        res = False
        try:
            print(f"Attempting to load config from: {self.config_file}")
            if not os.path.exists(self.config_file):
                print(f"Config file does not exist at: {self.config_file}")
                raise FileNotFoundError
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
            res = True
        except FileNotFoundError:
            print(f"PAIAConfig().json not found at {self.config_file}, using defaults")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Invalid PAIAConfig().json at {self.config_file}: {str(e)}, using defaults")
        except PermissionError as e:
            print(f"Permission denied for PAIAConfig().json at {self.config_file}: {str(e)}, using defaults")
        
        if not res:
            self.config = self.getDefault()
            self.config_file = None
            print("Loading default config ( file not found or error )")
                
        self.__populateFromJSON(self.config)
        print(f"Loaded config: host={self.host}, port={self.port}, ui_dir={self.ui_dir}, logging_level={self.logging_level}, logging_dir={self.logging_dir}")

        # Load service-specific configs, overriding matching nodes
        service_dir = os.path.join(self.base_dir, "service")
        for service_name in self.config.get("services", {}):
            service_config_path = os.path.join(service_dir, f"{service_name.replace('-', '_')}.json")
            try:
                print(f"Attempting to load service config from: {service_config_path}")
                if os.path.exists(service_config_path):
                    with open(service_config_path, "r") as f:
                        service_config = json.load(f)
                        # Update global config with service-specific values
                        self._merge_service_config(service_name, self.config["services"], service_config)
                        print(f"Updated service config for {service_name}: {self.config['services'][service_name]}")
                else:
                    print(f"No service config found for {service_name} at {service_config_path}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Invalid service config at {service_config_path}: {str(e)}")
            except PermissionError as e:
                print(f"Permission denied for service config at {service_config_path}: {str(e)}")
        
        self.configLoaded = True
        return True

    def __populateFromJSON(self, config: json):
        self.config = config
        self.host = self.config.get("server",{}).get("host","localhost")
        self.port =  int(self.config.get("server",{}).get("port",8000))
        self.ui_dir = self.config.get("ui",{}).get("directory","ui")
        self.ui_host = self.config.get("ui",{}).get("host","localhost")
        self.ui_port =  int(self.config.get("ui",{}).get("port",8080))
        self.logging_level = self.config.get("logging",{}).get("level","DEBUG")
        self.logging_dir = self.config.get("logging",{}).get("dir","localhost")



    def _merge_service_config(self, service_name ,global_config, service_config):
        """ Autocreate in global config """
        if not global_config.get(service_name):
            global_config.set(service_name, {})

        """Recursively update global_config with service_config values."""
        for key, value in service_config.items():
            if isinstance(value, dict) and key in global_config[service_name] and isinstance(global_config[service_name][key], dict):
                self._merge_service_config(global_config[service_name][key], value)
            else:   
                global_config[service_name][key] = value
