# -*- coding: utf-8 -*-

import argparse
import sys
from os import mkdir
import os.path
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import yoda
# import pandas as pd
# import seaborn as sns


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
    base, ext = os.path.splitext(param)
    if ext.lower() not in ('.yoda'):
        raise argparse.ArgumentTypeError('File must have a yoda extension')
    if not os.path.exists(param):
        raise IOError('{}: No such file'.format(param))
    return os.path.abspath(param)


parser = argparse.ArgumentParser(
    description = "Calculate (non-perturbative correction factors by computing) the ratio of analysis objects in two YODA files",
    add_help = True
)
parser.add_argument(
    "--full",
    type = valid_yoda_file,
    required = True,
    help = "YODA file containing the analyzed objects of the nominator (e.g. full) simulation run"
)
parser.add_argument(
    "--partial",
    type = valid_yoda_file,
    required = True,
    help = "YODA file containing the analyzed objects of the denominator (e.g. partial) simulation run"
)
parser.add_argument(
    "-m", "--match",
    dest="MATCH",
    metavar="PATT",
    default=None,
    help="only write out histograms whose path matches this regex"
)
parser.add_argument(
    "-M", "--unmatch",
    dest="UNMATCH",
    metavar="PATT",
    default=None,
    help="exclude histograms whose path matches this regex"
)
parser.add_argument(
    "--output-file", "-o",
    dest="OUTFILE",
    type=str,
    default="ratios.dat",
    help="output path for the YODA file containing the ratios"
)

args = parser.parse_args()


yoda_file_full = args.full
yoda_file_partial = args.partial

aos_full = yoda.readYODA(yoda_file_full, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)
aos_partial = yoda.readYODA(yoda_file_partial, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)

# loop through all histograms in both scenarios and divide full by partial
if not aos_full or not aos_partial:
    if not aos_full and not aos_partial:
        raise RuntimeError("No full and partial analysis objects matching the filters!")
    elif not aos_full:
        raise RuntimeError("No full analysis objects matching the filters!")
    else:
        raise RuntimeError("No partial analysis objects matching the filters!")
if not aos_full.viewkeys() == aos_partial.viewkeys():
    raise KeyError("Unmatched key(s) {} in provided YODA files {}, {}".format(
        (aos_full.viewkeys() - aos_partial.viewkeys()),
        aos_full,
        aos_partial
    ))

ratios = {}
for hist in aos_full.keys():
    print("Dividing AO {}".format(hist))
    ao_full = aos_full[hist]
    ao_partial = aos_partial[hist]
    try:
        ao_ratio = yoda.divide(ao_full, ao_partial)
        ratios[hist]=yoda.Scatter2D(ao_ratio, hist)
        # print("\t{}".format(type(ao_ratio)))
    except Exception as e:
        print("\tSkipping, since {}".format(e))
        print("\tfull: {}, \n\tpartial: {}".format(ao_full, ao_partial))
        continue

if os.path.splitext(args.OUTFILE)[1] == ".root":
    # try:
    #     import ROOT
    #     ROOT.gROOT.SetBatch(True)
    # except ImportError:
    #     sys.stderr.write("Could not load ROOT Python module, exiting...\n")
    #     sys.exit(2)

    # of = ROOT.TFile(args.OUTFILE, "recreate")
    # rootobjects = [
    #     yoda.root.to_root(
    #         ao,
    #         asgraph=args.AS_GRAPHS,
    #         usefocus=args.USE_FOCUS,
    #         widthscale=args.DIVBINSIZE
    #     ) for ao in ratios.values()
    # ]
    # ## Protect against "/" in the histogram name, which ROOT does not like
    # for obj in rootobjects:
    #     ## It's possible for the ROOT objects to be null, if conversion failed
    #     if obj is None:
    #         continue
    #     ## Split the name on "/" directory separators
    #     parts = obj.GetName().split("/")
    #     # Set ReturnExistingDirectory to True, to dodge warnings about existing directories
    #     of.mkdir(''.join(parts[:-1]), "", True)
    #     d = of.Get(''.join(parts[:-1]))
    #     ## Write the histo into the leaf dir
    #     d.WriteTObject(obj, parts[-1])
    # of.Close()
    raise NotImplementedError("Writing root files not supported for the moment!")
else:
    yoda.write(ratios, args.OUTFILE)
