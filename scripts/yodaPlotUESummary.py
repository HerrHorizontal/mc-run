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
    "--full",
    type = valid_yoda_file,
    required = True,
    help = "YODA file containing the analyzed Rick-Field-style UE observables in analysis objects"
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
    "--output-file", "-o",
    dest="OUTFILE",
    type=str,
    default="ratios.dat",
    help="output path for the YODA file containing the ratios"
)

args = parser.parse_args()