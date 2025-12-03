"""Property-based tests for Renamer component."""

import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import pytest

from src.renamer import Renamer, DuplicateNameError
from src.models import CaseType, OperationType


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
def pattern_and_replacement(draw):
    """Generate pattern and replacement strings for renaming."""
    # Simple patterns that are likely to match
    patterns = ['test', 'file', 'doc', 'img', '_', '-', '01', '02']
    pattern = draw(st.sampled_from(patterns))
    
    # Replacement can be any reasonable string
    replacement = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
        min_size=0,
        max_size=10
    ))
    
    return pattern, replacement


class TestPatternReplacement:
    """
    Feature: file-organizer, Property 5: Pattern replacement in filenames
    Validates: Requirements 2.1
    """
    
    @given(
        base_names=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
                min_size=1,
                max_size=15
            ),
            min_size=1,
            max_size=10,
            unique=True
        ),
        pattern=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
            min_size=1,
            max_size=5
        ),
        replacement=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
            min_size=0,
            max_size=10
        ),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg', '.png', '.doc'])
    )
    @settings(max_examples=100)
    def test_pattern_replacement_preserves_extensions(
        self, base_names, pattern, replacement, extension
    ):
        """
        For any set of filenames and a find-and-replace pattern, applying the 
        transformation should replace all occurrences of the pattern in matching 
        filenames while preserving file extensions.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files with the pattern embedded in their names
            file_paths = []
            for base_name in base_names:
                # Ensure pattern appears in filename by embedding it
                filename_with_pattern = f"{base_name}_{pattern}_suffix"
                full_name = filename_with_pattern + extension
                file_path = tmpdir_path / full_name
                file_path.write_text("content")
                file_paths.append(file_path)
            
            # Apply pattern replacement
            try:
                operations = renamer.rename_pattern(file_paths, pattern, replacement)
            except DuplicateNameError:
                # If duplicates would be created, that's valid behavior
                # The property is that it should detect and prevent this
                return
            
            # Verify all operations preserve extensions and replace pattern
            for operation in operations:
                source_ext = operation.source_path.suffix
                dest_ext = operation.dest_path.suffix
                
                # Property: Extension should be preserved
                assert source_ext == dest_ext, \
                    f"Extension should be preserved: {source_ext} -> {dest_ext}"
                
                # Property: Pattern should be replaced in stem
                source_stem = operation.source_path.stem
                dest_stem = operation.dest_path.stem
                
                # Since we embedded the pattern, it must be in the source
                assert pattern in source_stem, \
                    f"Pattern '{pattern}' should be in source stem '{source_stem}'"
                
                # Verify pattern was replaced with replacement
                expected_stem = source_stem.replace(pattern, replacement)
                assert dest_stem == expected_stem, \
                    f"Pattern should be replaced: {source_stem} -> {dest_stem}, expected {expected_stem}"
    
    @given(
        num_files=st.integers(min_value=1, max_value=15),
        pattern=st.sampled_from(['test', 'file', 'doc', 'img', 'old']),
        replacement=st.sampled_from(['new', 'updated', 'final', '', 'v2']),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg', '.png'])
    )
    @settings(max_examples=100)
    def test_pattern_replacement_replaces_all_occurrences(
        self, num_files, pattern, replacement, extension
    ):
        """
        Test that pattern replacement replaces ALL occurrences of the pattern
        in the filename stem, not just the first one.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files with multiple occurrences of the pattern
            file_paths = []
            for i in range(num_files):
                # Create filename with pattern appearing multiple times
                filename = f"{pattern}_{i}_{pattern}{extension}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                file_paths.append(file_path)
            
            # Apply pattern replacement
            try:
                operations = renamer.rename_pattern(file_paths, pattern, replacement)
            except DuplicateNameError:
                # Valid behavior - duplicates detected
                return
            
            # Verify all occurrences were replaced
            for operation in operations:
                source_stem = operation.source_path.stem
                dest_stem = operation.dest_path.stem
                
                # Count occurrences in source
                source_count = source_stem.count(pattern)
                
                # After replacement, pattern should not appear in destination
                # (unless replacement contains the pattern)
                if pattern not in replacement:
                    dest_count = dest_stem.count(pattern)
                    assert dest_count == 0, \
                        f"Pattern '{pattern}' should be completely replaced in '{dest_stem}'"
                
                # Verify replacement appears the correct number of times
                if replacement:
                    replacement_count = dest_stem.count(replacement)
                    assert replacement_count >= source_count, \
                        f"Replacement '{replacement}' should appear at least {source_count} times in '{dest_stem}'"



