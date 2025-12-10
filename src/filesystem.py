"""File system abstraction layer for file operations."""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.models import FileInfo


class FileSystemError(Exception):
    """Base exception for file system operations."""
    pass


class PermissionError(FileSystemError):
    """Raised when lacking permissions for file operations."""
    pass


class PathError(FileSystemError):
    """Raised when encountering invalid paths."""
    pass


class DiskSpaceError(FileSystemError):
    """Raised when insufficient disk space is available."""
    pass


class FileSystem:
    """Abstraction layer for file system operations with error handling."""
    
    def move_file(self, source: Path, dest: Path) -> None:
        """
        Move a file from source to destination with conflict handling.
        
        If a file exists at the destination, appends a numeric suffix.
        
        Args:
            source: Source file path
            dest: Destination file path
            
        Raises:
            PermissionError: If lacking permissions
            PathError: If paths are invalid
            DiskSpaceError: If insufficient disk space
        """
        try:
            # Validate paths
            if not source.exists():
                raise PathError(f"Source file does not exist: {source}")
            
            if not source.is_file():
                raise PathError(f"Source is not a file: {source}")
            
            # Check disk space
            self._check_disk_space(source, dest.parent)
            
            # Handle conflicts by adding numeric suffix
            final_dest = self._resolve_conflict(dest)
            
            # Ensure destination directory exists
            final_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source), str(final_dest))
            
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 13:  # Permission denied
                raise PermissionError(f"Permission denied: {e}")
            elif e.errno == 28:  # No space left on device
                raise DiskSpaceError(f"Insufficient disk space: {e}")
            else:
                raise PathError(f"Path error: {e}")
    
    def rename_file(self, source: Path, dest: Path) -> None:
        """
        Rename a file from source to destination.
        
        Args:
            source: Source file path
            dest: Destination file path
            
        Raises:
            PermissionError: If lacking permissions
            PathError: If paths are invalid
        """
        try:
            if not source.exists():
                raise PathError(f"Source file does not exist: {source}")
            
            if not source.is_file():
                raise PathError(f"Source is not a file: {source}")
            
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            source.rename(dest)
            
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 13:
                raise PermissionError(f"Permission denied: {e}")
            else:
                raise PathError(f"Path error: {e}")
    
    def create_directory(self, path: Path) -> None:
        """
        Create a directory if it doesn't exist.
        
        Args:
            path: Directory path to create
            
        Raises:
            PermissionError: If lacking permissions
            PathError: If path is invalid
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 13:
                raise PermissionError(f"Permission denied: {e}")
            else:
                raise PathError(f"Path error: {e}")
    
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """
        List files in a directory matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern for matching files (default: "*")
            
        Returns:
            List of file paths matching the pattern
            
        Raises:
            PermissionError: If lacking permissions
            PathError: If directory is invalid
        """
        try:
            if not directory.exists():
                raise PathError(f"Directory does not exist: {directory}")
            
            if not directory.is_dir():
                raise PathError(f"Path is not a directory: {directory}")
            
            # Use glob to find matching files
            files = [f for f in directory.glob(pattern) if f.is_file()]
            return files
            
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 13:
                raise PermissionError(f"Permission denied: {e}")
            else:
                raise PathError(f"Path error: {e}")
    
    def get_file_info(self, path: Path) -> FileInfo:
        """
        Get metadata information about a file.
        
        Args:
            path: File path
            
        Returns:
            FileInfo object with file metadata
            
        Raises:
            PermissionError: If lacking permissions
            PathError: If file doesn't exist or is invalid
        """
        try:
            if not path.exists():
                raise PathError(f"File does not exist: {path}")
            
            if not path.is_file():
                raise PathError(f"Path is not a file: {path}")
            
            stat = path.stat()
            
            return FileInfo(
                path=path,
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                created_time=datetime.fromtimestamp(stat.st_ctime),
                extension=path.suffix,
            )
            
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {e}")
        except OSError as e:
            if e.errno == 13:
                raise PermissionError(f"Permission denied: {e}")
            else:
                raise PathError(f"Path error: {e}")
    
    def _resolve_conflict(self, dest: Path) -> Path:
        """
        Resolve filename conflicts by appending numeric suffixes.
        
        Args:
            dest: Desired destination path
            
        Returns:
            Path with numeric suffix if conflict exists, otherwise original path
        """
        if not dest.exists():
            return dest
        
        # Extract stem and suffix
        stem = dest.stem
        suffix = dest.suffix
        parent = dest.parent
        
        # Try numeric suffixes until we find an available name
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _check_disk_space(self, source: Path, dest_dir: Path) -> None:
        """
        Check if sufficient disk space is available for the operation.
        
        Args:
            source: Source file to be moved
            dest_dir: Destination directory
            
        Raises:
            DiskSpaceError: If insufficient disk space
        """
        try:
            # Get file size
            file_size = source.stat().st_size
            
            # Get available space on destination
            stat = os.statvfs(dest_dir if dest_dir.exists() else dest_dir.parent)
            available_space = stat.f_bavail * stat.f_frsize
            
            # Check if we have enough space (with 10% buffer)
            required_space = file_size * 1.1
            if available_space < required_space:
                raise DiskSpaceError(
                    f"Insufficient disk space. Required: {required_space}, "
                    f"Available: {available_space}"
                )
        except OSError as e:
            # If we can't check disk space, log but don't fail
            pass
