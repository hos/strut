from libc.math cimport fabs

def hognestad_stress(double strain,
                     double cracking_stress,
                     double cracking_strain,
                     double ultimate_strain):

    cdef double result

    if strain < 0. and strain >= cracking_strain:
        result = -1 * cracking_stress * ((2 * strain / cracking_strain) - (strain / cracking_strain) * (strain / cracking_strain))
    elif strain < cracking_strain and strain >= ultimate_strain:
        result = -1 * cracking_stress + .15 * cracking_stress * (strain - cracking_strain) / (ultimate_strain - cracking_strain)
    else:
        result = 0.

    return result


def trilinear_stress(double strain,
                     double yield_stress,
                     double youngs_modulus,
                     double hardening_strain,
                     double ultimate_stress,
                     double ultimate_strain,
                     double yield_strain,
                     double youngs_modulus_strain_hardening):

    cdef double result
    cdef double strain_abs = fabs(strain)
    cdef double sign = 1. if strain > 0 else -1.

    if strain_abs <= yield_strain:
        result = sign * strain_abs * youngs_modulus
    elif strain_abs > yield_strain and strain_abs <= hardening_strain:
        result = sign * yield_strain * youngs_modulus
    elif strain_abs > hardening_strain and strain_abs <= ultimate_strain:
        result = sign * (youngs_modulus_strain_hardening * (strain_abs - hardening_strain) + yield_strain * youngs_modulus)
    else:
        result = 0.

    return result