class TestSequentialNumbering:
    """
    Feature: file-organizer, Property 6: Sequential numbering preserves extensions
    Validates: Requirements 2.2
    """
    
    @given(
        filenames=st.lists(file_names(), min_size=1, max_size=20, unique=True),
        template=st.sampled_from(['file_{n}', 'doc_{n}', 'image_{n}', '{n}', 'photo_{n}'])
    )
    @settings(max_examples=100)
    def test_sequential_numbering_preserves_extensions(self, filenames, template):
        """
        For any set of files renamed with sequential numbering, each file should 
        receive a unique sequential number and retain its original file extension.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files
            file_paths = []
            original_extensions = []
            for filename in filenames:
                file_path = tmpdir_path / filename
                file_path.write_text("content")
                file_paths.append(file_path)
                original_extensions.append(file_path.suffix)
            
            # Apply sequential numbering
            operations = renamer.rename_sequential(file_paths, template)
            
            # Verify we have the right number of operations
            assert len(operations) == len(file_paths), \
                f"Should have {len(file_paths)} operations, got {len(operations)}"
            
            # Track seen numbers and extensions
            seen_numbers = set()
            
            for idx, operation in enumerate(operations):
                # Verify extension is preserved
                source_ext = operation.source_path.suffix
                dest_ext = operation.dest_path.suffix
                
                assert source_ext == dest_ext, \
                    f"Extension should be preserved: {source_ext} -> {dest_ext}"
                
                # Verify sequential number is present and unique
                dest_stem = operation.dest_path.stem
                
                # Extract the number from the destination name
                expected_number = str(idx + 1)
                assert expected_number in dest_stem, \
                    f"Sequential number {expected_number} should be in {dest_stem}"
                
                # Verify the number is unique
                assert expected_number not in seen_numbers, \
                    f"Number {expected_number} should be unique"
                seen_numbers.add(expected_number)
    
    @given(
        num_files=st.integers(min_value=1, max_value=50),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg', '.png', '.doc'])
    )
    @settings(max_examples=100)
    def test_sequential_numbering_produces_unique_numbers(self, num_files, extension):
        """
        Test that sequential numbering produces unique sequential numbers for all files.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files with arbitrary names
            file_paths = []
            for i in range(num_files):
                file_path = tmpdir_path / f"random_{i}{extension}"
                file_path.write_text("content")
                file_paths.append(file_path)
            
            # Apply sequential numbering
            operations = renamer.rename_sequential(file_paths, "file_{n}")
            
            # Extract all numbers from destination filenames
            numbers = []
            for operation in operations:
                dest_stem = operation.dest_path.stem
                # Extract number from "file_N" format
                number_str = dest_stem.replace("file_", "")
                numbers.append(int(number_str))
            
            # Verify numbers are sequential starting from 1
            expected_numbers = list(range(1, num_files + 1))
            assert numbers == expected_numbers, \
                f"Numbers should be sequential from 1 to {num_files}, got {numbers}"



