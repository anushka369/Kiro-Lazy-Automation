"""Property-based tests for Organizer component."""

import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import pytest

from src.organizer import Organizer
from src.filesystem import FileSystem
from src.models import OperationType


# Custom strategies for generating test data
@st.composite
def file_with_extension(draw, extensions):
    """Generate a filename with a specific extension from the provided list."""
    base = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
        min_size=1,
        max_size=20
    ))
    ext = draw(st.sampled_from(extensions))
    return base + ext


class TestFileCategorization:
    """
    Feature: file-organizer, Property 1: File categorization by extension
    Validates: Requirements 1.1, 1.2
    """
    
    @given(
        num_docs=st.integers(min_value=0, max_value=5),
        num_images=st.integers(min_value=0, max_value=5),
        num_videos=st.integers(min_value=0, max_value=5),
        num_audio=st.integers(min_value=0, max_value=5),
        num_archives=st.integers(min_value=0, max_value=5),
        num_code=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_file_categorization_by_extension(
        self, num_docs, num_images, num_videos, num_audio, num_archives, num_code
    ):
        """
        For any set of files with various extensions, when organizing by type, 
        each file should be categorized into the correct predefined type group 
        (documents, images, videos, audio, archives, code) based on its extension 
        and moved to the corresponding subdirectory.
        """
        # Ensure we have at least one file
        total_files = num_docs + num_images + num_videos + num_audio + num_archives + num_code
        assume(total_files > 0)
        
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files for each category
            files_by_category = {
                'documents': [],
                'images': [],
                'videos': [],
                'audio': [],
                'archives': [],
                'code': []
            }
            
            # Documents
            doc_extensions = ['.pdf', '.doc', '.txt', '.csv', '.xlsx']
            for i in range(num_docs):
                ext = doc_extensions[i % len(doc_extensions)]
                filename = f"doc_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"document content {i}")
                files_by_category['documents'].append(file_path)
            
            # Images
            image_extensions = ['.jpg', '.png', '.gif', '.svg']
            for i in range(num_images):
                ext = image_extensions[i % len(image_extensions)]
                filename = f"image_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_bytes(b"fake image data")
                files_by_category['images'].append(file_path)
            
            # Videos
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov']
            for i in range(num_videos):
                ext = video_extensions[i % len(video_extensions)]
                filename = f"video_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_bytes(b"fake video data")
                files_by_category['videos'].append(file_path)
            
            # Audio
            audio_extensions = ['.mp3', '.wav', '.flac', '.ogg']
            for i in range(num_audio):
                ext = audio_extensions[i % len(audio_extensions)]
                filename = f"audio_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_bytes(b"fake audio data")
                files_by_category['audio'].append(file_path)
            
            # Archives
            archive_extensions = ['.zip', '.rar', '.7z', '.tar']
            for i in range(num_archives):
                ext = archive_extensions[i % len(archive_extensions)]
                filename = f"archive_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_bytes(b"fake archive data")
                files_by_category['archives'].append(file_path)
            
            # Code
            code_extensions = ['.py', '.js', '.java', '.cpp', '.html']
            for i in range(num_code):
                ext = code_extensions[i % len(code_extensions)]
                filename = f"code_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"// code content {i}")
                files_by_category['code'].append(file_path)
            
            # Collect all files
            all_files = []
            for category_files in files_by_category.values():
                all_files.extend(category_files)
            
            # Organize by type
            operations = organizer.organize_by_type(all_files, target_dir)
            
            # Verify we have the right number of operations
            assert len(operations) == total_files, \
                f"Should have {total_files} operations, got {len(operations)}"
            
            # Verify each operation categorizes correctly
            for operation in operations:
                source_path = operation.source_path
                dest_path = operation.dest_path
                
                # Get the extension
                extension = source_path.suffix.lower()
                
                # Determine expected category
                expected_category = organizer._get_category(extension)
                
                # Verify destination is in the correct category subdirectory
                assert dest_path.parent.name == expected_category, \
                    f"File {source_path.name} with extension {extension} should be in '{expected_category}' directory, but is in '{dest_path.parent.name}'"
                
                # Verify filename is preserved
                assert dest_path.name == source_path.name, \
                    f"Filename should be preserved: {source_path.name} -> {dest_path.name}"
                
                # Verify operation type
                assert operation.operation_type == OperationType.ORGANIZE_TYPE, \
                    f"Operation type should be ORGANIZE_TYPE"
    
    @given(
        extensions=st.lists(
            st.sampled_from([
                '.pdf', '.doc', '.txt',  # documents
                '.jpg', '.png', '.gif',  # images
                '.mp4', '.avi', '.mkv',  # videos
                '.mp3', '.wav', '.flac',  # audio
                '.zip', '.rar', '.7z',   # archives
                '.py', '.js', '.java'    # code
            ]),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_all_known_extensions_categorized(self, extensions):
        """
        Test that all known file extensions are properly categorized.
        """
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files with the given extensions
            files = []
            for idx, ext in enumerate(extensions):
                filename = f"file_{idx}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {idx}")
                files.append(file_path)
            
            # Organize by type
            operations = organizer.organize_by_type(files, target_dir)
            
            # Verify each file is categorized (not in 'other')
            for operation in operations:
                category = operation.dest_path.parent.name
                
                # All these extensions should be in known categories
                assert category in ['documents', 'images', 'videos', 'audio', 'archives', 'code'], \
                    f"Extension {operation.source_path.suffix} should be in a known category, got '{category}'"
    
    @given(
        num_files=st.integers(min_value=1, max_value=15),
        unknown_ext=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=97, max_codepoint=122),
            min_size=2,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_unknown_extensions_go_to_other(self, num_files, unknown_ext):
        """
        Test that files with unknown extensions are categorized as 'other'.
        """
        # Ensure the extension is truly unknown
        known_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp', '.tiff', '.tif',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg',
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso',
            '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', 
            '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.sh', '.bat'
        ]
        
        ext = f".{unknown_ext}"
        assume(ext.lower() not in known_extensions)
        
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files with unknown extension
            files = []
            for i in range(num_files):
                filename = f"file_{i}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                files.append(file_path)
            
            # Organize by type
            operations = organizer.organize_by_type(files, target_dir)
            
            # Verify all files go to 'other' category
            for operation in operations:
                category = operation.dest_path.parent.name
                assert category == 'other', \
                    f"Unknown extension {ext} should be categorized as 'other', got '{category}'"


class TestDirectoryCreation:
    """
    Feature: file-organizer, Property 2: Directory creation on demand
    Validates: Requirements 1.3
    """
    
    @given(
        extensions=st.lists(
            st.sampled_from(['.pdf', '.jpg', '.mp4', '.mp3', '.zip', '.py']),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_directory_creation_on_demand(self, extensions):
        """
        For any target subdirectory that does not exist, when moving a file to 
        that location, the system should create the directory before performing 
        the move operation.
        """
        organizer = Organizer()
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Ensure target directory doesn't exist initially
            assert not target_dir.exists(), "Target directory should not exist initially"
            
            # Create files
            files = []
            for idx, ext in enumerate(extensions):
                filename = f"file_{idx}{ext}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {idx}")
                files.append(file_path)
            
            # Organize by type (this creates operations)
            operations = organizer.organize_by_type(files, target_dir)
            
            # Track which category directories should be created
            expected_categories = set()
            for operation in operations:
                expected_categories.add(operation.dest_path.parent.name)
            
            # Execute the operations (simulate what the orchestrator would do)
            for operation in operations:
                # The directory should be created as part of the move
                filesystem.move_file(operation.source_path, operation.dest_path)
            
            # Verify that all necessary category directories were created
            for category in expected_categories:
                category_dir = target_dir / category
                assert category_dir.exists(), \
                    f"Category directory '{category}' should have been created"
                assert category_dir.is_dir(), \
                    f"'{category}' should be a directory"
            
            # Verify all files were moved successfully
            for operation in operations:
                assert operation.dest_path.exists(), \
                    f"File should exist at destination: {operation.dest_path}"
                assert not operation.source_path.exists(), \
                    f"Source file should not exist after move: {operation.source_path}"



class TestDateOrganization:
    """
    Feature: file-organizer, Property 13: Date-based organization correctness
    Validates: Requirements 4.1
    """
    
    @given(
        num_files=st.integers(min_value=1, max_value=15),
        year=st.integers(min_value=2020, max_value=2024),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28)  # Safe day range for all months
    )
    @settings(max_examples=100)
    def test_date_based_organization_correctness(self, num_files, year, month, day):
        """
        For any set of files with modification dates, organizing by date should 
        group files into year/month folder structures where each file is placed 
        in a folder corresponding to its modification date.
        """
        organizer = Organizer()
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files with specific modification times
            files = []
            file_dates = []
            
            for i in range(num_files):
                filename = f"file_{i}.txt"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                
                # Set modification time
                import time
                from datetime import datetime as dt
                
                # Create a datetime for this file
                file_date = dt(year, month, day, 12, 0, 0)
                timestamp = time.mktime(file_date.timetuple())
                
                # Set both access and modification time
                import os
                os.utime(file_path, (timestamp, timestamp))
                
                files.append(file_path)
                file_dates.append(file_date)
            
            # Organize by date
            operations = organizer.organize_by_date(files, target_dir, date_format="YYYY/MM")
            
            # Verify each file is placed in the correct date folder
            for idx, operation in enumerate(operations):
                expected_date = file_dates[idx]
                expected_folder = f"{expected_date.year}/{expected_date.month:02d}"
                
                # Get the relative path from target_dir
                relative_path = operation.dest_path.relative_to(target_dir)
                actual_folder = str(relative_path.parent)
                
                assert actual_folder == expected_folder, \
                    f"File should be in folder '{expected_folder}', but is in '{actual_folder}'"
                
                # Verify filename is preserved
                assert operation.dest_path.name == operation.source_path.name, \
                    f"Filename should be preserved: {operation.source_path.name} -> {operation.dest_path.name}"
    
    @given(
        files_data=st.lists(
            st.tuples(
                st.text(
                    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
                    min_size=1,
                    max_size=10
                ),
                st.integers(min_value=2020, max_value=2024),
                st.integers(min_value=1, max_value=12)
            ),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0]  # Unique filenames
        )
    )
    @settings(max_examples=100)
    def test_files_grouped_by_date(self, files_data):
        """
        Test that files with the same date are grouped together, and files with 
        different dates are in different folders.
        """
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files with various dates
            files = []
            expected_folders = {}
            
            for filename, year, month in files_data:
                full_name = f"{filename}.txt"
                file_path = tmpdir_path / full_name
                file_path.write_text(f"content of {filename}")
                
                # Set modification time
                import time
                from datetime import datetime as dt
                
                file_date = dt(year, month, 15, 12, 0, 0)
                timestamp = time.mktime(file_date.timetuple())
                
                import os
                os.utime(file_path, (timestamp, timestamp))
                
                files.append(file_path)
                expected_folders[full_name] = f"{year}/{month:02d}"
            
            # Organize by date
            operations = organizer.organize_by_date(files, target_dir, date_format="YYYY/MM")
            
            # Verify each file is in the correct folder
            for operation in operations:
                filename = operation.source_path.name
                expected_folder = expected_folders[filename]
                
                relative_path = operation.dest_path.relative_to(target_dir)
                actual_folder = str(relative_path.parent)
                
                assert actual_folder == expected_folder, \
                    f"File {filename} should be in '{expected_folder}', got '{actual_folder}'"


