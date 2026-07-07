"""
Normalization Layer
Converts raw provider JSON into standardized canonical data (currencies, dates, None).
"""

from typing import Dict, Any, Optional
import math
from datetime import datetime

class DataNormalizer:
    """
    Normalizes raw data from providers into canonical formats.
    """
    
    @staticmethod
    def normalize_value(val: Any) -> Optional[float | str]:
        """
        Standardizes missing or broken values to None.
        Converts numpy nans or generic strings to proper None types.
        """
        if val is None:
            return None
        if isinstance(val, (int, float)):
            if math.isnan(val) or math.isinf(val):
                return None
            return float(val)
        if isinstance(val, str):
            clean = val.strip().lower()
            if clean in ["n/a", "nan", "null", "none", "", "-"]:
                return None
            return val.strip()
        return val

    @staticmethod
    def normalize_currency(val: float, multiplier: str = "raw") -> float:
        """
        Standardizes currency base units. 
        Everything internally should be absolute base units (e.g., raw USD/INR).
        """
        if val is None:
            return None
        
        mult = multiplier.lower()
        if mult == "raw":
            return val
        elif mult in ["k", "thousands"]:
            return val * 1_000
        elif mult in ["m", "millions"]:
            return val * 1_000_000
        elif mult in ["b", "billions"]:
            return val * 1_000_000_000
        elif mult == "lakhs":
            return val * 100_000
        elif mult == "crores":
            return val * 10_000_000
        else:
            return val

    @staticmethod
    def normalize_date(date_val: Any) -> Optional[datetime]:
        """Normalizes various timestamp/date formats to a datetime object."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, (int, float)):
            # Assuming unix timestamp
            try:
                return datetime.fromtimestamp(date_val)
            except Exception:
                return None
        if isinstance(date_val, str):
            try:
                # Basic ISO format parse
                return datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            except ValueError:
                pass
        return None

    @classmethod
    def process_raw_data(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep-normalizes a raw dictionary representing financial data.
        """
        normalized = {}
        for key, value in raw_data.items():
            if isinstance(value, dict):
                normalized[key] = cls.process_raw_data(value)
            else:
                normalized[key] = cls.normalize_value(value)
        return normalized
