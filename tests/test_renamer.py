"""Unit tests for Renamer component."""

import tempfile
from pathlib import Path
import pytest

from src.renamer import Renamer, DuplicateNameError
from src.models import CaseType, OperationType


class TestRenamer:
    """Unit tests for Renamer class."""
    
    def test_rename_pattern_basic(self):
        """Test basic pattern replacement."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create test files
            file1 = tmpdir_path / "test_file_1.txt"
            file2 = tmpdir_path / "test_file_2.txt"
            file1.write_text("content")
            file2.write_text("content")
            
            operations = renamer.rename_pattern([file1, file2], "test", "new")
            
            assert len(operations) == 2
            assert operations[0].dest_path.name == "new_file_1.txt"
            assert operations[1].dest_path.name == "new_file_2.txt"
    
    def test_rename_pattern_preserves_extension(self):
        """Test that pattern replacement preserves file extensions."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "document.pdf"
            file1.write_text("content")
            
            operations = renamer.rename_pattern([file1], "document", "report")
            
            assert len(operations) == 1
            assert operations[0].dest_path.suffix == ".pdf"
            assert operations[0].dest_path.name == "report.pdf"
    
    def test_rename_pattern_detects_duplicates(self):
        """Test that duplicate filenames are detected."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files where pattern replacement creates duplicates
            file1 = tmpdir_path / "report_draft.txt"
            file2 = tmpdir_path / "summary_draft.txt"
            file1.write_text("content")
            file2.write_text("content")
            
            # Replace 'report' with 'summary' - file1 becomes 'summary_draft.txt'
            # which conflicts with file2's name
            with pytest.raises(DuplicateNameError):
                renamer.rename_pattern([file1, file2], "report", "summary")
    
    def test_rename_sequential_basic(self):
        """Test basic sequential numbering."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            files = []
            for i in range(3):
                file_path = tmpdir_path / f"file{i}.txt"
                file_path.write_text("content")
                files.append(file_path)
            
            operations = renamer.rename_sequential(files, "photo_{n}")
            
            assert len(operations) == 3
            assert operations[0].dest_path.name == "photo_1.txt"
            assert operations[1].dest_path.name == "photo_2.txt"
            assert operations[2].dest_path.name == "photo_3.txt"
    
    def test_rename_sequential_preserves_extensions(self):
        """Test that sequential numbering preserves different extensions."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "image.jpg"
            file2 = tmpdir_path / "document.pdf"
            file1.write_text("content")
            file2.write_text("content")
            
            operations = renamer.rename_sequential([file1, file2], "file_{n}")
            
            assert operations[0].dest_path.name == "file_1.jpg"
            assert operations[1].dest_path.name == "file_2.pdf"
    
    def test_rename_case_lowercase(self):
        """Test lowercase transformation."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "MyFile.txt"
            file1.write_text("content")
            
            operations = renamer.rename_case([file1], CaseType.LOWERCASE)
            
            assert len(operations) == 1
            assert operations[0].dest_path.name == "myfile.txt"
    
    def test_rename_case_uppercase(self):
        """Test uppercase transformation."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "myfile.txt"
            file1.write_text("content")
            
            operations = renamer.rename_case([file1], CaseType.UPPERCASE)
            
            assert len(operations) == 1
            assert operations[0].dest_path.name == "MYFILE.txt"
    
    def test_rename_case_title(self):
        """Test title case transformation."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "my_file_name.txt"
            file1.write_text("content")
            
            operations = renamer.rename_case([file1], CaseType.TITLE)
            
            assert len(operations) == 1
            assert operations[0].dest_path.name == "My_File_Name.txt"
    
    def test_add_prefix(self):
        """Test adding prefix to filenames."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "document.txt"
            file1.write_text("content")
            
            operations = renamer.add_prefix_suffix([file1], prefix="new_")
            
            assert len(operations) == 1
            assert operations[0].dest_path.name == "new_document.txt"
    
    def test_add_suffix(self):
        """Test adding suffix to filenames."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "document.txt"
            file1.write_text("content")
            
            operations = renamer.add_prefix_suffix([file1], suffix="_backup")
            
            assert len(operations) == 1
            assert operations[0].dest_path.name == "document_backup.txt"
    
    def test_add_prefix_and_suffix(self):
        """Test adding both prefix and suffix."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "document.txt"
            file1.write_text("content")
            
            operations = renamer.add_prefix_suffix([file1], prefix="old_", suffix="_v1")
            
            assert len(operations) == 1
            assert operations[0].dest_path.name == "old_document_v1.txt"
    
    def test_operations_have_correct_type(self):
        """Test that all operations have correct operation type."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "test.txt"
            file1.write_text("content")
            
            operations = renamer.rename_pattern([file1], "test", "new")
            
            assert all(op.operation_type == OperationType.RENAME for op in operations)
            assert all(not op.executed for op in operations)
    
    def test_no_operation_when_name_unchanged(self):
        """Test that no operation is created when filename doesn't change."""
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            file1 = tmpdir_path / "document.txt"
            file1.write_text("content")
            
            # Pattern that doesn't match
            operations = renamer.rename_pattern([file1], "nonexistent", "new")
            
            # No operations should be created
            assert len(operations) == 0
