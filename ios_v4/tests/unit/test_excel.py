import pytest
from pathlib import Path
from infrastructure.excel.backup import ExcelBackupManager

from datetime import datetime

def test_backup_creation(tmp_path):
    # Setup source file
    source_file = tmp_path / "test.xlsx"
    source_file.write_text("dummy content")
    
    backup_dir = tmp_path / ".backups"
    manager = ExcelBackupManager(backup_dir=backup_dir)
    
    # Act
    backup_path = manager.create_backup(source_file)
    
    # Assert
    assert backup_path.exists()
    now = datetime.now()
    expected_parent = backup_dir / now.strftime("%Y") / now.strftime("%m")
    assert backup_path.parent == expected_parent
    assert backup_path.read_text() == "dummy content"

def test_backup_source_not_found(tmp_path):
    manager = ExcelBackupManager(backup_dir=tmp_path / "backups")
    with pytest.raises(FileNotFoundError):
        manager.create_backup(tmp_path / "non_existent.xlsx")
