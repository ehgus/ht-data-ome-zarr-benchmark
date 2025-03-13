import zarr
import dask.array as da
from dask.diagnostics import ProgressBar
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import *

def add_random_noise(input_zarr_path, output_zarr_path, noise_range=(-5e-5, 5e-5), compressor = configure_compression('zstd-19'), filters = []):
    """
    Reads a Zarr file, adds random noise within the given range, and writes to a new Zarr file.

    Parameters:
    - input_zarr_path: Path to the input Zarr file.
    - output_zarr_path: Path to the output Zarr file.
    - noise_range: Tuple (min_noise, max_noise) defining the range of random noise.
    """
    # Open the input Zarr file
    input_zarr = da.from_zarr(input_zarr_path, component='0')
    chunksize = input_zarr.chunksize
    # Create a new Zarr file to store the modified data
    output_group = zarr.open_group(output_zarr_path, mode='w')
    output_zarr = output_group.require_dataset(
        "0",
        shape = input_zarr.shape,
        chunks = chunksize,
        dtype = input_zarr.dtype,
        compressor = compressor,
        filters = filters,
        dimension_separator = '/'
    )
    # Generate random noise
    if noise_range is not None:
        noise = da.random.uniform(noise_range[0], noise_range[1], input_zarr.shape, chunks=input_zarr.chunks)
        # Add noise to the data
        output_data = input_zarr + noise
    else:
        output_data = input_zarr
    # Store the noisy data in the output Zarr file
    print("Start conversion...")
    with ProgressBar():
        output_data.store(output_zarr, lock = False)

import argparse
import os
def main():
    parser = argparse.ArgumentParser(
        prog="Zarr Noise Adder",
        description="Add random noise to Zarr datasets"
    )
    parser.add_argument("src", type=str, help="Path to the source Zarr dataset.")
    parser.add_argument("dst", type=str, help="Path to save the modified Zarr dataset.")
    parser.add_argument(
        "--min-noise",
        type=float,
        default=-5e-5,
        help="Minimum noise value to add (default: -5e-5)."
    )
    parser.add_argument(
        "--max-noise",
        type=float,
        default=5e-5,
        help="Maximum noise value to add (default: 5e-5)."
    )
    parser.add_argument(
        "-c","--compressor",
        type=str,
        required=False,
        default="zstd-19",
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
    compressor = configure_compression(args.compressor)
    filters = configure_filters(args.filters)

    # Convert relative paths to absolute paths
    src_zarr_path = os.path.abspath(args.src)
    dst_zarr_path = os.path.abspath(args.dst)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(dst_zarr_path), exist_ok=True)

    # Add noise to the Zarr file
    if args.max_noise <= 0:
        noise_range = None
    else:
        noise_range=(args.min_noise, args.max_noise)
    add_random_noise(src_zarr_path, dst_zarr_path, noise_range=noise_range, compressor = compressor, filters = filters)

if __name__ == "__main__":
    main()
