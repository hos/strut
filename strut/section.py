import collections
from strut.material import Hognestad, Trilinear
import meshpy.triangle as triangle
from strut.utils import get_value_xml
import numpy as np
import math
from strut.defaults import N_CIRCLE_SEGMENTS, N_MAX_ELEMENTS

def round_trip_connect(start, end):
    result = []
    for i in range(start, end):
        result.append((i, i+1))
    result.append((end, start))
    return result


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
        if self.area_vector != None:
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


    def generate_mesh(self, max_volume=None):
        pass

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

