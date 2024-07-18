# -*- coding: utf-8 -*-

import argparse
import json
import os
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import yoda

from fit import scipy_fit as fit
from util import NumpyEncoder, json_numpy_obj_hook, valid_yoda_file


COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"]
XTICKS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]

GENERATOR_LABEL_DICT = {
    "herwig": r"MG $\oplus$ Herwig7",
    "sherpa": "Sherpa",
}


parser = argparse.ArgumentParser(
    description = "Plot (non-perturbative correction factors by computing) the ratio of analysis objects in (and origin nominator and denominator) YODA file(s)",
    add_help = True
)
parser.add_argument(
    "--fit",
    dest = "FIT",
    type = json.loads,
    help = "Optional dictionary of histogram names and corresponding JSON files containing fit results. If not given or non-existent, fits will be rerun."
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
    type=str,
    help="only write out histograms whose path matches this regex"
)
parser.add_argument(
    "-M", "--unmatch",
    dest="UNMATCH",
    metavar="PATT",
    default=None,
    type=str,
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
parser.add_argument(
    "--fit-method",
    dest="METHOD",
    choices=("Nelder-Mead","trust-exact","BFGS"),
    default="Nelder-Mead",
    help="optimizer method for performing the smoothing fit"
)
parser.add_argument(
    "--generator",
    choices=("herwig","sherpa"),
    default=None,
    help="Generator name to be used as plot title"
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

# yoda.plotting.mplinit(engine='MPL', font='TeX Gyre Pagella', fontsize="large", mfont=None, textfigs=True)

xmin = min(ao.xMin() for ao in aos_ratios.values())
xmax = max(ao.xMax() for ao in aos_ratios.values())

xticks = [x for x in XTICKS if x<=xmax and x>=xmin]

xlabel=args.XLABEL
ylabel=args.YLABEL

splittings = None
if args.SPLITTINGS:
    splittings = args.SPLITTINGS

jets = {"": dict(ident="", label="", linestyle="solid")}
if args.JETS:
    jets = args.JETS

fits_given = None
if args.FIT:
    fits_given = args.FIT

for sname, splits in splittings.items():
    for jet in jets.values():
        fig = plt.figure()
        fig.set_size_inches(6,2*0.5*len(splits))
        axmain = fig.add_subplot(1,1,1)

        axmain.set_xlabel(
            xlabel=r"{}".format(xlabel),
            x=1,
            ha="right",
            labelpad=None,
            fontsize="large"
        )
        axmain.set_ylabel(
            ylabel=r"$\frac{{{}}}{{{}}}+$X".format(LABELS[0], LABELS[1]),
            y=1,
            ha="right",
            labelpad=None,
            fontsize="large"
        )

        yminmain = args.yrange[0]
        ymaxmain = args.yrange[1]

        axmain.set_xlim([xmin, xmax])
        axmain.set_xscale("log")

        binlabels = []
        colors = []
        markers = []
        lnames = []
        aos = []
        for i,(k,v) in enumerate(sorted(splits.items())):
            for name, ao in aos_ratios.items():
                if v["ident"] in name and jet["ident"] in name:
                    yminmain = min(v["ylim"][0], yminmain)
                    ymaxmain = max(v["ylim"][1], ymaxmain)
                    binlabels.append(r"{}".format(v["label"]).replace("\n", " "))
                    colors.append(v["color"])
                    markers.append(v["marker"])
                    lnames.append(name.replace(v["ident"],k))
                    aos.append(ao)
                else:
                    continue
            axmain.set_ylim([yminmain, (ymaxmain-1)+(i+1)])
            axmain.axhline(1.0*(0.5*i+1), color="gray") #< Ratio = 1 marker line

        assert(len(binlabels) == len(aos))

        for i, (label, color, marker, lname, ao) in enumerate(reversed(list(zip(binlabels, colors, markers, lnames, aos)))):
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

            if fits_given:
                match = False
                # print("\t\tMatching {} in {}".format(jet["ident"], lname))
                for k,v in fits_given.items():
                    # print("\tMatching {} in {}?".format(v,lname))
                    if v in lname and jet["ident"] in k:
                        # print("\t\t\tMatch found! \n\t\t\t{} \n\t\t\tfor {}".format(k,lname))
                        match = True
                        if os.path.isfile(k):
                            with open(k, "r") as f:
                                fit_results = json.load(f, object_hook=json_numpy_obj_hook)
                        else:
                            raise RuntimeError("Found match, but fit file {} doesn't exist!".format(k))
                        if match:
                            break
                if not match:
                    print("No matching fit file found for {}! Misconfiguration? Writing to {}".format(lname, k))
                    fit_results = fit(xVals, yVals, np.amax(yErrs, axis=1), N_PARS=3, method=args.METHOD)
                    with open(k, "w") as f:
                        json.dump(fit_results, f, cls=NumpyEncoder)
            else:
                fit_results = fit(xVals, yVals, np.amax(yErrs, axis=1))

            xEdgesF = xEdges
            yEdgesF = np.append(fit_results["ys"], fit_results["ys"][-1])
            yEdgesFup = np.append(fit_results["ys"]+fit_results["yerrs"], (fit_results["ys"]+fit_results["yerrs"])[-1])
            yEdgesFdown = np.append(fit_results["ys"]-fit_results["yerrs"], (fit_results["ys"]-fit_results["yerrs"])[-1])
            # axmain.plot(
            #     xVals, fit_results["ys"]+(0.5*i),
            #     color=color, linestyle='-'
            # )
            # axmain.fill_between(
            #     xVals, fit_results["ys"]+fit_results["yerrs"]+(0.5*i), fit_results["ys"]-fit_results["yerrs"]+(0.5*i),
            #     facecolor=color, alpha=0.5
            # )
            axmain.step(xEdgesF, yEdgesF+(0.5*i), where="post", color=color, linestyle="-", label=label)
            axmain.fill_between(
                xEdgesF, yEdgesFup+(0.5*i), yEdgesFdown+(0.5*i),
                step="post",
                facecolor=color, alpha=0.5
            )

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
            fontsize="large",
            ha='left', va='top',
            transform=axmain.transAxes
        )

        title = ""
        if args.generator:
            title = GENERATOR_LABEL_DICT[args.generator]
        axmain.set_title(label=title, loc='left')

        name = "{}_{}_{}_summary".format(args.MATCH, jet["ident"], sname)
        print("name: {}".format(name))

        fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)), bbox_inches="tight")
        fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.pdf".format(name)), bbox_inches="tight")

        plt.close()
