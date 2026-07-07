import pytest
import yaml
from pathlib import Path
from config.config_loader import ConfigLoader

@pytest.fixture
def mock_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Create dummy settings
    settings_data = {"application": {"threads": 4}, "rules": {"active_version": "v4_0"}}
    with open(config_dir / "settings.yaml", "w") as f:
        yaml.dump(settings_data, f)
        
    # Create dummy column map
    column_data = {"sheets": {"master": "Universe"}}
    with open(config_dir / "column_map.yaml", "w") as f:
        yaml.dump(column_data, f)
        
    # Create dummy rule
    rules_data = {"metadata": {"version": "v4.0"}}
    with open(rules_dir / "v4_0.yaml", "w") as f:
        yaml.dump(rules_data, f)

    return tmp_path

def test_config_loader_initialization(mock_config_dir, monkeypatch):
    monkeypatch.chdir(mock_config_dir)
    loader = ConfigLoader(config_dir="config")
    
    assert loader.settings["application"]["threads"] == 4
    assert loader.column_map["sheets"]["master"] == "Universe"
    assert loader.rules["metadata"]["version"] == "v4.0"

def test_get_setting_nested(mock_config_dir, monkeypatch):
    monkeypatch.chdir(mock_config_dir)
    loader = ConfigLoader(config_dir="config")
    
    assert loader.get_setting("application.threads") == 4
    assert loader.get_setting("non.existent.path", "default") == "default"
