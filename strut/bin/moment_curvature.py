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
import math

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument("input", type = str,
                    help = "Input file")
parser.add_argument("-o", "--output", type = str, required=True,
                    help = "Output csv file")

RESOLUTION = 1000

def get_bounds(section, curvature):
    bounds = section.get_offset_bounds_for_nonzero_force(curvature)
    offsets = np.flipud(np.linspace(bounds[0], bounds[1], RESOLUTION))
    forces = []

    previous_force = section.force(curvature, offsets[0])
    for i in range(1, len(offsets)):
        force = section.force(curvature, offsets[i])

        if force * previous_force < 0:
            return (offsets[i-1], offsets[i])

        previous_force = force

    return bounds

    # pl.plot(offsets, forces)
    # pl.show()
    # sys.exit()


def __main__():

    import matplotlib
    matplotlib.rcParams['backend'] = "Qt4Agg"
    import matplotlib.pyplot as pl

    args = parser.parse_args()

    soup = BeautifulSoup(open(args.input, "r").read(), "html5lib")

    section = Section(soup)
    section.mesh()

    def solve_for_offset(section, curvature):
        def f(p):
            force = section.force(curvature, p)
            return force

        # min_offset, max_offset = section.get_offset_bounds_for_nonzero_force(curvature)
        min_offset, max_offset = get_bounds(section, curvature)

        roots = scipy.optimize.brentq(f, min_offset, max_offset)

        for part in section.parts:
            if np.sum(np.abs(part.stresses(curvature, roots))) < 1e-10:
                return float("nan")

        return roots

        # try:
        #     result = scipy.optimize.newton(f, max_offset)
        #     return result
        # except:
        #     return float("nan")

        # roots, error = scipy.optimize.leastsq(f, [0.00])
        # result = roots[0]
        # error = abs(section.force(curvature, result))
        # if error > 1e-5:
        #     return float("nan")
        # else:
        #     return result

    curvature_step = get_param_xml(soup.strut.section.analysis, "step_size")
    range_ = get_param_xml(soup.strut.section.analysis, "range")

    if not range_ in ["negative", "positive"]:
        raise Exception("Invalid value for range: %s"%(range_))

    curvatures = []
    offsets = []
    moments = []
    forces = []


    # curvature = -50e-3
    # bounds = section.get_offset_bounds_for_nonzero_force(curvature)
    # offsets = np.linspace(bounds[0], bounds[1], 100)
    # forces = []
    # for i in offsets:
    #     forces.append(section.force(curvature, i))
    # pl.plot(offsets, forces)
    # pl.show()
    # sys.exit()


    ofile = open(args.output, "w")
    ofile.write("# curvature offset force moment\n")

    curvature = 0
    while True:

        if curvature == 0:
            offset = 0
        else:
            offset = solve_for_offset(section, curvature)

        moment = section.moment(curvature, offset)
        force = section.force(curvature, offset)
        print("phi=%.3e, s=%.3e, f=%.3e m=%.3e"%(curvature, offset, force, moment))

        ofile.write("%e %e %e %e\n"%(curvature, offset, force, moment))
        ofile.flush()

        if section.check_for_failure(curvature, offset):
            break

        if range_ == "positive":
            curvature += curvature_step
        else:
            curvature -= curvature_step


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
