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


COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"]
XTICKS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]


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
    description = "Plot (non-perturbative correction factors by computing) the ratio of analysis objects in (and origin nominator and denominator) YODA file(s)",
    add_help = True
)
parser.add_argument(
    "--full",
    type = valid_yoda_file,
    help = "YODA file containing the analyzed objects of the nominator (e.g. full) simulation run"
)
parser.add_argument(
    "--partial",
    type = valid_yoda_file,
    help = "YODA file containing the analyzed objects of the denominator (e.g. partial) simulation run"
)
parser.add_argument(
    "--full-label",
    type = str,
    default = "full",
    help = "Legend label for the nominator (i.e. full) simulation"
)
parser.add_argument(
    "--partial-label",
    type = str,
    default = "partial",
    help = "Legend label for the denominator (i.e. partial) simulation"
)
parser.add_argument(
    "--ratio",
    type = valid_yoda_file,
    required = True,
    help = "YODA file containing the ratio of the analyzed objects"
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
    "--origin",
    dest="ORIGIN",
    action="store_true",
    help="plot the input cross-sections (full and partial) for the ratio calculations"
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
    "--yrange",
    nargs=2,
    type=float,
    default=[0.8,1.3],
    metavar=("ymin","ymax"),
    help="range for the y-axis of the ratio plot"
)
parser.add_argument(
    "--origin-ylabel",
    dest="YORIGIN",
    type=str,
    help="y-axis label for the top pad in case origin flag is set"
)
parser.add_argument(
    "--plot-dir", "-p",
    dest="PLOTDIR",
    type=str,
    default="plots",
    help="output path for the directory containing the ratio plots"
)
parser.add_argument(
    "--supress-legend", "-l",
    dest="NOLEGEND",
    action='store_true',
    help="supress plotting the legend"
)
parser.add_argument(
    "--summary-match", "-s",
    dest="SUMMARIES",
    nargs="*",
    help="list of strings used to match the analysis objects to produce a respective summary plot for"
)

args = parser.parse_args()

if args.YORIGIN and not args.ORIGIN:
    raise argparse.ArgumentError("Label for origin y-axis {} passed without turning on origin plot!".format(args.YORIGIN))
elif args.ORIGIN and not all([args.partial, args.full]):
    raise argparse.ArgumentError("Files containing the analysis objects for the full and partial simulation need to be given for origin pad!")
elif args.YORIGIN:
    originylabel = r"${}$".format(args.YORIGIN)
else:
    originylabel = "arb. units"


yoda_file_full = args.full
yoda_file_partial = args.partial
yoda_file_ratio = args.ratio

origin = args.ORIGIN

LABELS = [args.full_label, args.partial_label]

if origin:
    aos_full = yoda.readYODA(yoda_file_full, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)
    aos_partial = yoda.readYODA(yoda_file_partial, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)
aos_ratios = yoda.readYODA(yoda_file_ratio, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)

if origin:
    # check analysis objects in all scenarios and ratios
    if not aos_full.viewkeys() == aos_partial.viewkeys():
        raise KeyError("Unmatched key(s) {} in provided YODA files: full: {}, partial: {}".format(
            (aos_full.viewkeys() - aos_partial.viewkeys()),
            aos_full,
            aos_partial
        ))
    if not all(ao in aos_full for ao in aos_ratios.viewkeys()):
        raise KeyError("Not all keys {} of ratio file {} present in full origin file {}".format(
            aos_ratios.viewkeys(),
            yoda_file_ratio,
            yoda_file_full
        ))
    elif not all(ao in aos_partial for ao in aos_ratios.viewkeys()):
        raise KeyError("Not all keys {} of ratio file {} present in partial origin file {}".format(
            aos_ratios.viewkeys(),
            yoda_file_ratio,
            yoda_file_partial
        ))

import pprint
pp = pprint.PrettyPrinter(depth=2)
if origin:
    print("full AOs:")
    pp.pprint(aos_full)
    print("partial AOs:")
    pp.pprint(aos_partial)
print("ratios:")
pp.pprint(aos_ratios)

# plot the ratio histograms/scatters
if not os.path.isdir(args.PLOTDIR):
    os.mkdir(args.PLOTDIR)

yoda.plotting.mplinit(engine='MPL', font='TeX Gyre Pagella', fontsize=17, mfont=None, textfigs=True)

xmin = min(ao.xMin() for ao in aos_ratios.values())
xmax = max(ao.xMax() for ao in aos_ratios.values())

