

def configure_compression(compressor):
    """Configure the compressor with the specified parameters."""
    from numcodecs import Blosc, GZip, BZ2, LZMA, LZ4, Zlib, Zstd
    if compressor == "none":
        return None  # No compression
    elif compressor.startswith("blosc"):
        #  e.g., ‘zstd’, ‘blosclz’, ‘lz4’, ‘lz4hc’, ‘zlib’ or ‘snappy’.
        blosc_info = compressor.split("-")
        codec = blosc_info[1]
        clevel = int(blosc_info[2])
        shuffle = 0 if len(blosc_info) ==3 else int(blosc_info[3])
        return Blosc(cname=codec, clevel=clevel, shuffle=shuffle)
    else:
        comp_info = compressor.split("-")
        codec = comp_info[0]
        level = int(comp_info[1])
        if codec == "gzip":
            return GZip(level=level)
        elif codec == "bzip2":
            return BZ2(level=level)
        elif codec == "lzma":
            return LZMA(preset = level)
        elif codec == "lz4":
            return LZ4(acceleration=level)
        elif codec == "zlib":
            return Zlib(level=level)
        elif codec == "zstd":
            return Zstd(level=level)
        else:
            raise ValueError(f"Unsupported compressor: {codec}")


def configure_filters(filter_args):
    """Configure the filters with the specified parameters."""
    from numcodecs import FixedScaleOffset, Quantize, Delta, Shuffle, BitRound
    from utils.spatial_filter import SpatialDelta
    filters = []
    for filter_name in filter_args:
        if filter_name == "FixedScaleOffset":
            filters.append(FixedScaleOffset(offset=0, scale=1e4, dtype="f4", astype="i2")) # (-3.2768, 3.2768)
        elif filter_name == "Delta":
            filters.append(Delta(dtype="i2"))
        elif filter_name == "SpatialDelta":
            axes = eval(filter_name.split("-")[1]) if len(filter_name.split("-")) > 1 else (0,)
            filters.append(SpatialDelta(axes = axes, dtype = "i2"))
        elif filter_name.startswith("Shuffle"):
            elementsize = int(filter_name.split("-")[1]) if len(filter_name.split("-")) > 1 else 4
            filters.append(Shuffle(elementsize=elementsize))
        elif filter_name.startswith("BitRound"):
            keepbits = int(filter_name.split("-")[1]) if len(filter_name.split("-")) > 1 else (1 + 8 + 14) # float 32 w/ 4 digit accuracy
            filters.append(BitRound(keepbits=keepbits))
        else:
            raise ValueError(f"Unknown filter: {filter_name}")
    return filters