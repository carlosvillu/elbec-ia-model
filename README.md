# ELBEC IA Model

Text normalization and data processing tools for ELBEC Catalan text corpus. This repository contains Python scripts for processing and validating Catalan text files used in linguistic and AI research.

## Overview

This project provides utilities for:
- Normalizing Catalan text files by applying standardized transformations
- Validating file references in CSV datasets
- Processing text corpora organized in structured directories

## Scripts

### 1. normalize_texts.py

Normalizes Catalan text files by applying transformations compatible with ELBECTexthandler's PlainTextToPlainTextNormalizedMapper.js.

**Features:**
- Removes annotation markers (@o, @s)
- Replaces Catalan text markers with standard punctuation
  - `[% interrogació]` → `?`
  - `[% exclamació]` → `!`
  - `[% suspensius]` → `...`
- Handles paragraph breaks (`[% AP]`, `[% punt AP]`)
- Removes all content within brackets
- Normalizes whitespace

**Usage:**
```bash
python normalize_texts.py
```

The script processes all `.txt` files in the `data/POS1`, `data/POS2`, and `data/PRE` directories, creating normalized versions with the `_NOR` suffix.

**Example:**
- Input: `data/POS1/document.txt`
- Output: `data/POS1/document_NOR.txt`

### 2. add_file_exists_column.py

Validates file references in CSV files by checking if the referenced files exist in the filesystem.

**Features:**
- Adds a "File Exists" column to `consignas.csv` files
- Supports both `File ID` and `FileID` column names
- Provides statistics on existing vs. missing files
- Safe mode with confirmation prompt (unless `--force` is used)

**Usage:**
```bash
# Interactive mode (asks for confirmation if column exists)
python add_file_exists_column.py data/POS1

# Force mode (overwrites existing column without prompting)
python add_file_exists_column.py data/POS1 --force
```

**Output:**
```
Processing complete for data/POS1/consignas.csv
Total rows: 150
Files existing: 145
Files missing: 5
```

## Data Structure

The project expects the following directory structure:

```
elbec-ia-model/
├── data/
│   ├── POS1/
│   │   ├── consignas.csv
│   │   └── *.txt
│   ├── POS2/
│   │   ├── consignas.csv
│   │   └── *.txt
│   └── PRE/
│       ├── consignas.csv
│       └── *.txt
├── normalize_texts.py
└── add_file_exists_column.py
```

## Requirements

- Python 3.6+
- No external dependencies required (uses only standard library)

## License

This project is part of ELBEC research work.

## Contributing

This is a research project. For questions or suggestions, please open an issue.
