#!/usr/bin/env python3
"""
Writes the low-poly models of the game to data/models/: the vehicles (car, van, truck) and the heroes (allan, ghosty,
butcher, frosty), as OBJ files with a MTL file of their colors.

    python3 tools/make_models.py

The models are plain OBJ, so they can just as well be edited in Blender and saved over these. The game expects:

  * The wall is one segment of a concrete barrier, WALL_SEGMENT long along z, which the game repeats along each wall

  * Units are the units of the game. y is up, the model looks towards +z, and it stands on y = 0 with its middle at
    x = z = 0
  * A vehicle's body (the part that gets the color of the car) has the material 'body', whose color is pure white
    (Kd 1 1 1). The game finds it by that color. Nothing else of a vehicle may be pure white
  * The sizes match config.sd: a vehicle is CarWidth wide, and as long as CarLength, VanLength and TruckLength
"""

import math
import os

# Keep these in step with src/aov/config.sd (WALL_SEGMENT is WallSegmentLength)
CAR_WIDTH = 5.2
CAR_LENGTH = 8.0
VAN_LENGTH = 9.0
TRUCK_LENGTH = 16.0
WALL_WIDTH = 3.0
WALL_HEIGHT = 4.0
WALL_SEGMENT = 5.0

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "models")


class Model:
    def __init__(self, name):
        self.name = name
        self.materials = {}          # name -> (r, g, b)
        self.parts = []              # (material, [triangles]); a triangle is 3 (position, normal)

    def material(self, name, color):
        self.materials[name] = color
        return name

    def add(self, material, triangles):
        self.parts.append((material, triangles))

    # A box around its center
    def box(self, material, center, size):
        cx, cy, cz = center
        self.frustum(material, (cx, cy - size[1] / 2, cz), (size[0], size[2]), (size[0], size[2]), size[1])

    # A box whose top can be smaller than its bottom, e.g the cabin of a car. base is the middle of the bottom
    def frustum(self, material, base, bottom, top, height, top_offset_z=0.0):
        bx, by, bz = base
        b = [(bx - bottom[0] / 2, by, bz - bottom[1] / 2), (bx + bottom[0] / 2, by, bz - bottom[1] / 2),
             (bx + bottom[0] / 2, by, bz + bottom[1] / 2), (bx - bottom[0] / 2, by, bz + bottom[1] / 2)]
        t = [(bx - top[0] / 2, by + height, bz + top_offset_z - top[1] / 2), (bx + top[0] / 2, by + height, bz + top_offset_z - top[1] / 2),
             (bx + top[0] / 2, by + height, bz + top_offset_z + top[1] / 2), (bx - top[0] / 2, by + height, bz + top_offset_z + top[1] / 2)]
        quads = [
            (t[3], t[2], t[1], t[0]),        # top
            (b[0], b[1], b[2], b[3]),        # bottom
            (b[3], b[2], t[2], t[3]),        # +z (front)
            (b[1], b[0], t[0], t[1]),        # -z (back)
            (b[2], b[1], t[1], t[2]),        # +x
            (b[0], b[3], t[3], t[0]),        # -x
        ]
        self.add(material, [tri for q in quads for tri in flat_quad(q)])

    # A cylinder along an axis ('x', 'y' or 'z'), e.g a wheel
    def cylinder(self, material, center, radius, length, axis="y", segments=12, radius_end=None):
        if radius_end is None:
            radius_end = radius
        tris = []
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append((math.cos(a), math.sin(a)))

        def point(u, v, along, r):
            if axis == "x":
                return (center[0] + along, center[1] + u * r, center[2] + v * r)
            if axis == "z":
                return (center[0] + u * r, center[1] + v * r, center[2] + along)
            return (center[0] + u * r, center[1] + along, center[2] + v * r)

        h = length / 2
        for i in range(segments):
            u0, v0 = ring[i]
            u1, v1 = ring[(i + 1) % segments]
            p0, p1 = point(u0, v0, -h, radius), point(u1, v1, -h, radius)
            p2, p3 = point(u1, v1, h, radius_end), point(u0, v0, h, radius_end)
            for tri in flat_quad((p0, p1, p2, p3)):
                tris.append(tri)
            c0, c1 = point(0, 0, -h, 0), point(0, 0, h, 0)
            tris.append(flat_tri(c0, p1, p0))
            tris.append(flat_tri(c1, p3, p2))
        self.add(material, fix_winding(tris, center))

    # A sphere, squashed by scale (sx, sy, sz)
    def sphere(self, material, center, radius, scale=(1, 1, 1), rings=8, segments=12):
        tris = []

        def point(r, s):
            theta = math.pi * r / rings
            phi = 2 * math.pi * s / segments
            n = (math.sin(theta) * math.cos(phi), math.cos(theta), math.sin(theta) * math.sin(phi))
            p = (center[0] + n[0] * radius * scale[0], center[1] + n[1] * radius * scale[1], center[2] + n[2] * radius * scale[2])
            return p, normalize((n[0] / scale[0], n[1] / scale[1], n[2] / scale[2]))

        for r in range(rings):
            for s in range(segments):
                a, b, c, d = point(r, s), point(r + 1, s), point(r + 1, s + 1), point(r, s + 1)
                if r != 0:
                    tris.append((a, d, c))          # No triangle of zero size at the poles
                if r != rings - 1:
                    tris.append((a, c, b))
        self.add(material, fix_winding(tris, center, smooth=True))

    def write(self):
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, self.name + ".mtl"), "w") as f:
            f.write("# Generated by tools/make_models.py\n")
            for name, (r, g, b) in self.materials.items():
                f.write(f"\nnewmtl {name}\nKa 0 0 0\nKd {r:.4f} {g:.4f} {b:.4f}\nKs 0 0 0\nd 1\nillum 1\n")

        lines = ["# Generated by tools/make_models.py", f"mtllib {self.name}.mtl", f"o {self.name}", "vt 0 0"]
        positions, normals = [], []
        faces_by_material = {}
        for material, tris in self.parts:
            faces_by_material.setdefault(material, []).extend(tris)
        for material, tris in faces_by_material.items():
            lines.append(f"usemtl {material}")
            for tri in tris:
                idx = []
                for p, n in tri:
                    positions.append(p)
                    normals.append(n)
                    idx.append(len(positions))
                lines.append("f " + " ".join(f"{i}/1/{i}" for i in idx))
        head = [f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}" for p in positions]
        head += [f"vn {n[0]:.4f} {n[1]:.4f} {n[2]:.4f}" for n in normals]
        with open(os.path.join(OUT, self.name + ".obj"), "w") as f:
            f.write("\n".join(lines[:4] + head + lines[4:]) + "\n")
        print(f"{self.name}: {len(positions) // 3} triangles")


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def normalize(v):
    length = math.sqrt(dot(v, v)) or 1
    return (v[0] / length, v[1] / length, v[2] / length)