class TestPrefixSuffixAddition:
    """
    Feature: file-organizer, Property 7: Prefix and suffix addition
    Validates: Requirements 2.3
    """
    
    @given(
        filenames=st.lists(file_names(), min_size=1, max_size=15, unique=True),
        prefix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
            min_size=0,
            max_size=10
        ),
        suffix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_prefix_suffix_addition_preserves_extensions(self, filenames, prefix, suffix):
        """
        For any set of filenames and a prefix or suffix string, adding the 
        prefix/suffix should result in all filenames containing the added text 
        in the correct position while preserving extensions.
        """
        # Skip if both prefix and suffix are empty (no change)
        assume(prefix or suffix)
        
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files
            file_paths = []
            for filename in filenames:
                file_path = tmpdir_path / filename
                file_path.write_text("content")
                file_paths.append(file_path)
            
            # Apply prefix/suffix addition
            operations = renamer.add_prefix_suffix(file_paths, prefix, suffix)
            
            # Verify all operations preserve extensions and add prefix/suffix correctly
            for operation in operations:
                source_ext = operation.source_path.suffix
                dest_ext = operation.dest_path.suffix
                
                # Extension should be preserved
                assert source_ext == dest_ext, \
                    f"Extension should be preserved: {source_ext} -> {dest_ext}"
                
                source_stem = operation.source_path.stem
                dest_stem = operation.dest_path.stem
                
                # Verify prefix is at the beginning
                if prefix:
                    assert dest_stem.startswith(prefix), \
                        f"Destination stem should start with prefix '{prefix}': {dest_stem}"
                
                # Verify suffix is at the end (before extension)
                if suffix:
                    assert dest_stem.endswith(suffix), \
                        f"Destination stem should end with suffix '{suffix}': {dest_stem}"
                
                # Verify the original stem is in the middle
                expected_stem = prefix + source_stem + suffix
                assert dest_stem == expected_stem, \
                    f"Expected stem '{expected_stem}', got '{dest_stem}'"
    
    @given(
        num_files=st.integers(min_value=1, max_value=20),
        prefix=st.sampled_from(['new_', 'backup_', 'old_', 'test_', '']),
        suffix=st.sampled_from(['_copy', '_backup', '_v2', '_final', '']),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg'])
    )
    @settings(max_examples=100)
    def test_prefix_suffix_in_correct_positions(self, num_files, prefix, suffix, extension):
        """
        Test that prefix appears at the start and suffix at the end of the stem.
        """
        # Skip if both are empty
        assume(prefix or suffix)
        
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files with simple names
            file_paths = []
            for i in range(num_files):
                file_path = tmpdir_path / f"file{i}{extension}"
                file_path.write_text("content")
                file_paths.append(file_path)
            
            # Apply prefix/suffix
            operations = renamer.add_prefix_suffix(file_paths, prefix, suffix)
            
            for idx, operation in enumerate(operations):
                dest_stem = operation.dest_path.stem
                original_stem = f"file{idx}"
                
                # Check structure: prefix + original + suffix
                expected = prefix + original_stem + suffix
                assert dest_stem == expected, \
                    f"Expected '{expected}', got '{dest_stem}'"



