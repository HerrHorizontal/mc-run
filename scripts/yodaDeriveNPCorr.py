# -*- coding: utf-8 -*-

import argparse
import sys
from os import mkdir
import os.path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
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


# def fit(xVal, yVal, yErr):
#     """Fit function to NP points."""
#     import scipy.optimize as opt

#     N_PARS = 3
#     def _f(x, pars):
#         return pars[0] + pars[1]/x**pars[2]

#     def _chi2(pars):
#         _res = (_f(xVal, pars) - yVal) / yErr
#         return np.sum(_res**2)

#     # minimize function and take resulting azimuth
#     #result = opt.minimize_scalar(_chi2)
#     result = opt.minimize(_chi2, x0=(1,1,1))
#     return dict(result=result, pars=result.x, ys=_f(xVal, result.x), chi2ndf=result.fun/(len(xVal)-N_PARS), chi2=result.fun, ndf=(len(xVal)-N_PARS))


parser = argparse.ArgumentParser(
    description = "Calculate and plot (non-perturbative correction factors by computing) the ratio of two YODA files",
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
    "--xlabel",
    dest="XLABEL",
    type=str,
    default="Observable",
    help="label for the x-axis to plot"
)
parser.add_argument(
    "--ylabel",
    dest="YLABEL",
    type=str,
    default="NP corr.",
    help="label for the y-axis to plot"
)
parser.add_argument(
    "--output-file", "-o",
    dest="OUTFILE",
    type=str,
    default="ratios.dat",
    help="output path for the YODA file containing the ratios"
)
parser.add_argument(
    "--plot-dir", "-p",
    dest="PLOTDIR",
    type=str,
    default="plots",
    help="output path for the directory containing the ratio plots"
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

xmin = min(ao.xMin() for ao in ratios.values())
xmax = max(ao.xMax() for ao in ratios.values())
ymin = min(min(h.yVals()) for h in ratios.values())
ymax = 1.1*max(max(h.yVals()) for h in ratios.values())
ymin = float(ymin)
ymax = float(ymax)


xlabel=args.XLABEL
ylabel=args.YLABEL

for name, ao in ratios.items():
    name = name.replace("/","_").strip("_")

    # aa = plot_hist_on_axes_1d(axmain, axratio, h, href, COLORS[ih % len(COLORS)], LSTYLES[ih % len(LSTYLES)], errbar=True)

    fig = plt.figure(figsize=(8,6))
    axmain = fig.add_subplot(1,1,1)

    axmain.set_xlabel(xlabel=r"${}$".format(xlabel), x=1, ha="right", labelpad=None)
    axmain.set_ylabel(ylabel=r"{}".format(ylabel), y=1, ha="right", labelpad=None)

    axmain.set_xlim([xmin, xmax])
    axmain.set_ylim([ymin, ymax])
    axmain.set_xscale("log")

    xErrs = np.array(ao.xErrs())
    yErrs = np.array(ao.yErrs())
    xVals = np.array(ao.xVals())
    yVals = np.array(ao.yVals())
    xEdges = np.append(ao.xMins(), ao.xMax())
    yEdges = np.append(ao.yVals(), ao.yVals()[-1])

    axmain.errorbar(xVals, yVals, xerr=xErrs.T, yerr=yErrs.T, color="red", linestyle="none", linewidth=1.4, capthick=1.4)
    axmain.step(xEdges, yEdges, where="post", color="red", linestyle="-", linewidth=1.4)

    print(name)
    fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)))

    # yoda.plot(
    #     ao,
    #     outfile=os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)),
    #     ratio=False,
    #     show=False,
    #     axmain=axmain
    # )

