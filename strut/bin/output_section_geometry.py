import logging
logging.basicConfig(level=logging.INFO)

import argparse
import logging
import sys
from strut.section import Section
from bs4 import BeautifulSoup

import numpy as np
import scipy.optimize

from strut.material import *


logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument("input", type = str,
                    help = "Input file")
parser.add_argument("-o", "--output", type = str, required=True,
                    help = "Output csv file")
parser.add_argument("-f", "--facets", action="store_true",
                    help = "Just output the edges and not the mesh itself.")


def __main__():

    # import matplotlib
    # matplotlib.rcParams['backend'] = "Qt4Agg"
    # import matplotlib.pyplot as pl

    args = parser.parse_args()

    soup = BeautifulSoup(open(args.input, "r").read(), "html5lib")

    section = Section(soup)
    section.mesh()

    section.write_gnuplot_mesh(args.output, facets=args.facets)

if __name__ == "__main__":
    __main__()
