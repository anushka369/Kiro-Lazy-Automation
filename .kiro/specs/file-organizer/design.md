# Design Document

## Overview

The File Organizer is a Python-based command-line tool that automates tedious file management tasks. It provides a flexible, rule-based system for bulk file operations including renaming, organizing by type or date, and custom categorization. The tool emphasizes safety through dry-run mode and undo capabilities, making it suitable for both cautious and power users.

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐
│   CLI Layer     │  (Argument parsing, user interaction)
└────────┬────────┘
         │
┌────────▼────────┐
│  Orchestrator   │  (Coordinates operations, manages workflow)
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼──┐ ┌─────▼─────┐ ┌──▼──────┐
│Renamer│ │Org- │ │  Rule     │ │  Undo   │
│       │ │anizer│ │  Engine   │ │ Manager │
└───────┘ └─────┘ └───────────┘ └─────────┘
                        │
                   ┌────▼────┐
                   │  File   │
                   │ System  │
                   └─────────┘
```

The architecture uses a pipeline pattern where operations flow through validation, planning, execution, and logging phases.

## Components and Interfaces

### CLI Layer
- **Responsibility**: Parse command-line arguments and present results to users
- **Interface**: 
  - `parse_arguments() -> Config`: Parses CLI args into configuration object
  - `display_results(results: OperationResults) -> None`: Formats and displays operation results
  - `display_progress(current: int, total: int) -> None`: Shows progress indicator

### Orchestrator
- **Responsibility**: Coordinate operations, manage dry-run mode, and handle undo logging
- **Interface**:
  - `execute(config: Config) -> OperationResults`: Main entry point for all operations
  - `plan_operations(config: Config) -> List[Operation]`: Generate operation plan
  - `execute_operations(operations: List[Operation], dry_run: bool) -> OperationResults`: Execute or simulate operations

### Renamer
- **Responsibility**: Handle all filename transformation logic
- **Interface**:
  - `rename_pattern(files: List[Path], pattern: str, replacement: str) -> List[Operation]`: Find-and-replace renaming
  - `rename_sequential(files: List[Path], template: str) -> List[Operation]`: Sequential numbering
  - `rename_case(files: List[Path], case_type: CaseType) -> List[Operation]`: Case transformation
  - `add_prefix_suffix(files: List[Path], prefix: str, suffix: str) -> List[Operation]`: Add text to filenames

### Organizer
- **Responsibility**: Categorize and move files based on rules
- **Interface**:
  - `organize_by_type(files: List[Path], target_dir: Path) -> List[Operation]`: Organize by file extension
  - `organize_by_date(files: List[Path], target_dir: Path, format: str) -> List[Operation]`: Organize by modification date
  - `organize_custom(files: List[Path], rules: List[Rule]) -> List[Operation]`: Apply custom rules

### Rule Engine
- **Responsibility**: Parse and evaluate custom organization rules
- **Interface**:
  - `load_rules(config_path: Path) -> List[Rule]`: Load rules from configuration file
  - `match_file(file: Path, rule: Rule) -> bool`: Check if file matches rule pattern
  - `apply_rules(files: List[Path], rules: List[Rule]) -> List[Operation]`: Apply rules to files

### Undo Manager
- **Responsibility**: Track operations and enable reversal
- **Interface**:
  - `log_operation(operation: Operation) -> None`: Record an executed operation
  - `save_log(log_path: Path) -> None`: Persist undo log to disk
  - `load_log(log_path: Path) -> List[Operation]`: Load undo log from disk
  - `undo(log_path: Path) -> OperationResults`: Reverse operations from log

### File System
- **Responsibility**: Abstract file system operations for testability
- **Interface**:
  - `move_file(source: Path, dest: Path) -> None`: Move file with conflict handling
  - `rename_file(source: Path, dest: Path) -> None`: Rename file
  - `create_directory(path: Path) -> None`: Create directory if not exists
  - `list_files(directory: Path, pattern: str) -> List[Path]`: List files matching pattern
  - `get_file_info(path: Path) -> FileInfo`: Get file metadata

## Data Models

### Config
```python
@dataclass
class Config:
    target_dir: Path
    operation_type: OperationType  # RENAME, ORGANIZE_TYPE, ORGANIZE_DATE, CUSTOM
    dry_run: bool
    verbose: bool
    # Rename-specific
    pattern: Optional[str]
    replacement: Optional[str]
    sequential_template: Optional[str]
    case_type: Optional[CaseType]
    prefix: Optional[str]
    suffix: Optional[str]
    # Organize-specific
    date_format: Optional[str]
    rules_file: Optional[Path]
    file_pattern: str = "*"