class TestDateFolderFormat:
    """
    Feature: file-organizer, Property 14: Date folder format compliance
    Validates: Requirements 4.2
    """
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        year=st.integers(min_value=2020, max_value=2024),
        month=st.integers(min_value=1, max_value=12),
        date_format=st.sampled_from(["YYYY/MM", "YYYY-MM"])
    )
    @settings(max_examples=100)
    def test_date_folder_format_compliance(self, num_files, year, month, date_format):
        """
        For any date-based organization with a specified format (YYYY/MM or YYYY-MM), 
        all created folders should follow the specified format consistently.
        """
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files
            files = []
            for i in range(num_files):
                filename = f"file_{i}.txt"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                
                # Set modification time
                import time
                from datetime import datetime as dt
                
                file_date = dt(year, month, 15, 12, 0, 0)
                timestamp = time.mktime(file_date.timetuple())
                
                import os
                os.utime(file_path, (timestamp, timestamp))
                
                files.append(file_path)
            
            # Organize by date with specified format
            operations = organizer.organize_by_date(files, target_dir, date_format=date_format)
            
            # Verify all operations use the correct format
            for operation in operations:
                relative_path = operation.dest_path.relative_to(target_dir)
                folder_path = str(relative_path.parent)
                
                if date_format == "YYYY/MM":
                    # Should be in format: YYYY/MM
                    expected_format = f"{year}/{month:02d}"
                    assert folder_path == expected_format, \
                        f"Folder should be in format YYYY/MM: expected '{expected_format}', got '{folder_path}'"
                    
                    # Verify it contains a slash
                    assert "/" in folder_path, \
                        f"YYYY/MM format should contain '/': {folder_path}"
                
                elif date_format == "YYYY-MM":
                    # Should be in format: YYYY-MM
                    expected_format = f"{year}-{month:02d}"
                    assert folder_path == expected_format, \
                        f"Folder should be in format YYYY-MM: expected '{expected_format}', got '{folder_path}'"
                    
                    # Verify it contains a dash
                    assert "-" in folder_path, \
                        f"YYYY-MM format should contain '-': {folder_path}"
    
    @given(
        year=st.integers(min_value=2020, max_value=2024),
        month=st.integers(min_value=1, max_value=12)
    )
    @settings(max_examples=100)
    def test_month_always_two_digits(self, year, month):
        """
        Test that months are always formatted with two digits (01-12, not 1-12).
        """
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create a file
            file_path = tmpdir_path / "test.txt"
            file_path.write_text("content")
            
            # Set modification time
            import time
            from datetime import datetime as dt
            
            file_date = dt(year, month, 15, 12, 0, 0)
            timestamp = time.mktime(file_date.timetuple())
            
            import os
            os.utime(file_path, (timestamp, timestamp))
            
            # Test both formats
            for date_format in ["YYYY/MM", "YYYY-MM"]:
                operations = organizer.organize_by_date([file_path], target_dir, date_format=date_format)
                
                relative_path = operations[0].dest_path.relative_to(target_dir)
                folder_path = str(relative_path.parent)
                
                # Extract month from folder path
                if date_format == "YYYY/MM":
                    month_str = folder_path.split("/")[1]
                else:  # YYYY-MM
                    month_str = folder_path.split("-")[1]
                
                # Verify month is two digits
                assert len(month_str) == 2, \
                    f"Month should be two digits, got '{month_str}'"
                assert month_str == f"{month:02d}", \
                    f"Month should be {month:02d}, got {month_str}"


