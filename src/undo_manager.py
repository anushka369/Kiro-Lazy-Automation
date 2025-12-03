"""Undo Manager component for tracking and reversing file operations."""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.models import Operation, OperationResults, OperationType
from src.filesystem import FileSystem, FileSystemError


class UndoManagerError(Exception):
    """Base exception for undo manager operations."""
    pass


class UndoManager:
    """Manages operation logging and undo functionality."""
    
    def __init__(self, filesystem: FileSystem = None, log_dir: Optional[Path] = None):
        """
        Initialize the UndoManager.
        
        Args:
            filesystem: FileSystem instance for file operations (optional, creates new if not provided)
            log_dir: Directory to store undo logs (optional, defaults to ~/.file_organizer/undo_logs)
        """
        self.filesystem = filesystem or FileSystem()
        
        # Set default log directory to user's home directory
        if log_dir is None:
            home = Path.home()
            self.log_dir = home / ".file_organizer" / "undo_logs"
        else:
            self.log_dir = log_dir
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current operation log (in-memory)
        self.current_operations: List[Operation] = []
    
    def log_operation(self, operation: Operation) -> None:
        """
        Record an executed operation for potential undo.
        
        Args:
            operation: Operation object that was executed
        """
        # Mark as executed and add to current log
        operation.executed = True
        self.current_operations.append(operation)
    
    def save_log(self, log_path: Optional[Path] = None) -> Path:
        """
        Persist the current undo log to disk.
        
        Args:
            log_path: Optional custom path for the log file. If not provided,
                     generates a timestamped filename in the log directory.
        
        Returns:
            Path to the saved log file
        """
        if log_path is None:
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = self.log_dir / f"undo_log_{timestamp}.json"
        
        # Convert operations to JSON-serializable format
        operations_data = []
        for op in self.current_operations:
            op_dict = {
                "operation_type": op.operation_type.value,
                "source_path": str(op.source_path),
                "dest_path": str(op.dest_path),
                "timestamp": op.timestamp.isoformat(),
                "executed": op.executed
            }
            operations_data.append(op_dict)
        
        # Write to file
        with open(log_path, 'w') as f:
            json.dump(operations_data, f, indent=2)
        
        return log_path
    
    def load_log(self, log_path: Path) -> List[Operation]:
        """
        Load an undo log from disk.
        
        Args:
            log_path: Path to the log file
            
        Returns:
            List of Operation objects from the log
            
        Raises:
            UndoManagerError: If log file cannot be read or parsed
        """
        try:
            with open(log_path, 'r') as f:
                operations_data = json.load(f)
            
            # Convert JSON data back to Operation objects
            operations = []
            for op_dict in operations_data:
                operation = Operation(
                    operation_type=OperationType(op_dict["operation_type"]),
                    source_path=Path(op_dict["source_path"]),
                    dest_path=Path(op_dict["dest_path"]),
                    timestamp=datetime.fromisoformat(op_dict["timestamp"]),
                    executed=op_dict["executed"]
                )
                operations.append(operation)
            
            return operations
            
        except FileNotFoundError:
            raise UndoManagerError(f"Undo log not found: {log_path}")
        except json.JSONDecodeError as e:
            raise UndoManagerError(f"Invalid undo log format: {e}")
        except (KeyError, ValueError) as e:
            raise UndoManagerError(f"Corrupted undo log data: {e}")
    
    def undo(self, log_path: Optional[Path] = None) -> OperationResults:
        """
        Reverse operations from an undo log.
        
        If no log_path is provided, uses the most recent log file.
        
        Args:
            log_path: Optional path to specific log file to undo
            
        Returns:
            OperationResults with summary of undo operations
            
        Raises:
            UndoManagerError: If no undo log is found or operations cannot be reversed
        """
        # If no log path provided, find the most recent log
        if log_path is None:
            log_path = self._get_most_recent_log()
            if log_path is None:
                raise UndoManagerError("No recent operations found to undo")
        
        # Load operations from log
        operations = self.load_log(log_path)
        
        if not operations:
            raise UndoManagerError("No operations found in undo log")
        
        # Reverse operations in reverse order (LIFO)
        successful = 0
        skipped = 0
        errors = []
        reversed_operations = []
        
        for operation in reversed(operations):
            try:
                # Only undo executed operations
                if not operation.executed:
                    skipped += 1
                    continue
                
                # Reverse the operation: move from dest back to source
                if operation.dest_path.exists():
                    # Create a reverse operation for tracking
                    reverse_op = Operation(
                        operation_type=OperationType.UNDO,
                        source_path=operation.dest_path,
                        dest_path=operation.source_path,
                        timestamp=datetime.now(),
                        executed=False
                    )
                    
                    # Perform the reverse move
                    self.filesystem.move_file(operation.dest_path, operation.source_path)
                    
                    reverse_op.executed = True
                    reversed_operations.append(reverse_op)
                    successful += 1
                else:
                    # File doesn't exist at destination, can't undo
                    errors.append((operation.dest_path, "File not found at destination"))
                    skipped += 1
                    
            except FileSystemError as e:
                # Log error but continue with remaining operations
                errors.append((operation.dest_path, str(e)))
            except Exception as e:
                # Catch any unexpected errors
                errors.append((operation.dest_path, f"Unexpected error: {e}"))
        
        # Clean up empty directories after undo
        self._cleanup_empty_directories(operations)
        
        return OperationResults(
            successful=successful,
            skipped=skipped,
            errors=errors,
            operations=reversed_operations
        )
    
    def _get_most_recent_log(self) -> Optional[Path]:
        """
        Find the most recent undo log file.
        
        Returns:
            Path to the most recent log file, or None if no logs exist
        """
        # List all log files in the log directory
        log_files = list(self.log_dir.glob("undo_log_*.json"))
        
        if not log_files:
            return None
        
        # Sort by modification time (most recent first)
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return log_files[0]
    
    def _cleanup_empty_directories(self, operations: List[Operation]) -> None:
        """
        Remove empty directories after undo operations.
        
        Args:
            operations: List of operations that were undone
        """
        # Collect all destination directories
        directories = set()
        for operation in operations:
            directories.add(operation.dest_path.parent)
        
        # Try to remove empty directories (from deepest to shallowest)
        for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
            try:
                if directory.exists() and directory.is_dir():
                    # Only remove if empty
                    if not any(directory.iterdir()):
                        directory.rmdir()
            except Exception:
                # Ignore errors during cleanup
                pass
    
    def clear_current_log(self) -> None:
        """Clear the current in-memory operation log."""
        self.current_operations = []
    
    def has_undo_log(self) -> bool:
        """
        Check if there are any undo logs available.
        
        Returns:
            True if at least one undo log exists, False otherwise
        """
        return self._get_most_recent_log() is not None
    
    def get_log_files(self) -> List[Path]:
        """
        Get a list of all available undo log files.
        
        Returns:
            List of paths to undo log files, sorted by modification time (most recent first)
        """
        log_files = list(self.log_dir.glob("undo_log_*.json"))
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return log_files