```

### Operation
```python
@dataclass
class Operation:
    operation_type: OperationType
    source_path: Path
    dest_path: Path
    timestamp: datetime
    executed: bool = False
```

### Rule
```python
@dataclass
class Rule:
    name: str
    pattern: str  # Glob or regex
    destination: str  # Relative path from target directory
    priority: int
```

### OperationResults
```python
@dataclass
class OperationResults:
    successful: int
    skipped: int
    errors: List[Tuple[Path, str]]  # (file, error_message)
    operations: List[Operation]
```

### FileInfo
```python
@dataclass
class FileInfo:
    path: Path
    size: int
    modified_time: datetime
    created_time: datetime
    extension: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: File categorization by extension
*For any* set of files with various extensions, when organizing by type, each file should be categorized into the correct predefined type group (documents, images, videos, audio, archives, code) based on its extension and moved to the corresponding subdirectory.
**Validates: Requirements 1.1, 1.2**

### Property 2: Directory creation on demand
*For any* target subdirectory that does not exist, when moving a file to that location, the system should create the directory before performing the move operation.
**Validates: Requirements 1.3**

### Property 3: Conflict resolution with numeric suffixes
*For any* file being moved to a destination where a file with the same name already exists, the system should append a numeric suffix (e.g., "_1", "_2") to the new filename to prevent overwriting.
**Validates: Requirements 1.4**

### Property 4: Accurate operation reporting
*For any* completed operation, the system should report counts (successful, skipped, errors) that exactly match the actual number of operations performed in each category.
**Validates: Requirements 1.5, 7.2**

### Property 5: Pattern replacement in filenames
*For any* set of filenames and a find-and-replace pattern, applying the transformation should replace all occurrences of the pattern in matching filenames while preserving file extensions.
**Validates: Requirements 2.1**

### Property 6: Sequential numbering preserves extensions
*For any* set of files renamed with sequential numbering, each file should receive a unique sequential number and retain its original file extension.
**Validates: Requirements 2.2**

### Property 7: Prefix and suffix addition
*For any* set of filenames and a prefix or suffix string, adding the prefix/suffix should result in all filenames containing the added text in the correct position while preserving extensions.
**Validates: Requirements 2.3**

### Property 8: Case transformation correctness
*For any* filename and case transformation type (lowercase, uppercase, title case), applying the transformation should convert all characters to the specified case while preserving file extensions.
**Validates: Requirements 2.4**

### Property 9: Duplicate detection prevents conflicts
*For any* rename operation that would create duplicate filenames, the system should detect the conflict before execution and prevent the operation while reporting all conflicts.
**Validates: Requirements 2.5**

### Property 10: Dry-run mode file system invariant
*For any* operation executed in dry-run mode, the file system should remain completely unchanged - no files created, moved, renamed, or deleted.
**Validates: Requirements 3.1, 3.3**

### Property 11: Dry-run output completeness
*For any* operation planned in dry-run mode, the output should include the original filename, new filename, and operation type for each planned change.
**Validates: Requirements 3.2**

### Property 12: Dry-run summary accuracy
*For any* dry-run execution, the summary count of operations should exactly match the number of planned operations displayed.
**Validates: Requirements 3.4**

### Property 13: Date-based organization correctness
*For any* set of files with modification dates, organizing by date should group files into year/month folder structures where each file is placed in a folder corresponding to its modification date.
**Validates: Requirements 4.1**

### Property 14: Date folder format compliance
*For any* date-based organization with a specified format (YYYY/MM or YYYY-MM), all created folders should follow the specified format consistently.
**Validates: Requirements 4.2**

### Property 15: Date fallback to creation time
*For any* file where modification date is unavailable, the system should use the file's creation date for date-based organization.
**Validates: Requirements 4.3**

### Property 16: Filename preservation during date organization
*For any* file organized by date, the filename (excluding path) should remain identical before and after the organization operation.
**Validates: Requirements 4.4**

### Property 17: Custom rule application
*For any* valid configuration file with custom rules, the system should parse all rules and apply them to matching files, moving files to their specified destinations.
**Validates: Requirements 5.1, 5.2**

### Property 18: Rule priority ordering
*For any* file that matches multiple custom rules, only the first matching rule (by priority order) should be applied to that file.
**Validates: Requirements 5.3**

### Property 19: Invalid rule error handling
*For any* configuration containing both valid and invalid rules, the system should report errors for invalid rules and continue processing all valid rules.
**Validates: Requirements 5.4**

### Property 20: Undo log completeness
*For any* completed operation, the undo log should contain entries for all file movements and renames that were executed.
**Validates: Requirements 6.1**