xticks = [x for x in XTICKS if x<=xmax and x>=xmin]

xlabel=args.XLABEL
ylabel=args.YLABEL

summaries = dict()

for name, ao in aos_ratios.items():
    # aa = plot_hist_on_axes_1d(axmain, axratio, h, href, COLORS[ih % len(COLORS)], LSTYLES[ih % len(LSTYLES)], errbar=True)

    fig = plt.figure(figsize=(8,6))
    if origin:
        try:
            gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[2,1], hspace=0.05)
            axmain = fig.add_subplot(gs[1])
            axorigin = fig.add_subplot(gs[0])#, sharex=axmain)
        except:
            sys.stderr.write("matplotlib.gridspec not available: falling back to plotting without the original distributions\n")
            origin = False
    if not origin:
        fig.set_size_inches(6,2.67)
        axmain = fig.add_subplot(1,1,1)

    if origin:
        axorigin.set_ylabel(ylabel=originylabel, y=1, ha="right", labelpad=None)

        yminorigin = float(0.9*min(min(h.yVals()) for h in [aos_full[name], aos_partial[name]]))
        ymaxorigin = float(1.1*max(max(h.yVals()) for h in [aos_full[name], aos_partial[name]]))

        axorigin.set_xlim([xmin, xmax])
        axorigin.set_ylim([yminorigin, ymaxorigin])
        axorigin.set_xscale("log")
        axorigin.set_yscale("log")

        for i, aotop in enumerate([aos_full[name], aos_partial[name]]):
            xErrs = np.array(aotop.xErrs())
            yErrs = np.array(aotop.yErrs())
            xVals = np.array(aotop.xVals())
            yVals = np.array(aotop.yVals())
            xEdges = np.append(aotop.xMins(), aotop.xMax())
            yEdges = np.append(aotop.yVals(), aotop.yVals()[-1])

            label=r"${}$".format(LABELS[i])

            axorigin.errorbar(xVals, yVals, xerr=xErrs.T, yerr=yErrs.T, color=COLORS[i], linestyle="none", linewidth=1.4, capthick=1.4)
            axorigin.step(xEdges, yEdges, where="post", color=COLORS[i], linestyle="-", linewidth=1.4, label=label)

        # plt.setp(axorigin.get_xticklabels(), visible=False)
        axmain.set_xticks(xticks)
        axorigin.set_xticklabels([])

        axorigin.legend()

    axmain.axhline(1.0, color="gray") #< Ratio = 1 marker line

    axmain.set_xlabel(xlabel=r"${}$".format(xlabel), x=1, ha="right", labelpad=None)
    axmain.set_ylabel(ylabel=r"{}".format(ylabel), y=1, ha="right", labelpad=None)

    axmain.set_xlim([xmin, xmax])
    yminmain = args.yrange[0]
    ymaxmain = args.yrange[1]
    if float(min(ao.yVals())) < yminmain:
        yminmain = float(min(ao.yVals()))
    if float(1.1*max(ao.yVals())) > ymaxmain:
        ymaxmain = float(1.1*max(ao.yVals()))
    axmain.set_ylim([yminmain, ymaxmain])
    axmain.set_xscale("log")

    xErrs = np.array(ao.xErrs())
    yErrs = np.array(ao.yErrs())
    xVals = np.array(ao.xVals())
    yVals = np.array(ao.yVals())
    xEdges = np.append(ao.xMins(), ao.xMax())
    yEdges = np.append(ao.yVals(), ao.yVals()[-1])

    label=r"$\frac{{{}}}{{{}}}$".format(LABELS[0], LABELS[1])

    axmain.errorbar(xVals, yVals, xerr=xErrs.T, yerr=yErrs.T, color=COLORS[0], linestyle="none", linewidth=1.4, capthick=1.4)
    axmain.step(xEdges, yEdges, where="post", color=COLORS[0], linestyle="-", linewidth=1.4, label=label)

    axmain.set_xticks(xticks)
    axmain.set_xticklabels(xticks)

    if not args.NOLEGEND:
        axmain.legend()

    name = name.replace("/","_").strip("_")

    fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)), bbox_inches="tight")
    fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.pdf".format(name)), bbox_inches="tight")

    # yoda.plot(
    #     ao,
    #     outfile=os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)),
    #     ratio=False,
    #     show=False,
    #     axmain=axmain
    # )

