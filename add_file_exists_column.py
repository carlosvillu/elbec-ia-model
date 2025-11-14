#!/usr/bin/env python3
"""
Script to add a 'File Exists' column to consignas.csv files.
Checks if the files referenced in the 'File ID' column exist in the directory.

Usage:
    python add_file_exists_column.py <directory> [--force]

Example:
    python add_file_exists_column.py data/POS1
    python add_file_exists_column.py data/POS1 --force
"""

import csv
import sys
from pathlib import Path


def add_file_exists_column(directory, force=False):
    """
    Add a 'File Exists' column to the consignas.csv file in the specified directory.

    Args:
        directory: Path to the directory containing consignas.csv and .txt files
    """
    dir_path = Path(directory)
    csv_path = dir_path / "consignas.csv"

    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)

    if not csv_path.exists():
        print(f"Error: File '{csv_path}' does not exist")
        sys.exit(1)

    # Read the CSV file
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Check if 'File Exists' column already exists
        if 'File Exists' in fieldnames:
            if not force:
                print(f"Warning: 'File Exists' column already exists in {csv_path}")
                response = input("Do you want to overwrite it? (y/n): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    sys.exit(0)
            # Remove the existing column from fieldnames for reconstruction
            new_fieldnames = [f for f in fieldnames if f != 'File Exists']
        else:
            new_fieldnames = list(fieldnames)

        # Add 'File Exists' to fieldnames
        new_fieldnames.append('File Exists')

        for row in reader:
            # Try both 'File ID' and 'FileID' column names
            file_id = row.get('File ID') or row.get('FileID', '')
            if file_id:
                file_path = dir_path / file_id
                row['File Exists'] = 'true' if file_path.exists() else 'false'
            else:
                row['File Exists'] = 'false'
            rows.append(row)

    # Write the updated CSV file
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print statistics
    total = len(rows)
    existing = sum(1 for row in rows if row['File Exists'] == 'true')
    missing = total - existing

    print(f"\nProcessing complete for {csv_path}")
    print(f"Total rows: {total}")
    print(f"Files existing: {existing}")
    print(f"Files missing: {missing}")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python add_file_exists_column.py <directory> [--force]")
        print("\nExample:")
        print("  python add_file_exists_column.py data/POS1")
        print("  python add_file_exists_column.py data/POS1 --force")
        sys.exit(1)

    directory = sys.argv[1]
    force = len(sys.argv) == 3 and sys.argv[2] == '--force'
    add_file_exists_column(directory, force)


if __name__ == "__main__":
    main()
