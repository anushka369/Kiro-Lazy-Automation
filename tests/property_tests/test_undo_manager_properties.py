"""Property-based tests for UndoManager component."""

import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import pytest

from src.undo_manager import UndoManager
from src.filesystem import FileSystem
from src.models import Operation, OperationType


class TestUndoLogCompleteness:
    """
    Feature: file-organizer, Property 20: Undo log completeness
    Validates: Requirements 6.1
    """
    
    @given(
        num_operations=st.integers(min_value=1, max_value=20),
        operation_type=st.sampled_from([
            OperationType.RENAME,
            OperationType.ORGANIZE_TYPE,
            OperationType.ORGANIZE_DATE,
            OperationType.CUSTOM
        ])
    )
    @settings(max_examples=100)
    def test_undo_log_completeness(self, num_operations, operation_type):
        """
        For any completed operation, the undo log should contain entries for 
        all file movements and renames that were executed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            
            undo_manager = UndoManager(log_dir=log_dir)
            
            # Create a set of operations
            operations = []
            for i in range(num_operations):
                source = tmpdir_path / f"source_{i}.txt"
                dest = tmpdir_path / "dest" / f"dest_{i}.txt"
                
                operation = Operation(
                    operation_type=operation_type,
                    source_path=source,
                    dest_path=dest,
                    timestamp=datetime.now(),
                    executed=True
                )
                operations.append(operation)
                
                # Log the operation
                undo_manager.log_operation(operation)
            
            # Save the log
            log_path = undo_manager.save_log()
            
            # Verify log file was created
            assert log_path.exists(), "Log file should be created"
            
            # Load the log back
            loaded_operations = undo_manager.load_log(log_path)
            
            # Verify completeness: all operations should be in the log
            assert len(loaded_operations) == num_operations, \
                f"Log should contain all {num_operations} operations, got {len(loaded_operations)}"
            
            # Verify each operation is correctly logged
            for idx, (original, loaded) in enumerate(zip(operations, loaded_operations)):
                assert loaded.operation_type == original.operation_type, \
                    f"Operation {idx}: type mismatch"
                assert loaded.source_path == original.source_path, \
                    f"Operation {idx}: source path mismatch"
                assert loaded.dest_path == original.dest_path, \
                    f"Operation {idx}: dest path mismatch"
                assert loaded.executed == original.executed, \
                    f"Operation {idx}: executed flag mismatch"
    
    @given(
        operations_data=st.lists(
            st.tuples(
                st.text(
                    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
                    min_size=1,
                    max_size=15
                ),
                st.text(
                    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
                    min_size=1,
                    max_size=15
                ),
                st.sampled_from([
                    OperationType.RENAME,
                    OperationType.ORGANIZE_TYPE,
                    OperationType.ORGANIZE_DATE
                ])
            ),
            min_size=1,
            max_size=15
        )
    )
    @settings(max_examples=100)
    def test_log_preserves_operation_details(self, operations_data):
        """
        Test that all operation details (paths, types, timestamps) are preserved 
        in the undo log.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            
            undo_manager = UndoManager(log_dir=log_dir)
            
            # Create operations with various details
            operations = []
            for source_name, dest_name, op_type in operations_data:
                source = tmpdir_path / f"{source_name}.txt"
                dest = tmpdir_path / "organized" / f"{dest_name}.txt"
                
                operation = Operation(
                    operation_type=op_type,
                    source_path=source,
                    dest_path=dest,
                    timestamp=datetime.now(),
                    executed=True
                )
                operations.append(operation)
                undo_manager.log_operation(operation)
            
            # Save and reload
            log_path = undo_manager.save_log()
            loaded_operations = undo_manager.load_log(log_path)
            
            # Verify all details are preserved
            assert len(loaded_operations) == len(operations), \
                "All operations should be in the log"
            
            for original, loaded in zip(operations, loaded_operations):
                # Check all fields
                assert str(loaded.source_path) == str(original.source_path), \
                    "Source path should be preserved"
                assert str(loaded.dest_path) == str(original.dest_path), \
                    "Dest path should be preserved"
                assert loaded.operation_type == original.operation_type, \
                    "Operation type should be preserved"
                assert loaded.executed == original.executed, \
                    "Executed flag should be preserved"
                # Timestamps should be close (within a second due to serialization)
                time_diff = abs((loaded.timestamp - original.timestamp).total_seconds())
                assert time_diff < 1, \
                    "Timestamp should be preserved"


