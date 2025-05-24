# ai/microservice/base_service.py
import os
import importlib
import inspect
from ai import PAIA_CONFIG, PAIA_LOGGER

PAIA_SERVICE_REGISTRY = {}

class AIMicroService:
    def process(self, query):
        raise NotImplementedError("Subclasses must implement process method")

def load_services():
    service_dir = os.path.dirname(__file__)
    for filename in os.listdir(service_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "base_service.py"]:
            module_name = filename[:-3]
            service_name = module_name.replace("_", "-")
            
            is_enabled = PAIA_CONFIG.get().get("services", {}).get(service_name, {}).get("enabled", True)
            if not is_enabled:
                PAIA_LOGGER.info(f"Skipping disabled service: {service_name}")
                continue

            try:
                module = importlib.import_module(f"ai.microservice.{module_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, AIMicroService) and obj != AIMicroService:
                        PAIA_LOGGER.info(f"Loading service: {service_name}")
                        PAIA_SERVICE_REGISTRY[service_name] = obj
                        PAIA_LOGGER.info(f"Loaded service: {service_name}")
            except ImportError as e:
                PAIA_LOGGER.error(f"Error importing {module_name}: {str(e)}")
            except Exception as e:
                PAIA_LOGGER.error(f"Error loading {service_name}: {str(e)}")

def get_service(service_name):
    service_class = PAIA_SERVICE_REGISTRY.get(service_name)
    if service_class:
        PAIA_LOGGER.debug(f"Retrieved service: {service_name}")
        return service_class()
    PAIA_LOGGER.error(f"Service not found: {service_name}")
    return None

load_services()