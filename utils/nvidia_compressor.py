from numcodecs.abc import Codec
from nvidia import nvcomp
from numcodecs.compat import ensure_ndarray

class NvcompLZ4(Codec):
    """Numcodecs-compatible codec using nvCOMP LZ4 GPU compression."""
    codec_id = "nvcomp_lz4"
    def __init__(self):
        self.lz4_codec = nvcomp.Codec(algorithm="LZ4")

    def encode(self, buf):
        arr = nvcomp.as_array(bytes(buf))
        arr_d = arr.cuda()
        enc_d = self.lz4_codec.encode(arr_d)
        enc = bytes(enc_d.cpu())
        return enc

    def decode(self, buf, out=None):
        arr = nvcomp.as_array(bytes(buf))
        arr_d = arr.cuda()
        out_d = self.lz4_codec.decode(arr_d)
        out = bytes(out_d.cpu())
        #print(ensure_ndarray(out).view('f4')[0])
        return out
    
    def get_config(self):
        return dict(id=self.codec_id)

    def __repr__(self):
        r = f'{type(self).__name__}()'
        return r
        
class NvcompGDeflate(Codec):
    """Numcodecs-compatible codec using nvCOMP GDeflate GPU compression."""
    codec_id = "nvcomp_gdeflate"
    def __init__(self,level):
        self.level = level
        self.gdeflate_codec = nvcomp.Codec(algorithm="GDEFLATE", algorithm_type=level)

    def encode(self, buf):
        arr = ensure_ndarray(buf).view('u1')
        arr = nvcomp.as_array(arr)
        arr_d = arr.cuda()
        enc_d = self.gdeflate_codec.encode(arr_d)
        enc = bytes(enc_d.cpu())
        return enc

    def decode(self, buf, out=None):
        arr = nvcomp.as_array(buf)
        arr_d = arr.cuda()
        out_d = self.gdeflate_codec.decode(arr_d)
        out = bytes(out_d.cpu())
        return out
    
    def get_config(self):
        # override to handle encoding dtypes
        return dict(id=self.codec_id, level=self.level)
    
    def __repr__(self):
        r = f'{type(self).__name__}(level={self.level})'
        return r