def flat_tri(a, b, c):
    n = normalize(cross(sub(b, a), sub(c, a)))
    return ((a, n), (b, n), (c, n))


def flat_quad(q):
    return [flat_tri(q[0], q[1], q[2]), flat_tri(q[0], q[2], q[3])]


# Turns triangles to face away from a center (counter-clockwise from outside, as OpenGL wants)
def fix_winding(tris, center, smooth=False):
    out = []
    for tri in tris:
        (a, na), (b, nb), (c, nc) = tri
        face = cross(sub(b, a), sub(c, a))
        middle = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3)
        if dot(face, sub(middle, center)) < 0:
            b, c, nb, nc = c, b, nc, nb
        if not smooth:
            n = normalize(cross(sub(b, a), sub(c, a)))
            na = nb = nc = n
        out.append(((a, na), (b, nb), (c, nc)))
    return out


#
# Vehicles: the body is white, and gets the color of the car in the game
#

def vehicle_parts(m):
    m.material("body", (1, 1, 1))
    m.material("glass", (0.16, 0.22, 0.28))
    m.material("tire", (0.08, 0.08, 0.08))
    m.material("rim", (0.62, 0.62, 0.65))
    m.material("trim", (0.18, 0.18, 0.2))
    m.material("headlight", (1.0, 0.96, 0.78))
    m.material("taillight", (0.85, 0.08, 0.08))


