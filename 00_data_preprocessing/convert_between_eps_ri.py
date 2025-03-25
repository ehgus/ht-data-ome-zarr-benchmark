import zarr
import dask.array as da
import numpy as np
from dask.diagnostics import ProgressBar
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import *

def apply_func(input_zarr_path, output_zarr_path, fn, compressor = configure_compression('zstd-19'), filters = []):
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
    # reshape the input
    reshaped_input_zarr = da.moveaxis(input_zarr, 1, -1) # t,c,z,y,x -> t,z,y,x,c
    reshaped_input_zarr = reshaped_input_zarr.reshape(reshaped_input_zarr.shape[:-1] + (3,3))
    reshaped_input_zarr = reshaped_input_zarr.rechunk(
        reshaped_input_zarr.chunks[:-2] + ((3,),(3,))
    )
    reshaped_output_data = da.map_blocks(fn, reshaped_input_zarr, dtype = reshaped_input_zarr.dtype)
    # reshape the output
    reshaped_output_data = reshaped_output_data.reshape(reshaped_output_data.shape[:-2] + (9,))
    reshaped_output_data = da.moveaxis(reshaped_output_data, -1, 1)
    output_data = reshaped_output_data.rechunk(input_zarr.chunks)
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
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    parser.add_argument("isRI", type=str2bool, help="is RI information?")
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
    if args.isRI:
        def fn(x):
            x_arr = x.reshape((-1,3,3))
            y_arr = np.empty_like(x_arr)
            for i in range(x_arr.shape[0]):
                y_arr[i] =  x_arr[i] @ x_arr[i]
            y = y_arr.reshape(x.shape)
            return y
    else:
        def fn(x):
            x_arr = x.reshape((-1,3,3))
            x0_sqrt_arr = np.zeros_like(x_arr, shape=(x_arr.shape[0],3))
            x_delta_arr = x_arr.copy()
            y_arr = np.zeros_like(x_arr)
            for i in range(3):
                x0_sqrt_arr[:,i] = np.sqrt(x_arr[:,i,i])
                x_delta_arr[:,i,i] = 0
            # taylor sum of sqrt(x) = sqrt(x_0) * sqrt(1 + dx) = sqrt(x_0) * (1 + dx/2 - dx^2/8)
            for i in range(3):
                y_arr[:,i,i] += x0_sqrt_arr[:,i]
            y_arr += x_delta_arr/2
            for i in range(3):
                for j in range(3):
                    y_arr[:,j,i] -= np.sum(x_delta_arr[:,j,:]/x0_sqrt_arr*x_delta_arr[:,:,i],axis=1)/8
            y = y_arr.reshape(x.shape)
            return y
    apply_func(src_zarr_path, dst_zarr_path, fn, compressor = compressor, filters = filters)

if __name__ == "__main__":
    main()
