from strut.utils import get_value_xml
from strut.material_cython import hognestad_stress, trilinear_stress

class Material:
    min_strain = None
    max_strain = None

    def __init__(self):
        pass

    def stress(self, strain):
        pass

    def set_max_min_strain(self, soup):
        self.min_strain = float(soup["min_strain"])
        self.max_strain = float(soup["max_strain"])

class Trilinear(Material):
    def __init__(self, soup):
                 # youngs_modulus,
                 # youngs_modulus_strain_hardening,
                 # yield_strain,
                 # hardening_strain,
                 # ultimate_strain):

        # self.youngs_modulus = youngs_modulus
        # self.youngs_modulus_strain_hardening = youngs_modulus_strain_hardening
        # self.yield_strain = yield_strain
        # self.hardening_strain = hardening_strain
        # self.ultimate_strain = ultimate_strain

        self.yield_stress = get_value_xml(soup, "yield_stress")
        self.youngs_modulus = get_value_xml(soup, "youngs_modulus")
        self.hardening_strain = get_value_xml(soup, "hardening_strain")
        self.ultimate_stress = get_value_xml(soup, "ultimate_stress")
        self.ultimate_strain = get_value_xml(soup, "ultimate_strain")

        self.yield_strain = self.yield_stress / self.youngs_modulus

        self.youngs_modulus_strain_hardening = (self.ultimate_stress - self.yield_stress) / (self.ultimate_strain - self.hardening_strain)

        # import pdb; pdb.set_trace()
        self.set_max_min_strain(soup)

    def stress(self, strain):

        return trilinear_stress(strain,
                                self.yield_stress,
                                self.youngs_modulus,
                                self.hardening_strain,
                                self.ultimate_stress,
                                self.ultimate_strain,
                                self.yield_strain,
                                self.youngs_modulus_strain_hardening)

        # strain_abs = abs(strain)
        # sign = 1. if strain > 0 else -1.

        # if strain_abs <= self.yield_strain:
        #     result = sign * strain_abs * self.youngs_modulus
        # elif strain_abs > self.yield_strain and strain_abs <= self.hardening_strain:
        #     result = sign * self.yield_strain * self.youngs_modulus
        # elif strain_abs > self.hardening_strain and strain_abs <= self.ultimate_strain:
        #     result = sign * (self.youngs_modulus_strain_hardening * (strain_abs - self.hardening_strain) + self.yield_strain * self.youngs_modulus)
        # else:
        #     result = 0.

        # return result


class Hognestad(Material):
    def __init__(self, soup):
                 # cracking_stress,
                 # cracking_strain,
                 # ultimate_strain):

        self.cracking_stress = get_value_xml(soup, "cracking_stress")
        self.cracking_strain = get_value_xml(soup, "cracking_strain")
        self.ultimate_strain = get_value_xml(soup, "ultimate_strain")

        self.cracking_stress = abs(self.cracking_stress)
        self.cracking_strain = -1 * abs(self.cracking_strain)
        self.ultimate_strain = -1 * abs(self.ultimate_strain)

        self.set_max_min_strain(soup)

    def stress(self, strain):
        return hognestad_stress(strain, self.cracking_stress, self.cracking_strain, self.ultimate_strain)
        # if strain < 0. and strain >= self.cracking_strain:
        #     result = -1 * self.cracking_stress * ((2 * strain / self.cracking_strain) - (strain / self.cracking_strain) * (strain / self.cracking_strain))
        # elif strain < self.cracking_strain and strain >= self.ultimate_strain:
        #     result = -1 * self.cracking_stress + .15 * self.cracking_stress * (strain - self.cracking_strain) / (self.ultimate_strain - self.cracking_strain)
        # else:
        #     result = 0.

        # return result