def wheels(m, axles, radius=0.55, width=0.55):
    x = CAR_WIDTH / 2 - width / 2 + 0.05
    for z in axles:
        for side in (-1, 1):
            m.cylinder("tire", (side * x, radius, z), radius, width, axis="x", segments=12)
            m.cylinder("rim", (side * (x + 0.04), radius, z), radius * 0.55, width * 0.9, axis="x", segments=8)


def lights(m, front_z, back_z, y, inset=0.55):
    for side in (-1, 1):
        x = side * (CAR_WIDTH / 2 - inset)
        m.box("headlight", (x, y, front_z), (0.8, 0.32, 0.12))
        m.box("taillight", (x, y, back_z), (0.8, 0.32, 0.12))


def make_car():
    m = Model("car")
    vehicle_parts(m)
    w, l = CAR_WIDTH, CAR_LENGTH
    m.box("body", (0, 0.95, 0), (w, 0.9, l))                                         # The lower body
    m.box("trim", (0, 0.45, l / 2 - 0.1), (w, 0.3, 0.25))                             # Bumpers
    m.box("trim", (0, 0.45, -l / 2 + 0.1), (w, 0.3, 0.25))
    m.frustum("glass", (0, 1.4, -0.3), (w * 0.9, l * 0.55), (w * 0.78, l * 0.36), 0.85, top_offset_z=-0.2)
    m.box("body", (0, 2.3, -0.5), (w * 0.79, 0.12, l * 0.37))                         # The roof
    wheels(m, (l / 2 - 1.5, -l / 2 + 1.5))
    lights(m, l / 2, -l / 2, 1.05)
    m.write()


def make_van():
    m = Model("van")
    vehicle_parts(m)
    w, l = CAR_WIDTH, VAN_LENGTH
    m.box("body", (0, 1.75, -0.6), (w, 2.5, l - 1.2))                                 # The box
    m.frustum("body", (0, 0.5, l / 2 - 0.9), (w, 1.8), (w, 1.2), 1.4, top_offset_z=-0.3)   # The hood
    m.frustum("glass", (0, 1.9, l / 2 - 1.5), (w * 0.92, 0.8), (w * 0.88, 0.2), 0.95, top_offset_z=-0.3)
    m.box("glass", (w / 2 + 0.01, 2.2, l / 2 - 2.0), (0.04, 0.8, 1.1))               # Side windows
    m.box("glass", (-w / 2 - 0.01, 2.2, l / 2 - 2.0), (0.04, 0.8, 1.1))
    m.box("trim", (0, 0.45, l / 2 - 0.05), (w, 0.3, 0.25))
    m.box("trim", (0, 0.45, -l / 2 + 0.1), (w, 0.3, 0.25))
    wheels(m, (l / 2 - 1.6, -l / 2 + 1.7), radius=0.6)
    lights(m, l / 2 + 0.01, -l / 2, 1.1)
    m.write()


