"""Command-line interface for File Organizer."""

import sys
from pathlib import Path
from typing import Optional

import click

from src.models import Config, OperationType, CaseType, OperationResults
from src.orchestrator import Orchestrator, OrchestratorError
from src.undo_manager import UndoManager
from src.filesystem import FileSystem


# Global options that apply to all commands
def add_global_options(func):
    """Decorator to add common global options to commands."""
    func = click.option(
        '--dry-run',
        is_flag=True,
        help='Preview changes without executing them'
    )(func)
    func = click.option(
        '--verbose', '-v',
        is_flag=True,
        help='Display detailed information for each operation'
    )(func)
    func = click.option(
        '--target-dir', '-d',
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        default=Path.cwd(),
        help='Target directory to operate on (default: current directory)'
    )(func)
    func = click.option(
        '--pattern', '-p',
        default='*',
        help='File pattern to match (glob syntax, default: *)'
    )(func)
    return func


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    File Organizer - Automate file management tasks.
    
    Organize, rename, and manage files with ease using powerful automation rules.
    """
    pass


@cli.command('organize-type')
@add_global_options
def organize_type(dry_run: bool, verbose: bool, target_dir: Path, pattern: str):
    """
    Organize files by type into categorized subdirectories.
    
    Files are automatically categorized into folders like Documents, Images,
    Videos, Audio, Archives, and Code based on their file extensions.
    
    Example:
        file-organizer organize-type --target-dir ~/Downloads
    """
    config = Config(
        target_dir=target_dir,
        operation_type=OperationType.ORGANIZE_TYPE,
        dry_run=dry_run,
        verbose=verbose,
        file_pattern=pattern
    )
    
    execute_operation(config)


@cli.command('organize-date')
@add_global_options
@click.option(
    '--format', '-f',
    'date_format',
    type=click.Choice(['YYYY/MM', 'YYYY-MM'], case_sensitive=False),
    default='YYYY/MM',
    help='Date folder format (default: YYYY/MM)'
)
def organize_date(
    dry_run: bool,
    verbose: bool,
    target_dir: Path,
    pattern: str,
    date_format: str
):
    """
    Organize files by date into year/month folder structures.
    
    Files are grouped by their modification date. If modification date is
    unavailable, creation date is used as fallback.
    
    Example:
        file-organizer organize-date --format YYYY-MM --target-dir ~/Photos
    """
    config = Config(
        target_dir=target_dir,
        operation_type=OperationType.ORGANIZE_DATE,
        dry_run=dry_run,
        verbose=verbose,
        file_pattern=pattern,
        date_format=date_format
    )
    
    execute_operation(config)


@cli.command('rename')
@add_global_options
@click.option(
    '--find',
    help='Pattern to find in filenames (for find-and-replace)'
)
@click.option(
    '--replace',
    help='Replacement text (for find-and-replace)'
)
@click.option(
    '--sequential',
    help='Sequential numbering template (e.g., "file_{}.txt")'
)
@click.option(
    '--case',
    type=click.Choice(['lowercase', 'uppercase', 'title'], case_sensitive=False),
    help='Case transformation to apply'
)
@click.option(
    '--prefix',
    help='Prefix to add to filenames'
)
@click.option(
    '--suffix',
    help='Suffix to add to filenames (before extension)'
)
def rename(
    dry_run: bool,
    verbose: bool,
    target_dir: Path,
    pattern: str,
    find: Optional[str],
    replace: Optional[str],
    sequential: Optional[str],
    case: Optional[str],
    prefix: Optional[str],
    suffix: Optional[str]
):
    """
    Rename files using various transformation methods.
    
    Supports find-and-replace, sequential numbering, case transformation,
    and prefix/suffix addition. Only one rename method can be used at a time.
    
    Examples:
        file-organizer rename --find "old" --replace "new"
        file-organizer rename --sequential "photo_{}.jpg"
        file-organizer rename --case lowercase
        file-organizer rename --prefix "backup_"
    """
    # Validate find-and-replace pairing first
    if find and replace is None:
        click.echo("Error: --replace is required when using --find", err=True)
        sys.exit(1)
    
    if replace is not None and not find:
        click.echo("Error: --find is required when using --replace", err=True)
        sys.exit(1)
    
    # Validate that exactly one rename method is specified
    methods = [
        bool(find and replace is not None),
        bool(sequential is not None),
        bool(case is not None),
        bool(prefix or suffix)
    ]
    
    if sum(methods) == 0:
        click.echo("Error: Must specify one rename method", err=True)
        click.echo("Use --find/--replace, --sequential, --case, or --prefix/--suffix", err=True)
        sys.exit(1)
    
    if sum(methods) > 1:
        click.echo("Error: Only one rename method can be used at a time", err=True)
        sys.exit(1)
    
    # Convert case string to CaseType enum
    case_type = None
    if case:
        case_type = CaseType[case.upper()]
    
    config = Config(
        target_dir=target_dir,
        operation_type=OperationType.RENAME,
        dry_run=dry_run,
        verbose=verbose,
        file_pattern=pattern,
        pattern=find,
        replacement=replace,
        sequential_template=sequential,
        case_type=case_type,
        prefix=prefix,
        suffix=suffix
    )
    
    execute_operation(config)


@cli.command('custom')
@add_global_options
@click.option(
    '--rules', '-r',
    'rules_file',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help='Path to rules configuration file (YAML or JSON)'
)
def custom(
    dry_run: bool,
    verbose: bool,
    target_dir: Path,
    pattern: str,
    rules_file: Path
):
    """
    Organize files using custom rules from a configuration file.
    
    Rules define patterns to match files and destinations to move them to.
    Multiple rules can be specified with priority ordering.
    
    Example:
        file-organizer custom --rules my_rules.yaml --target-dir ~/Documents
    """
    config = Config(
        target_dir=target_dir,
        operation_type=OperationType.CUSTOM,
        dry_run=dry_run,
        verbose=verbose,
        file_pattern=pattern,
        rules_file=rules_file
    )
    
    execute_operation(config)


@cli.command('undo')
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Display detailed information for each operation'
)
def undo(verbose: bool):
    """
    Undo the most recent file organization operation.
    
    Restores files to their original locations and names. If some files
    cannot be restored, reports failures and continues with remaining files.
    
    Example:
        file-organizer undo
    """
    try:
        filesystem = FileSystem()
        undo_manager = UndoManager(filesystem)
        
        # Check if there's anything to undo
        if not undo_manager.has_undo_log():
            click.echo("No recent operations to undo.")
            return
        
        # Perform undo
        results = undo_manager.undo()
        
        # Display results
        display_results(results, verbose, is_undo=True)
        
    except Exception as e:
        click.echo(f"Error during undo: {e}", err=True)
        sys.exit(1)


def execute_operation(config: Config):
    """
    Execute a file operation with the given configuration.
    
    Args:
        config: Configuration object specifying the operation
    """
    try:
        orchestrator = Orchestrator()
        
        # Show dry-run notice
        if config.dry_run:
            click.echo("=== DRY RUN MODE - No files will be modified ===\n")
        
        # Execute operation
        results = orchestrator.execute(config)
        
        # Display results
        display_results(results, config.verbose, config.dry_run)
        
    except OrchestratorError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


def display_results(
    results: OperationResults,
    verbose: bool,
    dry_run: bool = False,
    is_undo: bool = False
):
    """
    Display operation results to the user.
    
    Args:
        results: OperationResults object with operation summary
        verbose: Whether to show detailed per-file information
        dry_run: Whether this was a dry-run operation
        is_undo: Whether this was an undo operation
    """
    # Show progress for operations with >10 files
    total_ops = len(results.operations)
    
    if verbose and total_ops > 0:
        click.echo("\nDetailed Operations:")
        click.echo("-" * 80)
        
        for i, operation in enumerate(results.operations, 1):
            # Show progress indicator for >10 files
            if total_ops > 10:
                click.echo(f"[{i}/{total_ops}] ", nl=False)
            
            # Determine status
            if operation.executed or dry_run:
                status = "WOULD EXECUTE" if dry_run else "SUCCESS"
                status_color = "yellow" if dry_run else "green"
            else:
                status = "SKIPPED"
                status_color = "blue"
            
            # Display operation details
            click.echo(
                f"{click.style(status, fg=status_color)} | "
                f"{operation.operation_type.value.upper()} | "
                f"{operation.source_path} → {operation.dest_path}"
            )
        
        click.echo("-" * 80)
    
    # Display summary
    click.echo("\n" + "=" * 80)
    
    if dry_run:
        click.echo("DRY RUN SUMMARY")
    elif is_undo:
        click.echo("UNDO SUMMARY")
    else:
        click.echo("OPERATION SUMMARY")
    
    click.echo("=" * 80)
    
    click.echo(f"Total operations: {total_ops}")
    click.echo(
        f"{click.style('Successful:', fg='green')} {results.successful}"
    )
    
    if results.skipped > 0:
        click.echo(
            f"{click.style('Skipped:', fg='blue')} {results.skipped}"
        )
    
    if results.errors:
        click.echo(
            f"{click.style('Errors:', fg='red')} {len(results.errors)}"
        )
        click.echo("\nError Details:")
        for file_path, error_msg in results.errors:
            click.echo(f"  • {file_path}: {error_msg}")
    
    click.echo("=" * 80)
    
    # Show next steps
    if not dry_run and not is_undo and results.successful > 0:
        click.echo("\nTo undo this operation, run: file-organizer undo")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
