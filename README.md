# File Organizer

A powerful command-line tool for automating tedious file management tasks. Organize files by type or date, bulk rename with patterns, and create custom organization rules - all with built-in safety features like dry-run mode and undo capabilities.

## Features

- **Organize by Type**: Automatically categorize files into folders (Documents, Images, Videos, Audio, Archives, Code)
- **Organize by Date**: Sort files into year/month folder structures based on modification dates
- **Bulk Rename**: Transform filenames with find-and-replace, sequential numbering, case changes, or prefix/suffix
- **Custom Rules**: Define your own organization patterns with YAML/JSON configuration files
- **Dry-Run Mode**: Preview all changes before executing them
- **Undo Support**: Reverse any operation to restore files to their original state
- **Progress Tracking**: Visual feedback for operations with many files
- **Error Resilience**: Continue processing even when individual files fail

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd file-organizer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package:
```bash
pip install -e .
```

## Quick Start

```bash
# Preview organizing your Downloads folder by file type
file-organizer organize-type --target-dir ~/Downloads --dry-run

# Actually organize the files
file-organizer organize-type --target-dir ~/Downloads

# Undo if you change your mind
file-organizer undo
```

## Usage

### Global Options

These options work with all commands:

- `--dry-run`: Preview changes without modifying files
- `--verbose, -v`: Show detailed information for each operation
- `--target-dir, -d PATH`: Directory to operate on (default: current directory)
- `--pattern, -p PATTERN`: File pattern to match using glob syntax (default: `*`)

### Commands

#### organize-type

Organize files by type into categorized subdirectories.

```bash
file-organizer organize-type [OPTIONS]
```

**Examples:**
```bash
# Organize all files in Downloads
file-organizer organize-type --target-dir ~/Downloads

# Organize only PDF files
file-organizer organize-type --pattern "*.pdf" --dry-run

# Organize with verbose output
file-organizer organize-type -v --target-dir ~/Documents
```

**File Categories:**
- **Documents**: .pdf, .doc, .docx, .txt, .rtf, .odt, .xls, .xlsx, .ppt, .pptx
- **Images**: .jpg, .jpeg, .png, .gif, .bmp, .svg, .webp, .ico
- **Videos**: .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm
- **Audio**: .mp3, .wav, .flac, .aac, .ogg, .wma, .m4a
- **Archives**: .zip, .tar, .gz, .rar, .7z, .bz2, .xz
- **Code**: .py, .js, .java, .cpp, .c, .h, .html, .css, .json, .xml, .yaml, .yml

#### organize-date

Organize files by date into year/month folder structures.

```bash
file-organizer organize-date [OPTIONS]
```

**Options:**
- `--format, -f FORMAT`: Date folder format - `YYYY/MM` or `YYYY-MM` (default: `YYYY/MM`)

**Examples:**
```bash
# Organize photos by date
file-organizer organize-date --target-dir ~/Photos

# Use dash format for folders
file-organizer organize-date --format YYYY-MM --target-dir ~/Documents

# Organize only image files by date
file-organizer organize-date --pattern "*.{jpg,png}" --target-dir ~/Pictures
```

#### rename

Rename files using various transformation methods.

```bash
file-organizer rename [OPTIONS]
```

**Options (use exactly one):**
- `--find TEXT --replace TEXT`: Find and replace text in filenames
- `--sequential TEMPLATE`: Rename with sequential numbers (e.g., `photo_{}.jpg`)
- `--case CASE`: Transform case - `lowercase`, `uppercase`, or `title`
- `--prefix TEXT`: Add prefix to filenames
- `--suffix TEXT`: Add suffix before extension

**Examples:**
```bash
# Find and replace
file-organizer rename --find "IMG" --replace "Photo" --target-dir ~/Pictures

# Sequential numbering
file-organizer rename --sequential "vacation_2024_{}.jpg" --pattern "*.jpg"

# Convert to lowercase
file-organizer rename --case lowercase --target-dir ~/Documents

# Add prefix
file-organizer rename --prefix "backup_" --pattern "*.txt"

# Add suffix
file-organizer rename --suffix "_old" --pattern "*.log"
```

#### custom

Organize files using custom rules from a configuration file.

```bash
file-organizer custom --rules RULES_FILE [OPTIONS]
```

**Options:**
- `--rules, -r PATH`: Path to YAML or JSON rules file (required)

**Examples:**
```bash
# Apply custom rules
file-organizer custom --rules my_rules.yaml --target-dir ~/Downloads

# Preview custom organization
file-organizer custom -r example_rules.yaml --dry-run -v
```

**Rules File Format:**

See `example_rules.yaml` for a complete example. Basic structure:

```yaml
rules:
  - name: Rule name
    pattern: "*.pdf"  # Glob pattern or "regex:..." for regex
    destination: documents/pdfs  # Relative to target directory
    priority: 1  # Lower numbers = higher priority
```

#### undo

Undo the most recent file organization operation.

```bash
file-organizer undo [OPTIONS]
```

