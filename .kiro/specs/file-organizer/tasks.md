# Implementation Plan

- [x] 1. Set up project structure and core data models
  - Create Python project with proper directory structure (src/, tests/)
  - Set up virtual environment and dependencies (click for CLI, hypothesis for property testing)
  - Define data models: Config, Operation, Rule, OperationResults, FileInfo
  - Create enums for OperationType and CaseType
  - _Requirements: All requirements (foundation)_

- [x] 2. Implement File System abstraction layer
  - Create FileSystem class with methods for move, rename, create_directory, list_files, get_file_info
  - Implement conflict detection and numeric suffix generation
  - Add error handling for permission errors, path errors, and disk space checks
  - _Requirements: 1.4, 7.3_

- [x] 2.1 Write property test for conflict resolution
  - **Property 3: Conflict resolution with numeric suffixes**
  - **Validates: Requirements 1.4**

- [x] 2.2 Write property test for error resilience
  - **Property 23: Error resilience during processing**
  - **Validates: Requirements 7.3**

- [x] 3. Implement Renamer component
  - Create Renamer class with rename_pattern, rename_sequential, rename_case, add_prefix_suffix methods
  - Implement pattern matching and replacement logic
  - Add duplicate detection for rename operations
  - Implement sequential numbering with template support
  - Add case transformation (lowercase, uppercase, title case)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3.1 Write property test for pattern replacement
  - **Property 5: Pattern replacement in filenames**
  - **Validates: Requirements 2.1**

- [x] 3.2 Write property test for sequential numbering
  - **Property 6: Sequential numbering preserves extensions**
  - **Validates: Requirements 2.2**

- [x] 3.3 Write property test for prefix/suffix addition
  - **Property 7: Prefix and suffix addition**
  - **Validates: Requirements 2.3**

- [x] 3.4 Write property test for case transformation
  - **Property 8: Case transformation correctness**
  - **Validates: Requirements 2.4**

- [x] 3.5 Write property test for duplicate detection
  - **Property 9: Duplicate detection prevents conflicts**
  - **Validates: Requirements 2.5**

- [x] 4. Implement Organizer component
  - Create Organizer class with organize_by_type, organize_by_date, organize_custom methods
  - Define file type categories and extension mappings (documents, images, videos, audio, archives, code)
  - Implement date-based organization with configurable folder format
  - Add fallback logic for missing modification dates
  - Ensure filename preservation during organization
  - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 4.3, 4.4_

- [x] 4.1 Write property test for file categorization
  - **Property 1: File categorization by extension**
  - **Validates: Requirements 1.1, 1.2**

- [x] 4.2 Write property test for directory creation
  - **Property 2: Directory creation on demand**
  - **Validates: Requirements 1.3**

- [x] 4.3 Write property test for date organization
  - **Property 13: Date-based organization correctness**
  - **Validates: Requirements 4.1**

- [x] 4.4 Write property test for date folder format
  - **Property 14: Date folder format compliance**
  - **Validates: Requirements 4.2**

- [x] 4.5 Write property test for date fallback
  - **Property 15: Date fallback to creation time**
  - **Validates: Requirements 4.3**

- [x] 4.6 Write property test for filename preservation
  - **Property 16: Filename preservation during date organization**
  - **Validates: Requirements 4.4**

- [x] 5. Implement Rule Engine
  - Create RuleEngine class with load_rules, match_file, apply_rules methods
  - Implement YAML/JSON configuration file parsing
  - Add glob and regex pattern matching for file rules
  - Implement priority-based rule application (first match wins)
  - Add validation for rule syntax and error reporting
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5.1 Write property test for custom rule application
  - **Property 17: Custom rule application**
  - **Validates: Requirements 5.1, 5.2**

- [x] 5.2 Write property test for rule priority
  - **Property 18: Rule priority ordering**
  - **Validates: Requirements 5.3**

- [x] 5.3 Write property test for invalid rule handling
  - **Property 19: Invalid rule error handling**
  - **Validates: Requirements 5.4**

- [x] 6. Implement Undo Manager
  - Create UndoManager class with log_operation, save_log, load_log, undo methods
  - Implement JSON-based undo log format with timestamps
  - Add logic to reverse operations (move back, rename back)
  - Implement partial undo with error reporting for failed reversals
  - Store undo logs in user's home directory or configurable location
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.1 Write property test for undo log completeness
  - **Property 20: Undo log completeness**
  - **Validates: Requirements 6.1**

- [x] 6.2 Write property test for undo round-trip
  - **Property 21: Undo operation round-trip**
  - **Validates: Requirements 6.2, 6.3**

- [x] 6.3 Write property test for partial undo
  - **Property 22: Partial undo resilience**
  - **Validates: Requirements 6.4**

- [x] 7. Implement Orchestrator
  - Create Orchestrator class with execute, plan_operations, execute_operations methods
  - Implement operation planning phase that generates Operation objects
  - Add dry-run mode that displays operations without executing
  - Implement operation execution with progress tracking
  - Add result aggregation and summary generation
  - Integrate all components (Renamer, Organizer, RuleEngine, UndoManager)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.1, 7.2_

- [x] 7.1 Write property test for dry-run invariant
  - **Property 10: Dry-run mode file system invariant**
  - **Validates: Requirements 3.1, 3.3**

- [x] 7.2 Write property test for dry-run output
  - **Property 11: Dry-run output completeness**
  - **Validates: Requirements 3.2**

- [x] 7.3 Write property test for dry-run summary
  - **Property 12: Dry-run summary accuracy**
  - **Validates: Requirements 3.4**

- [x] 7.4 Write property test for operation reporting
  - **Property 4: Accurate operation reporting**
  - **Validates: Requirements 1.5, 7.2**

- [x] 8. Implement CLI layer
  - Create CLI using Click library with command groups and options
  - Add commands: organize-type, organize-date, rename, custom, undo
  - Implement argument parsing and validation for all operation types
  - Add global flags: --dry-run, --verbose, --target-dir, --pattern
  - Implement progress indicator for operations with >10 files
  - Add result formatting and display (success/skip/error counts)
  - Implement verbose mode output with per-file details
  - _Requirements: 7.1, 7.4_

- [x] 8.1 Write property test for verbose output
  - **Property 24: Verbose mode output detail**
  - **Validates: Requirements 7.4**

- [x] 8.2 Write unit tests for CLI argument parsing
  - Test various command combinations and flag interactions
  - Test error messages for invalid arguments
  - Test help text generation
  - _Requirements: All requirements (CLI interface)_

- [x] 9. Add example configuration files and documentation
  - Create example rules.yaml with common organization patterns
  - Add README.md with installation instructions and usage examples
  - Document all CLI commands and options
  - Provide example workflows (organize downloads, bulk rename photos, etc.)
  - _Requirements: 5.1_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
