"""
Logger Module
Structured logging and audit trails.
"""

import sys
import json
from loguru import logger
from pathlib import Path


def setup_logger(log_level: str = "INFO", log_file: str = "logs/ios.log") -> None:
    """Configures the Loguru logger."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    
    # Console handler (standard formatting for humans)
    logger.add(
        sys.stdout, 
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # File handler (JSON serialized for automation/audit trails)
    logger.add(
        str(log_path),
        level=log_level,
        rotation="10 MB",
        retention="1 month",
        serialize=True
    )


def log_audit_trail(ticker: str, field: str, old_val: any, new_val: any, source: str, confidence: int) -> None:
    """
    Structured JSON log for data changes.
    """
    audit_data = {
        "event": "audit_trail",
        "ticker": ticker,
        "field": field,
        "old": old_val,
        "new": new_val,
        "source": source,
        "confidence": confidence
    }
    logger.info(json.dumps(audit_data))
