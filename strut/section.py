import collections
from strut.material import Hognestad, Trilinear
import meshpy.triangle as triangle
from strut.utils import get_value_xml
import numpy as np
import math
from strut.defaults import N_CIRCLE_SEGMENTS, N_MAX_ELEMENTS

TOLERANCE = 1e-15

def round_trip_connect(start, end):
    result = []
    for i in range(start, end):
        result.append((i, i+1))
    result.append((end, start))
    return result

def check_line_which_side(l0, l1, p):
    result = (l1[0]-l0[0]) * (p[1]-l0[1]) - (p[0]-l0[0]) * (l1[1]-l0[1])
    if abs(result) < TOLERANCE:
        result = 0
    return result

def transpose_list_of_lists(l):
    return list(map(list, zip(*l)))


class Section:
    def __init__(self, soup):
        geometry = soup.strut.section.geometry

        self.materials = {}

        for material in soup.strut.section.materials.find_all("material"):
            if material["type"] == "hognestad":
                self.materials[material["name"]] = Hognestad(material)
            elif material["type"] == "trilinear":
                self.materials[material["name"]] = Trilinear(material)

        self.parts = []

        for part in geometry.find_all("part"):

            if part["type"] == "polygon":
                new_part = PolygonSectionPart(part)
            elif part["type"] == "circle":
                new_part = CircleSectionPart(part)

            new_part.set_material(self.materials[part["material"]])

            self.parts.append(new_part)

    def moment(self, curvature, offset):
        total_moment = 0
        for part in self.parts:
            total_moment += part.moment(curvature, offset)
        return total_moment

    def force(self, curvature, offset):
        total_force = 0
        for part in self.parts:
            force = part.force(curvature, offset)
            total_force += force
        return total_force

    def mesh(self):
        for part in self.parts:
            part.mesh_and_generate_structures()

        total_area = sum([part.total_area() for part in self.parts])
        max_volume = total_area / N_MAX_ELEMENTS

        for part in self.parts:
            part.mesh_and_generate_structures(max_volume=max_volume)

    def get_offset_bounds_for_nonzero_force(self, curvature):
        # import matplotlib
        # matplotlib.rcParams['backend'] = "Qt4Agg"
        # import matplotlib.pyplot as pl

        bounding_points = []
        for part in self.parts:
            bounding_points += part.vertical_bounding

            asdf = transpose_list_of_lists(part.vertical_bounding + [part.vertical_bounding[0]])

            # pl.plot(asdf[1], asdf[0])

        offset_bounds = set()


        for p in bounding_points:
            offset = p[1] - curvature * p[0]
            test_line = [(0, offset),(1, curvature + offset)]

            # pl.plot(transpose_list_of_lists(test_line)[1],transpose_list_of_lists(test_line)[0])

            projections = []

            for q in bounding_points:
                # import pdb; pdb.set_trace()
                projections.append(check_line_which_side(test_line[0], test_line[1], q))


            if all(i >= 0 for i in projections) or all(i <= 0 for i in projections):
                # print("*", [i<=0 for i in projections], p)
                offset_bounds.add(offset)
            # else:
                # print([i<=0 for i in projections], p)


        # for offset in offset_bounds:
        #     test_line = [(-offset/curvature, 0),(0, offset)]

        #     pl.plot(transpose_list_of_lists(test_line)[1],transpose_list_of_lists(test_line)[0])

        # print(set(offset_bounds))

        # pl.show()
        # import sys
        # sys.exit()

        if len(offset_bounds) != 2:
            raise Exception("Something is wrong")
            # print(projections)
        # print(len(bounding_points))
        return (min(offset_bounds), max(offset_bounds))

    def write_gnuplot_mesh(self, filename, facets=False):
        lines = []
        for part in self.parts:
            part_lines = part.gnuplot_mesh_lines(filename, facets=facets)
            # print(len(part_lines))
            lines += part_lines
            # lines.append("")
        open(filename, "w").write("\n".join(lines))

