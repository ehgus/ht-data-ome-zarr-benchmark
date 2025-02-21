#! python

# Convert TCF file to ome-zarr file

# import zarr
import zarr
import ome_zarr
import ome_zarr.io
import ome_zarr.writer
import ome_zarr.format
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import *
import os
from TCFile import TCFile
import numpy as np

def tcf_to_omezarr(tcf_file_path, output_path, compressor, filters):
    """
    Convert TCF to ome-zarr

    Parameters:
    - tcf_file_path: path to the input HDF5 file.
    - output_path: path where the output HDF5 file will be created.
    Note: This function does not return anything.
    """
    axes = [
        {'name': 't', 'type': 'time', 'unit': 'second'},
        {'name': 'c', 'type': 'channel'},
        {'name': 'z', 'type': 'space', 'unit': 'micrometer'},
        {'name': 'y', 'type': 'space', 'unit': 'micrometer'},
        {'name': 'x', 'type': 'space', 'unit': 'micrometer'}
    ]
    # Refractive index
    for data_id, data_name in (("3D", "refractive_index"), ("3DFL", "fluorescence")):
        # load tcf data
        try:
            tcf_data = TCFile(tcf_file_path,data_id)
        except AssertionError as e:
            print(f"{data_id} data is not found in {tcf_file_path}. Skipping...")
            continue
        tcf_array = tcf_data.asdask() # t, c, z, y, x
        tcf_array = tcf_array.reshape(tcf_array.shape[0],1,*tcf_array.shape[1:]) # t, c, z, y, x
        # create zarr
        data_group = zarr.open_group(os.path.join(output_path,data_name+".ome.zarr"),mode='w')
        zarray_data = data_group.require_dataset(
            "0",
            shape = tcf_array.shape,
            exact = True,
            chunks = (1,1,32,256,256),
            dtype = tcf_array.dtype,
            compressor = compressor,
            filters = filters,
            dimension_separator = '/'
        )
        tcf_array.store(zarray_data, lock = False, compute = True)
        ome_zarr.writer.write_multiscales_metadata(
            group = data_group,
            datasets = [{
                "path": "0",
                "coordinateTransformations": [{
                    "type": "scale",
                    "scale": [1 if tcf_data.dt == 0 else float(tcf_data.dt), 1, *tcf_data.data_resolution],
                },
                {
                    "type": "translation",
                    "translation": [0, 0, *list(-np.array(tcf_data.data_resolution)*np.array(tcf_data.data_shape)/2)]
                }]
            }],
            fmt = ome_zarr.format.FormatV04(),
            name = data_name.replace("_", " "),
            axes = axes,
        )


# command-line handler
def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog='TCF -> NGFF converter',
        description='Convert TCF file into NGFF (ome-zarr) file'
    )
    parser.add_argument("src", type=str, help="Path of TCF file.")
    parser.add_argument("dst", type=str, help="Path to the save OME-Zarr file.")
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
    # validate arguments
    src_tcf = os.path.abspath(args.src)
    dst_dir = os.path.abspath(args.dst)
    compressor = configure_compression(args.compressor)
    filters = configure_filters(args.filters)
    if not os.path.exists(src_tcf):
        raise FileNotFoundError(f"Source file '{src_tcf}' not found.")
    os.makedirs(dst_dir, exist_ok=True)
    tcf_to_omezarr(src_tcf, dst_dir, compressor, filters)

if __name__ == "__main__":
    main()