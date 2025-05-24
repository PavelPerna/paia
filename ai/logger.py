# ai/logger.py
import logging
import logging.handlers
import os
from ai import PAIA_CONFIG, PAIASingleton

class PAIALogger(PAIASingleton):
    config = {"level": "DEBUG", "dir": ".", "file_name":"app.log"}
    def __init__(self):
        self.loggerLoaded = False
        self.logger = None
        self.config = PAIA_CONFIG.get().get("logging")
        self.config["logfile_path"] = os.path.join(self.config.get("dir"),self.config.get("file_name"))
    
    def loadLogger(self):
        if not self.loggerLoaded:
            logging_level = getattr(logging, self.config.get("level", "DEBUG"), logging.DEBUG)
            logging_dir = self.config.get("dir", ".")
            os.makedirs(logging_dir, exist_ok=True)
            self.logger = logging.getLogger('AIMicroService')
            self.logger.setLevel(logging_level)
            if not self.logger.handlers:
                handler = logging.handlers.RotatingFileHandler(self.config["logfile_path"], maxBytes=5*1024*1024, backupCount=3)
                handler.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
                self.logger.addHandler(handler)
                console = logging.StreamHandler()
                console.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
                self.logger.addHandler(console)
            self.loggerLoaded = True
        return self.logger
    def get(self):
        return self.loadLogger()

PAIA_LOGGER = PAIALogger().get()