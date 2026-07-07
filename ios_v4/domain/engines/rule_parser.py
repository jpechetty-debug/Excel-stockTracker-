"""
Rule Parser
Loads YAML rules and provides typed configurations for decision engines.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from infrastructure.logging.logger import logger


class RuleParser:
    """Parses and caches YAML rule configurations."""

    def __init__(self, rule_dir: Path | str = "rules"):
        self.rule_dir = Path(rule_dir)
        self._rules_cache: Dict[str, Dict[str, Any]] = {}

    def get_rules(self, rule_file: str) -> Dict[str, Any]:
        """Loads a YAML rule file. Caches the result in-memory."""
        if rule_file in self._rules_cache:
            return self._rules_cache[rule_file]
            
        file_path = self.rule_dir / f"{rule_file}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Rule file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self._rules_cache[rule_file] = data
            return data

    def get_rule_version(self, rule_file: str) -> str:
        """Returns the version embedded in the YAML."""
        data = self.get_rules(rule_file)
        return data.get("version", "unknown")
