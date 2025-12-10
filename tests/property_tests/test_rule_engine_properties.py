"""Property-based tests for Rule Engine component."""

import tempfile
import json
import yaml
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import pytest

from src.rule_engine import RuleEngine, InvalidRuleError, RuleEngineError
from src.models import Rule, OperationType


# Custom strategies for generating test data
@st.composite
def valid_rule_dict(draw):
    """Generate a valid rule dictionary."""
    name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_ '),
        min_size=1,
        max_size=20
    ))
    
    # Generate pattern (either glob or regex)
    use_regex = draw(st.booleans())
    if use_regex:
        # Simple regex patterns
        pattern = draw(st.sampled_from([
            'regex:.*\\.txt$',
            'regex:^test.*',
            'regex:.*_backup.*',
            'regex:^[0-9]+.*'
        ]))
    else:
        # Glob patterns
        pattern = draw(st.sampled_from([
            '*.txt',
            '*.pdf',
            'test_*',
            '*_backup.*',
            '*.jpg'
        ]))
    
    destination = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_/'),
        min_size=1,
        max_size=30
    ))
    
    priority = draw(st.integers(min_value=0, max_value=100))
    
    return {
        'name': name,
        'pattern': pattern,
        'destination': destination,
        'priority': priority
    }


@st.composite
def valid_rules_list(draw, min_size=1, max_size=10):
    """Generate a list of valid rules."""
    num_rules = draw(st.integers(min_value=min_size, max_value=max_size))
    rules = []
    
    for i in range(num_rules):
        rule = draw(valid_rule_dict())
        rules.append(rule)
    
    return rules


