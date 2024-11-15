import base64
import json
import os
from argparse import ArgumentTypeError

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        # convert np array to standard list
        # let the default encoder handle everything else
        if isinstance(obj, np.ndarray):
            ret = dict(ndarray=obj.tolist())
            return ret
        return super().default(obj)


def json_numpy_obj_hook(dct):
    """
    Decodes a previously encoded numpy ndarray
    with proper shape and dtype
    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and "__ndarray__" in dct:
        data = base64.b64decode(dct["__ndarray__"])
        return np.frombuffer(data, dct["dtype"]).reshape(dct["shape"])
    elif isinstance(dct, dict) and "ndarray" in dct:
        return np.array(dct["ndarray"])
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
    import colorsys

    import matplotlib.colors as mc

    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return mc.to_hex(
        colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2]), keep_alpha=True
    )


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
    if ext.lower() not in (".yoda"):
        raise ArgumentTypeError("File must have a yoda extension")
    if not os.path.exists(param):
        raise IOError("{}: No such file".format(param))
    return os.path.abspath(param)
