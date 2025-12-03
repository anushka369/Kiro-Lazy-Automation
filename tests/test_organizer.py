"""Unit tests for Organizer component."""

import tempfile
from pathlib import Path
from datetime import datetime
import time
import os

import pytest

from src.organizer import Organizer
from src.filesystem import FileSystem
from src.models import OperationType


class TestOrganizer:
    """Unit tests for Organizer class."""
    
    def test_organize_by_type_basic(self):
        """Test basic file organization by type."""
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create test files
            doc_file = tmpdir_path / "document.pdf"
            doc_file.write_text("document content")
            
            img_file = tmpdir_path / "image.jpg"
            img_file.write_bytes(b"image data")
            
            files = [doc_file, img_file]
            
            # Organize by type
            operations = organizer.organize_by_type(files, target_dir)
            
            # Verify operations
            assert len(operations) == 2
            assert operations[0].operation_type == OperationType.ORGANIZE_TYPE
            assert operations[1].operation_type == OperationType.ORGANIZE_TYPE
            
            # Verify destinations
            assert operations[0].dest_path.parent.name == "documents"
            assert operations[1].dest_path.parent.name == "images"
    
    def test_get_category_documents(self):
        """Test category detection for document files."""
        organizer = Organizer()
        
        assert organizer._get_category('.pdf') == 'documents'
        assert organizer._get_category('.doc') == 'documents'
        assert organizer._get_category('.txt') == 'documents'
        assert organizer._get_category('.xlsx') == 'documents'
    
    def test_get_category_images(self):
        """Test category detection for image files."""
        organizer = Organizer()
        
        assert organizer._get_category('.jpg') == 'images'
        assert organizer._get_category('.png') == 'images'
        assert organizer._get_category('.gif') == 'images'
        assert organizer._get_category('.svg') == 'images'
    
    def test_get_category_videos(self):
        """Test category detection for video files."""
        organizer = Organizer()
        
        assert organizer._get_category('.mp4') == 'videos'
        assert organizer._get_category('.avi') == 'videos'
        assert organizer._get_category('.mkv') == 'videos'
    
    def test_get_category_audio(self):
        """Test category detection for audio files."""
        organizer = Organizer()
        
        assert organizer._get_category('.mp3') == 'audio'
        assert organizer._get_category('.wav') == 'audio'
        assert organizer._get_category('.flac') == 'audio'
    
    def test_get_category_archives(self):
        """Test category detection for archive files."""
        organizer = Organizer()
        
        assert organizer._get_category('.zip') == 'archives'
        assert organizer._get_category('.rar') == 'archives'
        assert organizer._get_category('.7z') == 'archives'
    
    def test_get_category_code(self):
        """Test category detection for code files."""
        organizer = Organizer()
        
        assert organizer._get_category('.py') == 'code'
        assert organizer._get_category('.js') == 'code'
        assert organizer._get_category('.java') == 'code'
        assert organizer._get_category('.html') == 'code'
    
    def test_get_category_unknown(self):
        """Test category detection for unknown extensions."""
        organizer = Organizer()
        
        assert organizer._get_category('.xyz') == 'other'
        assert organizer._get_category('.unknown') == 'other'
    
    def test_get_category_case_insensitive(self):
        """Test that category detection is case-insensitive."""
        organizer = Organizer()
        
        assert organizer._get_category('.PDF') == 'documents'
        assert organizer._get_category('.JPG') == 'images'
        assert organizer._get_category('.MP3') == 'audio'
    
    def test_organize_by_date_yyyy_mm_format(self):
        """Test date-based organization with YYYY/MM format."""
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create a test file
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")
            
            # Set modification time to a specific date
            test_date = datetime(2023, 5, 15, 12, 0, 0)
            timestamp = time.mktime(test_date.timetuple())
            os.utime(test_file, (timestamp, timestamp))
            
            # Organize by date
            operations = organizer.organize_by_date([test_file], target_dir, date_format="YYYY/MM")
            
            # Verify operation
            assert len(operations) == 1
            assert operations[0].operation_type == OperationType.ORGANIZE_DATE
            
            # Verify date folder format
            relative_path = operations[0].dest_path.relative_to(target_dir)
            assert str(relative_path.parent) == "2023/05"
    
    def test_organize_by_date_yyyy_dash_mm_format(self):
        """Test date-based organization with YYYY-MM format."""
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create a test file
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")
            
            # Set modification time to a specific date
            test_date = datetime(2023, 5, 15, 12, 0, 0)
            timestamp = time.mktime(test_date.timetuple())
            os.utime(test_file, (timestamp, timestamp))
            
            # Organize by date
            operations = organizer.organize_by_date([test_file], target_dir, date_format="YYYY-MM")
            
            # Verify operation
            assert len(operations) == 1
            
            # Verify date folder format
            relative_path = operations[0].dest_path.relative_to(target_dir)
            assert str(relative_path.parent) == "2023-05"
    
    def test_organize_by_date_preserves_filename(self):
        """Test that date organization preserves the original filename."""
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create a test file with a specific name
            test_file = tmpdir_path / "important_document.pdf"
            test_file.write_text("content")
            
            # Organize by date
            operations = organizer.organize_by_date([test_file], target_dir)
            
            # Verify filename is preserved
            assert operations[0].dest_path.name == "important_document.pdf"
            assert operations[0].source_path.name == operations[0].dest_path.name
    
    def test_organize_custom_returns_empty_list(self):
        """Test that organize_custom returns empty list (not yet implemented)."""
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")
            target_dir = tmpdir_path / "organized"
            
            # Call organize_custom with empty rules
            operations = organizer.organize_custom([test_file], [], target_dir)
            
            # Should return empty list when no rules provided
            assert operations == []
