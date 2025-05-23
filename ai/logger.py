# ai/logger.py
import logging
import logging.handlers
from .singleton import PAIASingleton
  
class PAIALogger(PAIASingleton):
    def __init__(self):
        self.loggerLoaded = False

    def get(self):
        if not self.loggerLoaded:
            # Setup logging
            self.logger = logging.getLogger('AIMicroService')
            self.logger.setLevel(logging.DEBUG)
            if not self.logger.handlers:
                handler = logging.handlers.RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=3)
                handler.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
                self.logger.addHandler(handler)
                console = logging.StreamHandler()
                console.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
                self.logger.addHandler(console)
            self.loggerLoaded = True
        return self.logger