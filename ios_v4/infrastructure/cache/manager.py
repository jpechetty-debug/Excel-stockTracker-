"""
Cache Manager
Handles segmented persistence of Domain Models instead of raw responses.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from domain.exceptions import CacheMissError
from infrastructure.logging.logger import logger


class CacheManager:
    """Manages segregated JSON caches with type-specific TTLs."""
    
    TTL_POLICIES = {
        "quotes": timedelta(minutes=30),
        "profile": timedelta(days=30),
        "financials": timedelta(days=1),
        "balance_sheet": timedelta(days=1),
        "cash_flow": timedelta(days=1),
        "dividends": timedelta(days=7),
    }

    def __init__(self, base_dir: Path | str = ".cache"):
        self.base_dir = Path(base_dir)
        for sub_dir in self.TTL_POLICIES.keys():
            (self.base_dir / sub_dir).mkdir(parents=True, exist_ok=True)
            
    def get(self, data_type: str, key: str) -> Dict[str, Any]:
        """
        Retrieves a cached JSON object if it exists and hasn't expired.
        Raises CacheMissError on failure.
        """
        if data_type not in self.TTL_POLICIES:
            raise ValueError(f"Unknown cache data_type: {data_type}")
            
        file_path = self.base_dir / data_type / f"{key}.json"
        
        if not file_path.exists():
            raise CacheMissError(f"No cache found for {data_type}/{key}")
            
        # Check freshness
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        expiry = mtime + self.TTL_POLICIES[data_type]
        
        if datetime.now(timezone.utc) > expiry:
            raise CacheMissError(f"Cache expired for {data_type}/{key}")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Error reading cache {file_path}: {e}")
            raise CacheMissError(f"Corrupted cache for {data_type}/{key}")

    def set(self, data_type: str, key: str, data: Dict[str, Any]) -> None:
        """Saves a JSON-serializable dictionary to the cache."""
        if data_type not in self.TTL_POLICIES:
            raise ValueError(f"Unknown cache data_type: {data_type}")
            
        file_path = self.base_dir / data_type / f"{key}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write cache {file_path}: {e}")
