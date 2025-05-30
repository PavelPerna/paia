# ai/microservice/base_service.py
import os
import importlib
import inspect
import threading
from ai import PAIAConfig, PAIALogger

PAIA_SERVICE_REGISTRY = {}
PAIA_SERVICE_INSTANCE = {}

class AIMicroService:
    def process(self, query):
        raise NotImplementedError("Subclasses must implement process method")

def load_services():
    service_dir = os.path.dirname(__file__)
    for filename in os.listdir(service_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "base_service.py"]:
            module_name = filename[:-3]
            service_name = module_name.replace("_", "-")
            
            is_enabled = PAIAConfig().getConfig().get("services", {}).get(service_name, {}).get("enabled", True)
            if not is_enabled:
                PAIALogger().getLogger().info(f"Skipping disabled service: {service_name}")
                continue

            try:
                module = importlib.import_module(f"ai.microservice.{module_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, AIMicroService) and obj != AIMicroService:
                        PAIALogger().info(f"Loading service: {service_name}")
                        PAIA_SERVICE_REGISTRY[service_name] = obj
                        PAIALogger().info(f"Loaded service: {service_name}")
            except ImportError as e:
                PAIALogger().error(f"Error importing {module_name}: {str(e)}")
            except Exception as e:
                PAIALogger().error(f"Error loading {service_name}: {str(e)}")

def get_service(service_name):
    service_lock = threading.Lock()
    service_class = PAIA_SERVICE_REGISTRY.get(service_name)
    if service_class:
        try:
            service_lock.acquire()
            if not service_name in PAIA_SERVICE_INSTANCE:
                PAIALogger().debug(f"Adding service: {service_name}")
                PAIA_SERVICE_INSTANCE[service_name] = service_class()
            result = PAIA_SERVICE_INSTANCE[service_name]
            service_lock.release()
        except Exception as e:
            PAIALogger().debug(f"{str(e)}")
        return result    
    PAIALogger().error(f"Service not found: {service_name}")
    return None

load_services()