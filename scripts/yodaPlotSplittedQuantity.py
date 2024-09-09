# -*- coding: utf-8 -*-

import argparse
import json
import os.path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yoda
from util import valid_yoda_file

XTICKS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
GENERATOR_LABEL_DICT = {
    "herwig": "Herwig7",
    "sherpa": "Sherpa",
}


parser = argparse.ArgumentParser(
    description="Plot multiple Rick-Field-style UE observables for different phase-space regions into summary plots",
    add_help=True,
)
parser.add_argument(
    "--in",
    dest="INFILE",
    type=valid_yoda_file,
    required=True,
    help="YODA file containing the analyzed Rick-Field-style UE observables in analysis objects",
)
parser.add_argument(
    "--generator",
    choices=("herwig", "sherpa"),
    default=None,
    help="Generator name to be used as plot title",
)
parser.add_argument(
    "--xlabel",
    dest="XLABEL",
    type=str,
    default="Observable",
    help="label for the x-axis to plot",
)
parser.add_argument(
    "--ylabel",
    dest="YLABEL",
    type=str,
    default="NP corr.",
    help="label for the y-axis to plot",
)
parser.add_argument(
    "--yrange",
    nargs=2,
    type=float,
    default=[0.8, 1.3],
    metavar=("ymin", "ymax"),
    help="range for the y-axis of the ratio plot",
)
parser.add_argument(
    "-m",
    "--match",
    dest="MATCH",
    metavar="PATT",
    default=None,
    type=json.loads,
    help="only write out analysis objects whose path matches this regex",
)
parser.add_argument(
    "-M",
    "--unmatch",
    dest="UNMATCH",
    metavar="PATT",
    default=None,
    type=json.loads,
    help="exclude analysis objects whose path matches this regex",
)
parser.add_argument(
    "--splittings",
    "-s",
    dest="SPLITTINGS",
    type=json.loads,
    help="optional dictionary containing identifier used to match the analysis objects to plot and additional labels and axis-limits",
)
parser.add_argument(
    "--add-splittings-labels",
    dest="LABELS",
    type=str,
    nargs="*",
    help="additional plot labels to be plotted into canvas area under jet label, one per splitting",
)
parser.add_argument(
    "--jets",
    "-j",
    dest="JETS",
    type=json.loads,
    help="optional dictionary containing identifier used to match the jet splittings to plot and additional labels and styles",
)
parser.add_argument(
    "--plot-dir",
    "-p",
    dest="PLOTDIR",
    type=str,
    default="plots",
    help="output path for the directory containing the ratio plots",
)

args = parser.parse_args()


yoda_file = args.INFILE

print(f"match: {args.MATCH}")
print(f"unmatch: {args.UNMATCH}")

aos_dict = yoda.readYODA(
    yoda_file, asdict=True, patterns=list(args.MATCH), unpatterns=list(args.UNMATCH)
)

import pprint

pp = pprint.PrettyPrinter(depth=2)
print("analysis objects:")
pp.pprint(aos_dict)

# plot the analysis objects
if not os.path.isdir(args.PLOTDIR):
    os.mkdir(args.PLOTDIR)

xmin = min(ao.xMin() for ao in aos_dict.values())
xmax = max(ao.xMax() for ao in aos_dict.values())

xticks = [x for x in XTICKS if x <= xmax and x >= xmin]

xlabel = args.XLABEL
ylabel = args.YLABEL

splittings = None
if args.SPLITTINGS:
    splittings = args.SPLITTINGS

jets = {"": dict(ident="", label="", linestyle="solid")}
if args.JETS:
    jets = args.JETS

if args.LABELS:
    add_splittings_labels = args.LABELS
    assert len(add_splittings_labels) == len(splittings.keys())
else:
    add_splittings_labels = None

