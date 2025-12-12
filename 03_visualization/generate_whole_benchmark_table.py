#!/usr/bin/env python3
"""
Generate a comprehensive benchmark table by merging multiple dataset CSV files.

This script reads benchmark data from multiple CSV files (specified in a TOML config),
adds dataset labels, and combines them into a single comprehensive table.
Output is saved as both CSV and Excel formats.
"""

import argparse
import os
from pathlib import Path
import pandas as pd
import tomllib

def load_config(config_path):
    """Load configuration from TOML file."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'rb') as f:
        config = tomllib.load(f)

    # Validate configuration
    if 'table_name' not in config or 'data_path' not in config:
        raise ValueError("Configuration must contain 'table_name' and 'data_path' keys")

    if len(config['table_name']) != len(config['data_path']):
        raise ValueError(
            f"Mismatch between table_name ({len(config['table_name'])}) "
            f"and data_path ({len(config['data_path'])}) lengths"
        )

    return config


def load_and_label_csv(csv_path, dataset_name):
    """
    Load a CSV file and add a 'Dataset' column with the dataset name.

    Args:
        csv_path: Path to the CSV file
        dataset_name: Name of the dataset to add as a column

    Returns:
        pandas.DataFrame with an additional 'Dataset' column
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Add dataset name as the first column
    df.insert(0, 'Dataset', dataset_name)

    return df

def rescale_bandwdith_byte2Mbyte(df):
    df['compression speed (MiB/s)'] = df['compression speed (bytes/sec)']/2**20
    df['decompression speed (MiB/s)'] = df['decompression speed (bytes/sec)']/2**20
    del df['compression speed (bytes/sec)']
    del df['decompression speed (bytes/sec)']
    return df

def prettify_filter(df):
    df['filter option'] = df['filter option'].apply(lambda x: x.replace('BitRound-14', 'BitRound'))
    return df

def prettify_compressor(df):
    def extract_clevel(comp_option):
        clevel = comp_option.rsplit('-')[-1]
        if clevel == "none":
            return 0
        else:
            return int(clevel)
    df['compressor'] = df['compression option'].apply(lambda x: x.rsplit('-')[0])
    df['compression level'] = df['compression option'].apply(extract_clevel)
    del df['compression option']
    return df

def groupby_options(df):
    df = df.groupby([
        'Dataset',
        'compressor',
        'compression level',
        'filter option'
    ]).mean()

    return df

def merge_benchmark_tables(config):
    """
    Merge multiple benchmark CSV files into a comprehensive table.

    Args:
        config: Dictionary containing 'table_name' and 'data_path' lists

    Returns:
        pandas.DataFrame containing all merged data
    """
    dataframes = []

    for dataset_name, csv_path in zip(config['table_name'], config['data_path']):
        df = load_and_label_csv(csv_path, dataset_name)
        dataframes.append(df)

    # Concatenate all dataframes
    merged_df = pd.concat(dataframes, ignore_index=True)

    # Postprocess the merged dataframe
    merged_df = rescale_bandwdith_byte2Mbyte(merged_df)
    merged_df = prettify_filter(merged_df)
    merged_df = prettify_compressor(merged_df)
    merged_df = groupby_options(merged_df)

    return merged_df


def save_outputs(df, output_csv):
    """
    Save the dataframe as a CSV files.

    Args:
        df: pandas.DataFrame to save
        output_csv: Path for CSV output
        output_xlsx: Path for Excel output
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # Save as CSV
    df.to_csv(output_csv, index=True, header=True)
    print(f"\nSaved CSV: {output_csv}")


def main():
    """Main function to orchestrate the benchmark table generation."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive benchmark table from multiple CSV files"
    )
    parser.add_argument(
        'config',
        default='03_visualization/whole_benchmark_script.toml',
        help='Path to TOML configuration file (default: 03_visualization/whole_benchmark_script.toml)'
    )
    parser.add_argument(
        'output_csv',
        default='output/comprehensive-benchmark-table.csv',
        help='Path for CSV output (default: output/comprehensive-benchmark-table.csv)'
    )

    args = parser.parse_args()
    # Load configuration
    config = load_config(args.config)
    # Merge benchmark tables
    merged_df = merge_benchmark_tables(config)
    # Save outputs
    save_outputs(merged_df, args.output_csv)

if __name__ == "__main__":
    main()
