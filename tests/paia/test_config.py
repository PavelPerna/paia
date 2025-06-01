# tests/test_config.py
import pytest
import json
from paia import PAIAConfig

@pytest.fixture(autouse=True,scope="function")
def config_json(tmp_path):
    config_file = tmp_path / "config.json"
    config_data = {
        "server": {"host": "localhost", "port": 8000},
        "ui_dir": "ui",
        "services": {"text-generator": {"streamable": True, "parameters": []}}
    }
    config_file.write_text(json.dumps(config_data))
    return config_file

@pytest.fixture(autouse=True,scope="function")
def config_json_malformed(tmp_path):
    config_file = tmp_path / "config_malformed.json"
    config_file.write_text("{mal for mm;sdas meeet!")
    return config_file


@pytest.fixture(autouse=True,scope="function")
def config_json_access(tmp_path):
    config_file = tmp_path / "config_access.json"
    config_file.write_text("test")
    config_file.chmod(411)
    return config_file


def test_config_singleton():
    config1 = PAIAConfig()
    config2 = PAIAConfig()
    assert config1 is config2, "CONFIG should be a singleton"

def test_config_load(config_json):
    config = PAIAConfig().update(config_file=str(config_json))
    assert config["server"]["host"] == "localhost"
    assert config["ui_dir"] == "ui"
    assert config["services"]["text-generator"]["streamable"] is True

def test_config_missing_file(tmp_path):
    config = PAIAConfig().update(config_file=str(tmp_path / "missing.json"))
    assert config.get("is_default", False) == True

def test_config_malformed_file(config_json_malformed):
    config = PAIAConfig().update(config_file=str(config_json_malformed))
    assert config.get("is_default", False) == True

def test_config_access_file(config_json_access):
    config = PAIAConfig().update(config_file=str(config_json_access))
    assert config.get("is_default", False) == True

def test_config_ui_dir(config_json):
    PAIAConfig().update(config_file=str(config_json))
    assert PAIAConfig().ui_dir == "ui"