for i_s, (sname, splits) in enumerate(splittings.items()):
    for jet in jets.values():
        fig = plt.figure()
        fig.set_size_inches(6, 5 + (len(splits) - 5) / 2)
        axmain = fig.add_subplot(1, 1, 1)

        axmain.set_xlabel(
            xlabel=r"{}".format(xlabel),
            x=1,
            ha="right",
            labelpad=None,
            fontsize="large",
        )
        axmain.set_ylabel(
            ylabel=r"{}".format(ylabel),
            y=1,
            ha="right",
            labelpad=None,
            fontsize="large",
        )
        axmain.set_xlim([xmin, xmax])
        axmain.set_xscale("log")

        yminmain = args.yrange[0]
        ymaxmain = args.yrange[1]
        axmain.set_ylim([yminmain, ymaxmain])

        binlabels = []
        colors = []
        markers = []
        lnames = []
        aos = []
        for i, (k, v) in enumerate(sorted(splits.items())):
            for name, ao in aos_dict.items():
                # print("ident: {}".format(v["ident"]))
                # print(f"name: {name}")
                if (
                    v["ident"] in name and list(args.MATCH)[0] in name
                ):  # and jet["ident"] in name:
                    yminmain = min(v["ylim"][0], yminmain)
                    ymaxmain = max(v["ylim"][1], ymaxmain)
                    binlabels.append(r"{}".format(v["label"]).replace("\n", " "))
                    colors.append(v["color"])
                    markers.append(v["marker"])
                    lnames.append(name.replace(v["ident"], k))
                    aos.append(ao)
                else:
                    continue

        # print(f"AOS:\n{aos}")
        assert len(binlabels) == len(aos)
        assert len(colors) == len(aos)
        assert len(markers) == len(aos)
        assert len(lnames) == len(aos)

        for i, (label, color, marker, lname, ao) in enumerate(
            reversed(list(zip(binlabels, colors, markers, lnames, aos)))
        ):
            print("Plot bin {}...".format(label))
            xVals = np.array(ao.xVals())
            yVals = np.array(ao.yVals())
            xErrs = np.array(ao.xErrs())
            try:
                yErrs = np.array(ao.yErrs())
            except:
                # assume a 50% uncertainty if yoda yErrs estimation fails
                # TODO: implement a more robust yErrs method in yoda
                yErrs = yVals * 0.5
            xEdges = np.append(ao.xMins(), ao.xMax())
            yEdges = np.append(ao.yVals(), ao.yVals()[-1])
            yEdgesUp = yEdges + np.append(yErrs, yErrs[-1])
            yEdgesDown = yEdges - np.append(yErrs, yErrs[-1])
            # print(f"\t yVals: {yVals}")

            axmain.plot(xVals, yVals, color=color, linestyle="-", label=label)
            axmain.fill_between(
                xVals, yVals + yErrs, yVals - yErrs, facecolor=color, alpha=0.5
            )
            # axmain.step(xEdges, yEdges, where="post", color=color, linestyle="-", label=label)
            # axmain.fill_between(
            #     xEdges, yEdgesUp, yEdgesDown,
            #     step="post",
            #     facecolor=color, alpha=0.5
            # )

        axmain.set_xticks(xticks)
        axmain.set_xticklabels(xticks)
        axmain.yaxis.get_ticklocs(minor=True)
        axmain.minorticks_on()

        handles, labels = axmain.get_legend_handles_labels()
        axmain.legend(
            reversed(handles),
            reversed(labels),
            frameon=False,
            handlelength=1,
            loc="upper right",
        )

        # plot additional labels
        axmain.text(
            x=0.03,
            y=0.9,
            s=jet["label"],
            fontsize="large",
            ha="left",
            va="top",
            transform=axmain.transAxes,
        )
        axmain.text(
            x=0.03,
            y=0.97,
            s=add_splittings_labels[i_s],
            fontsize="x-large",
            fontweight="demi",
            ha="left",
            va="top",
            transform=axmain.transAxes,
        )

        title = ""
        if args.generator:
            title = GENERATOR_LABEL_DICT[args.generator]
        axmain.set_title(label=title, loc="left")

        name = "{}_{}_{}_summary".format(list(args.MATCH)[0], jet["ident"], sname)
        print("name: {}".format(name))

        fig.savefig(
            os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)),
            bbox_inches="tight",
        )
        fig.savefig(
            os.path.join(os.getcwd(), args.PLOTDIR, "{}.pdf".format(name)),
            bbox_inches="tight",
        )
        plt.close()
