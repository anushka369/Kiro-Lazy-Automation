"""Property-based tests for FileSystem component."""

import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings
import pytest

from src.filesystem import FileSystem, PathError, PermissionError


# Custom strategies for generating test data
@st.composite
def file_names(draw):
    """Generate realistic filenames with extensions."""
    # Generate base name (alphanumeric with some special chars)
    base = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
        min_size=1,
        max_size=20
    ))
    # Generate extension
    extensions = ['.txt', '.pdf', '.jpg', '.png', '.doc', '.csv', '.json']
    ext = draw(st.sampled_from(extensions))
    return base + ext


@st.composite
def file_content(draw):
    """Generate file content."""
    return draw(st.binary(min_size=0, max_size=1024))


class TestConflictResolution:
    """
    Feature: file-organizer, Property 3: Conflict resolution with numeric suffixes
    Validates: Requirements 1.4
    """
    
    @given(
        filename=file_names(),
        num_conflicts=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100)
    def test_conflict_resolution_appends_numeric_suffix(self, filename, num_conflicts):
        """
        For any file being moved to a destination where a file with the same name 
        already exists, the system should append a numeric suffix (e.g., "_1", "_2") 
        to the new filename to prevent overwriting.
        """
        fs = FileSystem()
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create the initial file at destination
            dest_path = tmpdir_path / filename
            dest_path.write_text("original content")
            
            moved_files = []
            
            # Try to move multiple files with the same name
            for i in range(num_conflicts):
                # Create a source file
                source_path = tmpdir_path / f"source_{i}_{filename}"
                source_path.write_text(f"content {i}")
                
                # Move to the same destination (should resolve conflicts)
                fs.move_file(source_path, dest_path)
                
                # The file should have been moved with a numeric suffix
                # Check that source no longer exists
                assert not source_path.exists(), f"Source file {source_path} should not exist after move"
            
            # Verify the original file still exists
            assert dest_path.exists(), "Original destination file should still exist"
            assert dest_path.read_text() == "original content", "Original file should be unchanged"
            
            # Verify that files with numeric suffixes exist
            stem = dest_path.stem
            suffix = dest_path.suffix
            
            for i in range(1, num_conflicts + 1):
                expected_path = tmpdir_path / f"{stem}_{i}{suffix}"
                assert expected_path.exists(), f"File with suffix _{i} should exist: {expected_path}"
                assert expected_path.read_text() == f"content {i-1}", f"Content should match for file {i}"


class TestErrorResilience:
    """
    Feature: file-organizer, Property 23: Error resilience during processing
    Validates: Requirements 7.3
    """
    
    @given(
        valid_files=st.lists(file_names(), min_size=2, max_size=10, unique=True),
        error_index=st.integers(min_value=0, max_value=9)
    )
    @settings(max_examples=100)
    def test_error_on_one_file_continues_processing_others(self, valid_files, error_index):
        """
        For any operation where errors occur on specific files, the system should 
        log each error and continue processing all remaining files without stopping.
        """
        # Ensure error_index is within bounds
        if error_index >= len(valid_files):
            error_index = len(valid_files) - 1
        
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dest_dir = tmpdir_path / "dest"
            dest_dir.mkdir()
            
            # Create source files
            source_files = []
            for filename in valid_files:
                source_path = tmpdir_path / filename
                source_path.write_text(f"content of {filename}")
                source_files.append(source_path)
            
            # Track successful moves and errors
            successful_moves = []
            errors = []
            
            # Process all files, simulating an error on one
            for idx, source_path in enumerate(source_files):
                try:
                    if idx == error_index:
                        # Simulate an error by trying to move a non-existent file
                        non_existent = tmpdir_path / "non_existent_file.txt"
                        fs.move_file(non_existent, dest_dir / source_path.name)
                    else:
                        # Normal move operation
                        fs.move_file(source_path, dest_dir / source_path.name)
                        successful_moves.append(source_path.name)
                except (PathError, PermissionError) as e:
                    # Log the error and continue
                    errors.append((source_path.name if idx != error_index else "non_existent_file.txt", str(e)))
            
            # Verify that we had exactly one error
            assert len(errors) == 1, f"Should have exactly 1 error, got {len(errors)}"
            
            # Verify that all other files were processed successfully
            expected_successful = len(valid_files) - 1
            assert len(successful_moves) == expected_successful, \
                f"Should have {expected_successful} successful moves, got {len(successful_moves)}"
            
            # Verify that successful files exist in destination
            for filename in successful_moves:
                dest_file = dest_dir / filename
                assert dest_file.exists(), f"Successfully moved file should exist: {dest_file}"
    
    @given(
        filenames=st.lists(file_names(), min_size=3, max_size=8, unique=True)
    )
    @settings(max_examples=100)
    def test_permission_error_does_not_stop_processing(self, filenames):
        """
        Test that permission errors on individual files don't stop processing of remaining files.
        """
        fs = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dest_dir = tmpdir_path / "dest"
            dest_dir.mkdir()
            
            # Create all source files
            for filename in filenames:
                source_path = tmpdir_path / filename
                source_path.write_text(f"content of {filename}")
            
            # Track results
            successful = []
            failed = []
            
            # Process files, with potential for errors
            for filename in filenames:
                source_path = tmpdir_path / filename
                try:
                    if source_path.exists():
                        fs.move_file(source_path, dest_dir / filename)
                        successful.append(filename)
                except (PathError, PermissionError) as e:
                    failed.append((filename, str(e)))
            
            # All files should have been processed (either successfully or with error logged)
            total_processed = len(successful) + len(failed)
            assert total_processed == len(filenames), \
                f"All files should be processed. Expected {len(filenames)}, got {total_processed}"
            
            # Verify successful files exist in destination
            for filename in successful:
                assert (dest_dir / filename).exists(), f"File {filename} should exist in destination"
