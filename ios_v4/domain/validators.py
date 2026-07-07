"""
Data Validator Module
Enforces bounds checking and assigns confidence scores.
"""

from typing import Optional, Tuple
from infrastructure.logging.logger import logger


class DataValidator:
    """Validates metrics and assigns confidence scores based on rules."""
    
    @staticmethod
    def validate_pe(value: Optional[float]) -> Tuple[Optional[float], int]:
        """Validates Price to Earnings ratio."""
        if value is None:
            return None, 0
        if value < 0:
            logger.warning(f"Validation Reject: Negative P/E {value}")
            return None, 0
        if value > 500:
            logger.warning(f"Validation Warning: Extremely high P/E {value}")
            return value, 80 # Calculated/Questionable
        return value, 95 # Provider official

    @staticmethod
    def validate_roe(value: Optional[float]) -> Tuple[Optional[float], int]:
        """Validates Return on Equity."""
        if value is None:
            return None, 0
        if value > 400 or value < -400:
            logger.warning(f"Validation Reject: Unrealistic ROE {value}%")
            return None, 0
        return value, 95

    @staticmethod
    def validate_price(value: Optional[float]) -> Tuple[Optional[float], int]:
        """Validates Current Price."""
        if value is None:
            return None, 0
        if value <= 0:
            logger.warning(f"Validation Reject: Price cannot be <= 0 ({value})")
            return None, 0
        return value, 100 # Highly confident in price quotes generally

    @staticmethod
    def assign_confidence(source: str, is_calculated: bool) -> int:
        """Assigns baseline confidence score."""
        if is_calculated:
            return 80
        if source.lower() == "yfinance":
            return 95
        if source.lower() == "official":
            return 100
        return 50
