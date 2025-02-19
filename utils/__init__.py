from utils.spatial_filter import SpatialDelta
from utils.argument_configuration import configure_compression, configure_filters

# codec registration
from numcodecs.registry import register_codec
register_codec(SpatialDelta)