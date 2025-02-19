
"""
usage: benchmark_lossless.py [-h] src dst compressor [filters ...]

Benchmark lossless compression strategies on experimental Zarr data.

positional arguments:
    src         Path to the source Zarr dataset.
    dst         Directory to save the compressed data.
    chunk_shape Chunk shape.
    compressor  Target compressor. Examples: 'gzip-5', 'blosc-zstd-3', or 'none' for no compression.
    filters     List of filters to apply before compression. Options: 'FixedScaleOffset', 'Delta', 'SpatialDelta'.

optional arguments:
  -h, --help  show this help message and exit
"""

import argparse
import time
import os
import zarr
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
from ome_zarr.writer import write_image
from ome_zarr.format import FormatV04
from ..utils import *

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark lossless compression strategies on experimental Zarr data."
    )
    parser.add_argument("src", type=str, help="Path to the source Zarr dataset.")
    parser.add_argument("dst", type=str, help="Destination directory to save the results.")
    parser.add_argument("chunk_shape", help="Chunk shape.")
    parser.add_argument(
        "compressor",
        type=str,
        help=(
            "Target compressor. Examples: 'gzip-5', 'blosc-zstd-3', or 'none' for no compression."
        ),
    )
    parser.add_argument(
        "filters",
        type=str,
        nargs="*",
        help=(
            "List of filters to apply before compression. Options: 'FixedScaleOffset', "
            "'Delta', 'SpatialDelta'."
        ),
    )
    
    args = parser.parse_args()
    # Validate source path
    src_path = args.src
    assert os.path.exists(src_path), f"Source path '{src_path}' does not exist."
    # Validate destination path
    dst_dir = args.dst
    last_filter = '' if not args.filters else args.filters[-1]
    dst_path = os.path.join(dst_dir, f'{args.compressor}_{last_filter}_{os.path.basename(src_path)}')
    assert os.path.exists(dst_dir), f"Destination directory '{dst_dir}' does not exist."
    assert not os.path.exists(dst_path), f"Destination path '{dst_path}' already exists."
    # configure compression and filter options
    compression = configure_compression(args.compressor)
    filters = configure_filters(args.filters)
    # read Zarr data
    reader = Reader(parse_url(src_path, mode = "r"))
    node = list(reader())[0]
    src_data = node.data[0]
    axes = node.metadata['axes']
    coordinate_transformations = node.metadata['coordinateTransformations']
    # Define chunk: check whther 'channel' axes exists
    input_chunk_shape = eval(args.chunk_shape)
    chunk_shape = input_chunk_shape[-node.data[0].ndim:]
    # Start Compression & writing
    store = parse_url(dst_path, mode="w").store
    root = zarr.group(store=store)
    start_time = time.process_time()
    write_image(
        image=src_data,
        group=root,
        scaler = None,
        fmt=FormatV04(),
        axes = axes,
        coordinate_transformations=coordinate_transformations,
        storage_options =dict(
            chunks = chunk_shape,
            compression = compression,
            filters = filters),
        compute = True,
        metadata=dict(
            name = ['Refractive index']
        ))
    end_time = time.process_time()
    elapsed_time = end_time - start_time
    print(f"Compression completed in {elapsed_time:.2f} seconds.")
    print(f"Output saved to {dst_path}.")
    with open(dst_path + '.txt', 'w') as f:
        f.write("Compression completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()

