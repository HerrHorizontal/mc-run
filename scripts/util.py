
import json
import base64
import os
from argparse import ArgumentTypeError
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        # If input object is a ndarray it will be converted into a dict holding 
        # dtype, shape and the data base64 encoded
        if isinstance(obj, np.ndarray):
            data_b64 = base64.b64encode(obj.data)
            ret = dict(__ndarray__=data_b64.decode('ascii'),
                        dtype=str(obj.dtype),
                        shape=obj.shape)
            return ret
        else:
            # Let the base class default method raise the TypeError
            return super(NumpyEncoder,self).default(obj)

def json_numpy_obj_hook(dct):
    """
    Decodes a previously encoded numpy ndarray
    with proper shape and dtype
    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        data = base64.b64decode(dct['__ndarray__'])
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
    return dct


def adjust_lightness(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return mc.to_hex(colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2]), keep_alpha=True)


def valid_yoda_file(param):
    """Helper function which checks for validity (YODA extension and existence) of the provided input files

    Args:
        param (AnyStr): File to check

    Raises:
        argparse.ArgumentTypeError: Wrong file extension
        IOError: No such file

    Returns:
        AnyStr@abspath: 
    """
    _, ext = os.path.splitext(param)
    if ext.lower() not in ('.yoda'):
        raise ArgumentTypeError('File must have a yoda extension')
    if not os.path.exists(param):
        raise IOError('{}: No such file'.format(param))
    return os.path.abspath(param)
