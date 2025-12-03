"""Renamer component for file renaming operations."""

import re
from pathlib import Path
from typing import List, Set
from datetime import datetime

from src.models import Operation, OperationType, CaseType


class RenameError(Exception):
    """Base exception for rename operations."""
    pass


class DuplicateNameError(RenameError):
    """Raised when rename operation would create duplicate filenames."""
    pass


class Renamer:
    """Handles all filename transformation logic."""
    
    def rename_pattern(
        self, 
        files: List[Path], 
        pattern: str, 
        replacement: str
    ) -> List[Operation]:
        """
        Apply find-and-replace pattern to filenames.
        
        Args:
            files: List of file paths to rename
            pattern: Pattern to find in filenames
            replacement: Replacement text
            
        Returns:
            List of Operation objects for the rename operations
            
        Raises:
            DuplicateNameError: If renaming would create duplicate filenames
        """
        operations = []
        new_names: Set[str] = set()
        duplicates: List[str] = []
        
        for file_path in files:
            # Get the filename without path
            original_name = file_path.name
            stem = file_path.stem
            extension = file_path.suffix
            
            # Apply pattern replacement to stem only (preserve extension)
            new_stem = stem.replace(pattern, replacement)
            
            # Skip if new stem is empty (invalid filename)
            if not new_stem:
                duplicates.append(original_name)
                continue
            
            new_name = new_stem + extension
            
            # Check for duplicates
            new_path = file_path.parent / new_name
            
            if new_name in new_names or (new_path.exists() and new_path != file_path):
                duplicates.append(original_name)
            else:
                new_names.add(new_name)
                
                # Only create operation if name actually changed
                if new_name != original_name:
                    operation = Operation(
                        operation_type=OperationType.RENAME,
                        source_path=file_path,
                        dest_path=new_path,
                        timestamp=datetime.now(),
                        executed=False
                    )
                    operations.append(operation)
        
        # If duplicates found, raise error
        if duplicates:
            raise DuplicateNameError(
                f"Rename would create duplicate filenames: {', '.join(duplicates)}"
            )
        
        return operations
    
    def rename_sequential(
        self, 
        files: List[Path], 
        template: str
    ) -> List[Operation]:
        """
        Rename files with sequential numbering.
        
        Args:
            files: List of file paths to rename
            template: Template string with {n} placeholder for number
                     Example: "file_{n}" -> "file_1.txt", "file_2.txt"
            
        Returns:
            List of Operation objects for the rename operations
        """
        operations = []
        
        for idx, file_path in enumerate(files, start=1):
            extension = file_path.suffix
            
            # Replace {n} placeholder with sequential number
            new_stem = template.replace('{n}', str(idx))
            new_name = new_stem + extension
            new_path = file_path.parent / new_name
            
            operation = Operation(
                operation_type=OperationType.RENAME,
                source_path=file_path,
                dest_path=new_path,
                timestamp=datetime.now(),
                executed=False
            )
            operations.append(operation)
        
        return operations
    
    def rename_case(
        self, 
        files: List[Path], 
        case_type: CaseType
    ) -> List[Operation]:
        """
        Transform filename case.
        
        Args:
            files: List of file paths to rename
            case_type: Type of case transformation (LOWERCASE, UPPERCASE, TITLE)
            
        Returns:
            List of Operation objects for the rename operations
        """
        operations = []
        
        for file_path in files:
            stem = file_path.stem
            extension = file_path.suffix
            
            # Apply case transformation to stem only
            if case_type == CaseType.LOWERCASE:
                new_stem = stem.lower()
            elif case_type == CaseType.UPPERCASE:
                new_stem = stem.upper()
            elif case_type == CaseType.TITLE:
                new_stem = stem.title()
            else:
                new_stem = stem
            
            new_name = new_stem + extension
            new_path = file_path.parent / new_name
            
            # Only create operation if name actually changed
            if new_name != file_path.name:
                operation = Operation(
                    operation_type=OperationType.RENAME,
                    source_path=file_path,
                    dest_path=new_path,
                    timestamp=datetime.now(),
                    executed=False
                )
                operations.append(operation)
        
        return operations
    
    def add_prefix_suffix(
        self, 
        files: List[Path], 
        prefix: str = "", 
        suffix: str = ""
    ) -> List[Operation]:
        """
        Add prefix and/or suffix to filenames.
        
        Args:
            files: List of file paths to rename
            prefix: Text to add at the beginning of filename
            suffix: Text to add at the end of filename (before extension)
            
        Returns:
            List of Operation objects for the rename operations
        """
        operations = []
        
        for file_path in files:
            stem = file_path.stem
            extension = file_path.suffix
            
            # Add prefix and suffix
            new_stem = prefix + stem + suffix
            new_name = new_stem + extension
            new_path = file_path.parent / new_name
            
            # Only create operation if name actually changed
            if new_name != file_path.name:
                operation = Operation(
                    operation_type=OperationType.RENAME,
                    source_path=file_path,
                    dest_path=new_path,
                    timestamp=datetime.now(),
                    executed=False
                )
                operations.append(operation)
        
        return operations
