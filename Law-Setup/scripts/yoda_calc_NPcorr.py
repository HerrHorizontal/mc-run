

import argparse
import os.path
import yoda

def valid_yoda_file(param):
    base, ext = os.path.splitext(param)
    if ext.lower() not in ('.yoda'):
        raise argparse.ArgumentTypeError('File must have a yoda extension')
    if not os.path.exists(param):
        raise argparse.ArgumentTypeError('{}: No such file'.format(param))
    return param

def get_parser():
    parser = argparse.ArgumentParser(
        description = "",
        add_help = True
    )
    parser.add_argument(
        "--full",
        type = valid_yoda_file,
        required = True,
        help = "YODA file containing the analyzed objects of the full simulation run"
    )
    parser.add_argument(
        "--partial",
        type = valid_yoda_file,
        required = True,
        help = "YODA file containing the analyzed objects of the full simulation run"
    )
    parser.add_argument(
        "--output", "-o",
        type = str,
        default = "ratios.yoda"
        help = "output path for the YODA file containing the ratios"
    )
    return parser

def __main__():

    args = get_parser().parse_args()

    yoda_file_full = args.full
    yoda_file_partial = args.partial

    aos_full = yoda.read(yoda_file_full)
    aos_partial = yoda.read(yoda_file_partial)

    #TODO: loop through all histograms in both scenarios and divide full by partial

    #TODO: plot the ratio histograms/scatters
