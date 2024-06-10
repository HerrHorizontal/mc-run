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

from util import json_numpy_obj_hook, adjust_lightness

COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"]
XTICKS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]

parser = argparse.ArgumentParser(
    description="Plot a comparison of NP-correction factors created in multiple campaigns",
    add_help=True
)
parser.add_argument(
    "-c", "--campaign",
    action="append",
    type=str,
    help="Campaign identifier and dictionary containing the bins as key and corresponding fitting files as values"
)
parser.add_argument(
    "-f", "--fit",
    action="append",
    type=json.loads,
    help="Campaign identifier and dictionary containing the bins as key and corresponding fitting files as values"
)
parser.add_argument(
    "--mods",
    dest = "CAMPAIGN_MODS",
    type=json.loads,
    required = True,
    help = "Dictionary containing the plot style and label modifications for the individual campaigns"
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
    "--supress-legend", "-l",
    dest="NOLEGEND",
    action='store_true',
    help="supress plotting the legend"
)

args = parser.parse_args()

LABELS = [args.full_label, args.partial_label]

if not os.path.isdir(args.PLOTDIR):
    os.mkdir(args.PLOTDIR)

xlabel=args.XLABEL
ylabel=args.YLABEL#

CAMPAIGN_MODS = args.CAMPAIGN_MODS

jets = None
if args.JETS:
    jets = args.JETS

splittings = None
if args.SPLITTINGS:
    splittings = args.SPLITTINGS

aos_dicts = dict()
for campaign, fitfiles in zip(args.campaign, args.fit):
    for fitfile, bin in fitfiles.items():
        for jet in jets.values():
            if jet["ident"] in fitfile:
                with open(fitfile) as f:
                    aos_dicts["_".join([campaign, jet["ident"], bin])] = json.load(f, object_hook=json_numpy_obj_hook)
                    aos_dicts["_".join([campaign, jet["ident"], bin])]["path"] = fitfile


xmin = min(np.min(ao["xs"]) for ao in aos_dicts.values())*0.9
xmax = max(np.max(ao["xs"]) for ao in aos_dicts.values())*1.1

print("x-Range: ", xmin, xmax)

xticks = [x for x in XTICKS if x<=xmax and x>=xmin]


# make a plot for each splitting and jet combination
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

        # set styles for individual analysis objects
        campaigns = []
        shifts = []
        labels = []
        colors = []
        markers = []
        linestyles = []
        lnames = []
        aos = []
        print("splits: {}".format(len(splits)))
        for i,(k,v) in enumerate(reversed(sorted(splits.items()))):
            print("aos: {}".format(len(aos_dicts)))
            for name, ao in aos_dicts.items():
                if k in name and jet["ident"] in name:
                    print("campaigns: {}".format(len(args.fit)))
                    for campaign in args.campaign:
                        if campaign in name:
                            yminmain = min(v["ylim"][0], yminmain)
                            ymaxmain = max(v["ylim"][1], ymaxmain)
                            campaigns.append(campaign)
                            shifts.append(i)
                            labels.append(r"{}".format(v["label"]).replace("\n", " "))
                            colors.append(adjust_lightness(v["color"],CAMPAIGN_MODS[campaign]["lightencolor"]))
                            markers.append(v["marker"])
                            linestyles.append(CAMPAIGN_MODS[campaign]["linestyle"])
                            lnames.append(name.replace(v["ident"],k))
                            aos.append(ao)
            axmain.set_ylim([yminmain, (ymaxmain-1)+(i+1)])
            axmain.axhline(1.0*(0.5*i+1), color="gray") #< Ratio = 1 marker line

        assert(len(campaigns) > 0)
        assert(len(campaigns) == len(aos))
        assert(len(shifts) == len(aos))
        assert(len(colors) == len(aos))
        assert(len(linestyles) == len(aos))
        assert(len(labels) == len(aos))

        # plot
        for i, (campaign, shift, label, color, marker, linestyle, lname, ao) in enumerate(reversed(list(zip(campaigns, shifts, labels, colors, markers, linestyles, lnames, aos)))):
            print("Plot bin {} for campaign {} ...".format(label, campaign))
            print(shift, color, marker, linestyle, lname)
            xVals = np.array(ao["xs"])
            # print("x: {}".format(xVals))
            yVals = np.array(ao["ys"])
            # print("y: {}".format(yVals))
            yErrs = np.array(ao["yerrs"])
            # print("y_err: {}".format(yErrs))
            assert(xVals.shape == yVals.shape)
            assert(yVals.shape == yErrs.shape)

            if i % len(args.campaign) == 1:
                label = label+" (+{:.1f})".format(0.5*shift)
            else:
                label = None

            axmain.plot(
                xVals, yVals+(0.5*shift),
                color=color, linestyle=linestyle, label=label
            )
            axmain.fill_between(
                xVals, yVals+yErrs+(0.5*shift), yVals-yErrs+(0.5*shift),
                facecolor=color, alpha=0.5
            )

        axmain.set_xticks(xticks)
        axmain.set_xticklabels(xticks)
        axmain.yaxis.get_ticklocs(minor=True)
        axmain.minorticks_on()

        if not args.NOLEGEND:
            handles, labels = axmain.get_legend_handles_labels()
            campaign_handles = []
            # adjust legend handles for plotted analysis objects
            for handle in handles:
                campaign_handle = mpl.lines.Line2D([0],[0],color="black")
                campaign_handle.update_from(handle)
                campaign_handle.set_linestyle("solid")
                campaign_handles.append(campaign_handle)
            # add legend handles and labels to distinguish campaigns
            for campaign in args.campaign:
                add_handle = mpl.lines.Line2D([0],[0],color="black")
                add_handle.update_from(handles[-1])
                add_handle.set_color(adjust_lightness("black",CAMPAIGN_MODS[campaign]["lightencolor"]))
                add_handle.set_linestyle(CAMPAIGN_MODS[campaign]["linestyle"])
                campaign_handles = [add_handle] + campaign_handles
                campaign_label = CAMPAIGN_MODS[campaign]["label"]
                labels = [campaign_label] + labels
            assert(len(handles)+len(args.campaign) == len(campaign_handles))
            axmain.legend(campaign_handles, labels, frameon=False, handlelength=1.5, loc='upper right')

        axmain.text(
            x=0.03, y=0.97,
            s=jet["label"],
            fontsize=12,
            ha='left', va='top',
            transform=axmain.transAxes
        )
        # axmain.set_title(label=CAMPAIGN_MODS["LHC-LO-ZplusJet"]["label"], loc='left')

        name = "{}_{}_summary".format(jet["ident"], sname)
        print("name: {}".format(name))

        fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.png".format(name)), bbox_inches="tight")
        fig.savefig(os.path.join(os.getcwd(), args.PLOTDIR, "{}.pdf".format(name)), bbox_inches="tight")

        plt.close()