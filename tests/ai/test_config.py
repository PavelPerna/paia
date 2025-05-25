# tests/test_config.py
import pytest
import json
from ai import PAIAConfig

@pytest.fixture(autouse=True)
def config_json(tmp_path):
    config_file = tmp_path / "config.json"
    config_data = {
        "server": {"host": "localhost", "port": 8000},
        "ui_dir": "ui",
        "services": {"text-generator": {"streamable": True, "parameters": []}}
    }
    config_file.write_text(json.dumps(config_data))
    return config_file

def test_config_singleton():
    config1 = PAIAConfig()
    config2 = PAIAConfig()
    assert config1 is config2, "CONFIG should be a singleton"

def test_config_load(config_json):
    config = PAIAConfig().update(path=str(config_json))
    assert config["server"]["host"] == "localhost"
    assert config["ui_dir"] == "ui"
    assert config["services"]["text-generator"]["streamable"] is True

def test_config_missing_file(tmp_path):
    config = PAIAConfig().update(path=str(tmp_path / "missing.json"))
    assert config.get("is_default", False) == True

def test_config_ui_dir(config_json):
    PAIAConfig().update(path=str(config_json))
    assert PAIAConfig().ui_dir == "ui"