class TestCustomRuleApplication:
    """
    Feature: file-organizer, Property 17: Custom rule application
    Validates: Requirements 5.1, 5.2
    """
    
    @given(
        num_txt_files=st.integers(min_value=1, max_value=10),
        num_pdf_files=st.integers(min_value=0, max_value=10),
        num_jpg_files=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_custom_rule_application(self, num_txt_files, num_pdf_files, num_jpg_files):
        """
        For any valid configuration file with custom rules, the system should 
        parse all rules and apply them to matching files, moving files to their 
        specified destinations.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create a configuration file with rules
            config_data = {
                'rules': [
                    {
                        'name': 'Text files',
                        'pattern': '*.txt',
                        'destination': 'text_files',
                        'priority': 1
                    },
                    {
                        'name': 'PDF documents',
                        'pattern': '*.pdf',
                        'destination': 'pdf_docs',
                        'priority': 2
                    },
                    {
                        'name': 'Images',
                        'pattern': '*.jpg',
                        'destination': 'images',
                        'priority': 3
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Verify rules were loaded
            assert len(rules) == 3, f"Should have loaded 3 rules, got {len(rules)}"
            
            # Create test files
            files = []
            expected_destinations = {}
            
            # Text files
            for i in range(num_txt_files):
                filename = f"file_{i}.txt"
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                files.append(file_path)
                expected_destinations[filename] = 'text_files'
            
            # PDF files
            for i in range(num_pdf_files):
                filename = f"doc_{i}.pdf"
                file_path = tmpdir_path / filename
                file_path.write_bytes(b"fake pdf")
                files.append(file_path)
                expected_destinations[filename] = 'pdf_docs'
            
            # JPG files
            for i in range(num_jpg_files):
                filename = f"image_{i}.jpg"
                file_path = tmpdir_path / filename
                file_path.write_bytes(b"fake image")
                files.append(file_path)
                expected_destinations[filename] = 'images'
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify we have the right number of operations
            total_files = num_txt_files + num_pdf_files + num_jpg_files
            assert len(operations) == total_files, \
                f"Should have {total_files} operations, got {len(operations)}"
            
            # Verify each operation moves to the correct destination
            for operation in operations:
                filename = operation.source_path.name
                expected_dest = expected_destinations[filename]
                
                # Check that destination is correct
                assert operation.dest_path.parent.name == expected_dest, \
                    f"File {filename} should be moved to '{expected_dest}', got '{operation.dest_path.parent.name}'"
                
                # Verify filename is preserved
                assert operation.dest_path.name == filename, \
                    f"Filename should be preserved: {filename}"
                
                # Verify operation type
                assert operation.operation_type == OperationType.CUSTOM, \
                    "Operation type should be CUSTOM"
    
    @given(
        num_files=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100)
    def test_regex_pattern_matching(self, num_files):
        """
        Test that regex patterns work correctly for matching files.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create a configuration with regex patterns
            config_data = {
                'rules': [
                    {
                        'name': 'Test files',
                        'pattern': 'regex:^test_.*',
                        'destination': 'test_files',
                        'priority': 1
                    },
                    {
                        'name': 'Backup files',
                        'pattern': 'regex:.*_backup\\..*',
                        'destination': 'backups',
                        'priority': 2
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Create test files
            files = []
            expected_destinations = {}
            
            # Half should be test files, half should be backup files
            for i in range(num_files):
                if i % 2 == 0:
                    filename = f"test_{i}.txt"
                    expected_dest = 'test_files'
                else:
                    filename = f"file_{i}_backup.txt"
                    expected_dest = 'backups'
                
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                files.append(file_path)
                expected_destinations[filename] = expected_dest
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify all files matched
            assert len(operations) == num_files, \
                f"All {num_files} files should match a rule"
            
            # Verify correct destinations
            for operation in operations:
                filename = operation.source_path.name
                expected_dest = expected_destinations[filename]
                
                assert operation.dest_path.parent.name == expected_dest, \
                    f"File {filename} should be in '{expected_dest}', got '{operation.dest_path.parent.name}'"
    
    @given(
        format_type=st.sampled_from(['yaml', 'json'])
    )
    @settings(max_examples=100)
    def test_both_yaml_and_json_formats(self, format_type):
        """
        Test that both YAML and JSON configuration formats work correctly.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration data
            config_data = {
                'rules': [
                    {
                        'name': 'Documents',
                        'pattern': '*.txt',
                        'destination': 'docs',
                        'priority': 1
                    }
                ]
            }
            
            # Save in the specified format
            if format_type == 'yaml':
                config_path = tmpdir_path / "rules.yaml"
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f)
            else:  # json
                config_path = tmpdir_path / "rules.json"
                with open(config_path, 'w') as f:
                    json.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Verify rules were loaded
            assert len(rules) == 1, "Should have loaded 1 rule"
            assert rules[0].name == 'Documents'
            assert rules[0].pattern == '*.txt'
            assert rules[0].destination == 'docs'
            
            # Create a test file
            file_path = tmpdir_path / "test.txt"
            file_path.write_text("content")
            
            # Apply rules
            operations = rule_engine.apply_rules([file_path], rules, target_dir)
            
            # Verify operation was created
            assert len(operations) == 1
            assert operations[0].dest_path.parent.name == 'docs'
    
    @given(
        num_matching=st.integers(min_value=1, max_value=10),
        num_non_matching=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_only_matching_files_get_operations(self, num_matching, num_non_matching):
        """
        Test that only files matching rules get operations created.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration with specific pattern
            config_data = {
                'rules': [
                    {
                        'name': 'Text files only',
                        'pattern': '*.txt',
                        'destination': 'text',
                        'priority': 1
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Create matching files
            files = []
            for i in range(num_matching):
                file_path = tmpdir_path / f"match_{i}.txt"
                file_path.write_text(f"content {i}")
                files.append(file_path)
            
            # Create non-matching files
            for i in range(num_non_matching):
                file_path = tmpdir_path / f"nomatch_{i}.pdf"
                file_path.write_bytes(b"pdf content")
                files.append(file_path)
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify only matching files got operations
            assert len(operations) == num_matching, \
                f"Only {num_matching} files should match, got {len(operations)} operations"
            
            # Verify all operations are for .txt files
            for operation in operations:
                assert operation.source_path.suffix == '.txt', \
                    "Only .txt files should have operations"



class TestRulePriorityOrdering:
    """
    Feature: file-organizer, Property 18: Rule priority ordering
    Validates: Requirements 5.3
    """
    
    @given(
        num_files=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100)
    def test_rule_priority_ordering(self, num_files):
        """
        For any file that matches multiple custom rules, only the first matching 
        rule (by priority order) should be applied to that file.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration with overlapping rules
            # All rules match .txt files, but with different priorities
            config_data = {
                'rules': [
                    {
                        'name': 'High priority rule',
                        'pattern': '*.txt',
                        'destination': 'high_priority',
                        'priority': 1  # Lowest number = highest priority
                    },
                    {
                        'name': 'Medium priority rule',
                        'pattern': '*.txt',
                        'destination': 'medium_priority',
                        'priority': 5
                    },
                    {
                        'name': 'Low priority rule',
                        'pattern': '*.txt',
                        'destination': 'low_priority',
                        'priority': 10
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Create test files (all .txt, so all match all rules)
            files = []
            for i in range(num_files):
                file_path = tmpdir_path / f"file_{i}.txt"
                file_path.write_text(f"content {i}")
                files.append(file_path)
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify we have exactly one operation per file
            assert len(operations) == num_files, \
                f"Should have {num_files} operations (one per file), got {len(operations)}"
            
            # Verify all operations use the highest priority rule (priority 1)
            for operation in operations:
                assert operation.dest_path.parent.name == 'high_priority', \
                    f"File {operation.source_path.name} should match highest priority rule (high_priority), got '{operation.dest_path.parent.name}'"
    
    @given(
        num_files=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_first_match_wins(self, num_files):
        """
        Test that once a file matches a rule, it doesn't match subsequent rules.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration with specific and general rules
            config_data = {
                'rules': [
                    {
                        'name': 'Specific test files',
                        'pattern': 'test_*.txt',
                        'destination': 'test_files',
                        'priority': 1
                    },
                    {
                        'name': 'All text files',
                        'pattern': '*.txt',
                        'destination': 'all_text',
                        'priority': 2
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Create test files - half match first rule, all match second rule
            files = []
            expected_destinations = {}
            
            for i in range(num_files):
                if i % 2 == 0:
                    filename = f"test_{i}.txt"
                    expected_dest = 'test_files'  # Matches first rule
                else:
                    filename = f"file_{i}.txt"
                    expected_dest = 'all_text'  # Only matches second rule
                
                file_path = tmpdir_path / filename
                file_path.write_text(f"content {i}")
                files.append(file_path)
                expected_destinations[filename] = expected_dest
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify correct number of operations
            assert len(operations) == num_files, \
                f"Should have {num_files} operations"
            
            # Verify each file went to the correct destination
            for operation in operations:
                filename = operation.source_path.name
                expected_dest = expected_destinations[filename]
                actual_dest = operation.dest_path.parent.name
                
                assert actual_dest == expected_dest, \
                    f"File {filename} should be in '{expected_dest}', got '{actual_dest}'"
    
    @given(
        priorities=st.lists(
            st.integers(min_value=1, max_value=100),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_priority_sorting(self, priorities):
        """
        Test that rules are applied in priority order regardless of definition order.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create rules with random priorities
            # All rules match the same pattern
            rules_data = []
            for idx, priority in enumerate(priorities):
                rules_data.append({
                    'name': f'Rule {idx}',
                    'pattern': '*.txt',
                    'destination': f'dest_{priority}',
                    'priority': priority
                })
            
            config_data = {'rules': rules_data}
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Create a test file
            file_path = tmpdir_path / "test.txt"
            file_path.write_text("content")
            
            # Apply rules
            operations = rule_engine.apply_rules([file_path], rules, target_dir)
            
            # Verify only one operation was created
            assert len(operations) == 1, "Should have exactly one operation"
            
            # Verify it matches the rule with the lowest priority number (highest priority)
            min_priority = min(priorities)
            expected_dest = f'dest_{min_priority}'
            actual_dest = operations[0].dest_path.parent.name
            
            assert actual_dest == expected_dest, \
                f"File should match rule with priority {min_priority}, got destination '{actual_dest}'"
    
    @given(
        num_txt_files=st.integers(min_value=1, max_value=8),
        num_pdf_files=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=100)
    def test_different_files_different_rules(self, num_txt_files, num_pdf_files):
        """
        Test that different file types can match different rules based on priority.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration with non-overlapping rules
            config_data = {
                'rules': [
                    {
                        'name': 'Text files',
                        'pattern': '*.txt',
                        'destination': 'text',
                        'priority': 1
                    },
                    {
                        'name': 'PDF files',
                        'pattern': '*.pdf',
                        'destination': 'pdfs',
                        'priority': 2
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Create files
            files = []
            
            for i in range(num_txt_files):
                file_path = tmpdir_path / f"file_{i}.txt"
                file_path.write_text(f"content {i}")
                files.append(file_path)
            
            for i in range(num_pdf_files):
                file_path = tmpdir_path / f"doc_{i}.pdf"
                file_path.write_bytes(b"pdf content")
                files.append(file_path)
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify correct number of operations
            total_files = num_txt_files + num_pdf_files
            assert len(operations) == total_files, \
                f"Should have {total_files} operations"
            
            # Count operations by destination
            text_count = sum(1 for op in operations if op.dest_path.parent.name == 'text')
            pdf_count = sum(1 for op in operations if op.dest_path.parent.name == 'pdfs')
            
            assert text_count == num_txt_files, \
                f"Should have {num_txt_files} text operations, got {text_count}"
            assert pdf_count == num_pdf_files, \
                f"Should have {num_pdf_files} PDF operations, got {pdf_count}"



class TestInvalidRuleErrorHandling:
    """
    Feature: file-organizer, Property 19: Invalid rule error handling
    Validates: Requirements 5.4
    """
    
    @given(
        num_valid=st.integers(min_value=1, max_value=5),
        num_invalid=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100)
    def test_invalid_rule_error_handling(self, num_valid, num_invalid):
        """
        For any configuration containing both valid and invalid rules, the system 
        should report errors for invalid rules and continue processing all valid rules.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration with mix of valid and invalid rules
            rules_data = []
            
            # Add valid rules
            for i in range(num_valid):
                rules_data.append({
                    'name': f'Valid rule {i}',
                    'pattern': f'*.txt',
                    'destination': f'valid_{i}',
                    'priority': i
                })
            
            # Add invalid rules (missing required fields)
            invalid_rules = [
                {'name': 'Missing pattern', 'destination': 'dest'},  # Missing pattern
                {'pattern': '*.txt', 'destination': 'dest'},  # Missing name
                {'name': 'Missing dest', 'pattern': '*.txt'},  # Missing destination
                {'name': 'Empty name', 'pattern': '*.txt', 'destination': 'dest', 'name': ''},  # Empty name
                {'name': 'Invalid priority', 'pattern': '*.txt', 'destination': 'dest', 'priority': 'high'},  # Invalid priority type
            ]
            
            # Add some invalid rules
            for i in range(min(num_invalid, len(invalid_rules))):
                rules_data.append(invalid_rules[i])
            
            config_data = {'rules': rules_data}
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules - should not raise exception, but should print warnings
            rules = rule_engine.load_rules(config_path)
            
            # Verify only valid rules were loaded
            assert len(rules) == num_valid, \
                f"Should have loaded {num_valid} valid rules, got {len(rules)}"
            
            # Verify all loaded rules are valid
            for rule in rules:
                assert rule.name.startswith('Valid rule'), \
                    f"Loaded rule should be valid, got: {rule.name}"
                assert rule.pattern == '*.txt'
                assert rule.destination.startswith('valid_')
            
            # Create test files
            files = []
            for i in range(3):
                file_path = tmpdir_path / f"file_{i}.txt"
                file_path.write_text(f"content {i}")
                files.append(file_path)
            
            # Apply rules - should work with valid rules only
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # Verify operations were created (using valid rules)
            assert len(operations) == 3, \
                "Should have created operations for all files using valid rules"
    
    @given(
        num_files=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_invalid_regex_patterns_skipped(self, num_files):
        """
        Test that rules with invalid regex patterns are skipped during matching.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target_dir = tmpdir_path / "organized"
            
            # Create configuration with invalid regex pattern
            config_data = {
                'rules': [
                    {
                        'name': 'Invalid regex',
                        'pattern': 'regex:[invalid(regex',  # Invalid regex
                        'destination': 'invalid',
                        'priority': 1
                    },
                    {
                        'name': 'Valid rule',
                        'pattern': '*.txt',
                        'destination': 'valid',
                        'priority': 2
                    }
                ]
            }
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules - invalid regex should cause error during parsing
            # The invalid regex rule should be skipped
            rules = rule_engine.load_rules(config_path)
            
            # Should have loaded only the valid rule
            assert len(rules) == 1, \
                f"Should have loaded 1 valid rule (invalid regex skipped), got {len(rules)}"
            
            # Create test files
            files = []
            for i in range(num_files):
                file_path = tmpdir_path / f"file_{i}.txt"
                file_path.write_text(f"content {i}")
                files.append(file_path)
            
            # Apply rules
            operations = rule_engine.apply_rules(files, rules, target_dir)
            
            # All files should match the valid rule
            assert len(operations) == num_files, \
                f"All {num_files} files should match the valid rule"
            
            # All should go to 'valid' destination
            for operation in operations:
                assert operation.dest_path.parent.name == 'valid', \
                    "Files should match the valid rule, not the invalid regex rule"
    
    @given(
        format_type=st.sampled_from(['yaml', 'json'])
    )
    @settings(max_examples=100)
    def test_malformed_config_raises_error(self, format_type):
        """
        Test that malformed configuration files raise appropriate errors.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create malformed configuration (not a dict with 'rules' key)
            if format_type == 'yaml':
                config_path = tmpdir_path / "rules.yaml"
                with open(config_path, 'w') as f:
                    f.write("just a string, not valid structure")
            else:  # json
                config_path = tmpdir_path / "rules.json"
                with open(config_path, 'w') as f:
                    f.write('["not", "a", "dict"]')
            
            # Loading should raise InvalidRuleError
            with pytest.raises(InvalidRuleError):
                rule_engine.load_rules(config_path)
    
    def test_missing_config_file_raises_error(self):
        """
        Test that missing configuration files raise appropriate errors.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "nonexistent.yaml"
            
            # Loading should raise RuleEngineError
            with pytest.raises(RuleEngineError):
                rule_engine.load_rules(config_path)
    
    def test_unsupported_format_raises_error(self):
        """
        Test that unsupported configuration formats raise appropriate errors.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "rules.txt"
            
            # Create a text file
            with open(config_path, 'w') as f:
                f.write("some text")
            
            # Loading should raise RuleEngineError
            with pytest.raises(RuleEngineError):
                rule_engine.load_rules(config_path)
    
    @given(
        num_valid=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100)
    def test_all_valid_rules_loaded_successfully(self, num_valid):
        """
        Test that when all rules are valid, all are loaded successfully.
        """
        rule_engine = RuleEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create configuration with all valid rules
            rules_data = []
            for i in range(num_valid):
                rules_data.append({
                    'name': f'Rule {i}',
                    'pattern': f'*.{i}',
                    'destination': f'dest_{i}',
                    'priority': i
                })
            
            config_data = {'rules': rules_data}
            
            config_path = tmpdir_path / "rules.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load rules
            rules = rule_engine.load_rules(config_path)
            
            # Verify all rules were loaded
            assert len(rules) == num_valid, \
                f"Should have loaded all {num_valid} valid rules"
            
            # Verify each rule has correct properties
            for i, rule in enumerate(rules):
                # Rules might not be in the same order, so check by name
                if rule.name == f'Rule {i}':
                    assert rule.pattern == f'*.{i}'
                    assert rule.destination == f'dest_{i}'
                    assert rule.priority == i