class SectionPart:
    material = None
    mesh = None
    area_vector = None
    centroid_matrix = None

    def __init__(self):
        pass

    def set_material(self, material):
        self.material = material

    def moment(self, curvature, offset):

        neutral_axis = -1 * offset / curvature

        moment_arm = self.centroid_matrix[:,1] - neutral_axis
        stress = np.vectorize(lambda strain: self.material.stress(strain))
        strain = curvature * self.centroid_matrix[:,1] + offset

        moment = np.sum(self.area_vector * moment_arm * stress(strain))

        # moment = 0.
        # for idx in range(len(self.mesh.elements)):
        #     # centroid = element_centroid(self.mesh, idx)
        #     # area = element_area(self.mesh, idx)
        #     area = self.area_vector[idx]
        #     moment_arm = self.centroid_matrix[idx,1] - neutral_axis
        #     strain = curvature * self.centroid_matrix[idx,1] + offset
        #     moment += self.material.stress(strain) * area * moment_arm

        return moment

    def force(self, curvature, offset):

        stress = np.vectorize(lambda strain: self.material.stress(strain))
        strain = curvature * self.centroid_matrix[:,1] + offset
        force = self.area_vector.dot(stress(strain))

        # force = np.sum(force_vector)

        # force = 0.
        # for idx in range(len(self.mesh.elements)):
        #     # centroid = element_centroid(self.mesh, idx)
        #     # area = element_area(self.mesh, idx)
        #     area = self.area_vector[idx]
        #     strain = curvature * self.centroid_matrix[idx,1] + offset
        #     tmp = self.material.stress(strain) * area
        #     # print(self.material, strain)
        #     force += tmp

        return force

    def total_area(self):
        if self.area_vector is None:
            self.generate_area_vector()
        return np.sum(self.area_vector)

    def generate_area_vector(self):
        area_vector = []
        for idx in range(len(self.mesh.elements)):
            area_vector.append(element_area(self.mesh, idx))
        self.area_vector = np.array(area_vector)

    def generate_centroid_matrix(self):
        centroid_matrix = []
        for idx in range(len(self.mesh.elements)):
            centroid_matrix.append(element_centroid(self.mesh, idx))
        self.centroid_matrix = np.array(centroid_matrix)

    def mesh_and_generate_structures(self, max_volume=None):
        self.generate_mesh(max_volume=max_volume)
        self.generate_area_vector()
        self.generate_centroid_matrix()
        self.generate_vertical_bounding_values()

    def generate_vertical_bounding_values(self):
        self.vertical_bounding = [
            (min(self.centroid_matrix[:,1]), self.material.min_strain),
            (max(self.centroid_matrix[:,1]), self.material.min_strain),
            (max(self.centroid_matrix[:,1]), self.material.max_strain),
            (min(self.centroid_matrix[:,1]), self.material.max_strain),
        ]
        # print(self.vertical_bounding)

    def generate_mesh(self, max_volume=None):
        pass

    def gnuplot_mesh_lines(self, filename, facets=False):
        result = []
        gp_file = open(filename, "w")

        if facets:
            segments = self.mesh.facets
        else:
            segments = self.mesh.elements

        for points in segments:
            for pt in points:
                result.append("%f %f" % tuple(self.mesh.points[pt]))
            result.append("%f %f" % tuple(self.mesh.points[points[0]]))
            result.append("")

        return result

class PolygonSectionPart(SectionPart):
    def __init__(self, soup):
        self.vertices = []

        for i in soup.vertices.find_all("vertex"):
            self.vertices.append((float(i["x"]), float(i["y"])))

    def generate_mesh(self, max_volume=None):
        info = triangle.MeshInfo()
        info.set_points(self.vertices)
        info.set_facets(round_trip_connect(0, len(self.vertices)-1))

        if max_volume:
            self.mesh = triangle.build(info, max_volume=max_volume, min_angle=25)
        else:
            self.mesh = triangle.build(info, min_angle=25)

        # triangle.write_gnuplot_mesh("triangles.dat", self.mesh)


class CircleSectionPart(SectionPart):
    def __init__(self, soup):
        self.center = (float(soup.vertex["x"]), float(soup.vertex["y"]))

        self.radius = get_value_xml(soup, "radius")

        self.vertices = get_circle_points(self.center, self.radius, N_CIRCLE_SEGMENTS)

    def generate_mesh(self, max_volume=None):
        info = triangle.MeshInfo()
        info.set_points(self.vertices)
        info.set_facets(round_trip_connect(0, len(self.vertices)-1))

        if max_volume:
            self.mesh = triangle.build(info, max_volume=max_volume, min_angle=25)
        else:
            self.mesh = triangle.build(info, min_angle=25)


def get_circle_points(center, radius, n_segments):
    center = np.array(center)
    points = []

    for theta in np.linspace(0, 2 * math.pi, n_segments + 1):
        new_point = center + np.array(
            (radius * math.cos(theta),
             radius * math.sin(theta)))

        points.append(new_point.tolist())
    return points

def element_area(mesh, idx):
    p1 = mesh.points[mesh.elements[idx][0]]
    p2 = mesh.points[mesh.elements[idx][1]]
    p3 = mesh.points[mesh.elements[idx][2]]

    area = abs(0.5*(p1[0] * (p2[1]-p3[1]) +
                    p2[0] * (p3[1]-p1[1]) +
                    p3[0] * (p1[1]-p2[1])))

    return area

def element_centroid(mesh, idx):
    p1 = mesh.points[mesh.elements[idx][0]]
    p2 = mesh.points[mesh.elements[idx][1]]
    p3 = mesh.points[mesh.elements[idx][2]]

    centroid = ((p1[0]+p2[0]+p3[0])/3., (p1[1]+p2[1]+p3[1])/3.)

    return centroid

