import numpy as np
from numcodecs.abc import Codec

class Squeeze(Codec):
    """A numcodecs codec that squeezes arrays on encode, does nothing on decode."""

    codec_id = 'squeeze'

    def encode(self, buf):
        arr = np.asarray(buf)
        squeezed = np.squeeze(arr)
        return squeezed

    def decode(self, buf, out=None):
        return buf