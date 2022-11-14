# -*- coding: utf-8 -*-

import argparse
import sys
from os import mkdir
import os.path
import yoda
# import pandas as pd
# import seaborn as sns


def valid_yoda_file(param):
    base, ext = os.path.splitext(param)
    if ext.lower() not in ('.yoda'):
        raise argparse.ArgumentTypeError('File must have a yoda extension')
    if not os.path.exists(param):
        raise argparse.ArgumentTypeError('{}: No such file'.format(param))
    return param


parser = argparse.ArgumentParser(
    description = "Calculate and plot (non-perturbative correction factors by computing) the ratio of two YODA files",
    add_help = True
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
    "--output-file", "-o",
    dest="OUTFILE",
    type = str,
    default = "ratios.dat",
    help = "output path for the YODA file containing the ratios"
)
parser.add_argument(
    "--plot-dir", "-p",
    dest="PLOTDIR",
    type = str,
    default = "plots",
    help = "output path for the YODA file containing the ratios"
)


args = parser.parse_args()

yoda_file_full = args.full
yoda_file_partial = args.partial

aos_full = yoda.readYODA(yoda_file_full, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)
aos_partial = yoda.readYODA(yoda_file_partial, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)

# loop through all histograms in both scenarios and divide full by partial
if not aos_full.viewkeys() == aos_partial.viewkeys():
    raise KeyError("Unmatched key(s) {} in provided YODA files {}, {}".format(
        (aos_full.viewkeys() - aos_partial.viewkeys()),
        aos_full,
        aos_partial
    ))

ratios = {}
for hist in aos_full.keys():
    ratios[hist]=yoda.divide(aos_full[hist], aos_partial[hist])

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
    yoda.write(ratios.values(), args.OUTFILE)

# plot the ratio histograms/scatters
if not os.path.isdir(args.PLOTDIR):
    os.mkdir(args.PLOTDIR)

yoda.plotting.mplinit(engine='MPL', font='TeX Gyre Pagella', fontsize=17, mfont=None, textfigs=True)
for name, ao in ratios.items():
    name = name.replace("/","_").strip("_")
    yoda.plot(ao, outfile=os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)), ratio=False, show=False)