class TestDateFallback:
    """
    Feature: file-organizer, Property 15: Date fallback to creation time
    Validates: Requirements 4.3
    """
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        year=st.integers(min_value=2020, max_value=2024),
        month=st.integers(min_value=1, max_value=12)
    )
    @settings(max_examples=100)
    def test_date_fallback_to_creation_time(self, num_files, year, month):
        """
        For any file where modification date is unavailable, the system should 
        use the file's creation date for date-based organization.
        
        This test mocks the FileSystem to simulate files where modification time
        is None, forcing the fallback to creation time.
        """
        from unittest.mock import Mock
        from datetime import datetime as dt
        
        # Create a mock filesystem that returns FileInfo with None for modified_time
        mock_filesystem = Mock(spec=FileSystem)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files
            files = []
            expected_folders = []
            
            for i in range(num_files):
                filename = f"file_{i}.txt"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                files.append(file_path)
                
                # Expected folder based on creation time
                expected_folders.append(f"{year}/{month:02d}")
            
            # Mock get_file_info to return FileInfo with None modified_time
            def mock_get_file_info(path):
                from src.models import FileInfo
                creation_date = dt(year, month, 15, 12, 0, 0)
                return FileInfo(
                    path=path,
                    size=100,
                    modified_time=None,  # Simulate unavailable modification time
                    created_time=creation_date,  # Should fall back to this
                    extension=path.suffix
                )
            
            mock_filesystem.get_file_info.side_effect = mock_get_file_info
            
            # Create organizer with mocked filesystem
            organizer = Organizer(filesystem=mock_filesystem)
            
            # Organize by date
            operations = organizer.organize_by_date(files, target_dir, date_format="YYYY/MM")
            
            # Verify operations were created
            assert len(operations) == num_files, \
                f"Should have {num_files} operations"
            
            # Verify all operations use the creation time (fallback)
            for idx, operation in enumerate(operations):
                relative_path = operation.dest_path.relative_to(target_dir)
                folder_path = str(relative_path.parent)
                
                # Should be in the expected folder based on creation time
                assert folder_path == expected_folders[idx], \
                    f"File should be in folder '{expected_folders[idx]}' (from creation time), got '{folder_path}'"
                
                # Verify the format is correct
                parts = folder_path.split("/")
                assert len(parts) == 2, \
                    f"Date folder should have year and month: {folder_path}"
                
                year_str, month_str = parts
                
                # Verify year matches
                assert year_str == str(year), \
                    f"Year should be {year}, got {year_str}"
                
                # Verify month matches
                assert month_str == f"{month:02d}", \
                    f"Month should be {month:02d}, got {month_str}"
            
            # Verify get_file_info was called for each file
            assert mock_filesystem.get_file_info.call_count == num_files, \
                f"get_file_info should be called {num_files} times"


