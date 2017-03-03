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


def __main__():

    # import matplotlib
    # matplotlib.rcParams['backend'] = "Qt4Agg"
    # import matplotlib.pyplot as pl

    args = parser.parse_args()

    soup = BeautifulSoup(open(args.input, "r").read(), "html5lib")

    section = Section(soup)
    section.mesh()

    def solve_for_offset(section, curvature):
        def f(p):
            force = section.force(curvature, p)
            return force

        # try:
        #     result = scipy.optimize.newton(f, 0.)
        # except:
        #     return float("nan")

        roots, error = scipy.optimize.leastsq(f, [0.])
        result = roots[0]
        error = abs(section.force(curvature, result))

        if error > 1e-5:
            return float("nan")
        else:
            return result

    curvatures = np.linspace(-5e-3, -1e-10, 200)
    offsets = []
    moments = []
    forces = []

    ofile = open(args.output, "w")

    for curvature in curvatures:
        offset = solve_for_offset(section, curvature)
        moment = section.moment(curvature, offset)
        force = section.force(curvature, offset)
        print(offset, force)

        ofile.write("%e %e %e %e\n"%(curvature, offset, force, moment))
        ofile.flush()

    # for curvature, offset, force, moment in zip(curvatures, offsets, forces, moments):

    # pl.plot(-1*np.array(curvatures), -1*np.array(moments), "+-", linewidth=3)
    # pl.show()

    # hognestad = section.parts[0].material
    # x = np.linspace(-0.005, 0.005, 200)
    # y = [hognestad.stress(i) for i in x]
    # pl.plot(x,y)
    # pl.show()

    # trilinear = section.parts[1].material
    # x = np.linspace(-0.16, 0.16, 200)
    # y = [trilinear.stress(i) for i in x]
    # pl.plot(x,y)
    # pl.show()


if __name__ == "__main__":
    __main__()
