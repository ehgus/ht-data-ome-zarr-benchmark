# Data from `Kim, G., Ahn, D., Kang, M. et al. Rapid species identification of pathogenic bacteria 
# from a minute quantity exploiting three-dimensional quantitative phase imaging and artificial neural network. 
# Light Sci Appl 11, 190 (2022). https://doi.org/10.1038/s41377-022-00881-x`

# Convert deep learning trainining data from mat73 to NGFF (ome-zarr) format.

import zarr
from scipy.io import loadmat
import h5py
import ome_zarr.writer
import ome_zarr.format
import os
from glob import glob
import random
import math

# Warning: This function is too specific to my case,
# So it is not recommended to use it directly.

def convert_matdataset2ngff(src_mat_path, dst_ngff_path, num_stitching, compressor, filters):
    random_path = random.sample(src_mat_path, k = math.prod(num_stitching))
    # configure the size of data for a single file
    with h5py.File(random_path[0], 'r') as mat:
        data_shape = mat['data'].shape
        data_dtype = mat['data'].dtype
        data_resolution = (
            mat['resz'][0].item(),
            mat['resy'][0].item(),
            mat['resx'][0].item()
        )
    array_shape = [d * s for d, s in zip(data_shape, num_stitching)]
    # generate the destination path
    data_group = zarr.open_group(dst_ngff_path, mode='w')
    zarray_data = data_group.require_dataset(
        "0",
        shape=array_shape,
        exact=True,
        chunks=(32, 256, 256),
        dtype=data_dtype,
        compressor=compressor,
        filters=filters,
        dimension_separator='/'
    )
    # save each mat file to the destination path
    for i, mat_path in enumerate(random_path):
        try:
            mat = loadmat(mat_path)
            data = mat['data'].transpose(2, 1, 0)  # z, y, x
        except NotImplementedError:
            with h5py.File(mat_path, 'r') as mat:
                data = mat['data'][:] # z, y, x
        # calculate the index to save the data
        z_index = i // (num_stitching[1] * num_stitching[2])
        y_index = (i // num_stitching[2]) % num_stitching[1]
        x_index = i % num_stitching[2]
        # calculate the slice for saving
        z_slice = slice(z_index * data_shape[0], (z_index + 1) * data_shape[0])
        y_slice = slice(y_index * data_shape[1], (y_index + 1) * data_shape[1])
        x_slice = slice(x_index * data_shape[2], (x_index + 1) * data_shape[2])
        # save the data
        zarray_data[z_slice, y_slice, x_slice] = data

    # write metadata
    ome_zarr.writer.write_multiscales_metadata(
        group=data_group,
        datasets=[{
            "path": "0",
            "coordinateTransformations": [{
                "type": "scale",
                "scale": data_resolution
            },
            {
                "type": "translation",
                "translation": [0, 0, 0]
            }]
        }],
        fmt = ome_zarr.format.FormatV04(),
        name = ["Refractive index"],
        axes = [
            {'name': 'z', 'type': 'space', 'unit': 'micrometer'},
            {'name': 'y', 'type': 'space', 'unit': 'micrometer'},
            {'name': 'x', 'type': 'space', 'unit': 'micrometer'}
        ]
    )

import os
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import *
# command-line handler
def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog='MAT73 -> NGFF converter',
        description='Convert mat7.3 file into NGFF (ome-zarr) file'
    )
    parser.add_argument("src", type=str, help="Path of training data directory. Represents a regex path.")
    parser.add_argument("dst", type=str, help="Path to the save OME-Zarr files.")
    parser.add_argument("num_stitching", help="Number of data to be stitched along ZYX axes. e.g., (1, 1, 1)")
    parser.add_argument(
        "-c","--compressor",
        type=str,
        required=False,
        default="zstd-16",
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
    # validate arguments
    src_regex_path = os.path.abspath(args.src)
    dst_ngff_path = os.path.abspath(args.dst)
    compressor = configure_compression(args.compressor)
    input_num_stitching = eval(args.num_stitching)
    filters = configure_filters(args.filters)
    src_mat_path = glob(src_regex_path)
    if not src_mat_path:
        raise FileNotFoundError(f"File in '{src_regex_path}' is not found.")
    os.makedirs(dst_ngff_path, exist_ok=True)
    convert_matdataset2ngff(src_mat_path, dst_ngff_path, input_num_stitching, compressor, filters)

if __name__ == "__main__":
    main()