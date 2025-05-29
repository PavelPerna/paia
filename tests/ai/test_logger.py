# tests/test_logger.py
import pytest
import os
import logging
import json
from ai import PAIALogger, PAIALogger

def test_logger_singleton(dir_fix):
    logger1 = PAIALogger()
    logger2 = PAIALogger()
    assert logger1 is logger2, "LOGGER should be a singleton"

def test_logger_initialization(tmp_path,dir_fix):
    log_dir = tmp_path / "logs"
    logger = PAIALogger().update(config = {"level": logging.INFO, "dir": str(log_dir)})
    assert logger.level == logging.INFO
    assert os.path.exists(log_dir / "app.log")

def test_logger_write(tmp_path,dir_fix):
    log_dir = tmp_path / "logs"
    logger = PAIALogger().update(config = {"level": logging.DEBUG, "dir": str(log_dir)})
    assert logger.level == logging.DEBUG
    logger.info("Test message")
    with open(os.path.join(str(log_dir), "app.log")) as f:
        assert "Test message" in f.read()