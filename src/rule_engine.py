"""Rule Engine for custom file organization rules."""

import json
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from fnmatch import fnmatch

from src.models import Rule, Operation, OperationType
from datetime import datetime


class RuleEngineError(Exception):
    """Base exception for rule engine operations."""
    pass


class InvalidRuleError(RuleEngineError):
    """Raised when a rule has invalid syntax or configuration."""
    pass


class RuleEngine:
    """Handles parsing and application of custom organization rules."""
    
    def __init__(self):
        """Initialize the Rule Engine."""
        self.rules: List[Rule] = []
    
    def load_rules(self, config_path: Path) -> List[Rule]:
        """
        Load rules from a YAML or JSON configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            List of Rule objects loaded from the file
            
        Raises:
            RuleEngineError: If file cannot be read or parsed
            InvalidRuleError: If rules have invalid syntax
        """
        try:
            if not config_path.exists():
                raise RuleEngineError(f"Configuration file not found: {config_path}")
            
            # Read file content
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Parse based on file extension
            if config_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(content)
            elif config_path.suffix == '.json':
                data = json.loads(content)
            else:
                raise RuleEngineError(
                    f"Unsupported configuration format: {config_path.suffix}. "
                    "Use .yaml, .yml, or .json"
                )
            
            # Extract rules from data
            if not isinstance(data, dict) or 'rules' not in data:
                raise InvalidRuleError(
                    "Configuration must contain a 'rules' key with a list of rules"
                )
            
            rules_data = data['rules']
            if not isinstance(rules_data, list):
                raise InvalidRuleError("'rules' must be a list")
            
            # Parse each rule
            rules = []
            errors = []
            
            for idx, rule_data in enumerate(rules_data):
                try:
                    rule = self._parse_rule(rule_data, idx)
                    rules.append(rule)
                except InvalidRuleError as e:
                    errors.append(f"Rule {idx}: {str(e)}")
            
            # Report errors but continue with valid rules
            if errors:
                error_msg = "\n".join(errors)
                # Store errors but don't raise - continue with valid rules
                print(f"Warning: Invalid rules found:\n{error_msg}")
            
            self.rules = rules
            return rules
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise RuleEngineError(f"Failed to parse configuration file: {e}")
        except IOError as e:
            raise RuleEngineError(f"Failed to read configuration file: {e}")
    
    def _parse_rule(self, rule_data: Dict[str, Any], index: int) -> Rule:
        """
        Parse a single rule from configuration data.
        
        Args:
            rule_data: Dictionary containing rule configuration
            index: Index of the rule in the configuration (for error reporting)
            
        Returns:
            Rule object
            
        Raises:
            InvalidRuleError: If rule has invalid syntax
        """
        # Validate required fields
        if not isinstance(rule_data, dict):
            raise InvalidRuleError(f"Rule must be a dictionary, got {type(rule_data)}")
        
        required_fields = ['name', 'pattern', 'destination']
        for field in required_fields:
            if field not in rule_data:
                raise InvalidRuleError(f"Missing required field: {field}")
        
        name = rule_data['name']
        pattern = rule_data['pattern']
        destination = rule_data['destination']
        priority = rule_data.get('priority', index)
        
        # Validate field types
        if not isinstance(name, str) or not name.strip():
            raise InvalidRuleError("'name' must be a non-empty string")
        
        if not isinstance(pattern, str) or not pattern.strip():
            raise InvalidRuleError("'pattern' must be a non-empty string")
        
        if not isinstance(destination, str) or not destination.strip():
            raise InvalidRuleError("'destination' must be a non-empty string")
        
        if not isinstance(priority, int):
            raise InvalidRuleError("'priority' must be an integer")
        
        # Validate regex pattern if it starts with 'regex:'
        if pattern.startswith('regex:'):
            regex_pattern = pattern[6:]  # Remove 'regex:' prefix
            try:
                re.compile(regex_pattern)
            except re.error as e:
                raise InvalidRuleError(f"Invalid regex pattern: {e}")
        
        return Rule(
            name=name,
            pattern=pattern,
            destination=destination,
            priority=priority
        )
    
    def match_file(self, file: Path, rule: Rule) -> bool:
        """
        Check if a file matches a rule's pattern.
        
        Args:
            file: File path to check
            rule: Rule to match against
            
        Returns:
            True if file matches the rule pattern, False otherwise
        """
        filename = file.name
        
        # Check if pattern is regex (starts with 'regex:')
        if rule.pattern.startswith('regex:'):
            regex_pattern = rule.pattern[6:]  # Remove 'regex:' prefix
            try:
                return bool(re.match(regex_pattern, filename))
            except re.error:
                # Invalid regex, skip this rule
                return False
        else:
            # Use glob pattern matching
            return fnmatch(filename, rule.pattern)
    
    def apply_rules(
        self, 
        files: List[Path], 
        rules: List[Rule],
        target_dir: Path
    ) -> List[Operation]:
        """
        Apply custom rules to files, creating operations for matching files.
        
        Args:
            files: List of file paths to process
            rules: List of Rule objects to apply
            target_dir: Base target directory for relative destinations
            
        Returns:
            List of Operation objects for files that matched rules
        """
        operations = []
        
        # Sort rules by priority (lower priority number = higher priority)
        sorted_rules = sorted(rules, key=lambda r: r.priority)
        
        # Track which files have been matched (first match wins)
        matched_files = set()
        
        for file_path in files:
            # Skip if already matched
            if file_path in matched_files:
                continue
            
            # Try to match against rules in priority order
            for rule in sorted_rules:
                if self.match_file(file_path, rule):
                    # Create destination path
                    dest_dir = target_dir / rule.destination
                    dest_path = dest_dir / file_path.name
                    
                    # Create operation
                    operation = Operation(
                        operation_type=OperationType.CUSTOM,
                        source_path=file_path,
                        dest_path=dest_path,
                        timestamp=datetime.now(),
                        executed=False
                    )
                    operations.append(operation)
                    
                    # Mark as matched (first match wins)
                    matched_files.add(file_path)
                    break  # Stop checking rules for this file
        
        return operations
