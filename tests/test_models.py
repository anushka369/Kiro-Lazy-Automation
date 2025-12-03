"""Unit tests for core data models."""

from datetime import datetime
from pathlib import Path

from src.models import (
    Config,
    Operation,
    Rule,
    OperationResults,
    FileInfo,
    OperationType,
    CaseType,
)


def test_operation_type_enum():
    """Test OperationType enum values."""
    assert OperationType.RENAME.value == "rename"
    assert OperationType.ORGANIZE_TYPE.value == "organize_type"
    assert OperationType.ORGANIZE_DATE.value == "organize_date"
    assert OperationType.CUSTOM.value == "custom"
    assert OperationType.UNDO.value == "undo"


def test_case_type_enum():
    """Test CaseType enum values."""
    assert CaseType.LOWERCASE.value == "lowercase"
    assert CaseType.UPPERCASE.value == "uppercase"
    assert CaseType.TITLE.value == "title"


def test_config_creation():
    """Test Config dataclass creation with required fields."""
    config = Config(
        target_dir=Path("/tmp/test"),
        operation_type=OperationType.RENAME,
        dry_run=True,
        verbose=False,
    )
    assert config.target_dir == Path("/tmp/test")
    assert config.operation_type == OperationType.RENAME
    assert config.dry_run is True
    assert config.verbose is False
    assert config.file_pattern == "*"


def test_operation_creation():
    """Test Operation dataclass creation."""
    now = datetime.now()
    op = Operation(
        operation_type=OperationType.RENAME,
        source_path=Path("/tmp/old.txt"),
        dest_path=Path("/tmp/new.txt"),
        timestamp=now,
    )
    assert op.operation_type == OperationType.RENAME
    assert op.source_path == Path("/tmp/old.txt")
    assert op.dest_path == Path("/tmp/new.txt")
    assert op.timestamp == now
    assert op.executed is False


def test_rule_creation():
    """Test Rule dataclass creation."""
    rule = Rule(
        name="Documents",
        pattern="*.pdf",
        destination="documents",
        priority=1,
    )
    assert rule.name == "Documents"
    assert rule.pattern == "*.pdf"
    assert rule.destination == "documents"
    assert rule.priority == 1


def test_operation_results_creation():
    """Test OperationResults dataclass creation."""
    results = OperationResults(
        successful=5,
        skipped=2,
        errors=[(Path("/tmp/error.txt"), "Permission denied")],
        operations=[],
    )
    assert results.successful == 5
    assert results.skipped == 2
    assert len(results.errors) == 1
    assert results.errors[0][0] == Path("/tmp/error.txt")
    assert results.errors[0][1] == "Permission denied"


def test_file_info_creation():
    """Test FileInfo dataclass creation."""
    now = datetime.now()
    file_info = FileInfo(
        path=Path("/tmp/test.txt"),
        size=1024,
        modified_time=now,
        created_time=now,
        extension=".txt",
    )
    assert file_info.path == Path("/tmp/test.txt")
    assert file_info.size == 1024
    assert file_info.modified_time == now
    assert file_info.created_time == now
    assert file_info.extension == ".txt"
