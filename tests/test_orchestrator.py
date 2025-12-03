"""Unit tests for Orchestrator component."""

import tempfile
import shutil
from pathlib import Path
import pytest

from src.orchestrator import Orchestrator, OrchestratorError
from src.models import Config, OperationType, CaseType
from src.filesystem import FileSystem


class TestOrchestrator:
    """Test suite for Orchestrator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.orchestrator = Orchestrator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_organize_by_type(self):
        """Test organizing files by type."""
        # Create test files
        (self.temp_dir / "doc.pdf").write_text("content")
        (self.temp_dir / "image.jpg").write_text("content")
        (self.temp_dir / "code.py").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.ORGANIZE_TYPE,
            dry_run=False
        )
        
        results = self.orchestrator.execute(config)
        
        assert results.successful == 3
        assert results.skipped == 0
        assert len(results.errors) == 0
        
        # Verify files were moved to correct categories
        assert (self.temp_dir / "documents" / "doc.pdf").exists()
        assert (self.temp_dir / "images" / "image.jpg").exists()
        assert (self.temp_dir / "code" / "code.py").exists()
    
    def test_execute_rename_pattern(self):
        """Test pattern-based renaming."""
        # Create test files
        (self.temp_dir / "old_file1.txt").write_text("content")
        (self.temp_dir / "old_file2.txt").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.RENAME,
            pattern="old",
            replacement="new",
            dry_run=False
        )
        
        results = self.orchestrator.execute(config)
        
        assert results.successful == 2
        assert (self.temp_dir / "new_file1.txt").exists()
        assert (self.temp_dir / "new_file2.txt").exists()
        assert not (self.temp_dir / "old_file1.txt").exists()
    
    def test_execute_dry_run_no_changes(self):
        """Test that dry-run mode doesn't modify files."""
        # Create test files
        (self.temp_dir / "file1.txt").write_text("content")
        (self.temp_dir / "file2.jpg").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.ORGANIZE_TYPE,
            dry_run=True
        )
        
        results = self.orchestrator.execute(config)
        
        # Operations should be planned but not executed
        assert results.successful == 2
        assert len(results.operations) == 2
        
        # Files should still be in original location
        assert (self.temp_dir / "file1.txt").exists()
        assert (self.temp_dir / "file2.jpg").exists()
        assert not (self.temp_dir / "documents").exists()
        assert not (self.temp_dir / "images").exists()
    
    def test_plan_operations_organize_type(self):
        """Test operation planning for organize by type."""
        # Create test files
        (self.temp_dir / "doc.pdf").write_text("content")
        (self.temp_dir / "image.png").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.ORGANIZE_TYPE
        )
        
        operations = self.orchestrator.plan_operations(config)
        
        assert len(operations) == 2
        assert all(op.operation_type == OperationType.ORGANIZE_TYPE for op in operations)
        assert operations[0].source_path.name in ["doc.pdf", "image.png"]
    
    def test_plan_operations_rename_sequential(self):
        """Test operation planning for sequential renaming."""
        # Create test files
        (self.temp_dir / "file1.txt").write_text("content")
        (self.temp_dir / "file2.txt").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.RENAME,
            sequential_template="doc_{n}"
        )
        
        operations = self.orchestrator.plan_operations(config)
        
        assert len(operations) == 2
        assert operations[0].dest_path.name in ["doc_1.txt", "doc_2.txt"]
    
    def test_execute_operations_with_errors(self):
        """Test that errors are properly reported."""
        # Create a test file
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Create an operation with a non-existent source file
        from src.models import Operation
        from datetime import datetime
        
        # Create operation that will fail (source doesn't exist)
        non_existent = self.temp_dir / "nonexistent.txt"
        
        operation = Operation(
            operation_type=OperationType.RENAME,
            source_path=non_existent,  # This file doesn't exist
            dest_path=self.temp_dir / "dest.txt",
            timestamp=datetime.now()
        )
        
        results = self.orchestrator.execute_operations([operation], dry_run=False)
        
        # Should have an error
        assert len(results.errors) > 0
    
    def test_undo_logging(self):
        """Test that operations are logged for undo."""
        # Create test files
        (self.temp_dir / "file.txt").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.RENAME,
            pattern="file",
            replacement="renamed",
            dry_run=False
        )
        
        # Execute operation
        results = self.orchestrator.execute(config)
        
        # Check that undo log was created
        undo_logs = self.orchestrator.undo_manager.get_log_files()
        assert len(undo_logs) > 0
    
    def test_empty_directory(self):
        """Test handling of empty directory."""
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.ORGANIZE_TYPE
        )
        
        results = self.orchestrator.execute(config)
        
        assert results.successful == 0
        assert len(results.operations) == 0
    
    def test_invalid_rename_config(self):
        """Test error handling for invalid rename configuration."""
        # Create a test file so planning doesn't return empty
        (self.temp_dir / "test.txt").write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.RENAME,
            # Missing required rename parameters
        )
        
        with pytest.raises(OrchestratorError):
            self.orchestrator.plan_operations(config)
    
    def test_organize_by_date(self):
        """Test organizing files by date."""
        # Create test files
        test_file = self.temp_dir / "document.pdf"
        test_file.write_text("content")
        
        config = Config(
            target_dir=self.temp_dir,
            operation_type=OperationType.ORGANIZE_DATE,
            date_format="YYYY/MM",
            dry_run=False
        )
        
        results = self.orchestrator.execute(config)
        
        assert results.successful == 1
        # File should be in a year/month folder
        year_folders = list(self.temp_dir.glob("*/"))
        assert len(year_folders) > 0
