"""
Configuration Loader Module
Responsible for reading YAML configurations.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Loads and provides access to YAML configurations."""

    def __init__(self, config_dir: Path | str = "config"):
        self.config_dir = Path(config_dir)
        self.settings = self._load_yaml("settings.yaml")
        self.column_map = self._load_yaml("column_map.yaml")

        active_rule_version = self.settings.get("rules", {}).get("active_version", "v4_0")
        rules_path = Path("rules") / f"{active_rule_version}.yaml"
        self.rules = self._load_yaml_absolute(rules_path)

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Loads a YAML file from the config directory."""
        filepath = self.config_dir / filename
        return self._load_yaml_absolute(filepath)

    def _load_yaml_absolute(self, filepath: Path) -> Dict[str, Any]:
        """Loads a YAML file from an absolute or exact path."""
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                return data if data else {}
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML file {filepath}: {e}")

    def get_setting(self, path: str, default: Any = None) -> Any:
        """Retrieves a nested setting using dot notation (e.g. 'application.threads')."""
        keys = path.split('.')
        current = self.settings
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
