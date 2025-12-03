"""Unit tests for FileSystem component."""

import tempfile
import shutil
from pathlib import Path
import pytest

from src.filesystem import FileSystem, PathError, PermissionError, DiskSpaceError
from src.models import FileInfo


class TestFileSystem:
    """Unit tests for FileSystem operations."""
    
    def test_move_file_basic(self):
        """Test basic file move operation."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create source file
            source = tmpdir_path / "source.txt"
            source.write_text("test content")
            
            # Move to destination
            dest = tmpdir_path / "dest.txt"
            fs.move_file(source, dest)
            
            # Verify
            assert not source.exists()
            assert dest.exists()
            assert dest.read_text() == "test content"
    
    def test_move_file_with_conflict(self):
        """Test file move with existing destination."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create destination file
            dest = tmpdir_path / "file.txt"
            dest.write_text("original")
            
            # Create source file
            source = tmpdir_path / "source.txt"
            source.write_text("new content")
            
            # Move should create file_1.txt
            fs.move_file(source, dest)
            
            # Verify original is unchanged
            assert dest.read_text() == "original"
            
            # Verify new file with suffix exists
            new_file = tmpdir_path / "file_1.txt"
            assert new_file.exists()
            assert new_file.read_text() == "new content"
    
    def test_move_file_nonexistent_source(self):
        """Test moving non-existent file raises PathError."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            source = tmpdir_path / "nonexistent.txt"
            dest = tmpdir_path / "dest.txt"
            
            with pytest.raises(PathError):
                fs.move_file(source, dest)
    
    def test_create_directory(self):
        """Test directory creation."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            new_dir = tmpdir_path / "subdir" / "nested"
            
            fs.create_directory(new_dir)
            
            assert new_dir.exists()
            assert new_dir.is_dir()
    
    def test_list_files(self):
        """Test listing files with pattern."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create test files
            (tmpdir_path / "file1.txt").write_text("content")
            (tmpdir_path / "file2.txt").write_text("content")
            (tmpdir_path / "file3.pdf").write_text("content")
            (tmpdir_path / "subdir").mkdir()
            
            # List all files
            all_files = fs.list_files(tmpdir_path)
            assert len(all_files) == 3
            
            # List only txt files
            txt_files = fs.list_files(tmpdir_path, "*.txt")
            assert len(txt_files) == 2
    
    def test_get_file_info(self):
        """Test getting file metadata."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("test content")
            
            info = fs.get_file_info(test_file)
            
            assert isinstance(info, FileInfo)
            assert info.path == test_file
            assert info.size > 0
            assert info.extension == ".txt"
            assert info.modified_time is not None
            assert info.created_time is not None
    
    def test_rename_file(self):
        """Test file rename operation."""
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create source file
            source = tmpdir_path / "old_name.txt"
            source.write_text("content")
            
            # Rename
            dest = tmpdir_path / "new_name.txt"
            fs.rename_file(source, dest)
            
            # Verify
            assert not source.exists()
            assert dest.exists()
            assert dest.read_text() == "content"
