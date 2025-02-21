import zarr
import dask.array as da
import h5py
import ome_zarr.writer
import ome_zarr.format

# Warning: This function is too specific to my case,
# So it is not recommended to use it directly.

def convert_mat2ngff(src_mat_path, dst_ngff_path, compressor, filters):
    with h5py.File(src_mat_path, 'r') as mat:
        raw_data = da.from_array(mat['e']) # z, y, x, c (3 x 3)
        transposed_data = raw_data.transpose(3, 4, 0, 1, 2) # c (3 x 3), z, y, x
        data = transposed_data.reshape(1, 9, raw_data.shape[0], raw_data.shape[1], raw_data.shape[2]) # t, c, z, y, x
        metadata = mat['para']
        resolution = (1, 1, metadata['imres'][2].item(), metadata['imres'][1].item(), metadata['imres'][0].item())
        # save the result
        data_group = zarr.open_group(dst_ngff_path, mode='w')
        zarray_data = data_group.require_dataset(
            "0",
            shape=data.shape,
            exact=True,
            chunks=(1, 1, 32, 256, 256),
            dtype=data.dtype,
            compressor=compressor,
            filters=filters,
            dimension_separator='/'
        )
        da.to_zarr(data, zarray_data, lock=False, compute=True)
        assert da.all(da.equal(zarray_data, data)).compute(), "The save array and original array should be the same"
    ome_zarr.writer.write_multiscales_metadata(
        group=data_group,
        datasets=[{
            "path": "0",
            "coordinateTransformations": [{
                "type": "scale",
                "scale": resolution
            },
            {
                "type": "translation",
                "translation": calculate_translate(src_mat_path)
            }]
        }],
        fmt = ome_zarr.format.FormatV04(),
        name = ["Refractive index XX",
                "Refractive index XY",
                "Refractive index XZ",
                "Refractive index YX",
                "Refractive index YY",
                "Refractive index YZ",
                "Refractive index ZX",
                "Refractive index ZY",
                "Refractive index ZZ"],
        axes = [
            {'name': 't','type': 'time', 'unit': 'second'},
            {'name': 'c', 'type': 'channel'},
            {'name': 'z', 'type': 'space', 'unit': 'micrometer'},
            {'name': 'y', 'type': 'space', 'unit': 'micrometer'},
            {'name': 'x', 'type': 'space', 'unit': 'micrometer'}
        ]       
    )


import re
def calculate_translate(src_mat_path):
    regex = re.compile(r'_(?P<scan_order1>[0-9]{3})_(?P<scan_order2>[0-9]{3})_DT.mat')
    m = regex.search(src_mat_path)
    if m is None:
        return (0,0,0,0,0)
    scan_order1 = int(m.group('scan_order1')) - 1 
    scan_order2 = int(m.group('scan_order2')) - 1
    if scan_order1 % 2 == 1:
        # if scan_order1 is odd, reverse the scan_order2
        scan_order2 = 19 - scan_order2
    print(f"scan_order1: {scan_order1}, scan_order2: {scan_order2}")
    # get y,x translation
    # (raw:001_002, conv: 00,01): (y,x): 50.04673729, -0.89369174
    # (raw:002_020, conv: 01,00): (y,x): -2.80351751, -47.16170531
    dy = -2.80351751 * scan_order1 + 50.04673729 * scan_order2
    dx = -47.16170531 * scan_order1 - 0.89369174 * scan_order2
    return (0,0,0,dy,dx)


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
    parser.add_argument("src", type=str, help="Path of mat7.3 file.")
    parser.add_argument("dst", type=str, help="Path to the save OME-Zarr file.")
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
    src_mat = os.path.abspath(args.src)
    dst_dir = os.path.abspath(args.dst)
    compressor = configure_compression(args.compressor)
    filters = configure_filters(args.filters)
    if not os.path.exists(src_mat):
        raise FileNotFoundError(f"Source file '{src_mat}' not found.")
    os.makedirs(dst_dir, exist_ok=True)
    convert_mat2ngff(src_mat, dst_dir, compressor, filters)

if __name__ == "__main__":
    main()