#!/usr/bin/env python3
"""
Text Evaluation Script

Evaluates all normalized texts (_NOR.txt files) using the deployed evaluation API.
For each folder (POS1, POS2, PRE), it reads consignas, processes texts, and saves results.

Usage:
    python evaluate_texts.py --api-host https://your-runpod-instance.proxy.runpod.net
    python evaluate_texts.py --api-host https://api.example.com --batch-size 20
    python evaluate_texts.py --api-host http://localhost:8000 --folders POS1 POS2
"""

import argparse
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import requests
import pandas as pd


# Configuration
DEFAULT_API_PORT = "8000"
DEFAULT_FOLDERS = ['POS1', 'POS2', 'PRE']
DEFAULT_DATA_DIR = 'data'
DEFAULT_BATCH_SIZE = 10


def load_consignas_csv(folder_path: Path) -> pd.DataFrame:
    """
    Load the consignas CSV file for a given folder.
    Handles different column name variations (File ID vs FileID, Consigna vs TEXTpost2)
    """
    csv_path = folder_path / 'consignas.csv'
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    # Normalize column names
    if 'File ID' in df.columns:
        df.rename(columns={'File ID': 'FileID'}, inplace=True)
    if 'TEXTpost2' in df.columns:
        df.rename(columns={'TEXTpost2': 'Consigna'}, inplace=True)

    return df


def get_nor_files(folder_path: Path) -> List[Path]:
    """
    Get all _NOR.txt files in a folder, sorted by name.
    """
    nor_files = sorted(folder_path.glob('*_NOR.txt'))
    return nor_files


def extract_id_from_filename(filename: str) -> Optional[str]:
    """
    Extract the ID from a filename like 'POS1_11410001_NOR.txt' -> '11410001'
    """
    match = re.search(r'_(\d+)_NOR\.txt$', filename)
    if match:
        return match.group(1)
    return None


def extract_curso_from_id(text_id: str) -> str:
    """
    Extract the curso (grade level) from the text ID.
    The third character (index 2) of the ID represents the grade level.

    Examples:
        '11410003' -> '4' -> '4t ESO'
        '11510082' -> '5' -> '5è ESO'
    """
    if not text_id or len(text_id) < 3:
        return '4t ESO'  # Default fallback

    try:
        curso_num = int(text_id[2])

        # Catalan ordinal mapping for ESO grades
        curso_ordinals = {
            1: '1r ESO',
            2: '2n ESO',
            3: '3r ESO',
            4: '4t ESO',
            5: '5è ESO',
            6: '6è ESO'
        }

        return curso_ordinals.get(curso_num, f'{curso_num}è ESO')
    except (ValueError, IndexError):
        return '4t ESO'  # Default fallback


