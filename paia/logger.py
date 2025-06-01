# ai/logger.py
import logging
import logging.handlers
import os
import json

from paia import PAIASingleton

class PAIALogger(metaclass=PAIASingleton):

    config_default = {"level": "DEBUG", "dir": ".", "file_name":"app.log"}

    def __init__(self):
        self.loggerLoaded = False
        self.logger = None
        self.__populateFromConfig(self.config_default)
        
    def __populateFromConfig(self, config:json = None):
        if config:
            self.logging_dir = config.get("dir",self.config_default.get("dir"))
            self.logging_file = config.get("file_name",self.config_default.get("file_name"))
            self.level = config.get("level",self.config_default.get("level"))
            self.logging_fullpath = os.path.join(self.logging_dir,self.logging_file)
            self.config = config
        
    
    def __loadLogger(self, config:json = None):
        if not self.loggerLoaded:
            self.__populateFromConfig(config)
            os.makedirs(self.logging_dir, exist_ok=True)
            self.logger = logging.getLogger('PAIAService')
            self.logger.setLevel(self.level)
            # Clean handlers
            if self.logger.hasHandlers():
                for handler in self.logger.handlers:
                    self.logger.removeHandler(handler)
            # Recreat handlers on load/reload
            handler = logging.handlers.RotatingFileHandler(self.logging_fullpath, maxBytes=5*1024*1024, backupCount=3)
            handler.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
            self.logger.addHandler(handler)
            console = logging.StreamHandler()
            console.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
            self.logger.addHandler(console)
            self.loggerLoaded = True
        return self.logger
    
    def update(self, config:json = None):
        self.loggerLoaded = False
        return self.__loadLogger(config)

    def getLogger(self):
        return self.__loadLogger()

    def info(self, val):
        return self.__loadLogger().info(val)

    def warning(self, val):
        return self.__loadLogger().warning(val)    

    def error(self, val):
        return self.__loadLogger().error(val)

    def debug(self, val):
        return self.__loadLogger().debug(val)