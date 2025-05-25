import os
import sys
parent_path = os.path.abspath(os.path.join(str(__file__),'..','..','..'))
sys.path.append(parent_path)

from ai import PAIAConfig,PAIALogger

config1 = PAIAConfig()
config2 = PAIAConfig()
logger1 = PAIALogger({"level": "DEBUG", "dir": "logs"})
logger2 = PAIALogger({"level": "DEBUG", "dir2": "logs"})
print(f"Singleton tesd 1 (PAIAConfig==PAIAConfig) Result:{config1 is config2}")  # True
print(f"Singleton tesd 1 (PAIALogger==PAIALogger) Result:{logger1 is logger2}")  # True
print # True