class TestCaseTransformation:
    """
    Feature: file-organizer, Property 8: Case transformation correctness
    Validates: Requirements 2.4
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
        extension=st.sampled_from(['.txt', '.pdf', '.jpg', '.png', '.doc']),
        case_type=st.sampled_from([CaseType.LOWERCASE, CaseType.UPPERCASE, CaseType.TITLE])
    )
    @settings(max_examples=100)
    def test_case_transformation_preserves_extensions(self, filenames, extension, case_type):
        """
        For any filename and case transformation type (lowercase, uppercase, title case), 
        applying the transformation should convert all characters to the specified case 
        while preserving file extensions.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files
            file_paths = []
            for filename in filenames:
                full_name = filename + extension
                file_path = tmpdir_path / full_name
                file_path.write_text("content")
                file_paths.append(file_path)
            
            # Apply case transformation
            operations = renamer.rename_case(file_paths, case_type)
            
            # Verify all operations preserve extensions and apply correct case
            for operation in operations:
                source_ext = operation.source_path.suffix
                dest_ext = operation.dest_path.suffix
                
                # Extension should be preserved
                assert source_ext == dest_ext, \
                    f"Extension should be preserved: {source_ext} -> {dest_ext}"
                
                source_stem = operation.source_path.stem
                dest_stem = operation.dest_path.stem
                
                # Verify correct case transformation
                if case_type == CaseType.LOWERCASE:
                    expected_stem = source_stem.lower()
                    assert dest_stem == expected_stem, \
                        f"Expected lowercase '{expected_stem}', got '{dest_stem}'"
                
                elif case_type == CaseType.UPPERCASE:
                    expected_stem = source_stem.upper()
                    assert dest_stem == expected_stem, \
                        f"Expected uppercase '{expected_stem}', got '{dest_stem}'"
                
                elif case_type == CaseType.TITLE:
                    expected_stem = source_stem.title()
                    assert dest_stem == expected_stem, \
                        f"Expected title case '{expected_stem}', got '{dest_stem}'"
    
    @given(
        base_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122),
            min_size=1,
            max_size=15
        ),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg'])
    )
    @settings(max_examples=100)
    def test_case_transformation_types(self, base_name, extension):
        """
        Test that each case type produces the expected transformation.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a file
            file_path = tmpdir_path / (base_name + extension)
            file_path.write_text("content")
            
            # Test lowercase
            ops_lower = renamer.rename_case([file_path], CaseType.LOWERCASE)
            if ops_lower:  # Only if name changed
                assert ops_lower[0].dest_path.stem == base_name.lower()
            
            # Test uppercase
            ops_upper = renamer.rename_case([file_path], CaseType.UPPERCASE)
            if ops_upper:  # Only if name changed
                assert ops_upper[0].dest_path.stem == base_name.upper()
            
            # Test title case
            ops_title = renamer.rename_case([file_path], CaseType.TITLE)
            if ops_title:  # Only if name changed
                assert ops_title[0].dest_path.stem == base_name.title()



class TestDuplicateDetection:
    """
    Feature: file-organizer, Property 9: Duplicate detection prevents conflicts
    Validates: Requirements 2.5
    """
    
    @given(
        base_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
            min_size=1,
            max_size=15
        ),
        num_duplicates=st.integers(min_value=2, max_value=10),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg']),
        pattern=st.sampled_from(['test', 'file', 'doc', '01', '02']),
        replacement=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_duplicate_detection_prevents_conflicts(
        self, base_name, num_duplicates, extension, pattern, replacement
    ):
        """
        For any rename operation that would create duplicate filenames, the system 
        should detect the conflict before execution and prevent the operation while 
        reporting all conflicts.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files that will result in duplicates after pattern replacement
            file_paths = []
            for i in range(num_duplicates):
                # Create filenames that contain the pattern
                filename = f"{base_name}_{pattern}_{i}{extension}"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                file_paths.append(file_path)
            
            # Try to apply pattern replacement that would create duplicates
            try:
                operations = renamer.rename_pattern(file_paths, pattern, replacement)
                
                # If no exception was raised, verify no duplicates in results
                dest_names = [op.dest_path.name for op in operations]
                unique_names = set(dest_names)
                
                # All destination names should be unique
                assert len(dest_names) == len(unique_names), \
                    f"Duplicate names detected in operations: {dest_names}"
                
            except DuplicateNameError as e:
                # This is expected behavior - duplicates were detected
                assert "duplicate" in str(e).lower(), \
                    f"Error message should mention duplicates: {e}"
    
    @given(
        filenames=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
                min_size=1,
                max_size=10
            ),
            min_size=2,
            max_size=8,
            unique=True
        ),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg'])
    )
    @settings(max_examples=100)
    def test_duplicate_detection_with_existing_files(self, filenames, extension):
        """
        Test that duplicate detection works when destination files already exist.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create source files
            file_paths = []
            for filename in filenames:
                file_path = tmpdir_path / (filename + extension)
                file_path.write_text("source content")
                file_paths.append(file_path)
            
            # Create a destination file that would conflict
            if filenames:
                conflict_name = "renamed" + extension
                conflict_path = tmpdir_path / conflict_name
                conflict_path.write_text("existing content")
                
                # Try to rename all files to the same name (should detect conflict)
                try:
                    # Replace all filenames with empty string to force same destination
                    operations = renamer.rename_pattern(
                        file_paths, 
                        filenames[0], 
                        "renamed"
                    )
                    
                    # If successful, verify no conflicts
                    dest_paths = [op.dest_path for op in operations]
                    
                    # Check that we don't overwrite the existing file
                    for dest_path in dest_paths:
                        if dest_path == conflict_path:
                            # Should not happen - would be a conflict
                            assert False, f"Operation would overwrite existing file: {conflict_path}"
                    
                except DuplicateNameError:
                    # Expected - duplicates were detected
                    pass
    
    @given(
        num_files=st.integers(min_value=3, max_value=10),
        extension=st.sampled_from(['.txt', '.pdf', '.jpg'])
    )
    @settings(max_examples=100)
    def test_no_false_positive_duplicate_detection(self, num_files, extension):
        """
        Test that duplicate detection doesn't raise false positives for unique renames.
        """
        renamer = Renamer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create files with unique names
            file_paths = []
            for i in range(num_files):
                file_path = tmpdir_path / f"file_{i}{extension}"
                file_path.write_text(f"content {i}")
                file_paths.append(file_path)
            
            # Apply a pattern that keeps names unique
            operations = renamer.rename_pattern(file_paths, "file", "document")
            
            # Should not raise DuplicateNameError
            # Verify all destination names are unique
            dest_names = [op.dest_path.name for op in operations]
            assert len(dest_names) == len(set(dest_names)), \
                f"All destination names should be unique: {dest_names}"
