#!/usr/bin/env python3
"""
Text Normalization Script

This script normalizes Catalan text files by applying the same transformations
as the UABTexthandler PlanTextToPlainTextNormalizedMapper.js, plus an additional
step to remove content within brackets.

Usage:
    python normalize_texts.py
"""

import os
import re
from pathlib import Path


def normalize_text(text):
    """
    Apply all normalization transformations to the input text.

    The transformations are applied in the following order:
    1. Remove @o markers
    2. Remove @s markers (including @s:word patterns)
    3. Replace space-dot-newline with single spaces
    4. Replace [% interrogació] with ?
    5. Replace [% exclamació] with !
    6. Replace [% suspensius] with ...
    7. Replace [% punt AP] with period and double newlines
    8. Replace [% AP] with double newlines
    9. Remove everything between brackets [...] (NEW)
    10. Trim whitespace

    Args:
        text (str): The input text to normalize

    Returns:
        str: The normalized text
    """
    # 1. Remove @o markers
    text = text.replace('@o', '')

    # 2. Remove @s markers (including @s:\w+ patterns)
    text = re.sub(r'@s(?::\w+)?', '', text)

    # 3. Replace space-dot-newline with single spaces
    text = re.sub(r' \.\n', ' ', text)

    # 4. Replace [% interrogació] with ?
    text = text.replace('[% interrogació]', '?')

    # 5. Replace [% exclamació] with !
    text = text.replace('[% exclamació]', '!')

    # 6. Replace [% suspensius] with ...
    text = text.replace('[% suspensius]', '...')

    # 7. Replace [% punt AP] surrounded by spaces with period and double newlines
    text = re.sub(r' \[% punt AP\] ', '.\n\n', text)

    # 8. Replace [% AP] (with optional spacing) with double newlines
    text = re.sub(r'\s*\[% AP\]\s*', '\n\n', text)

    # 9. Remove everything between brackets [...] (including the brackets)
    text = re.sub(r'\[.*?\]', '', text)

    # 10. Trim whitespace
    text = text.strip()

    return text


def process_file(input_path):
    """
    Process a single file: read, normalize, and save with _NOR suffix.

    Args:
        input_path (Path): Path to the input file

    Returns:
        Path: Path to the output file
    """
    # Read the original file
    with open(input_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # Apply normalization
    normalized_text = normalize_text(original_text)

    # Create output filename with _NOR suffix
    output_filename = input_path.stem + '_NOR' + input_path.suffix
    output_path = input_path.parent / output_filename

    # Write the normalized text
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(normalized_text)

    return output_path


def main():
    """
    Main function to process all .txt files in data directories.
    """
    # Define the data directory
    data_dir = Path(__file__).parent / 'data'

    # Define subdirectories to process
    subdirs = ['POS1', 'POS2', 'PRE']

    total_files = 0
    processed_files = 0

    print("Starting text normalization...")
    print("=" * 60)

    for subdir in subdirs:
        subdir_path = data_dir / subdir

        if not subdir_path.exists():
            print(f"Warning: Directory {subdir_path} does not exist. Skipping.")
            continue

        # Find all .txt files that don't end with _NOR.txt
        txt_files = [f for f in subdir_path.glob('*.txt') if not f.stem.endswith('_NOR')]

        print(f"\nProcessing {subdir}/ ({len(txt_files)} files)...")

        for txt_file in txt_files:
            total_files += 1
            try:
                output_file = process_file(txt_file)
                processed_files += 1

                if processed_files % 100 == 0:
                    print(f"  Processed {processed_files}/{total_files} files...")

            except Exception as e:
                print(f"  Error processing {txt_file.name}: {e}")

    print("\n" + "=" * 60)
    print(f"Normalization complete!")
    print(f"Total files processed: {processed_files}/{total_files}")
    print(f"Normalized files saved with '_NOR' suffix")


if __name__ == '__main__':
    main()
