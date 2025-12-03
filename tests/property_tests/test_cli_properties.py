"""Property-based tests for CLI functionality."""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from hypothesis import given, strategies as st, settings

from src.cli import cli
from src.models import OperationResults, Operation, OperationType
from datetime import datetime


# Custom strategies for generating test data
@st.composite
def file_names(draw):
    """Generate realistic filenames."""
    base = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
        min_size=1,
        max_size=20
    ))
    extensions = ['.txt', '.pdf', '.jpg', '.png', '.doc', '.mp3', '.mp4']
    ext = draw(st.sampled_from(extensions))
    return base + ext


@st.composite
def operation_lists(draw):
    """Generate lists of operations for testing."""
    num_operations = draw(st.integers(min_value=1, max_value=20))
    operations = []
    
    for _ in range(num_operations):
        op_type = draw(st.sampled_from(list(OperationType)))
        source = Path(f"/tmp/source/{draw(file_names())}")
        dest = Path(f"/tmp/dest/{draw(file_names())}")
        
        operation = Operation(
            operation_type=op_type,
            source_path=source,
            dest_path=dest,
            timestamp=datetime.now(),
            executed=draw(st.booleans())
        )
        operations.append(operation)
    
    return operations


class TestVerboseOutputProperty:
    """Test verbose mode output properties."""
    
    @given(operations=operation_lists())
    @settings(max_examples=100)
    def test_verbose_output_contains_all_operation_details(self, operations):
        """
        **Feature: file-organizer, Property 24: Verbose mode output detail**
        
        For any operation executed in verbose mode, the output should include
        detailed information (source, destination, operation type, status) for
        each individual file operation.
        
        **Validates: Requirements 7.4**
        """
        # Create a mock results object
        results = OperationResults(
            successful=sum(1 for op in operations if op.executed),
            skipped=sum(1 for op in operations if not op.executed),
            errors=[],
            operations=operations
        )
        
        # Import display_results to test it directly
        from src.cli import display_results
        from io import StringIO
        import sys
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Call display_results with verbose=True
            display_results(results, verbose=True, dry_run=False)
            
            output = captured_output.getvalue()
            
            # Property: For each operation, verbose output must contain:
            # 1. Source path
            # 2. Destination path
            # 3. Operation type
            # 4. Status (SUCCESS, SKIPPED, etc.)
            
            for operation in operations:
                # Check that source path appears in output
                assert str(operation.source_path) in output, \
                    f"Source path {operation.source_path} not found in verbose output"
                
                # Check that destination path appears in output
                assert str(operation.dest_path) in output, \
                    f"Destination path {operation.dest_path} not found in verbose output"
                
                # Check that operation type appears in output
                assert operation.operation_type.value.upper() in output, \
                    f"Operation type {operation.operation_type.value} not found in verbose output"
                
                # Check that a status indicator appears
                # (SUCCESS, SKIPPED, or similar)
                status_keywords = ['SUCCESS', 'SKIPPED', 'ERROR', 'WOULD EXECUTE']
                assert any(keyword in output for keyword in status_keywords), \
                    "No status indicator found in verbose output"
        
        finally:
            sys.stdout = old_stdout
    
    @given(operations=operation_lists())
    @settings(max_examples=100)
    def test_verbose_output_shows_progress_for_large_operations(self, operations):
        """
        For any operation with more than 10 files, verbose mode should show
        progress indicators with current file and total count.
        
        **Validates: Requirements 7.1**
        """
        # Only test when we have more than 10 operations
        if len(operations) <= 10:
            return
        
        results = OperationResults(
            successful=len(operations),
            skipped=0,
            errors=[],
            operations=operations
        )
        
        from src.cli import display_results
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            display_results(results, verbose=True, dry_run=False)
            output = captured_output.getvalue()
            
            # Property: For operations with >10 files, output should contain
            # progress indicators like [1/N], [2/N], etc.
            total = len(operations)
            
            # Check for at least the first and last progress indicators
            assert f"[1/{total}]" in output, \
                f"Progress indicator [1/{total}] not found for large operation"
            
            assert f"[{total}/{total}]" in output, \
                f"Progress indicator [{total}/{total}] not found for large operation"
        
        finally:
            sys.stdout = old_stdout
    
    @given(operations=operation_lists())
    @settings(max_examples=100)
    def test_non_verbose_output_omits_details(self, operations):
        """
        For any operation executed in non-verbose mode, the output should
        show only the summary without per-file details.
        """
        results = OperationResults(
            successful=len(operations),
            skipped=0,
            errors=[],
            operations=operations
        )
        
        from src.cli import display_results
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Call display_results with verbose=False
            display_results(results, verbose=False, dry_run=False)
            output = captured_output.getvalue()
            
            # Property: Non-verbose output should NOT contain individual file paths
            # (unless they're in error messages)
            # It should only show the summary
            
            # Check that summary is present
            assert "OPERATION SUMMARY" in output or "SUMMARY" in output, \
                "Summary not found in non-verbose output"
            
            # Check that total operations count is present
            assert f"Total operations: {len(operations)}" in output, \
                "Total operations count not found in summary"
            
            # For non-verbose mode with no errors, individual file paths
            # should not appear in the detailed operations section
            if not results.errors:
                # The output should be much shorter than verbose mode
                # We can check that "Detailed Operations:" is NOT present
                assert "Detailed Operations:" not in output, \
                    "Detailed operations section should not appear in non-verbose mode"
        
        finally:
            sys.stdout = old_stdout
