
"""
usage: benchmark_sampling_lossless.py [-h] src dst compressor [filters ...]

Benchmark lossless compression strategies after sampling chunks of experimental Zarr data.

positional arguments:
  src         Path to the target npy file.
  dst         Directory to save the the benchmark results.
  compressor  Target compressor. Examples: 'gzip-5', 'blosc-zstd-3', or 'none' for no compression.
  filters     List of filters to apply before compression. Examples: 'FixedScaleOffset', 'Delta', 'SpatialDelta'.

optional arguments:
  -h, --help  show this help message and exit
"""

import argparse
from timeit import default_timer
import os
import numpy as np
import dask.array as da
from dask.diagnostics import Profiler
import zarr
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import *

def main(args=None, verbose=True):
    if args is None:
        parser = argparse.ArgumentParser(
            description="Benchmark lossless compression strategies on experimental npy-dask data."
        )
        parser.add_argument("src", type=str, help="Path to the source npy-dask dataset.")
        parser.add_argument("dst", type=str, help="Path to the save benchmark result.")
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
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Error: Source path '{src_path}' does not exist.")
    # Validate dst directory
    dst_dir = args.dst
    if args.dst:
        os.makedirs(dst_dir, exist_ok=True)
    # configure compression and filter options
    compression = configure_compression(args.compressor)
    filters = configure_filters(args.filters)
    # read npy data
    src_sampled_array = da.from_npy_stack(src_path)
    # Prepare benchmarking
    z = zarr.create(
        shape = src_sampled_array.shape,
        chunks = src_sampled_array.chunksize,
        dtype = src_sampled_array.dtype,
        compressor = compression,
        filters = filters,
        store = zarr.MemoryStore()
    )
    ## Start benchmarking
    # Check the compression ratio / compressio speed
    with Profiler() as prof:
        da.store(src_sampled_array, z, lock=False, compute=True, return_stored=False, scheduler="threads")
    # if key starts with "from-npy-stack" : [load array from disk](https://github.com/dask/dask/blob/80b0737c9ad5848fa779efb8f841b9fa35c8ff36/dask/array/core.py#L5793)
    # if key starts with "store-map": [zip data](https://github.com/dask/dask/blob/80b0737c9ad5848fa779efb8f841b9fa35c8ff36/dask/array/core.py#L1190)
    elapsed_compression_time = sum(map(lambda rst: rst.end_time - rst.start_time if rst.key[0].startswith("store-map") else 0, prof.results))
    src_size = z.nbytes
    compressed_size = z.nbytes_stored
    ratio = src_size / compressed_size
    if elapsed_compression_time == 0:
        compression_speed = np.nan
    else:
        compression_speed = src_size / elapsed_compression_time
    # Check the decompression speed
    # decompression does not use dask
    start_time = default_timer()
    np_arr = np.array(z, dtype = z.dtype)
    end_time = default_timer()
    elapsed_decompression_time = end_time - start_time
    
    if elapsed_decompression_time == 0:
        decompression_speed = np.nan
    else:
        decompression_speed = src_size / elapsed_decompression_time
    # Check the decompressed data
    if not da.allclose(src_sampled_array, np_arr, atol=1e-4):
        print("Warning: Decompressed data does not match the original data!!")
    if verbose:
        print(f"Compression ratio: {ratio:.2f}")
        print(f"Compression speed: {compression_speed:.3f} bytes/sec")
        print(f"Decompression speed: {decompression_speed:.3f} bytes/sec")
        print("Decompressed data matches the original data.")
    # Write the benchmark results to a file
    # Create a filename with context about compression and filters
    compression_info = args.compressor.replace("-", "_")
    filters_info = "_".join(args.filters) if args.filters else "no_filters"
    if args.dst:
        filename = os.path.join(dst_dir,f"benchmark_results-for_{os.path.basename(src_path)}-{compression_info}-{filters_info}.txt") 
        with open(filename, "w") as f:
            f.write(f"Compression ratio: {ratio:.3f}\n")
            f.write(f"Compression speed: {compression_speed:.3f} bytes/sec\n")
            f.write(f"Decompression speed: {decompression_speed:.3f} bytes/sec\n")
            f.write("Decompressed data matches the original data.\n")
            f.write("="*10 + "\n")
            f.write(str(z.info))
    return {"compression ratio": ratio, "compression speed": compression_speed, "decompression speed": decompression_speed}

if __name__ == "__main__":
    main()