def make_truck():
    m = Model("truck")
    vehicle_parts(m)
    m.material("trailer", (0.9, 0.9, 0.87))
    m.material("chassis", (0.22, 0.22, 0.24))
    w, l = CAR_WIDTH, TRUCK_LENGTH
    cab = 3.4
    front = l / 2
    m.box("chassis", (0, 0.75, 0), (w * 0.8, 0.4, l - 0.4))
    m.box("body", (0, 2.0, front - cab / 2), (w, 2.7, cab))                           # The cab
    m.box("glass", (0, 2.65, front + 0.01), (w * 0.9, 1.0, 0.04))                    # Windscreen
    m.box("glass", (w / 2 + 0.01, 2.65, front - 0.9), (0.04, 0.9, 1.2))
    m.box("glass", (-w / 2 - 0.01, 2.65, front - 0.9), (0.04, 0.9, 1.2))
    m.box("body", (0, 3.45, front - cab / 2 - 0.2), (w * 0.9, 0.3, cab - 0.6))        # The air deflector on its roof
    m.box("trim", (0, 0.6, front), (w, 0.45, 0.3))
    trailer = l - cab - 0.5
    m.box("trailer", (0, 2.45, -l / 2 + trailer / 2), (w + 0.1, 3.4, trailer))      # The trailer
    m.box("trim", (0, 0.9, -l / 2 + 0.05), (w, 0.3, 0.2))
    wheels(m, (front - 1.3, front - cab - 1.4, -l / 2 + 2.6, -l / 2 + 1.2), radius=0.6, width=0.6)
    lights(m, front + 0.02, -l / 2 - 0.02, 0.95)
    m.write()


#
# Heroes: about 4 units tall, looking towards +z
#

SKIN = (0.93, 0.74, 0.6)
BLACK = (0.05, 0.05, 0.06)


def eyes(m, y, z, spacing, size=0.22):
    m.material("eye", BLACK)
    m.box("eye", (spacing, y, z), (size, size * 1.2, 0.08))
    m.box("eye", (-spacing, y, z), (size, size * 1.2, 0.08))


def make_allan():
    m = Model("allan")
    m.material("shirt", (0.84, 0.19, 0.19))
    m.material("jeans", (0.17, 0.25, 0.45))
    m.material("skin", SKIN)
    m.material("hair", (0.38, 0.24, 0.12))
    m.material("shoe", (0.12, 0.1, 0.09))
    for side in (-1, 1):
        m.box("shoe", (side * 0.33, 0.15, 0.1), (0.5, 0.3, 0.8))
        m.box("jeans", (side * 0.33, 0.95, 0), (0.48, 1.4, 0.5))
        m.box("shirt", (side * 0.95, 2.3, 0), (0.36, 1.1, 0.4))                      # Arms
        m.box("skin", (side * 0.95, 1.6, 0), (0.3, 0.32, 0.32))                       # Hands
    m.box("shirt", (0, 2.3, 0), (1.5, 1.4, 0.75))                                     # Torso
    m.box("skin", (0, 3.1, 0), (0.35, 0.2, 0.35))                                     # Neck
    m.box("skin", (0, 3.55, 0), (0.9, 0.85, 0.85))                                    # Head
    m.box("hair", (0, 4.02, -0.05), (0.96, 0.18, 0.95))
    m.box("hair", (0, 3.7, -0.43), (0.96, 0.6, 0.1))
    eyes(m, 3.62, 0.43, 0.2, 0.16)
    m.write()


def make_ghosty():
    m = Model("ghosty")
    m.material("sheet", (0.92, 0.94, 1.0))
    m.cylinder("sheet", (0, 1.3, 0), 0.95, 1.6, axis="y", segments=14, radius_end=0.85)   # The body widens to the hem
    m.sphere("sheet", (0, 2.1, 0), 0.86, rings=8, segments=14)                       # The head
    for i in range(7):                                                                # The ragged hem
        a = 2 * math.pi * i / 7
        m.cylinder("sheet", (math.cos(a) * 0.72, 0.38, math.sin(a) * 0.72), 0.26, 0.4, axis="y", segments=6, radius_end=0.3)
    for side in (-1, 1):
        m.sphere("sheet", (side * 1.0, 1.75, 0.15), 0.25, scale=(1, 1.6, 1), rings=5, segments=8)   # Arms
    eyes(m, 2.25, 0.82, 0.28, 0.24)
    m.material("mouth", (0.2, 0.2, 0.25))
    m.box("mouth", (0, 1.85, 0.8), (0.3, 0.2, 0.08))
    m.write()


