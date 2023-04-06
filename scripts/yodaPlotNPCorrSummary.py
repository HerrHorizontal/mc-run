# -*- coding: utf-8 -*-

import argparse
import json
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


def fit(xVal, yVal, yErr):
    """Fit function to ratio points."""
    import scipy.optimize as opt

    N_PARS = 3
    def _f(x, pars):
        return pars[0]*x**(pars[1]) + pars[2]

    def _chi2(pars):
        _res = (_f(xVal, pars) - yVal) / yErr
        return np.sum(_res**2)

    # minimize function and take resulting azimuth
    #result = opt.minimize_scalar(_chi2)
    result = opt.minimize(_chi2, x0=(0,-1,1), bounds=((-np.inf,np.inf),(-np.inf,0),(-10,10)))
    return dict(result=result, pars=result.x, ys=_f(xVal, result.x), chi2ndf=result.fun/(len(xVal)-N_PARS), chi2=result.fun, ndf=(len(xVal)-N_PARS))


parser = argparse.ArgumentParser(
    description = "Plot (non-perturbative correction factors by computing) the ratio of analysis objects in (and origin nominator and denominator) YODA file(s)",
    add_help = True
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
    "--splittings", "-s",
    dest="SPLITTINGS",
    type=json.loads,
    help="optional dictionary containing identifier used to match the analysis objects to plot and additional labels and axis-limits"
)
parser.add_argument(
    "--jets", "-j",
    dest="JETS",
    type=json.loads,
    help="optional dictionary containing identifier used to match the jet splittings to plot and additional labels and styles"
)

args = parser.parse_args()


yoda_file_ratio = args.ratio

LABELS = [args.full_label, args.partial_label]

aos_ratios = yoda.readYODA(yoda_file_ratio, asdict=True, patterns=args.MATCH, unpatterns=args.UNMATCH)

import pprint
pp = pprint.PrettyPrinter(depth=2)
print("ratios:")
pp.pprint(aos_ratios)

# plot the ratio histograms/scatters
if not os.path.isdir(args.PLOTDIR):
    os.mkdir(args.PLOTDIR)

yoda.plotting.mplinit(engine='MPL', font='TeX Gyre Pagella', fontsize=12, mfont=None, textfigs=True)

xmin = min(ao.xMin() for ao in aos_ratios.values())
xmax = max(ao.xMax() for ao in aos_ratios.values())

xticks = [x for x in XTICKS if x<=xmax and x>=xmin]

xlabel=args.XLABEL
ylabel=args.YLABEL

if args.SPLITTINGS:
    splittings = args.SPLITTINGS
if args.JETS:
    jets = args.JETS

for sname, splits in splittings.items():
    for jet in jets.values():
        fig = plt.figure()
        fig.set_size_inches(6,2*0.5*len(splits))
        axmain = fig.add_subplot(1,1,1)

        axmain.set_xlabel(xlabel=r"${}$".format(xlabel), x=1, ha="right", labelpad=None)
        axmain.set_ylabel(ylabel=r"$\frac{{{}}}{{{}}}+$X".format(LABELS[0], LABELS[1]), y=1, ha="right", labelpad=None)

        yminmain = args.yrange[0]
        ymaxmain = args.yrange[1]

        axmain.set_xlim([xmin, xmax])
        axmain.set_xscale("log")

        binlabels = []
        colors = []
        markers = []
        aos = []
        for i,(k,v) in enumerate(sorted(splits.items())):
            for name, ao in aos_ratios.items():
                if v["ident"] in name and jet["ident"] in name:
                    yminmain = min(v["ylim"][0], yminmain)
                    ymaxmain = max(v["ylim"][1], ymaxmain)
                    binlabels.append(r"{}".format(v["label"]).replace("\n", " "))
                    colors.append(v["color"])
                    markers.append(v["marker"])
                    aos.append(ao)
                else:
                    continue
            axmain.set_ylim([yminmain, (ymaxmain-1)+(i+1)])
            axmain.axhline(1.0*(0.5*i+1), color="gray") #< Ratio = 1 marker line

        assert(len(binlabels) == len(aos))

        for i, (label, color, marker, ao) in enumerate(reversed(zip(binlabels, colors, markers, aos))):
            print("Plot bin {}...".format(label))
            xErrs = np.array(ao.xErrs())
            yErrs = np.array(ao.yErrs())
            xVals = np.array(ao.xVals())
            yVals = np.array(ao.yVals())
            xEdges = np.append(ao.xMins(), ao.xMax())
            yEdges = np.append(ao.yVals(), ao.yVals()[-1])

            label = label+" (+{:.1f})".format(0.5*i)
            # axmain.errorbar(xVals, yVals+(0.5*i), xerr=xErrs.T, yerr=yErrs.T, color=color, marker=marker, linestyle="none", linewidth=1.4, capthick=1.4, label=label)
            # axmain.step(xEdges, yEdges, where="post", color=COLORS[0], linestyle="-", linewidth=1.4, label=label)

            fit_results = fit(xVals, yVals, np.amax(yErrs, axis=1))

            xEdgesF = xEdges
            yEdgesF = np.append(fit_results["ys"], fit_results["ys"][-1])
            # axmain.plot(
            #     xVals, fit_results["ys"]+(0.5*i),
            #     color=color, linestyle='-'
            # )
            axmain.step(xEdgesF, yEdgesF+(0.5*i), where="post", color=color, linestyle="-", linewidth=1.8, label=label)

        axmain.set_xticks(xticks)
        axmain.set_xticklabels(xticks)
        axmain.yaxis.get_ticklocs(minor=True)
        axmain.minorticks_on()

        if not args.NOLEGEND:
            handles, labels = axmain.get_legend_handles_labels()
            axmain.legend(reversed(handles), reversed(labels), frameon=False, handlelength=1, loc='upper right')

        axmain.text(
            x=0.03, y=0.97,
            s=jet["label"],
            fontsize=12,
            ha='left', va='top',
            transform=axmain.transAxes
        )
        axmain.set_title(label=r"MG $\oplus$ Herwig7", loc='left')

        name = "{}_{}_{}_summary".format(args.MATCH, jet["ident"], sname)
        print("name: {}".format(name))

        fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)), bbox_inches="tight")
        fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.pdf".format(name)), bbox_inches="tight")

        plt.close()
