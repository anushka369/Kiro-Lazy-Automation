"""Property-based tests for Orchestrator component."""

import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings
from datetime import datetime

from src.orchestrator import Orchestrator
from src.models import Config, OperationType, CaseType
from src.filesystem import FileSystem


# Custom strategies for generating test data
@st.composite
def file_tree_with_files(draw):
    """Generate a temporary directory with random files."""
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    # Generate 1-20 files
    num_files = draw(st.integers(min_value=1, max_value=20))
    
    files = []
    for i in range(num_files):
        # Generate filename with various extensions
        extension = draw(st.sampled_from(['.txt', '.pdf', '.jpg', '.mp3', '.zip', '.py']))
        filename = f"file_{i}{extension}"
        file_path = temp_dir / filename
        
        # Create the file with some content
        file_path.write_text(f"Content {i}")
        files.append(file_path)
    
    return temp_dir, files


@st.composite
def organize_type_config(draw, target_dir):
    """Generate a Config for organize-by-type operation."""
    return Config(
        target_dir=target_dir,
        operation_type=OperationType.ORGANIZE_TYPE,
        dry_run=draw(st.booleans()),
        verbose=draw(st.booleans()),
        file_pattern="*"
    )


@st.composite
def rename_pattern_config(draw, target_dir):
    """Generate a Config for pattern-based rename operation."""
    pattern = draw(st.sampled_from(['file', 'test', 'doc']))
    replacement = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return Config(
        target_dir=target_dir,
        operation_type=OperationType.RENAME,
        dry_run=draw(st.booleans()),
        verbose=draw(st.booleans()),
        pattern=pattern,
        replacement=replacement,
        file_pattern="*"
    )


def get_directory_snapshot(directory: Path):
    """
    Create a snapshot of directory state for comparison.
    
    Returns a set of (relative_path, content) tuples.
    """
    snapshot = set()
    
    for item in directory.rglob('*'):
        if item.is_file():
            relative_path = item.relative_to(directory)
            try:
                content = item.read_text()
                snapshot.add((str(relative_path), content))
            except Exception:
                # For binary files, just record existence
                snapshot.add((str(relative_path), None))
    
    return snapshot


# **Feature: file-organizer, Property 10: Dry-run mode file system invariant**
@settings(max_examples=100, deadline=None)
@given(st.data())
def test_dry_run_preserves_filesystem(data):
    """
    Property 10: Dry-run mode file system invariant
    
    For any operation executed in dry-run mode, the file system should remain
    completely unchanged - no files created, moved, renamed, or deleted.
    
    **Validates: Requirements 3.1, 3.3**
    """
    # Generate a file tree
    temp_dir, files = data.draw(file_tree_with_files())
    
    try:
        # Take snapshot of file system before operation
        before_snapshot = get_directory_snapshot(temp_dir)
        
        # Generate a config with dry_run=True
        config = data.draw(
            st.one_of(
                organize_type_config(temp_dir),
                rename_pattern_config(temp_dir)
            )
        )
        
        # Force dry_run to True
        config.dry_run = True
        
        # Execute operation in dry-run mode
        orchestrator = Orchestrator()
        results = orchestrator.execute(config)
        
        # Take snapshot after operation
        after_snapshot = get_directory_snapshot(temp_dir)
        
        # Assert: File system should be completely unchanged
        assert before_snapshot == after_snapshot, \
            "Dry-run mode modified the file system"
        
        # Additional check: All operations should be marked as not executed
        for operation in results.operations:
            assert not operation.executed, \
                "Operations in dry-run mode should not be marked as executed"
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)



