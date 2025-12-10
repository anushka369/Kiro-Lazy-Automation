# File Organizer - Quick Reference

A quick reference guide for common File Organizer commands and patterns.

## Common Commands

### Organize Files by Type
```bash
# Basic usage
file-organizer organize-type --target-dir ~/Downloads

# Preview first
file-organizer organize-type --target-dir ~/Downloads --dry-run

# Only specific files
file-organizer organize-type --pattern "*.pdf" --target-dir ~/Documents
```

### Organize Files by Date
```bash
# Default format (YYYY/MM)
file-organizer organize-date --target-dir ~/Photos

# Dash format (YYYY-MM)
file-organizer organize-date --format YYYY-MM --target-dir ~/Documents

# Only images
file-organizer organize-date --pattern "*.{jpg,png}" --target-dir ~/Pictures
```

### Rename Files

#### Find and Replace
```bash
file-organizer rename --find "old_name" --replace "new_name"
```

#### Sequential Numbering
```bash
file-organizer rename --sequential "photo_{}.jpg" --pattern "*.jpg"
file-organizer rename --sequential "file_{}.txt" --target-dir ~/Documents
```

#### Case Transformation
```bash
file-organizer rename --case lowercase
file-organizer rename --case uppercase
file-organizer rename --case title
```

#### Add Prefix/Suffix
```bash
file-organizer rename --prefix "backup_"
file-organizer rename --suffix "_old"
file-organizer rename --prefix "2024_" --suffix "_archive"
```

### Custom Rules
```bash
file-organizer custom --rules my_rules.yaml --target-dir ~/Downloads
file-organizer custom -r example_rules.yaml --dry-run --verbose
```

### Undo
```bash
file-organizer undo
file-organizer undo --verbose
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | - | Preview changes without executing |
| `--verbose` | `-v` | Show detailed per-file information |
| `--target-dir PATH` | `-d PATH` | Directory to operate on |
| `--pattern GLOB` | `-p GLOB` | File pattern to match |

## File Type Categories

| Category | Extensions |
|----------|------------|
| **Documents** | .pdf, .doc, .docx, .txt, .rtf, .odt, .xls, .xlsx, .ppt, .pptx |
| **Images** | .jpg, .jpeg, .png, .gif, .bmp, .svg, .webp, .ico |
| **Videos** | .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm |
| **Audio** | .mp3, .wav, .flac, .aac, .ogg, .wma, .m4a |
| **Archives** | .zip, .tar, .gz, .rar, .7z, .bz2, .xz |
| **Code** | .py, .js, .java, .cpp, .c, .h, .html, .css, .json, .xml, .yaml, .yml |

## Pattern Matching

### Glob Patterns
```bash
# All files
--pattern "*"

# Specific extension
--pattern "*.pdf"

# Multiple extensions
--pattern "*.{jpg,png,gif}"

# Files starting with "test"
--pattern "test*"

# Files containing "report"
--pattern "*report*"

# Single character wildcard
--pattern "file?.txt"  # Matches file1.txt, fileA.txt, etc.
```

### Regex Patterns (in rules files)
```yaml
# Case-insensitive matching
pattern: "regex:(?i)screenshot.*\\.png"

# Files starting with numbers
pattern: "regex:^[0-9]+.*"

# Files with dates (YYYY-MM-DD)
pattern: "regex:.*[0-9]{4}-[0-9]{2}-[0-9]{2}.*"

# Invoice or receipt files
pattern: "regex:(?i)(invoice|receipt).*\\.(pdf|png)"
```

## Rules File Template

```yaml
rules:
  - name: Rule description
    pattern: "*.ext"           # Glob or "regex:..." pattern
    destination: folder/path   # Relative to target directory
    priority: 1                # Lower = higher priority
  
  - name: Another rule
    pattern: "regex:pattern"
    destination: another/folder
    priority: 2
```

## Common Workflows

### Clean Downloads Folder
```bash
# 1. Preview
file-organizer organize-type --target-dir ~/Downloads --dry-run -v

# 2. Execute
file-organizer organize-type --target-dir ~/Downloads

# 3. Undo if needed
file-organizer undo
```

### Rename Camera Photos
```bash
# Preview
file-organizer rename --sequential "vacation_{}.jpg" \
  --pattern "IMG_*.jpg" --dry-run

# Execute
file-organizer rename --sequential "vacation_{}.jpg" \
  --pattern "IMG_*.jpg"
```

### Archive Old Files
```bash
# Organize by date
file-organizer organize-date --format YYYY-MM --target-dir ~/Documents

# Add archive prefix to folders
file-organizer rename --prefix "Archive_" --target-dir ~/Documents
```

### Project Organization
```bash
# Create rules file (project_rules.yaml)
# Then apply
file-organizer custom --rules project_rules.yaml --dry-run
file-organizer custom --rules project_rules.yaml
```

## Tips & Tricks

### Always Preview First
```bash
# Add --dry-run to any command
file-organizer organize-type --dry-run --verbose
```

### Use Verbose Mode for Details
```bash
# See exactly what happens to each file
file-organizer organize-type -v
```

### Combine with Shell Commands
```bash
# Count files before organizing
ls -1 ~/Downloads | wc -l

# Organize
file-organizer organize-type --target-dir ~/Downloads

# Count files after
ls -1 ~/Downloads | wc -l
```

### Test Patterns
```bash
# Use ls to test glob patterns first
ls ~/Downloads/*.pdf
ls ~/Downloads/*.{jpg,png}

# Then use in file-organizer
file-organizer organize-type --pattern "*.pdf"
```

### Backup Before Major Operations
```bash
# Create backup
cp -r ~/Important ~/Important_backup

# Run operation
file-organizer organize-type --target-dir ~/Important

# If something goes wrong
file-organizer undo
# or restore from backup
```

## Troubleshooting

### Permission Denied
```bash
# Check permissions
ls -la ~/target-directory

# Fix ownership
sudo chown -R $USER:$USER ~/target-directory
```

### Pattern Not Matching
```bash
# Use quotes around patterns
file-organizer rename --pattern "*.{jpg,png}" --case lowercase

# Test pattern with ls first
ls *.{jpg,png}
```

### Undo Not Available
```bash
# Check if undo log exists
ls -la ~/.file_organizer/undo_log.json

# Undo only works for the most recent operation
```

### Dry-Run Shows Nothing
```bash
# Check if files match pattern
ls --pattern-you-used

# Check target directory
ls -la ~/target-directory

# Use verbose mode
file-organizer organize-type --dry-run --verbose
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error occurred |

## Environment

### Undo Log Location
```
~/.file_organizer/undo_log.json
```

### Configuration Files
- YAML: `.yaml` or `.yml` extension
- JSON: `.json` extension

## Getting Help

```bash
# General help
file-organizer --help

# Command-specific help
file-organizer organize-type --help
file-organizer rename --help
file-organizer custom --help
file-organizer undo --help

# Version
file-organizer --version
```
