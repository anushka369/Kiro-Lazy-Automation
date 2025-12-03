"""Organizer component for file categorization and organization."""

from pathlib import Path
from typing import List, Dict
from datetime import datetime

from src.models import Operation, OperationType
from src.filesystem import FileSystem


class OrganizerError(Exception):
    """Base exception for organizer operations."""
    pass


class Organizer:
    """Handles file categorization and organization logic."""
    
    # File type categories and their extension mappings
    FILE_TYPE_CATEGORIES: Dict[str, List[str]] = {
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp', '.tiff', '.tif'],
        'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'],
        'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
        'code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.sh', '.bat']
    }
    
    def __init__(self, filesystem: FileSystem = None):
        """
        Initialize the Organizer.
        
        Args:
            filesystem: FileSystem instance for file operations (optional, creates new if not provided)
        """
        self.filesystem = filesystem or FileSystem()
    
    def organize_by_type(self, files: List[Path], target_dir: Path) -> List[Operation]:
        """
        Organize files by type into category subdirectories.
        
        Args:
            files: List of file paths to organize
            target_dir: Target directory where category subdirectories will be created
            
        Returns:
            List of Operation objects for the organization operations
        """
        operations = []
        
        for file_path in files:
            # Get file extension
            extension = file_path.suffix.lower()
            
            # Determine category
            category = self._get_category(extension)
            
            # Create destination path
            dest_dir = target_dir / category
            dest_path = dest_dir / file_path.name
            
            # Create operation
            operation = Operation(
                operation_type=OperationType.ORGANIZE_TYPE,
                source_path=file_path,
                dest_path=dest_path,
                timestamp=datetime.now(),
                executed=False
            )
            operations.append(operation)
        
        return operations
    
    def organize_by_date(
        self, 
        files: List[Path], 
        target_dir: Path, 
        date_format: str = "YYYY/MM"
    ) -> List[Operation]:
        """
        Organize files by modification date into year/month folder structures.
        
        Args:
            files: List of file paths to organize
            target_dir: Target directory where date subdirectories will be created
            date_format: Format for date folders ("YYYY/MM" or "YYYY-MM")
            
        Returns:
            List of Operation objects for the organization operations
        """
        operations = []
        
        for file_path in files:
            # Get file info to access dates
            file_info = self.filesystem.get_file_info(file_path)
            
            # Use modification time, fallback to creation time if unavailable
            file_date = file_info.modified_time
            if file_date is None:
                file_date = file_info.created_time
            
            # Format the date folder path
            if date_format == "YYYY/MM":
                date_folder = f"{file_date.year}/{file_date.month:02d}"
            elif date_format == "YYYY-MM":
                date_folder = f"{file_date.year}-{file_date.month:02d}"
            else:
                # Default to YYYY/MM
                date_folder = f"{file_date.year}/{file_date.month:02d}"
            
            # Create destination path (preserve filename)
            dest_dir = target_dir / date_folder
            dest_path = dest_dir / file_path.name
            
            # Create operation
            operation = Operation(
                operation_type=OperationType.ORGANIZE_DATE,
                source_path=file_path,
                dest_path=dest_path,
                timestamp=datetime.now(),
                executed=False
            )
            operations.append(operation)
        
        return operations
    
    def organize_custom(self, files: List[Path], rules: List, target_dir: Path) -> List[Operation]:
        """
        Apply custom organization rules to files.
        
        Args:
            files: List of file paths to organize
            rules: List of Rule objects defining custom organization logic
            target_dir: Base target directory for relative destinations
            
        Returns:
            List of Operation objects for the organization operations
        """
        from src.rule_engine import RuleEngine
        
        rule_engine = RuleEngine()
        operations = rule_engine.apply_rules(files, rules, target_dir)
        
        return operations
    
    def _get_category(self, extension: str) -> str:
        """
        Determine the category for a file based on its extension.
        
        Args:
            extension: File extension (including the dot, e.g., '.txt')
            
        Returns:
            Category name (e.g., 'documents', 'images', etc.)
            Returns 'other' if extension doesn't match any category
        """
        extension = extension.lower()
        
        for category, extensions in self.FILE_TYPE_CATEGORIES.items():
            if extension in extensions:
                return category
        
        # Default category for unknown extensions
        return 'other'
