# ai/microservice/base_service.py
import os
import importlib
import inspect
import json
import threading
from ai.config import PAIAConfig
from ai.logger import PAIALogger

logger = PAIALogger().get()

SERVICE_REGISTRY = {}

class AIMicroService:
    def process(self, query):
        raise NotImplementedError("Subclasses must implement process method")

def load_services():
    config = PAIAConfig().get()
    service_dir = os.path.dirname(__file__)
    for filename in os.listdir(service_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "base_service.py"]:
            module_name = filename[:-3]
            service_name = module_name.replace("_", "-")
            
            is_enabled = config.get("services", {}).get(service_name, {}).get("enabled", True)
            if not is_enabled:
                logger.info(f"Skipping disabled service: {service_name}")
                continue

            try:
                module = importlib.import_module(f"ai.microservice.{module_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, AIMicroService) and obj != AIMicroService:
                        logger.info(f"Loading service: {service_name}")
                        SERVICE_REGISTRY[service_name] = obj
                        logger.info(f"Loaded service: {service_name}")
            except ImportError as e:
                logger.error(f"Error importing {module_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Error loading {service_name}: {str(e)}")

def get_service(service_name):
    service_class = SERVICE_REGISTRY.get(service_name)
    if service_class:
        logger.debug(f"Retrieved service: {service_name}")
        return service_class()
    logger.error(f"Service not found: {service_name}")
    return None

load_services()