class TestUndoRoundTrip:
    """
    Feature: file-organizer, Property 21: Undo operation round-trip
    Validates: Requirements 6.2, 6.3
    """
    
    @given(
        num_files=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100)
    def test_undo_operation_round_trip(self, num_files):
        """
        For any set of file operations followed immediately by an undo command, 
        all files should be restored to their original locations and names, 
        returning the file system to its pre-operation state.
        """
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            dest_dir = tmpdir_path / "organized"
            
            undo_manager = UndoManager(filesystem=filesystem, log_dir=log_dir)
            
            # Create source files and record their initial state
            source_files = []
            file_contents = {}
            
            for i in range(num_files):
                filename = f"file_{i}.txt"
                file_path = tmpdir_path / filename
                content = f"content of file {i}"
                file_path.write_text(content)
                
                source_files.append(file_path)
                file_contents[filename] = content
            
            # Perform operations (move files to organized directory)
            operations = []
            for source_file in source_files:
                dest_file = dest_dir / source_file.name
                
                operation = Operation(
                    operation_type=OperationType.ORGANIZE_TYPE,
                    source_path=source_file,
                    dest_path=dest_file,
                    timestamp=datetime.now(),
                    executed=False
                )
                
                # Execute the operation
                filesystem.move_file(source_file, dest_file)
                operation.executed = True
                
                # Log it
                undo_manager.log_operation(operation)
                operations.append(operation)
            
            # Verify files were moved
            for source_file in source_files:
                assert not source_file.exists(), \
                    f"Source file should not exist after move: {source_file}"
            
            for operation in operations:
                assert operation.dest_path.exists(), \
                    f"Dest file should exist after move: {operation.dest_path}"
            
            # Save the log
            log_path = undo_manager.save_log()
            
            # Perform undo
            results = undo_manager.undo(log_path)
            
            # Verify undo was successful
            assert results.successful == num_files, \
                f"All {num_files} operations should be undone successfully, got {results.successful}"
            assert len(results.errors) == 0, \
                f"No errors should occur during undo, got {results.errors}"
            
            # Verify files are back at original locations
            for source_file in source_files:
                assert source_file.exists(), \
                    f"Source file should exist after undo: {source_file}"
                
                # Verify content is preserved
                content = source_file.read_text()
                expected_content = file_contents[source_file.name]
                assert content == expected_content, \
                    f"File content should be preserved: expected '{expected_content}', got '{content}'"
            
            # Verify destination files are gone
            for operation in operations:
                assert not operation.dest_path.exists(), \
                    f"Dest file should not exist after undo: {operation.dest_path}"
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        subdirs=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=97, max_codepoint=122),
                min_size=3,
                max_size=10
            ),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_undo_with_nested_directories(self, num_files, subdirs):
        """
        Test that undo works correctly with nested directory structures.
        """
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            
            undo_manager = UndoManager(filesystem=filesystem, log_dir=log_dir)
            
            # Create source files
            source_files = []
            for i in range(num_files):
                filename = f"file_{i}.txt"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                source_files.append(file_path)
            
            # Move files to nested subdirectories
            operations = []
            for idx, source_file in enumerate(source_files):
                # Pick a subdirectory for this file
                subdir = subdirs[idx % len(subdirs)]
                dest_dir = tmpdir_path / "organized" / subdir
                dest_file = dest_dir / source_file.name
                
                operation = Operation(
                    operation_type=OperationType.ORGANIZE_TYPE,
                    source_path=source_file,
                    dest_path=dest_file,
                    timestamp=datetime.now(),
                    executed=False
                )
                
                # Execute
                filesystem.move_file(source_file, dest_file)
                operation.executed = True
                undo_manager.log_operation(operation)
                operations.append(operation)
            
            # Save log and undo
            log_path = undo_manager.save_log()
            results = undo_manager.undo(log_path)
            
            # Verify all files are back
            assert results.successful == num_files, \
                f"All operations should be undone"
            
            for source_file in source_files:
                assert source_file.exists(), \
                    f"File should be restored: {source_file}"