def make_butcher():
    m = Model("butcher")
    m.material("skin", (0.86, 0.62, 0.52))
    m.material("apron", (0.85, 0.82, 0.76))
    m.material("blood", (0.55, 0.06, 0.07))
    m.material("pants", (0.3, 0.22, 0.17))
    m.material("metal", (0.6, 0.6, 0.64))
    m.material("handle", (0.35, 0.2, 0.1))
    for side in (-1, 1):
        m.box("pants", (side * 0.5, 0.75, 0), (0.7, 1.5, 0.8))                        # Legs
        m.box("skin", (side * 1.45, 2.35, 0), (0.6, 1.4, 0.65))                       # Arms
        m.box("skin", (side * 1.45, 1.5, 0.05), (0.55, 0.45, 0.55))                   # Fists
    m.sphere("skin", (0, 2.45, 0), 1.25, scale=(1, 0.95, 0.85), rings=8, segments=14)   # The belly
    m.box("apron", (0, 2.1, 0.86), (1.7, 1.9, 0.12))
    m.box("blood", (0.35, 2.3, 0.93), (0.4, 0.3, 0.04))
    m.box("blood", (-0.4, 1.7, 0.93), (0.3, 0.45, 0.04))
    m.sphere("skin", (0, 3.85, 0.1), 0.62, rings=7, segments=12)                      # The head
    eyes(m, 3.95, 0.66, 0.22, 0.16)
    # The meat hook in the right hand
    m.cylinder("handle", (-1.45, 1.5, 0.45), 0.12, 0.6, axis="z", segments=6)
    m.cylinder("metal", (-1.45, 1.5, 1.0), 0.07, 0.6, axis="z", segments=6)
    m.cylinder("metal", (-1.45, 1.25, 1.3), 0.07, 0.55, axis="y", segments=6)
    m.cylinder("metal", (-1.45, 1.0, 1.1), 0.07, 0.45, axis="z", segments=6)
    m.write()


def make_frosty():
    m = Model("frosty")
    m.material("snow", (0.97, 0.98, 1.0))
    m.material("coal", BLACK)
    m.material("carrot", (0.95, 0.5, 0.12))
    m.material("scarf", (0.2, 0.7, 0.85))
    m.material("hat", (0.08, 0.08, 0.1))
    m.material("hatband", (0.75, 0.12, 0.15))
    m.material("stick", (0.4, 0.27, 0.15))
    m.sphere("snow", (0, 0.85, 0), 0.95, rings=8, segments=14)
    m.sphere("snow", (0, 2.1, 0), 0.72, rings=8, segments=14)
    m.sphere("snow", (0, 3.1, 0), 0.52, rings=8, segments=14)
    m.cylinder("scarf", (0, 2.65, 0), 0.56, 0.22, axis="y", segments=14)
    m.box("scarf", (0.3, 2.3, 0.55), (0.24, 0.6, 0.1))
    for y in (2.3, 1.9, 1.15):                                                        # Buttons
        m.box("coal", (0, y, 0.7 if y > 1.5 else 0.93), (0.14, 0.14, 0.1))
    m.cylinder("carrot", (0, 3.1, 0.7), 0.1, 0.45, axis="z", segments=8, radius_end=0.01)
    eyes(m, 3.25, 0.47, 0.18, 0.12)
    m.cylinder("hat", (0, 3.6, 0), 0.6, 0.06, axis="y", segments=14)                  # Brim
    m.cylinder("hat", (0, 3.95, 0), 0.4, 0.7, axis="y", segments=14)
    m.cylinder("hatband", (0, 3.7, 0), 0.41, 0.12, axis="y", segments=14)
    for side in (-1, 1):                                                              # Stick arms
        m.cylinder("stick", (side * 1.15, 2.4, 0), 0.06, 1.1, axis="x", segments=5)
        m.cylinder("stick", (side * 1.6, 2.65, 0), 0.05, 0.5, axis="y", segments=5)
    m.write()