**Options:**
- `--verbose, -v`: Show detailed information for each restored file

**Examples:**
```bash
# Undo last operation
file-organizer undo

# Undo with details
file-organizer undo --verbose
```

## Example Workflows

### Workflow 1: Organize Messy Downloads Folder

```bash
# Step 1: Preview what will happen
file-organizer organize-type --target-dir ~/Downloads --dry-run --verbose

# Step 2: Execute the organization
file-organizer organize-type --target-dir ~/Downloads

# Step 3: If you don't like it, undo
file-organizer undo
```

### Workflow 2: Bulk Rename Photos from Camera

```bash
# Step 1: Preview sequential renaming
file-organizer rename --sequential "vacation_hawaii_{}.jpg" \
  --pattern "DSC*.jpg" --target-dir ~/Photos/Hawaii --dry-run

# Step 2: Apply the rename
file-organizer rename --sequential "vacation_hawaii_{}.jpg" \
  --pattern "DSC*.jpg" --target-dir ~/Photos/Hawaii
```

### Workflow 3: Archive Old Files by Date

```bash
# Step 1: Organize files by date
file-organizer organize-date --format YYYY-MM --target-dir ~/Documents

# Step 2: Rename folders to add "Archive_" prefix
file-organizer rename --prefix "Archive_" --target-dir ~/Documents
```

### Workflow 4: Custom Project Organization

Create a `project_rules.yaml`:

```yaml
rules:
  - name: Source code
    pattern: "*.{py,js,java,cpp}"
    destination: src
    priority: 1
  
  - name: Test files
    pattern: "test_*.py"
    destination: tests
    priority: 2
  
  - name: Documentation
    pattern: "*.{md,txt,rst}"
    destination: docs
    priority: 3
  
  - name: Configuration
    pattern: "*.{yaml,yml,json,toml,ini}"
    destination: config
    priority: 4
```

Apply the rules:

```bash
file-organizer custom --rules project_rules.yaml --target-dir ~/my_project --dry-run
file-organizer custom --rules project_rules.yaml --target-dir ~/my_project
```

### Workflow 5: Clean Up Screenshot Files

```bash
# Step 1: Rename screenshots to lowercase
file-organizer rename --case lowercase --pattern "Screenshot*" --target-dir ~/Desktop

# Step 2: Add date prefix
file-organizer rename --prefix "2024_" --pattern "screenshot*" --target-dir ~/Desktop

# Step 3: Move to organized folder
file-organizer organize-date --pattern "2024_screenshot*" --target-dir ~/Desktop
```

## Safety Features

### Dry-Run Mode

Always test operations first with `--dry-run`:

```bash
file-organizer organize-type --target-dir ~/Important --dry-run --verbose
```

This shows exactly what will happen without modifying any files.

### Undo Support

Every operation creates an undo log. If something goes wrong:

```bash
file-organizer undo
```

Files are restored to their original locations and names.

### Conflict Resolution

When a file with the same name exists at the destination, the tool automatically appends a numeric suffix (`_1`, `_2`, etc.) to prevent data loss.

### Error Resilience

If an error occurs with one file, the tool logs it and continues processing remaining files. All errors are reported at the end.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/ --ignore=tests/property_tests/

# Run property-based tests only
pytest tests/property_tests/

# Run with coverage
pytest --cov=src --cov-report=html
```

### Project Structure

```
.
├── src/                      # Source code
│   ├── cli.py               # Command-line interface
│   ├── orchestrator.py      # Operation coordination
│   ├── organizer.py         # File organization logic
│   ├── renamer.py           # File renaming logic
│   ├── rule_engine.py       # Custom rule processing
│   ├── undo_manager.py      # Undo functionality
│   ├── filesystem.py        # File system abstraction
│   └── models.py            # Data models
├── tests/                    # Test suite
│   ├── test_*.py            # Unit tests
│   └── property_tests/      # Property-based tests
│       └── test_*_properties.py
├── .kiro/specs/             # Feature specifications
│   └── file-organizer/
│       ├── requirements.md  # Requirements document
│       ├── design.md        # Design document
│       └── tasks.md         # Implementation tasks
├── example_rules.yaml       # Example configuration
├── requirements.txt         # Python dependencies
├── setup.py                # Package configuration
└── README.md               # This file
```

## Troubleshooting

### Permission Errors

If you get permission errors:

```bash
# Check file permissions
ls -la ~/target-directory

# Run with appropriate permissions or change ownership
sudo chown -R $USER:$USER ~/target-directory
```

### Pattern Matching Issues

Use quotes around patterns with special characters:

```bash
# Correct
file-organizer rename --pattern "*.{jpg,png}" --case lowercase

# Incorrect (shell may expand the pattern)
file-organizer rename --pattern *.jpg --case lowercase
```

### Undo Not Available

Undo logs are stored in `~/.file_organizer/undo_log.json`. If this file is deleted or corrupted, undo won't work. The log is overwritten with each new operation.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions, please open an issue on the project repository.