def read_text_file(file_path: Path) -> str:
    """
    Read and return the content of a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def submit_evaluation_job(api_base_url: str, items: List[Dict]) -> Optional[Dict]:
    """
    Submit a batch of texts for evaluation.
    Returns the job information including job_id and stream_url.
    """
    url = f"{api_base_url}/evaluate"
    payload = {"items": items}

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting evaluation job: {e}")
        return None


def stream_results(api_base_url: str, job_id: str) -> List[Dict]:
    """
    Stream results from the API using Server-Sent Events.
    Returns a list of all evaluation results.
    """
    url = f"{api_base_url}/stream/{job_id}"
    results = []

    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        buffer = ""
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                buffer += chunk

                # Process complete events
                while '\n\n' in buffer:
                    event_text, buffer = buffer.split('\n\n', 1)

                    # Parse SSE format
                    lines = event_text.strip().split('\n')
                    event_data = {}

                    for line in lines:
                        if line.startswith('event:'):
                            event_data['event'] = line[6:].strip()
                        elif line.startswith('data:'):
                            try:
                                event_data['data'] = json.loads(line[5:].strip())
                            except json.JSONDecodeError:
                                pass

                    # Handle different event types
                    if event_data.get('event') == 'batch_complete':
                        batch_results = event_data.get('data', {}).get('results', [])
                        results.extend(batch_results)

                        # Print progress
                        progress = event_data.get('data', {}).get('progress', {})
                        if progress:
                            print(f"  Progress: {progress.get('completed', 0)}/{progress.get('total', 0)} "
                                  f"({progress.get('percentage', 0):.1f}%)")

                    elif event_data.get('event') == 'complete':
                        print("  Job completed successfully")
                        break

                    elif event_data.get('event') == 'error':
                        error_msg = event_data.get('data', {}).get('message', 'Unknown error')
                        print(f"  Error: {error_msg}")
                        break

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error streaming results: {e}")
        return results


def evaluate_texts(api_base_url: str, items: List[Dict]) -> List[Dict]:
    """
    Submit texts for evaluation and wait for results.
    """
    print(f"  Submitting {len(items)} texts for evaluation...")

    # Submit job
    job_info = submit_evaluation_job(api_base_url, items)
    if not job_info:
        print("  Failed to submit evaluation job")
        return []

    job_id = job_info.get('job_id')
    print(f"  Job submitted with ID: {job_id}")
    print(f"  Estimated time: {job_info.get('estimated_time_seconds', 0)} seconds")

    # Stream results
    print("  Streaming results...")
    results = stream_results(api_base_url, job_id)

    print(f"  Received {len(results)} results")
    return results


def process_folder(api_base_url: str, folder_name: str, data_dir: str, batch_size: int) -> pd.DataFrame:
    """
    Process all _NOR.txt files in a folder.
    Returns a DataFrame with evaluation results.
    """
    print(f"\n{'='*80}")
    print(f"Processing folder: {folder_name}")
    print(f"{'='*80}\n")

    folder_path = Path(data_dir) / folder_name

    # Load consignas CSV
    consignas_df = load_consignas_csv(folder_path)
    if consignas_df.empty:
        print(f"No consignas.csv found for {folder_name}")
        return pd.DataFrame()

    print(f"Loaded {len(consignas_df)} consignas")

    # Get all _NOR.txt files
    nor_files = get_nor_files(folder_path)
    print(f"Found {len(nor_files)} _NOR.txt files")

    if not nor_files:
        print(f"No _NOR.txt files found in {folder_name}")
        return pd.DataFrame()

    # Prepare results storage
    all_results = []

    # Process files in batches
    for i in range(0, len(nor_files), batch_size):
        batch_files = nor_files[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(nor_files)-1)//batch_size + 1} "
              f"({len(batch_files)} files)...")

        # Prepare batch items
        batch_items = []
        file_metadata = []  # Store metadata for matching results later

        for file_path in batch_files:
            # Extract ID from filename
            text_id = extract_id_from_filename(file_path.name)
            if not text_id:
                print(f"  Warning: Could not extract ID from {file_path.name}")
                continue

            # Extract curso from ID
            curso = extract_curso_from_id(text_id)

            # Read text content
            respuesta = read_text_file(file_path)
            if not respuesta:
                print(f"  Warning: Empty file {file_path.name}")
                continue

            # Get consigna from CSV
            consigna_row = consignas_df[consignas_df['ID'].astype(str) == text_id]
            if consigna_row.empty:
                print(f"  Warning: No consigna found for ID {text_id}")
                consigna = "N/A"
            else:
                consigna = consigna_row.iloc[0]['Consigna']

            # Prepare API item
            batch_items.append({
                "id_alumno": text_id,
                "curso": curso,
                "consigna": consigna,
                "respuesta": respuesta
            })

            # Store metadata
            file_metadata.append({
                'id': text_id,
                'filename': file_path.name,
                'consigna': consigna,
                'curso': curso
            })

        if not batch_items:
            print("  No valid items in this batch, skipping...")
            continue

        # Evaluate batch
        results = evaluate_texts(api_base_url, batch_items)

        # Match results with metadata
        for result in results:
            id_alumno = result.get('id_alumno')
            metadata = next((m for m in file_metadata if m['id'] == id_alumno), None)

            if metadata:
                all_results.append({
                    'folder': folder_name,
                    'id': id_alumno,
                    'filename': metadata['filename'],
                    'curso': metadata['curso'],
                    'consigna': metadata['consigna'],
                    'nota': result.get('nota'),
                    'feedback': result.get('feedback')
                })

        # Small delay between batches to avoid overwhelming the API
        if i + batch_size < len(nor_files):
            time.sleep(1)

    # Create DataFrame
    results_df = pd.DataFrame(all_results)

    print(f"\n{'-'*80}")
    print(f"Completed processing {folder_name}")
    print(f"Total results: {len(results_df)}")
    if not results_df.empty:
        print(f"Average nota: {results_df['nota'].mean():.2f}")
        print(f"Nota range: {results_df['nota'].min():.0f} - {results_df['nota'].max():.0f}")
    print(f"{'-'*80}\n")

    return results_df


def check_api_health(api_base_url: str) -> bool:
    """
    Check if the API is healthy and ready to accept requests.
    Returns True if healthy, False otherwise.
    """
    print("Checking API health...")
    try:
        health_url = f"{api_base_url}/health"
        response = requests.get(health_url, timeout=10)
        response.raise_for_status()
        health_data = response.json()

        print(f"  Status: {health_data.get('status', 'unknown')}")
        print(f"  Model loaded: {health_data.get('model_loaded', False)}")
        print(f"  GPU available: {health_data.get('gpu_available', False)}")
        print("\n✓ API is ready!\n")
        return True
    except Exception as e:
        print(f"  Warning: Could not check API health: {e}")
        print("  Continuing anyway...\n")
        return False


def combine_results(folders: List[str], data_dir: str, timestamp: str) -> None:
    """
    Combine all results from different folders into a single CSV.
    """
    print(f"\n{'='*80}")
    print("Combining results from all folders")
    print(f"{'='*80}\n")

    all_results = []

    for folder_name in folders:
        folder_path = Path(data_dir) / folder_name
        csv_files = sorted(folder_path.glob(f"results_{folder_name}_*.csv"))

        if csv_files:
            # Get the most recent file
            latest_csv = csv_files[-1]
            df = pd.read_csv(latest_csv)
            all_results.append(df)
            print(f"Loaded {len(df)} results from {latest_csv.name}")

    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_output = f"results_all_folders_{timestamp}.csv"
        combined_df.to_csv(combined_output, index=False, encoding='utf-8')

        print(f"\n✓ Combined results saved to: {combined_output}")
        print(f"\nTotal results: {len(combined_df)}")
        print(f"\nOverall statistics:")
        print(combined_df.groupby('folder')['nota'].describe())
    else:
        print("No results files found to combine")


def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(
        description='Evaluate normalized texts using the deployed API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --api-host https://your-runpod-instance.proxy.runpod.net
  %(prog)s --api-host http://localhost:8000 --batch-size 20
  %(prog)s --api-host https://api.example.com --folders POS1 POS2
  %(prog)s --api-host https://api.example.com --no-combine
        """
    )

    parser.add_argument(
        '--api-host',
        required=True,
        help='API host URL (e.g., https://your-runpod-instance.proxy.runpod.net)'
    )
    parser.add_argument(
        '--api-port',
        default=DEFAULT_API_PORT,
        help=f'API port (default: {DEFAULT_API_PORT})'
    )
    parser.add_argument(
        '--folders',
        nargs='+',
        default=DEFAULT_FOLDERS,
        help=f'Folders to process (default: {" ".join(DEFAULT_FOLDERS)})'
    )
    parser.add_argument(
        '--data-dir',
        default=DEFAULT_DATA_DIR,
        help=f'Data directory path (default: {DEFAULT_DATA_DIR})'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f'Batch size for processing (default: {DEFAULT_BATCH_SIZE})'
    )
    parser.add_argument(
        '--no-combine',
        action='store_true',
        help='Do not combine results from all folders into a single CSV'
    )
    parser.add_argument(
        '--skip-health-check',
        action='store_true',
        help='Skip API health check before processing'
    )

    args = parser.parse_args()

    # Build API base URL
    api_host = args.api_host
    if api_host.startswith('http'):
        api_base_url = api_host
    else:
        api_base_url = f"http://{api_host}:{args.api_port}"

    print(f"\n{'='*80}")
    print("Text Evaluation Script")
    print(f"{'='*80}\n")
    print(f"API Base URL: {api_base_url}")
    print(f"Folders to process: {', '.join(args.folders)}")
    print(f"Data directory: {args.data_dir}")
    print(f"Batch size: {args.batch_size}")
    print()

    # Check API health
    if not args.skip_health_check:
        check_api_health(api_base_url)

    # Generate timestamp for output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Process each folder
    for folder_name in args.folders:
        try:
            # Process folder
            results_df = process_folder(api_base_url, folder_name, args.data_dir, args.batch_size)

            if results_df.empty:
                print(f"No results for {folder_name}, skipping CSV generation\n")
                continue

            # Save to CSV
            output_filename = f"results_{folder_name}_{timestamp}.csv"
            output_path = Path(args.data_dir) / folder_name / output_filename
            results_df.to_csv(output_path, index=False, encoding='utf-8')

            print(f"✓ Results saved to: {output_path}\n")

            # Display summary statistics
            print(f"Summary for {folder_name}:")
            print(results_df['nota'].describe())
            print("\n")

        except Exception as e:
            print(f"Error processing {folder_name}: {e}\n")
            continue

    # Combine results if requested
    if not args.no_combine:
        combine_results(args.folders, args.data_dir, timestamp)

    print("\n" + "="*80)
    print("All folders processed!")
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