class TestPartialUndoResilience:
    """
    Feature: file-organizer, Property 22: Partial undo resilience
    Validates: Requirements 6.4
    """
    
    @given(
        num_files=st.integers(min_value=3, max_value=15),
        num_to_delete=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100)
    def test_partial_undo_resilience(self, num_files, num_to_delete):
        """
        For any undo operation where some files cannot be restored, the system 
        should report failures for those specific files and successfully restore 
        all other files.
        """
        # Ensure we don't try to delete more files than we have
        assume(num_to_delete < num_files)
        
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            dest_dir = tmpdir_path / "organized"
            
            undo_manager = UndoManager(filesystem=filesystem, log_dir=log_dir)
            
            # Create and move files
            source_files = []
            operations = []
            
            for i in range(num_files):
                filename = f"file_{i}.txt"
                source_file = tmpdir_path / filename
                source_file.write_text(f"content {i}")
                source_files.append(source_file)
                
                dest_file = dest_dir / filename
                
                operation = Operation(
                    operation_type=OperationType.ORGANIZE_TYPE,
                    source_path=source_file,
                    dest_path=dest_file,
                    timestamp=datetime.now(),
                    executed=False
                )
                
                # Execute the move
                filesystem.move_file(source_file, dest_file)
                operation.executed = True
                undo_manager.log_operation(operation)
                operations.append(operation)
            
            # Save the log
            log_path = undo_manager.save_log()
            
            # Delete some destination files to simulate failures
            files_to_delete = operations[:num_to_delete]
            for operation in files_to_delete:
                if operation.dest_path.exists():
                    operation.dest_path.unlink()
            
            # Perform undo
            results = undo_manager.undo(log_path)
            
            # Verify partial success
            expected_successful = num_files - num_to_delete
            assert results.successful == expected_successful, \
                f"Should successfully undo {expected_successful} operations, got {results.successful}"
            
            # Verify errors were reported for deleted files
            assert len(results.errors) >= num_to_delete, \
                f"Should report at least {num_to_delete} errors, got {len(results.errors)}"
            
            # Verify the files that could be restored were restored
            restored_count = 0
            for operation in operations[num_to_delete:]:
                if operation.source_path.exists():
                    restored_count += 1
            
            assert restored_count == expected_successful, \
                f"Should restore {expected_successful} files, got {restored_count}"
    
    @given(
        num_files=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=100)
    def test_undo_continues_after_errors(self, num_files):
        """
        Test that undo continues processing remaining files even when some 
        operations fail.
        """
        filesystem = FileSystem()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            log_dir = tmpdir_path / "logs"
            dest_dir = tmpdir_path / "organized"
            
            undo_manager = UndoManager(filesystem=filesystem, log_dir=log_dir)
            
            # Create and move files
            operations = []
            for i in range(num_files):
                source_file = tmpdir_path / f"file_{i}.txt"
                source_file.write_text(f"content {i}")
                
                dest_file = dest_dir / f"file_{i}.txt"
                
                operation = Operation(
                    operation_type=OperationType.ORGANIZE_TYPE,
                    source_path=source_file,
                    dest_path=dest_file,
                    timestamp=datetime.now(),
                    executed=False
                )
                
                filesystem.move_file(source_file, dest_file)
                operation.executed = True
                undo_manager.log_operation(operation)
                operations.append(operation)
            
            # Save log
            log_path = undo_manager.save_log()
            
            # Delete every other destination file
            deleted_count = 0
            for idx, operation in enumerate(operations):
                if idx % 2 == 0 and operation.dest_path.exists():
                    operation.dest_path.unlink()
                    deleted_count += 1
            
            # Perform undo
            results = undo_manager.undo(log_path)
            
            # Verify that undo processed all operations
            total_processed = results.successful + len(results.errors)
            assert total_processed == num_files, \
                f"Should process all {num_files} operations, processed {total_processed}"
            
            # Verify some operations succeeded and some failed
            assert results.successful > 0, \
                "Some operations should succeed"
            assert len(results.errors) > 0, \
                "Some operations should fail"
            
            # Verify the successful + errors equals total
            assert results.successful + len(results.errors) == num_files, \
                "Successful + errors should equal total operations"
