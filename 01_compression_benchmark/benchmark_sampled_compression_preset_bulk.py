

"""
usage: benchmark_sampling_lossless.py [-h] src dst

Benchmark lossless compression strategies after sampling chunks of experimental Zarr data.

positional arguments:
  src         Path to the target npy file.
  dst         Directory to save the the benchmark results.

optional arguments:
  -h, --help  show this help message and exit
"""

import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm
from ..utils import *
import zarr
import dask.array as da
from dask.diagnostics import Profiler
from timeit import default_timer
import os
from glob import glob
import tomllib
def read_benchmark_recipe(recipe_file):
    with open(recipe_file, 'rb') as f:
        data = tomllib.load(f)
    
    compression_recipes = []
    for comp in data['compressors']:
        name = comp['name']
        levels = comp['level']
        for level in levels:
            compression_recipes.append(f'{name}-{level}')
    
    filters_recipes = []
    for filt in data['filters']:
        filters_recipes.append(filt['name'])
    
    return compression_recipes, filters_recipes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark lossless compression strategies on experimental npy-dask data."
    )
    parser.add_argument("bench_recipe", type=str, help="Path to the benchmark recipe")
    parser.add_argument("src", type=str, help="Path to the source npy-dask dataset.")
    parser.add_argument("dst", type=str, help="Path to the save benchmark result.")
    parser.add_argument("--debug",action='store_true', help="Activate the debug mode.")
    args = parser.parse_args()
    compression_recipes, filters_recipes = read_benchmark_recipe(args.bench_recipe)
    dst_path = args.dst
    os.makedirs(dst_path, exist_ok=True)
    # Validate source path
    src_path = args.src
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Error: Source path '{src_path}' does not exist.")
    # load data
    # The data is preloaded to the memory to avoid the overhead
    src_sampled_array_tmp = da.from_npy_stack(src_path)
    chunksize = src_sampled_array_tmp.chunksize
    src_sampled_array = da.from_array(src_sampled_array_tmp.compute(), chunks=chunksize)
    # Prepare required parameters
    zarr_condition = [(configure_compression("none"), configure_filters([]))]
    compression_option = ["none"]
    filter_option = ["none"]
    for compression_name in compression_recipes:
        compressor = configure_compression(compression_name)
        for filter_name_list in filters_recipes:
            filter_name = "-".join(filter_name_list) if filter_name_list else "none"
            filters = configure_filters(filter_name_list)
            zarr_condition.append((compressor, filters))
            compression_option.append(compression_name)
            filter_option.append(filter_name)
    num_rows = len(zarr_condition)
    compression_ratio_stack = np.zeros((num_rows,))
    compression_speed_stack = np.zeros((num_rows,))
    decompression_speed_stack = np.zeros((num_rows,))
    np_arr = np.zeros(
        shape = src_sampled_array.shape,
        dtype = src_sampled_array.dtype
    )
    # Benchmark
    for idx ,(compressor, filters) in tqdm(enumerate(zarr_condition), unit = f" / {len(zarr_condition)}"):
        z = zarr.create(
            shape = src_sampled_array.shape,
            chunks = chunksize,
            dtype = src_sampled_array.dtype,
            compressor = compressor,
            filters = filters,
            store = zarr.MemoryStore()
        )
        with Profiler() as prof:
            da.store(src_sampled_array, z, lock=False, compute=True, return_stored=False, scheduler="threads")
        # if key starts with "from-npy-stack" : [load array from disk](https://github.com/dask/dask/blob/80b0737c9ad5848fa779efb8f841b9fa35c8ff36/dask/array/core.py#L5793)
        # if key starts with "store-map": [zip data](https://github.com/dask/dask/blob/80b0737c9ad5848fa779efb8f841b9fa35c8ff36/dask/array/core.py#L5793)
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
        np_arr[:] = z
        end_time = default_timer()
        elapsed_decompression_time = end_time - start_time
        
        if elapsed_decompression_time == 0:
            decompression_speed = np.nan
        else:
            decompression_speed = src_size / elapsed_decompression_time
        # Check the decompressed data
        if not da.allclose(src_sampled_array, np_arr, atol=1e-4):
            print("\nDecompressed data does not match the original data.")
            print(compression_option[idx], filter_option[idx])
            if args.debug:
                orig_fname = os.path.join(dst_path, f"original_data.npy")
                if not os.path.exists(orig_fname):
                    np.save(orig_fname, src_sampled_array.compute())
                np.save(os.path.join(dst_path, f"decompressed_data_{compression_option[idx]}_{filter_option[idx]}.npy"),np_arr)
        compression_ratio_stack[idx] = ratio
        compression_speed_stack[idx] = compression_speed
        decompression_speed_stack[idx] = decompression_speed
        del z
    df = pd.DataFrame({
        "compression option" : compression_option,
        "filter option" : filter_option,
        "compression ratio" : compression_ratio_stack,
        "compression speed (bytes/sec)" : compression_speed_stack,
        "decompression speed (bytes/sec)" : decompression_speed_stack})
    csv_id = len(glob(os.path.join(dst_path,"compression_benchmark*"))) + 1
    df.to_csv(os.path.join(dst_path,f"compression_benchmark_{csv_id}.csv"),index=False)
