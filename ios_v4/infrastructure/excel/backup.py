"""
Excel Backup Module
Ensures the original workbook is safely backed up before any modifications.
"""

import shutil
from pathlib import Path
from datetime import datetime
from infrastructure.logging.logger import logger


class ExcelBackupManager:
    """Handles secure backup creation of workbooks into YYYY/MM folders."""

    def __init__(self, backup_dir: Path | str = ".backups"):
        self.base_backup_dir = Path(backup_dir)

    def create_backup(self, source_path: Path | str) -> Path:
        """
        Creates a timestamped backup of the target Excel file in a YYYY/MM structure.
        Raises FileNotFoundError if source doesn't exist.
        """
        src = Path(source_path)
        if not src.exists():
            logger.error(f"Cannot backup. Source file not found: {src}")
            raise FileNotFoundError(f"Source file not found: {src}")

        now = datetime.now()
        year_month_dir = self.base_backup_dir / now.strftime("%Y") / now.strftime("%m")
        year_month_dir.mkdir(parents=True, exist_ok=True)

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{src.stem}_backup_{timestamp}{src.suffix}"
        dest = year_month_dir / backup_filename

        try:
            shutil.copy2(src, dest)
            logger.info(f"Backup successfully created at: {dest}")
            return dest
        except Exception as e:
            logger.error(f"Failed to create backup of {src}: {e}")
            raise