#
# The wall: a segment of a concrete barrier, standing on y = 0, WALL_SEGMENT long
#

def make_wall():
    m = Model("wall")
    m.material("concrete", (0.72, 0.7, 0.66))
    m.material("concrete_dark", (0.5, 0.48, 0.45))
    m.material("stripe", (0.95, 0.75, 0.15))
    m.material("joint", (0.3, 0.29, 0.27))
    length = WALL_SEGMENT - 0.1                                                       # A gap for the joint
    m.frustum("concrete_dark", (0, 0, 0), (WALL_WIDTH, length), (WALL_WIDTH * 0.8, length), 0.5)   # The foot
    m.frustum("concrete", (0, 0.5, 0), (WALL_WIDTH * 0.8, length), (WALL_WIDTH * 0.45, length), 1.2)
    m.frustum("concrete", (0, 1.7, 0), (WALL_WIDTH * 0.45, length), (WALL_WIDTH * 0.38, length), WALL_HEIGHT - 2.0)
    m.box("concrete_dark", (0, WALL_HEIGHT - 0.15, 0), (WALL_WIDTH * 0.42, 0.3, length))   # The cap
    for side in (-1, 1):                                                              # A yellow band on both faces
        m.box("stripe", (side * WALL_WIDTH * 0.2, 2.6, 0), (0.06, 0.35, length * 0.98))
    m.box("joint", (0, 0.25, WALL_SEGMENT / 2 - 0.05), (WALL_WIDTH * 0.7, 0.5, 0.1))
    m.write()


#
# Scenery on the grass: small, so the heroes stay easy to see
#

def make_tuft():
    m = Model("tuft")
    m.material("blade", (0.36, 0.55, 0.24))
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        r = 0.12 + 0.05 * (k % 3)
        height = 0.45 + 0.12 * ((k * 5) % 3)
        x, z = math.cos(a) * r, math.sin(a) * r
        lean = 0.12
        m.frustum("blade", (x, 0, z), (0.09, 0.05), (0.01, 0.01), height, top_offset_z=lean * math.sin(a))
    m.write()


def make_flower(name, petal):
    m = Model(name)
    m.material("stem", (0.3, 0.5, 0.2))
    m.material("petal", petal)
    m.material("middle", (0.95, 0.8, 0.2) if petal[2] > 0.5 else (0.45, 0.28, 0.1))
    m.cylinder("stem", (0, 0.2, 0), 0.025, 0.4, axis="y", segments=4)
    for k in range(5):
        a = 2 * math.pi * k / 5
        m.sphere("petal", (math.cos(a) * 0.08, 0.42, math.sin(a) * 0.08), 0.06, scale=(1.3, 0.4, 1.3), rings=3, segments=5)
    m.sphere("middle", (0, 0.44, 0), 0.045, rings=3, segments=5)
    m.write()


def make_rock():
    m = Model("rock")
    m.material("stone", (0.55, 0.54, 0.5))
    m.material("stone_dark", (0.42, 0.41, 0.38))
    m.sphere("stone", (0, 0.12, 0), 0.4, scale=(1.2, 0.55, 0.9), rings=4, segments=7)
    m.sphere("stone_dark", (0.3, 0.07, 0.2), 0.22, scale=(1.1, 0.6, 1.0), rings=3, segments=6)
    m.write()


if __name__ == "__main__":
    make_tuft()
    make_flower("flower_yellow", (0.98, 0.85, 0.25))
    make_flower("flower_white", (0.95, 0.95, 0.92))
    make_flower("flower_purple", (0.62, 0.4, 0.85))
    make_rock()
    make_wall()
    make_car()
    make_van()
    make_truck()
    make_allan()
    make_ghosty()
    make_butcher()
    make_frosty()
