# ELBEC IA Model

Text normalization and data processing tools for ELBEC Catalan text corpus. This repository contains Python scripts for processing and validating Catalan text files used in linguistic and AI research.

## Overview

This project provides utilities for:
- Normalizing Catalan text files by applying standardized transformations
- Validating file references in CSV datasets
- Processing text corpora organized in structured directories

## Scripts

### 1. evaluate_texts.py

Evaluates all normalized texts (_NOR.txt files) using a deployed evaluation API (typically on RunPod.io).

**Features:**
- Processes all `_NOR.txt` files in POS1, POS2, and PRE folders
- Extracts curso (grade level) dynamically from text ID
- Submits texts in batches to the evaluation API
- Streams results in real-time using Server-Sent Events
- Generates CSV files with evaluation results (nota and feedback)
- Supports configurable batch sizes and folder selection
- Health check validation before processing

**Usage:**
```bash
# Install dependencies first
pip install -r requirements.txt

# Basic usage
python evaluate_texts.py --api-host https://your-runpod-instance.proxy.runpod.net

# Custom batch size
python evaluate_texts.py --api-host https://api.example.com --batch-size 20

# Process specific folders only
python evaluate_texts.py --api-host https://api.example.com --folders POS1 POS2

# Skip health check
python evaluate_texts.py --api-host https://api.example.com --skip-health-check

# Don't combine results
python evaluate_texts.py --api-host https://api.example.com --no-combine
```

**Output:**
- Per-folder CSVs: `data/{folder}/results_{folder}_{timestamp}.csv`
- Combined CSV: `results_all_folders_{timestamp}.csv` (unless `--no-combine` is used)
- Columns: folder, id, filename, curso, consigna, nota, feedback

**Grade Level Extraction:**
The curso is automatically extracted from the text ID (third character):
- `POS1_11410003_NOR.txt` → ID: `11410003` → curso: `4t ESO`
- `POS1_11510082_NOR.txt` → ID: `11510082` → curso: `5è ESO`

### 2. evaluate_texts.ipynb

Jupyter notebook version of the evaluation script with the same functionality. Provides an interactive environment for text evaluation with detailed progress visualization.

**Usage:**
```bash
jupyter notebook evaluate_texts.ipynb
```

Update the `API_HOST` variable in the first cell and run all cells sequentially.

### 3. normalize_texts.py

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

### 4. add_file_exists_column.py

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
- For `evaluate_texts.py` and `evaluate_texts.ipynb`:
  - `requests>=2.31.0`
  - `pandas>=2.0.0`
  - Install with: `pip install -r requirements.txt`
- For other scripts: No external dependencies required (uses only standard library)

## License

This project is part of ELBEC research work.

## Contributing

This is a research project. For questions or suggestions, please open an issue.