class TestFilenamePreservation:
    """
    Feature: file-organizer, Property 16: Filename preservation during date organization
    Validates: Requirements 4.4
    """
    
    @given(
        filenames=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_ '),
                min_size=1,
                max_size=20
            ),
            min_size=1,
            max_size=15,
            unique=True
        ),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg', '.png', '.doc'])
    )
    @settings(max_examples=100)
    def test_filename_preservation_during_date_organization(self, filenames, extension):
        """
        For any file organized by date, the filename (excluding path) should 
        remain identical before and after the organization operation.
        """
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files
            files = []
            for filename in filenames:
                full_name = filename + extension
                file_path = tmpdir_path / full_name
                file_path.write_text(f"content of {filename}")
                files.append(file_path)
            
            # Organize by date
            operations = organizer.organize_by_date(files, target_dir, date_format="YYYY/MM")
            
            # Verify filename is preserved for each operation
            for operation in operations:
                source_name = operation.source_path.name
                dest_name = operation.dest_path.name
                
                assert source_name == dest_name, \
                    f"Filename should be preserved: '{source_name}' -> '{dest_name}'"
                
                # Verify extension is preserved
                assert operation.source_path.suffix == operation.dest_path.suffix, \
                    f"Extension should be preserved"
                
                # Verify stem is preserved
                assert operation.source_path.stem == operation.dest_path.stem, \
                    f"Filename stem should be preserved"
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        date_format=st.sampled_from(["YYYY/MM", "YYYY-MM"])
    )
    @settings(max_examples=100)
    def test_only_path_changes_not_filename(self, num_files, date_format):
        """
        Test that only the directory path changes, not the actual filename.
        """
        organizer = Organizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create files with various names
            files = []
            original_names = []
            
            for i in range(num_files):
                filename = f"important_file_{i}.txt"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                files.append(file_path)
                original_names.append(filename)
            
            # Organize by date
            operations = organizer.organize_by_date(files, target_dir, date_format=date_format)
            
            # Verify filenames are unchanged
            for idx, operation in enumerate(operations):
                assert operation.dest_path.name == original_names[idx], \
                    f"Filename should not change: expected '{original_names[idx]}', got '{operation.dest_path.name}'"
                
                # Verify only the parent directory changed
                assert operation.source_path.name == operation.dest_path.name, \
                    "Only the directory path should change, not the filename"
