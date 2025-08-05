from utils.spatial_filter import SpatialDelta
from utils.argument_configuration import configure_compression, configure_filters
from utils.nvidia_compressor import NvcompLZ4, NvcompGDeflate
from utils.squeeze_filter import Squeeze

# codec registration
from numcodecs.registry import register_codec
register_codec(NvcompLZ4)
register_codec(NvcompGDeflate)
register_codec(SpatialDelta)
register_codec(Squeeze)