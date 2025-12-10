"""Unit tests for UndoManager component."""

import tempfile
import json
from pathlib import Path
from datetime import datetime
import pytest

from src.undo_manager import UndoManager, UndoManagerError
from src.filesystem import FileSystem
from src.models import Operation, OperationType, OperationResults


class TestUndoManagerBasics:
    """Test basic UndoManager functionality."""
    
    def test_initialization_default_log_dir(self):
        """Test that UndoManager initializes with default log directory."""
        undo_manager = UndoManager()
        
        # Should use home directory
        expected_dir = Path.home() / ".file_organizer" / "undo_logs"
        assert undo_manager.log_dir == expected_dir
        assert undo_manager.log_dir.exists()
    
    def test_initialization_custom_log_dir(self):
        """Test that UndoManager can use a custom log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_logs"
            undo_manager = UndoManager(log_dir=custom_dir)
            
            assert undo_manager.log_dir == custom_dir
            assert custom_dir.exists()
    
    def test_log_operation(self):
        """Test logging a single operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            operation = Operation(
                operation_type=OperationType.RENAME,
                source_path=Path("/tmp/source.txt"),
                dest_path=Path("/tmp/dest.txt"),
                timestamp=datetime.now(),
                executed=False
            )
            
            undo_manager.log_operation(operation)
            
            assert len(undo_manager.current_operations) == 1
            assert undo_manager.current_operations[0].executed is True
    
    def test_clear_current_log(self):
        """Test clearing the current operation log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            # Add some operations
            for i in range(3):
                operation = Operation(
                    operation_type=OperationType.RENAME,
                    source_path=Path(f"/tmp/source_{i}.txt"),
                    dest_path=Path(f"/tmp/dest_{i}.txt"),
                    timestamp=datetime.now(),
                    executed=True
                )
                undo_manager.log_operation(operation)
            
            assert len(undo_manager.current_operations) == 3
            
            undo_manager.clear_current_log()
            
            assert len(undo_manager.current_operations) == 0


class TestLogSaveAndLoad:
    """Test saving and loading undo logs."""
    
    def test_save_log_default_path(self):
        """Test saving log with default timestamped filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            operation = Operation(
                operation_type=OperationType.ORGANIZE_TYPE,
                source_path=Path("/tmp/file.txt"),
                dest_path=Path("/tmp/organized/file.txt"),
                timestamp=datetime.now(),
                executed=True
            )
            undo_manager.log_operation(operation)
            
            log_path = undo_manager.save_log()
            
            assert log_path.exists()
            assert log_path.parent == log_dir
            assert log_path.name.startswith("undo_log_")
            assert log_path.suffix == ".json"
    
    def test_save_log_custom_path(self):
        """Test saving log to a custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            custom_path = Path(tmpdir) / "custom_log.json"
            
            undo_manager = UndoManager(log_dir=log_dir)
            
            operation = Operation(
                operation_type=OperationType.RENAME,
                source_path=Path("/tmp/old.txt"),
                dest_path=Path("/tmp/new.txt"),
                timestamp=datetime.now(),
                executed=True
            )
            undo_manager.log_operation(operation)
            
            log_path = undo_manager.save_log(custom_path)
            
            assert log_path == custom_path
            assert custom_path.exists()
    
    def test_load_log_success(self):
        """Test loading a valid undo log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            # Create and save operations
            operations = []
            for i in range(3):
                operation = Operation(
                    operation_type=OperationType.ORGANIZE_DATE,
                    source_path=Path(f"/tmp/file_{i}.txt"),
                    dest_path=Path(f"/tmp/2024/01/file_{i}.txt"),
                    timestamp=datetime.now(),
                    executed=True
                )
                operations.append(operation)
                undo_manager.log_operation(operation)
            
            log_path = undo_manager.save_log()
            
            # Load the log
            loaded_operations = undo_manager.load_log(log_path)
            
            assert len(loaded_operations) == 3
            for original, loaded in zip(operations, loaded_operations):
                assert loaded.operation_type == original.operation_type
                assert loaded.source_path == original.source_path
                assert loaded.dest_path == original.dest_path
    
    def test_load_log_nonexistent_file(self):
        """Test loading a log file that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            nonexistent_path = Path(tmpdir) / "nonexistent.json"
            
            with pytest.raises(UndoManagerError, match="Undo log not found"):
                undo_manager.load_log(nonexistent_path)
    
    def test_load_log_invalid_json(self):
        """Test loading a log file with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            invalid_log = Path(tmpdir) / "invalid.json"
            invalid_log.write_text("{ invalid json }")
            
            with pytest.raises(UndoManagerError, match="Invalid undo log format"):
                undo_manager.load_log(invalid_log)
    
    def test_load_log_corrupted_data(self):
        """Test loading a log file with corrupted data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            corrupted_log = Path(tmpdir) / "corrupted.json"
            # Valid JSON but missing required fields
            corrupted_log.write_text('[{"operation_type": "rename"}]')
            
            with pytest.raises(UndoManagerError, match="Corrupted undo log data"):
                undo_manager.load_log(corrupted_log)


class TestUndoOperations:
    """Test undo functionality."""
    
    def test_undo_simple_move(self):
        """Test undoing a simple file move operation."""
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            
            undo_manager = UndoManager(filesystem=filesystem, log_dir=log_dir)
            
            # Create source file
            source_file = tmpdir_path / "source.txt"
            source_file.write_text("test content")
            
            dest_file = tmpdir_path / "dest" / "source.txt"
            
            # Perform move
            filesystem.move_file(source_file, dest_file)
            
            # Log the operation
            operation = Operation(
                operation_type=OperationType.ORGANIZE_TYPE,
                source_path=source_file,
                dest_path=dest_file,
                timestamp=datetime.now(),
                executed=True
            )
            undo_manager.log_operation(operation)
            
            # Save log
            log_path = undo_manager.save_log()
            
            # Verify file was moved
            assert not source_file.exists()
            assert dest_file.exists()
            
            # Undo
            results = undo_manager.undo(log_path)
            
            # Verify undo was successful
            assert results.successful == 1
            assert len(results.errors) == 0
            assert source_file.exists()
            assert not dest_file.exists()
            assert source_file.read_text() == "test content"
    
    def test_undo_no_log_found(self):
        """Test undo when no log file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            with pytest.raises(UndoManagerError, match="No recent operations found"):
                undo_manager.undo()
    
    def test_undo_empty_log(self):
        """Test undo with an empty log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            # Create empty log
            log_path = log_dir / "empty_log.json"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("[]")
            
            with pytest.raises(UndoManagerError, match="No operations found in undo log"):
                undo_manager.undo(log_path)
    
    def test_undo_most_recent_log(self):
        """Test that undo uses the most recent log when no path is specified."""
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            
            undo_manager = UndoManager(filesystem=filesystem, log_dir=log_dir)
            
            # Create and log first operation
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("content 1")
            dest1 = tmpdir_path / "dest1" / "file1.txt"
            
            filesystem.move_file(file1, dest1)
            op1 = Operation(
                operation_type=OperationType.ORGANIZE_TYPE,
                source_path=file1,
                dest_path=dest1,
                timestamp=datetime.now(),
                executed=True
            )
            undo_manager.log_operation(op1)
            log1 = undo_manager.save_log()
            
            # Clear and create second operation (more recent)
            undo_manager.clear_current_log()
            
            import time
            time.sleep(0.1)  # Ensure different timestamp
            
            file2 = tmpdir_path / "file2.txt"
            file2.write_text("content 2")
            dest2 = tmpdir_path / "dest2" / "file2.txt"
            
            filesystem.move_file(file2, dest2)
            op2 = Operation(
                operation_type=OperationType.ORGANIZE_TYPE,
                source_path=file2,
                dest_path=dest2,
                timestamp=datetime.now(),
                executed=True
            )
            undo_manager.log_operation(op2)
            log2 = undo_manager.save_log()
            
            # Undo without specifying path (should use most recent)
            results = undo_manager.undo()
            
            # Should have undone file2, not file1
            assert file2.exists()
            assert not dest2.exists()
            assert not file1.exists()  # Still moved
            assert dest1.exists()  # Still at destination


class TestGetLogFiles:
    """Test retrieving log files."""
    
    def test_get_log_files_empty(self):
        """Test getting log files when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            log_files = undo_manager.get_log_files()
            
            assert len(log_files) == 0
    
    def test_get_log_files_multiple(self):
        """Test getting multiple log files sorted by recency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            undo_manager = UndoManager(log_dir=log_dir)
            
            # Create multiple logs
            import time
            
            for i in range(3):
                operation = Operation(
                    operation_type=OperationType.RENAME,
                    source_path=Path(f"/tmp/file_{i}.txt"),
                    dest_path=Path(f"/tmp/renamed_{i}.txt"),
                    timestamp=datetime.now(),
                    executed=True
                )
                undo_manager.log_operation(operation)
                time.sleep(1.1)  # Ensure different timestamps (save_log uses seconds precision)
                undo_manager.save_log()
                undo_manager.clear_current_log()
            
            log_files = undo_manager.get_log_files()
            
            assert len(log_files) == 3
            
            # Verify they're sorted by recency (most recent first)
            for i in range(len(log_files) - 1):
                assert log_files[i].stat().st_mtime >= log_files[i + 1].stat().st_mtime
