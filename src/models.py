"""Core data models for the File Organizer."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class OperationType(Enum):
    """Types of file operations supported by the organizer."""
    RENAME = "rename"
    ORGANIZE_TYPE = "organize_type"
    ORGANIZE_DATE = "organize_date"
    CUSTOM = "custom"
    UNDO = "undo"


class CaseType(Enum):
    """Case transformation types for renaming operations."""
    LOWERCASE = "lowercase"
    UPPERCASE = "uppercase"
    TITLE = "title"


@dataclass
class Config:
    """Configuration for file organization operations."""
    target_dir: Path
    operation_type: OperationType
    dry_run: bool = False
    verbose: bool = False
    
    # Rename-specific options
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    sequential_template: Optional[str] = None
    case_type: Optional[CaseType] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    
    # Organize-specific options
    date_format: Optional[str] = None
    rules_file: Optional[Path] = None
    file_pattern: str = "*"


@dataclass
class Operation:
    """Represents a single file operation to be performed or undone."""
    operation_type: OperationType
    source_path: Path
    dest_path: Path
    timestamp: datetime
    executed: bool = False


@dataclass
class Rule:
    """Custom organization rule for file matching and categorization."""
    name: str
    pattern: str  # Glob or regex pattern
    destination: str  # Relative path from target directory
    priority: int


@dataclass
class OperationResults:
    """Results summary from executing file operations."""
    successful: int
    skipped: int
    errors: List[Tuple[Path, str]]  # (file, error_message)
    operations: List[Operation]


@dataclass
class FileInfo:
    """Metadata information about a file."""
    path: Path
    size: int
    modified_time: datetime
    created_time: datetime
    extension: str
