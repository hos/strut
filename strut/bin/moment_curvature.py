import logging
logging.basicConfig(level=logging.INFO)

# import glob
# import configparser
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
# parser.add_argument("-o", "--output", type = str,
#                     help = "(Optional) Output json file")
# parser.add_argument("-d", "--debug", action="store_true",
#                     help = "(Optional) Debug")


def __main__():

    import matplotlib
    matplotlib.rcParams['backend'] = "Qt4Agg"
    import matplotlib.pyplot as pl

    args = parser.parse_args()

    soup = BeautifulSoup(open(args.input, "r").read(), "html5lib")

    section = Section(soup)
    # print(xmldict)
    section.mesh()

    # print(section.moment(1e-3, 0.5))
    print(section.force(-1e-3, 0.))

    def solve_for_offset(section, curvature):
        def f(p):
            force = section.force(curvature, p)
            # print(force)
            return force
        try:
            roots = scipy.optimize.newton(f, 0.)
            return roots
            # roots = scipy.optimize.leastsq(f, [0.])
            # return roots[0]
        except:
            return 0.
        # print(error)



    # print(solve_for_offset(section, 10e-3))

    curvatures = np.linspace(-5e-3, -1e-5, 200)
    offsets = []
    moments = []

    for i in curvatures:
        offset = solve_for_offset(section, i)
        offsets.append(offset)
        moments.append(section.moment(i, offset))
        print(offset, section.force(i, offset))


    pl.plot(-1*np.array(curvatures), -1*np.array(moments), "+-", linewidth=3)
    pl.show()

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



    # for i in np.linspace(-1,1,100):
    #     print(section.force(1e-3, i))


if __name__ == "__main__":
    __main__()
