import threading
import importlib
import inspect
import os

from paia import PAIASingleton,PAIALogger,PAIAConfig,PAIAService

class PAIAServiceManager(metaclass=PAIASingleton):
    def __init__(self):
        self._lock = threading.Lock()
        self._service_names : dict[str] = {}
        self._service_registry : dict[type] = {}
        self._service_instances : dict[PAIAService] = {}
        self._services_loaded : bool = False

    def get_services(self, as_str : bool = False): 
        if not self._services_loaded:
            self._load_services()
        
        if as_str:
            return self._service_names
        
        return self._service_registry
        
    def get_service(self, service_name: str) -> PAIAService | None:
        if not self._services_loaded:
            self._load_services()
        result = None
        try:
            self._lock.acquire()
            service_class = self._service_registry[service_name]
            if service_class:
                if not service_name in self._service_instances:
                    PAIALogger().debug(f"Adding service: {service_name}")
                    self._service_instances[service_name] = service_class()
                result = self._service_instances[service_name]
        except Exception as e:
            PAIALogger().error(f"{str(e)}")
        if self._lock.locked():
            self._lock.release()
        if result:
            return result

        PAIALogger().error(f"Service not found: {service_name}")
        return None
    
    def _load_services(self) -> bool:
        if self._services_loaded:
            return True
        try:
            self._lock.acquire()
            service_dir = os.path.dirname(__file__)       
            self._service_names["services"] = []             
            for filename in os.listdir(service_dir):
                if filename.endswith(".py") and filename not in ["__init__.py", "service.py","manager.py"]:
                    module_name = filename[:-3]
                    service_name = module_name.replace("_", "-")
                    is_enabled = PAIAConfig().getConfig().get("services", {}).get(service_name, {}).get("enabled", True)
                    if not is_enabled:
                        PAIALogger().getLogger().info(f"Skipping disabled service: {service_name}")
                        continue
                    try:
                        module = importlib.import_module(f"paia.service.{module_name}")
                        for _,module_obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(module_obj, PAIAService) and module_obj != PAIAService:
                                PAIALogger().info(f"Loading service: {service_name}")
                                self._service_names["services"].append(service_name)
                                self._service_registry[service_name] = module_obj
                                PAIALogger().info(f"Loaded service: {service_name}")
                    except ImportError as e:
                        PAIALogger().error(f"Error importing {module_name}: {str(e)}")
                    except Exception as e:
                        PAIALogger().error(f"Error loading {service_name}: {str(e)}")
        except Exception as e:
            PAIALogger().error(f"Error loading {service_name}: {str(e)}")
            # Loaded ok        
        if self._lock.locked(): self._lock.release()
        self._services_loaded = True
        return True
