# tests/test_build_ui.py
import os
import pytest
from paia import PAIAConfig

@pytest.fixture
def ui_dir(tmp_path):
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    return ui_dir

def test_build_ui_generation(ui_dir, dir_fix):
    PAIAConfig().ui_dir = str(ui_dir)
    from build_ui import build_ui
    build_ui()
    assert os.path.exists(ui_dir / "index.html")
    assert os.path.exists(ui_dir / "styles.css")
    assert os.path.exists(ui_dir / "script.js")
    assert os.path.exists(ui_dir / "api.js")
    with open(ui_dir / "index.html", encoding='utf-8') as f:
        data = f.read()
        assert data.find('data-theme="light"')
        assert data.find('type="module"')