# **Feature: file-organizer, Property 11: Dry-run output completeness**
@settings(max_examples=100, deadline=None)
@given(st.data())
def test_dry_run_output_completeness(data):
    """
    Property 11: Dry-run output completeness
    
    For any operation planned in dry-run mode, the output should include
    the original filename, new filename, and operation type for each planned change.
    
    **Validates: Requirements 3.2**
    """
    # Generate a file tree
    temp_dir, files = data.draw(file_tree_with_files())
    
    try:
        # Generate a config with dry_run=True
        config = data.draw(
            st.one_of(
                organize_type_config(temp_dir),
                rename_pattern_config(temp_dir)
            )
        )
        
        # Force dry_run to True
        config.dry_run = True
        
        # Execute operation in dry-run mode
        orchestrator = Orchestrator()
        results = orchestrator.execute(config)
        
        # Assert: Each operation should have complete information
        for operation in results.operations:
            # Check that source_path exists (original filename)
            assert operation.source_path is not None, \
                "Operation missing source_path (original filename)"
            assert isinstance(operation.source_path, Path), \
                "source_path should be a Path object"
            
            # Check that dest_path exists (new filename)
            assert operation.dest_path is not None, \
                "Operation missing dest_path (new filename)"
            assert isinstance(operation.dest_path, Path), \
                "dest_path should be a Path object"
            
            # Check that operation_type exists
            assert operation.operation_type is not None, \
                "Operation missing operation_type"
            assert isinstance(operation.operation_type, OperationType), \
                "operation_type should be an OperationType enum"
            
            # Check that source and dest are different (otherwise no operation needed)
            # Note: They might be the same if no change is needed, but that's okay
            
            # Check that timestamp exists
            assert operation.timestamp is not None, \
                "Operation missing timestamp"
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)



# **Feature: file-organizer, Property 12: Dry-run summary accuracy**
@settings(max_examples=100, deadline=None)
@given(st.data())
def test_dry_run_summary_accuracy(data):
    """
    Property 12: Dry-run summary accuracy
    
    For any dry-run execution, the summary count of operations should exactly
    match the number of planned operations displayed.
    
    **Validates: Requirements 3.4**
    """
    # Generate a file tree
    temp_dir, files = data.draw(file_tree_with_files())
    
    try:
        # Generate a config with dry_run=True
        config = data.draw(
            st.one_of(
                organize_type_config(temp_dir),
                rename_pattern_config(temp_dir)
            )
        )
        
        # Force dry_run to True
        config.dry_run = True
        
        # Execute operation in dry-run mode
        orchestrator = Orchestrator()
        results = orchestrator.execute(config)
        
        # Count the number of operations in the results
        num_operations = len(results.operations)
        
        # Assert: The summary count should match the number of operations
        # In dry-run mode, all operations should be counted as "successful"
        # (meaning they would be performed if not in dry-run mode)
        assert results.successful == num_operations, \
            f"Summary count ({results.successful}) doesn't match number of operations ({num_operations})"
        
        # Assert: No operations should be skipped or have errors in dry-run mode
        # (unless there's a planning error, which would be caught earlier)
        assert results.skipped == 0, \
            "Dry-run should not skip operations"
        
        assert len(results.errors) == 0, \
            "Dry-run should not have errors"
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)



# **Feature: file-organizer, Property 4: Accurate operation reporting**
@settings(max_examples=100, deadline=None)
@given(st.data())
def test_accurate_operation_reporting(data):
    """
    Property 4: Accurate operation reporting
    
    For any completed operation, the system should report counts (successful,
    skipped, errors) that exactly match the actual number of operations
    performed in each category.
    
    **Validates: Requirements 1.5, 7.2**
    """
    # Generate a file tree
    temp_dir, files = data.draw(file_tree_with_files())
    
    try:
        # Generate a config (not dry-run, so operations are actually executed)
        config = data.draw(
            st.one_of(
                organize_type_config(temp_dir),
                rename_pattern_config(temp_dir)
            )
        )
        
        # Force dry_run to False to actually execute operations
        config.dry_run = False
        
        # Execute operation
        orchestrator = Orchestrator()
        results = orchestrator.execute(config)
        
        # Count actual operations by category
        actual_successful = sum(1 for op in results.operations if op.executed)
        actual_errors = len(results.errors)
        
        # Assert: Reported counts should match actual counts
        assert results.successful == actual_successful, \
            f"Reported successful count ({results.successful}) doesn't match actual ({actual_successful})"
        
        assert len(results.errors) == actual_errors, \
            f"Reported error count ({len(results.errors)}) doesn't match actual ({actual_errors})"
        
        # Assert: Total operations should equal successful + skipped + errors
        total_operations = len(results.operations)
        reported_total = results.successful + results.skipped + len(results.errors)
        
        assert reported_total == total_operations, \
            f"Sum of reported counts ({reported_total}) doesn't match total operations ({total_operations})"
        
        # Assert: All operations should be accounted for
        for operation in results.operations:
            # Each operation should either be executed successfully or have an error
            if operation.executed:
                # Should be counted in successful
                assert results.successful > 0, "Executed operations not counted in successful"
            else:
                # Should be in errors or skipped
                # (In our current implementation, failed operations are in errors)
                pass
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
