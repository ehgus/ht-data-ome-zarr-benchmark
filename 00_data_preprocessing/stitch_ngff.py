from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
import dask.array as da
import ome_zarr.writer
import ome_zarr.format
from multiview_stitcher import (
    spatial_image_utils,
    fusion,
    io,
)
import zarr
from dask.diagnostics import ProgressBar

def fuse_spatial_images(spatial_images):
    fused_sim = fusion.fuse(
        spatial_images,
        transform_key=io.METADATA_TRANSFORM_KEY
    )
    return fused_sim

def fuse_ngff_files(src_ngff_pathes, dst_ngff_path, compressor, filters):
    # load all ngff data
    sims = []
    for path in src_ngff_pathes:
        reader = Reader(parse_url(path))
        node = list(reader())[0]
        arr_data = node.data[0]
        metadata = node.metadata
        arr_shape = {'t':1, 'c':1, 'z':1, 'y':1, 'x':1}
        translation = {'t':0, 'c':0, 'z':0, 'y':0, 'x':0}
        scale = {'t':1, 'c':1, 'z':1, 'y':1, 'x':1}
        coord_order = [axis['name'] for axis in metadata['axes']]
        dims = ['t', 'c', 'z', 'y', 'x']
        c_coordinate_name = metadata['name']
        if not isinstance(c_coordinate_name, list):
            c_coordinate_name = [c_coordinate_name]
        # reshape arr_data
        for c, i in zip(coord_order, arr_data.shape):
            arr_shape[c] = i
        arr_data = arr_data.reshape([arr_shape[c] for c in dims])
        # get translation
        for metadata in metadata['coordinateTransformations'][0]:
            if metadata['type'] == 'translation':
                translation_order = metadata['translation']
                for key, val in zip(coord_order, translation_order):
                    translation[key] = val
            if metadata['type'] == 'scale':
                scale_order = metadata['scale']
                for key, val in zip(coord_order, scale_order):
                    scale[key] = val
        # generate spatial_image
        sim = spatial_image_utils.get_sim_from_array(
            arr_data,
            dims = dims,
            scale = scale,
            translation = translation,
            transform_key=io.METADATA_TRANSFORM_KEY,
            c_coords=c_coordinate_name
        )
        sims.append(sim)
    # concatenate the data
    print("stitch the data...")
    fused_sim = fuse_spatial_images(sims)
    fused_arr_data = fused_sim.data
    # save the result
    data_group = zarr.open_group(dst_ngff_path, mode='w')
    zarray_data = data_group.require_dataset(
        "0",
        shape = fused_arr_data.shape,
        exact = True,
        chunks = (1,1,32,256,256),
        dtype = fused_arr_data.dtype,
        compressor = compressor,
        filters = filters,
        dimension_separator = '/'
    )
    print("save the fused data...")
    with ProgressBar():
       da.to_zarr(fused_arr_data, zarray_data, lock=False, compute=True)
    ome_zarr.writer.write_multiscales_metadata(
        group = data_group,
        datasets = [{
            "path": "0",
            "coordinateTransformations": [{
                "type": "scale",
                "scale": [scale[c] for c in dims]
            },
            {
                "type": "translation",
                "translation": [translation[c] for c in dims]
            }],
        }],
        fmt = ome_zarr.format.FormatV04(),
        name = c_coordinate_name,
        axes = [
            {'name': 't', 'type': 'time', 'unit': 'second'},
            {'name': 'c', 'type': 'channel'},
            {'name': 'z', 'type': 'space', 'unit': 'micrometer'},
            {'name': 'y', 'type': 'space', 'unit': 'micrometer'},
            {'name': 'x', 'type': 'space', 'unit': 'micrometer'}
        ]
    )


import argparse
import os
from glob import glob
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import *
def main():    
    parser = argparse.ArgumentParser(
        prog='simple OME-Zarr stitcher',
        description='Stitch multiple OME-Zarr files '
    )
    parser.add_argument("src", type=str, help="Path to the source npy-dask dataset.")
    parser.add_argument("dst", type=str, help="Path to the save benchmark result.")
    parser.add_argument(
        "-c","--compressor",
        type=str,
        required=False,
        default="zstd-3",
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
    src_ngff_pathes = glob(os.path.abspath(args.src))
    dst_ngff_path = os.path.abspath(args.dst)
    compressor = configure_compression(args.compressor)
    filters = configure_filters(args.filters)
    if len(src_ngff_pathes) == 0:
        raise ValueError("No NGFF files found in the source directory.")
    os.makedirs(dst_ngff_path, exist_ok=True)
    fuse_ngff_files(src_ngff_pathes, dst_ngff_path, compressor, filters)

if __name__ == "__main__":
    main()