"""Unit tests for CLI argument parsing and command validation."""

import tempfile
from pathlib import Path
from click.testing import CliRunner
import pytest

from src.cli import cli


class TestCLIArgumentParsing:
    """Test CLI argument parsing and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_organize_type_basic_command(self):
        """Test basic organize-type command with default options."""
        result = self.runner.invoke(cli, ['organize-type', '--dry-run'])
        
        # Should succeed (even with no files)
        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
    
    def test_organize_type_with_target_dir(self):
        """Test organize-type with custom target directory."""
        result = self.runner.invoke(cli, [
            'organize-type',
            '--target-dir', self.temp_dir,
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_organize_type_with_pattern(self):
        """Test organize-type with file pattern."""
        result = self.runner.invoke(cli, [
            'organize-type',
            '--pattern', '*.txt',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_organize_type_with_verbose(self):
        """Test organize-type with verbose flag."""
        result = self.runner.invoke(cli, [
            'organize-type',
            '--verbose',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_organize_date_basic_command(self):
        """Test basic organize-date command."""
        result = self.runner.invoke(cli, ['organize-date', '--dry-run'])
        
        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
    
    def test_organize_date_with_format_slash(self):
        """Test organize-date with YYYY/MM format."""
        result = self.runner.invoke(cli, [
            'organize-date',
            '--format', 'YYYY/MM',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_organize_date_with_format_dash(self):
        """Test organize-date with YYYY-MM format."""
        result = self.runner.invoke(cli, [
            'organize-date',
            '--format', 'YYYY-MM',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_organize_date_invalid_format(self):
        """Test organize-date with invalid format."""
        result = self.runner.invoke(cli, [
            'organize-date',
            '--format', 'INVALID',
            '--dry-run'
        ])
        
        # Should fail with invalid choice
        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'invalid choice' in result.output.lower()
    
    def test_rename_with_find_replace(self):
        """Test rename command with find-and-replace."""
        result = self.runner.invoke(cli, [
            'rename',
            '--find', 'old',
            '--replace', 'new',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_sequential(self):
        """Test rename command with sequential numbering."""
        result = self.runner.invoke(cli, [
            'rename',
            '--sequential', 'file_{}.txt',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_case_lowercase(self):
        """Test rename command with lowercase transformation."""
        result = self.runner.invoke(cli, [
            'rename',
            '--case', 'lowercase',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_case_uppercase(self):
        """Test rename command with uppercase transformation."""
        result = self.runner.invoke(cli, [
            'rename',
            '--case', 'uppercase',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_case_title(self):
        """Test rename command with title case transformation."""
        result = self.runner.invoke(cli, [
            'rename',
            '--case', 'title',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_prefix(self):
        """Test rename command with prefix."""
        result = self.runner.invoke(cli, [
            'rename',
            '--prefix', 'backup_',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_suffix(self):
        """Test rename command with suffix."""
        result = self.runner.invoke(cli, [
            'rename',
            '--suffix', '_old',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_with_prefix_and_suffix(self):
        """Test rename command with both prefix and suffix."""
        result = self.runner.invoke(cli, [
            'rename',
            '--prefix', 'backup_',
            '--suffix', '_old',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
    
    def test_rename_no_method_specified(self):
        """Test rename command with no rename method specified."""
        result = self.runner.invoke(cli, [
            'rename',
            '--dry-run'
        ])
        
        # Should fail with error message
        assert result.exit_code != 0
        assert 'Must specify one rename method' in result.output
    
    def test_rename_multiple_methods_specified(self):
        """Test rename command with multiple rename methods."""
        result = self.runner.invoke(cli, [
            'rename',
            '--find', 'old',
            '--replace', 'new',
            '--case', 'lowercase',
            '--dry-run'
        ])
        
        # Should fail with error message
        assert result.exit_code != 0
        assert 'Only one rename method' in result.output
    
    def test_rename_find_without_replace(self):
        """Test rename command with --find but no --replace."""
        result = self.runner.invoke(cli, [
            'rename',
            '--find', 'old',
            '--dry-run'
        ])
        
        # Should fail with error message
        assert result.exit_code != 0
        assert '--replace is required' in result.output
    
    def test_rename_replace_without_find(self):
        """Test rename command with --replace but no --find."""
        result = self.runner.invoke(cli, [
            'rename',
            '--replace', 'new',
            '--dry-run'
        ])
        
        # Should fail with error message
        assert result.exit_code != 0
        assert '--find is required' in result.output
    
    def test_custom_command_basic(self):
        """Test custom command with rules file."""
        # Create a temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('rules: []\n')
            rules_file = f.name
        
        try:
            result = self.runner.invoke(cli, [
                'custom',
                '--rules', rules_file,
                '--dry-run'
            ])
            
            assert result.exit_code == 0
        finally:
            Path(rules_file).unlink()
    
    def test_custom_command_missing_rules_file(self):
        """Test custom command without rules file."""
        result = self.runner.invoke(cli, [
            'custom',
            '--dry-run'
        ])
        
        # Should fail - rules file is required
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'required' in result.output.lower()
    
    def test_custom_command_nonexistent_rules_file(self):
        """Test custom command with non-existent rules file."""
        result = self.runner.invoke(cli, [
            'custom',
            '--rules', '/nonexistent/file.yaml',
            '--dry-run'
        ])
        
        # Should fail - file doesn't exist
        assert result.exit_code != 0
    
    def test_undo_command_basic(self):
        """Test undo command."""
        result = self.runner.invoke(cli, ['undo'])
        
        # Should succeed (even if no operations to undo)
        assert result.exit_code == 0
    
    def test_undo_command_with_verbose(self):
        """Test undo command with verbose flag."""
        result = self.runner.invoke(cli, ['undo', '--verbose'])
        
        assert result.exit_code == 0
    
    def test_help_text_main(self):
        """Test main help text."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'File Organizer' in result.output
        assert 'organize-type' in result.output
        assert 'organize-date' in result.output
        assert 'rename' in result.output
        assert 'custom' in result.output
        assert 'undo' in result.output
    
    def test_help_text_organize_type(self):
        """Test organize-type help text."""
        result = self.runner.invoke(cli, ['organize-type', '--help'])
        
        assert result.exit_code == 0
        assert 'Organize files by type' in result.output
        assert '--dry-run' in result.output
        assert '--verbose' in result.output
        assert '--target-dir' in result.output
        assert '--pattern' in result.output
    
    def test_help_text_organize_date(self):
        """Test organize-date help text."""
        result = self.runner.invoke(cli, ['organize-date', '--help'])
        
        assert result.exit_code == 0
        assert 'Organize files by date' in result.output
        assert '--format' in result.output
    
    def test_help_text_rename(self):
        """Test rename help text."""
        result = self.runner.invoke(cli, ['rename', '--help'])
        
        assert result.exit_code == 0
        assert 'Rename files' in result.output
        assert '--find' in result.output
        assert '--replace' in result.output
        assert '--sequential' in result.output
        assert '--case' in result.output
        assert '--prefix' in result.output
        assert '--suffix' in result.output
    
    def test_help_text_custom(self):
        """Test custom help text."""
        result = self.runner.invoke(cli, ['custom', '--help'])
        
        assert result.exit_code == 0
        assert 'custom rules' in result.output
        assert '--rules' in result.output
    
    def test_help_text_undo(self):
        """Test undo help text."""
        result = self.runner.invoke(cli, ['undo', '--help'])
        
        assert result.exit_code == 0
        assert 'Undo' in result.output or 'undo' in result.output
    
    def test_version_option(self):
        """Test version option."""
        result = self.runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert '0.1.0' in result.output
    
    def test_global_flags_combination(self):
        """Test combination of global flags."""
        result = self.runner.invoke(cli, [
            'organize-type',
            '--dry-run',
            '--verbose',
            '--pattern', '*.txt',
            '--target-dir', self.temp_dir
        ])
        
        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
    
    def test_invalid_command(self):
        """Test invalid command."""
        result = self.runner.invoke(cli, ['invalid-command'])
        
        assert result.exit_code != 0
        assert 'No such command' in result.output or 'Error' in result.output