### Property 21: Undo operation round-trip
*For any* set of file operations followed immediately by an undo command, all files should be restored to their original locations and names, returning the file system to its pre-operation state.
**Validates: Requirements 6.2, 6.3**

### Property 22: Partial undo resilience
*For any* undo operation where some files cannot be restored, the system should report failures for those specific files and successfully restore all other files.
**Validates: Requirements 6.4**

### Property 23: Error resilience during processing
*For any* operation where errors occur on specific files, the system should log each error and continue processing all remaining files without stopping.
**Validates: Requirements 7.3**

### Property 24: Verbose mode output detail
*For any* operation executed in verbose mode, the output should include detailed information (source, destination, operation type, status) for each individual file operation.
**Validates: Requirements 7.4**

## Error Handling

The system implements comprehensive error handling at multiple levels:

### File System Errors
- **Permission Errors**: When lacking permissions to read/write files, log the specific file and error, skip that file, and continue processing
- **Path Errors**: When encountering invalid paths, report the error with the problematic path and continue
- **Disk Space**: Before operations, check available disk space; if insufficient, abort with clear error message

### Configuration Errors
- **Invalid Rules**: Parse errors in configuration files should be reported with line numbers and specific issues
- **Missing Files**: When configuration references non-existent files, report the missing file and continue with valid rules
- **Syntax Errors**: YAML/JSON parsing errors should show the specific syntax issue and location

### Operation Errors
- **Conflict Detection**: Before executing operations, validate that no conflicts exist (duplicate names, circular moves)
- **Atomic Operations**: Each file operation should be atomic - either fully succeed or fully fail with rollback
- **Undo Failures**: When undo operations fail, log which files couldn't be restored and why

### User Input Errors
- **Invalid Arguments**: CLI should validate all arguments and provide helpful error messages with examples
- **Missing Required Args**: Show which required arguments are missing and how to provide them
- **Conflicting Options**: Detect mutually exclusive options and explain the conflict

## Testing Strategy

The File Organizer will use a comprehensive testing approach combining unit tests and property-based tests to ensure correctness and reliability.

### Property-Based Testing

We will use **Hypothesis** (Python's property-based testing library) to verify universal properties across randomly generated inputs. Hypothesis will automatically generate diverse test cases including edge cases we might not think of manually.

**Configuration**:
- Each property-based test will run a minimum of 100 iterations
- Tests will use custom strategies to generate realistic file structures, names, and operations
- Each property test will include a comment tag referencing the design document property

**Test Organization**:
- Property tests will be in `tests/property_tests/` directory
- Each module will test related properties (e.g., `test_rename_properties.py`, `test_organize_properties.py`)
- Tests will use the format: `# Feature: file-organizer, Property X: <property description>`

**Custom Strategies**:
- `file_names()`: Generate realistic filenames with various extensions, special characters, and edge cases
- `file_trees()`: Generate directory structures with nested folders and files
- `rename_patterns()`: Generate find-replace patterns, sequential templates, and transformations
- `organization_rules()`: Generate valid and invalid custom rules
- `file_dates()`: Generate realistic file timestamps including edge cases

### Unit Testing

Unit tests will verify specific examples, integration points, and error conditions:

**Core Functionality Tests**:
- Test each component (Renamer, Organizer, RuleEngine) with specific examples
- Verify error handling with known problematic inputs
- Test edge cases like empty directories, single files, special characters

**Integration Tests**:
- Test CLI argument parsing with various command combinations
- Verify end-to-end workflows (organize → undo, rename → dry-run)
- Test configuration file loading and rule application

**Mock Usage**:
- Mock file system operations for fast, isolated unit tests
- Use real file system for integration tests in temporary directories
- Mock progress display for testing without terminal output

### Test Utilities

**Fixtures**:
- `temp_file_tree()`: Create temporary directory structures for testing
- `sample_files()`: Generate files with specific properties (dates, extensions, sizes)
- `mock_config()`: Create configuration objects for testing

**Assertions**:
- `assert_file_exists()`: Verify file exists at expected location
- `assert_file_moved()`: Verify file moved from source to destination
- `assert_filesystem_unchanged()`: Verify no files were modified (for dry-run tests)

### Testing Workflow

1. **Implementation First**: Implement each feature component before writing tests
2. **Property Tests**: Write property-based tests for universal behaviors
3. **Unit Tests**: Add unit tests for specific examples and edge cases
4. **Integration Tests**: Verify components work together correctly
5. **Regression Tests**: Add tests for any bugs discovered during use

This dual approach ensures both general correctness (via properties) and specific behavior verification (via unit tests), providing comprehensive coverage and confidence in the system's reliability.
