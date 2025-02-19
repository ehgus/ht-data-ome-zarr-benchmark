"""
usage: generate_benchmark_sample.py [-h] src dst numbers

Sample chunks of experimental Zarr data and save them in npy format.

positional arguments:
    src         Path to the source Zarr dataset.
    dst         Path to the dst npy file.
    numbers     Number of chunks to sample.
    chunk_shape Chunk shape.
    edge_padding    Number pixels not to be selected
    --channel     Selected channel (Default: None)

optional arguments:
    -h, --help  show this help message and exit
"""

import argparse
import os
import numpy as np
import dask.array as da
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
from numcodecs import *

def main():
    parser = argparse.ArgumentParser(
        description="Sample chunks of experimental Zarr data and save them in npy format."
    )
    parser.add_argument("src", type=str, help="Path to the source Zarr dataset.")
    parser.add_argument("dst", type=str, help="Path to the dst npy file.")
    parser.add_argument("numbers", type=int, help="Number of chunks to sample.")
    parser.add_argument("chunk_shape", help="Chunk shape.")
    parser.add_argument("edge_padding", default = "(0,0,0,0,0)", help="Number pixels not to be selected")
    parser.add_argument("--channel", type=int, help="Selected channel.")
    args = parser.parse_args()
    # Validate source path
    src_path = args.src
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Error: Source path '{src_path}' does not exist.")
    # read Zarr data
    reader = Reader(parse_url(src_path, mode = "r"))
    node = list(reader())[0]
    src_data = node.data[0]
    padding_pixel = eval(args.edge_padding)
    src_slices = tuple(slice(pad_index, -pad_index if pad_index != 0 else None) for pad_index in padding_pixel)
    src_data = src_data[src_slices] # prevent potential errors merged at stitching
    if args.channel is not None:
        src_data = src_data[:,args.channel:args.channel+1,:,:,:]
    # Define chunk: check whether 'channel' axes exists
    # First, get the `args.numbers` number of chunks' indices randomly.
    input_chunk_shape = eval(args.chunk_shape)
    chunk_shape = input_chunk_shape[-node.data[0].ndim:]
    chunk_dim = [src_data.shape[i] // chunk_shape[i] for i in range(node.data[0].ndim)]
    print(f"src data size : {src_data.shape}")
    num_of_chunk = args.numbers
    if num_of_chunk <= 0:
        raise ValueError("The number of chunks to sample must be a positive integer.")
    total_chunks = np.prod(chunk_dim)
    if num_of_chunk > total_chunks:
        raise ValueError(f"The number of chunks to sample ({num_of_chunk}) exceeds the total number of chunks ({total_chunks}).")
    rng = np.random.default_rng(12345)
    linear_chunk_indices = rng.permutation(np.prod(chunk_dim))[:num_of_chunk]
    chunk_indices = np.unravel_index(linear_chunk_indices, chunk_dim)
    # Second, generate the src_array containing the sampled chunks.
    src_chunk_list = []
    for chunk_idx in zip(*chunk_indices):
        src_chunk = src_data[tuple(slice(chunk_idx[j]*chunk_shape[j], (chunk_idx[j]+1)*chunk_shape[j]) for j in range(node.data[0].ndim))]
        src_chunk_list.append(src_chunk)
    src_sampled_array = da.concatenate(src_chunk_list, axis=0)
    src_sampled_array = src_sampled_array.rechunk(chunk_shape)
    # Save the sampled chunks to npy file
    da.to_npy_stack(args.dst, src_sampled_array, axis = 0)
    print(f"Sampled chunks saved to {args.dst}")

if __name__ == "__main__":
        main()
