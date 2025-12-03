"""Orchestrator component for coordinating file operations."""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.models import (
    Config, Operation, OperationResults, OperationType, CaseType
)
from src.filesystem import FileSystem, FileSystemError
from src.renamer import Renamer, RenameError
from src.organizer import Organizer, OrganizerError
from src.rule_engine import RuleEngine, RuleEngineError
from src.undo_manager import UndoManager, UndoManagerError


class OrchestratorError(Exception):
    """Base exception for orchestrator operations."""
    pass


class Orchestrator:
    """Coordinates all file organization operations and manages workflow."""
    
    def __init__(
        self,
        filesystem: Optional[FileSystem] = None,
        renamer: Optional[Renamer] = None,
        organizer: Optional[Organizer] = None,
        rule_engine: Optional[RuleEngine] = None,
        undo_manager: Optional[UndoManager] = None
    ):
        """
        Initialize the Orchestrator with component dependencies.
        
        Args:
            filesystem: FileSystem instance (optional, creates new if not provided)
            renamer: Renamer instance (optional, creates new if not provided)
            organizer: Organizer instance (optional, creates new if not provided)
            rule_engine: RuleEngine instance (optional, creates new if not provided)
            undo_manager: UndoManager instance (optional, creates new if not provided)
        """
        self.filesystem = filesystem or FileSystem()
        self.renamer = renamer or Renamer()
        self.organizer = organizer or Organizer(self.filesystem)
        self.rule_engine = rule_engine or RuleEngine()
        self.undo_manager = undo_manager or UndoManager(self.filesystem)
    
    def execute(self, config: Config) -> OperationResults:
        """
        Main entry point for executing file operations.
        
        Coordinates the full workflow: planning, execution, and logging.
        
        Args:
            config: Configuration object specifying the operation to perform
            
        Returns:
            OperationResults with summary of the operation
            
        Raises:
            OrchestratorError: If operation cannot be completed
        """
        try:
            # Phase 1: Plan operations
            operations = self.plan_operations(config)
            
            # Phase 2: Execute operations (or simulate in dry-run mode)
            results = self.execute_operations(operations, config.dry_run)
            
            # Phase 3: Log operations for undo (only if not dry-run and successful)
            if not config.dry_run and results.successful > 0:
                # Log all executed operations
                for operation in results.operations:
                    if operation.executed:
                        self.undo_manager.log_operation(operation)
                
                # Save the undo log
                self.undo_manager.save_log()
                
                # Clear the current log for next operation
                self.undo_manager.clear_current_log()
            
            return results
            
        except (FileSystemError, RenameError, OrganizerError, RuleEngineError, UndoManagerError) as e:
            raise OrchestratorError(f"Operation failed: {e}")
    
    def plan_operations(self, config: Config) -> List[Operation]:
        """
        Generate a plan of operations based on configuration.
        
        This phase determines what operations need to be performed without
        actually executing them.
        
        Args:
            config: Configuration object specifying the operation
            
        Returns:
            List of Operation objects representing the planned operations
            
        Raises:
            OrchestratorError: If planning fails
        """
        # Get list of files to process
        files = self.filesystem.list_files(config.target_dir, config.file_pattern)
        
        if not files:
            return []
        
        # Generate operations based on operation type
        operations = []
        
        if config.operation_type == OperationType.RENAME:
            operations = self._plan_rename_operations(config, files)
        
        elif config.operation_type == OperationType.ORGANIZE_TYPE:
            operations = self.organizer.organize_by_type(files, config.target_dir)
        
        elif config.operation_type == OperationType.ORGANIZE_DATE:
            date_format = config.date_format or "YYYY/MM"
            operations = self.organizer.organize_by_date(files, config.target_dir, date_format)
        
        elif config.operation_type == OperationType.CUSTOM:
            if not config.rules_file:
                raise OrchestratorError("Custom operation requires a rules file")
            
            # Load rules from configuration file
            rules = self.rule_engine.load_rules(config.rules_file)
            operations = self.rule_engine.apply_rules(files, rules, config.target_dir)
        
        elif config.operation_type == OperationType.UNDO:
            # Undo operations are handled differently (not planned)
            raise OrchestratorError("Undo operations should use undo_manager directly")
        
        else:
            raise OrchestratorError(f"Unknown operation type: {config.operation_type}")
        
        return operations
    
    def _plan_rename_operations(self, config: Config, files: List[Path]) -> List[Operation]:
        """
        Plan rename operations based on configuration.
        
        Args:
            config: Configuration with rename-specific options
            files: List of files to rename
            
        Returns:
            List of Operation objects for rename operations
        """
        # Determine which rename operation to perform
        if config.pattern and config.replacement is not None:
            # Pattern-based rename
            return self.renamer.rename_pattern(files, config.pattern, config.replacement)
        
        elif config.sequential_template:
            # Sequential numbering
            return self.renamer.rename_sequential(files, config.sequential_template)
        
        elif config.case_type:
            # Case transformation
            return self.renamer.rename_case(files, config.case_type)
        
        elif config.prefix or config.suffix:
            # Prefix/suffix addition
            prefix = config.prefix or ""
            suffix = config.suffix or ""
            return self.renamer.add_prefix_suffix(files, prefix, suffix)
        
        else:
            raise OrchestratorError(
                "Rename operation requires one of: pattern/replacement, "
                "sequential_template, case_type, or prefix/suffix"
            )
    
    def execute_operations(
        self, 
        operations: List[Operation], 
        dry_run: bool = False
    ) -> OperationResults:
        """
        Execute or simulate a list of operations.
        
        Args:
            operations: List of Operation objects to execute
            dry_run: If True, simulate operations without modifying files
            
        Returns:
            OperationResults with summary of execution
        """
        successful = 0
        skipped = 0
        errors = []
        
        for operation in operations:
            try:
                if dry_run:
                    # In dry-run mode, just mark as "would be executed"
                    # Don't actually modify the file system
                    operation.executed = False
                    successful += 1
                else:
                    # Execute the actual operation
                    self._execute_single_operation(operation)
                    operation.executed = True
                    successful += 1
                    
            except FileSystemError as e:
                # Log error and continue with remaining operations
                errors.append((operation.source_path, str(e)))
            except Exception as e:
                # Catch unexpected errors
                errors.append((operation.source_path, f"Unexpected error: {e}"))
        
        return OperationResults(
            successful=successful,
            skipped=skipped,
            errors=errors,
            operations=operations
        )
    
    def _execute_single_operation(self, operation: Operation) -> None:
        """
        Execute a single file operation.
        
        Args:
            operation: Operation to execute
            
        Raises:
            FileSystemError: If operation fails
        """
        # Ensure destination directory exists
        self.filesystem.create_directory(operation.dest_path.parent)
        
        # Execute based on operation type
        if operation.operation_type in [
            OperationType.RENAME,
            OperationType.ORGANIZE_TYPE,
            OperationType.ORGANIZE_DATE,
            OperationType.CUSTOM
        ]:
            # All these operations involve moving/renaming files
            self.filesystem.move_file(operation.source_path, operation.dest_path)
        
        elif operation.operation_type == OperationType.UNDO:
            # Undo operations also move files (back to original location)
            self.filesystem.move_file(operation.source_path, operation.dest_path)
        
        else:
            raise OrchestratorError(f"Unknown operation type: {operation.operation_type}")
