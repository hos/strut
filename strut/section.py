import collections
from strut.material import Hognestad, Trilinear
import meshpy.triangle as triangle
from strut.utils import get_value_xml
import numpy as np
import math
from strut.defaults import N_CIRCLE_SEGMENTS

def round_trip_connect(start, end):
  result = []
  for i in range(start, end):
      result.append((i, i+1))
  result.append((end, start))
  return result


class Section:
    def __init__(self, soup):
        # print(soup.strut)

        geometry = soup.strut.section.geometry
        # geometry = section["geometry"]

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
            # print(part.material, force)
            total_force += force
        return total_force


    def mesh(self):
        for part in self.parts:
            part.mesh()


class SectionPart:
    material = None
    mesh = None

    def __init__(self):
        pass

    def set_material(self, material):
        self.material = material

    def moment(self, curvature, offset):
        neutral_axis = -1 * offset / curvature

        moment = 0.

        for idx in range(len(self.mesh.elements)):
            centroid = element_centroid(self.mesh, idx)
            area = element_area(self.mesh, idx)
            moment_arm = centroid[1] - neutral_axis
            strain = curvature * centroid[1] + offset
            moment += self.material.stress(strain) * area * moment_arm

        return moment

    def force(self, curvature, offset):
        force = 0.

        for idx in range(len(self.mesh.elements)):
            centroid = element_centroid(self.mesh, idx)
            area = element_area(self.mesh, idx)
            strain = curvature * centroid[1] + offset
            tmp = self.material.stress(strain) * area
            # print(self.material, strain)
            force += tmp

        return force

    def mesh(self):
        pass

class PolygonSectionPart(SectionPart):
    def __init__(self, soup):
        self.vertices = []

        for i in soup.vertices.find_all("vertex"):
            self.vertices.append((float(i["x"]), float(i["y"])))

    def mesh(self):
        info = triangle.MeshInfo()
        info.set_points(self.vertices)
        info.set_facets(round_trip_connect(0, len(self.vertices)-1))

        self.mesh = triangle.build(info, max_volume=1e-3, min_angle=25)

        # triangle.write_gnuplot_mesh("triangles.dat", self.mesh)


class CircleSectionPart(SectionPart):
    def __init__(self, soup):
        self.center = (float(soup.vertex["x"]), float(soup.vertex["y"]))

        self.radius = get_value_xml(soup, "radius")

        self.vertices = get_circle_points(self.center, self.radius, N_CIRCLE_SEGMENTS)


    def mesh(self):
        info = triangle.MeshInfo()
        info.set_points(self.vertices)
        info.set_facets(round_trip_connect(0, len(self.vertices)-1))

        self.mesh = triangle.build(info, max_volume=1e-3, min_angle=25)

        # import pdb; pdb.set_trace()

        # for points in self.mesh.elements:
        #     print("ASD")
        #     for pt in points:
        #         print(self.mesh.points[pt])

        # for idx in range(len(self.mesh.elements)):
        #     print(element_centroid(self.mesh, idx))
        #     # print(element_area(self.mesh, idx))


        # for value in soup.find_all("value"):
        #     if value["name"] == "radius":
        #         self.radius = value["v"]

        # print(self.center, self.radius)


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

