# ai/logger.py
import logging
import logging.handlers
import os
import json
from ai import PAIAConfig, PAIASingleton

class PAIALogger(metaclass=PAIASingleton):
    config = {"level": "DEBUG", "dir": ".", "file_name":"app.log"}
    def __init__(self):
        self.loggerLoaded = False
        self.logger = None
        self.config = PAIAConfig().getConfig().get("logging")
        self.__populateFromConfig(self.config)
        
    def __populateFromConfig(self, config:json = None):
        self.config = config
        self.logging_dir = config.get("dir",".")
        self.logging_file = config.get("file_name","app.log")
        self.logging_fullpath = os.path.join(self.logging_dir,self.logging_file)
        self.level = config.get("level","INFO")

    
    def __loadLogger(self):
        if self.loggerLoaded == False:
            self.__populateFromConfig(self.config)
            os.makedirs(self.logging_dir, exist_ok=True)
            self.logger = logging.getLogger('AIMicroService')
            self.logger.setLevel(self.level)
            if not self.loggerLoaded:
                handler = logging.handlers.RotatingFileHandler(self.logging_fullpath, maxBytes=5*1024*1024, backupCount=3)
                handler.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
                self.logger.addHandler(handler)
                console = logging.StreamHandler()
                console.setFormatter(logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s'))
                self.logger.addHandler(console)
            self.loggerLoaded = True
        return self.logger
    
    def update(self,config:json = None):
        self.loggerLoaded = False
        if config:
            self.config = config
        return self.__loadLogger()

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