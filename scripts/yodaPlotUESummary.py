# -*- coding: utf-8 -*-

import argparse
import os.path
import matplotlib as mpl

mpl.use("Agg")
import yoda

from util import valid_yoda_file

parser = argparse.ArgumentParser(
    description = "Plot multiple Rick-Field-style UE observables for different phase-space regions into summary plots",
    add_help = True
)
parser.add_argument(
    "--in",
    type = valid_yoda_file,
    required = True,
    help = "YODA file containing the analyzed Rick-Field-style UE observables in analysis objects"
)
parser.add_argument(
    "--label",
    type = str,
    default = "full",
    help = "Legend label for the quantity"
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
    "-m", "--match",
    dest="MATCH",
    metavar="PATT",
    default=None,
    type=str,
    nargs="*",
    help="only write out analysis objects whose path matches these regexes"
)
parser.add_argument(
    "-M", "--unmatch",
    dest="UNMATCH",
    metavar="PATT",
    default=None,
    type=str,
    nargs="*",
    help="exclude analysis objects whose path matches these regexes"
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
    "--plot-dir", "-p",
    dest="PLOTDIR",
    type=str,
    default="plots",
    help="output path for the directory containing the ratio plots"
)
parser.add_argument(
    "--output-file", "-o",
    dest="OUTFILE",
    type=str,
    default="ratios.dat",
    help="output path for the YODA file containing the ratios"
)

args = parser.parse_args()


