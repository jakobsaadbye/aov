#!/usr/bin/env python3
"""
Writes the models of the vehicles, the wall, the city and the small things on the grass to data/models/, with
tools/sculpt.py: smooth shapes with a hand-painted texture each. The heroes are in tools/make_heroes.py.

    python3 tools/make_models.py                  all of them
    python3 tools/make_models.py car tree         only these

The rules the game expects:

  * Units are the units of the game. y is up, the model looks towards +z, and it stands on y = 0 with its middle at
    x = z = 0
  * A vehicle's body (the part that gets the color of the car) is made with tint=True: it is in the material 'body',
    whose color is pure white (Kd 1 1 1), and the game finds it by that color. Its painting is light grey, so the color
    shows, with the shading and the seams painted in
  * The sizes match config.sd: a vehicle is CarWidth wide, and as long as CarLength, VanLength, TruckLength, BusLength
  * The wall is one segment of a concrete barrier, WALL_SEGMENT long along z, which the game repeats along each wall
  * A building is BUILDING_SIZE square and its height as made; the game scales it, so one model makes many buildings
"""

import math
import sys

import numpy as np

from sculpt import (Model, Paint, blob, bands, box, color, cylinder, edges, ellipsoid, extrude, fbm, glass, grime,
                    lathe, leather, metal, painted, plane, rect, rgb, smoothstep, sphere, stains, stone, stripes,
                    tinted, tube, wood, _hash3, _varied)

# Keep these in step with src/core/config.sd (WALL_SEGMENT is WallSegmentLength)
CAR_WIDTH = 5.2
CAR_LENGTH = 8.0
VAN_LENGTH = 9.0
TRUCK_LENGTH = 16.0
BUS_LENGTH = 18.0
WALL_WIDTH = 3.0
WALL_HEIGHT = 4.0
WALL_SEGMENT = 5.0
BUILDING_SIZE = 16.0

#
# Vehicles
#


def body_paint(seams=(), lightness=0.9):
    """The painting of a body the game colors: light grey with soft shade, darker seams across it at seams (z), and a
    darker sill along the bottom"""
    def fn(ctx):
        out = _varied(ctx, (lightness,) * 3, 0.04, 1.2, warm=0)
        z, y = ctx.p[..., 2], ctx.p[..., 1]
        side = np.abs(ctx.n[..., 0]) > 0.4
        k = np.zeros(ctx.shape)
        for s in seams:
            k = np.maximum(k, (np.abs(z - s) < 0.035) * side * 0.45)
        sill = smoothstep(0.75, 0.55, y) * 0.35
        shine = smoothstep(0.4, 0.95, ctx.n[..., 1]) * 0.08
        return out * (1 - k - sill)[..., None] + shine[..., None]
    return Paint(fn)


TIRE = Paint(lambda ctx: _varied(ctx, (0.1, 0.1, 0.11), 0.06, 3) * (0.85 + 0.3 * (np.sin(ctx.u * 2 * np.pi * 24) > 0.6))[..., None])


def wheels(m, axles, radius=0.62, width=0.6):
    x = CAR_WIDTH / 2 - width / 2 + 0.05
    first = None
    for z in axles:
        for side in (1, -1):
            pos = (side * (x + width / 2), radius, z)
            t = cylinder(pos, radius, width, rot=(0, 0, 90 if side > 0 else -90))
            if first is None:
                first = (m.add(t, TIRE), m.add(cylinder((side * (x + width / 2 + 0.02), radius, z), radius * 0.55, 0.06, rot=(0, 0, 90)),
                                                metal((0.72, 0.72, 0.76)) + edges(0.2, 0.08, dark=True)))
            else:
                m.add(t, TIRE, share=first[0])
                m.add(cylinder((side * (x + width / 2 + 0.02), radius, z), radius * 0.55, 0.06, rot=(0, 0, 90 if side > 0 else -90)),
                      metal((0.72, 0.72, 0.76)), share=first[1])


def lights(m, front_z, back_z, y, inset=0.62, size=(0.36, 0.2)):
    for side in (1, -1):
        x = side * (CAR_WIDTH / 2 - inset)
        m.add(ellipsoid((x, y, front_z), (size[0], size[1], 0.1)), color((1.0, 0.96, 0.8), 0.02))
        m.add(ellipsoid((x, y, back_z), (size[0], size[1], 0.1)), color((0.9, 0.1, 0.08), 0.03))


def bumper(m, z, y=0.55, width=CAR_WIDTH):
    m.add(blob((0, y, z), (width / 2 + 0.05, 0.22, 0.2), (0.35, 0.35)), color((0.2, 0.2, 0.22)) + edges(0.15, 0.05))


def make_car():
    m = Model("car", ground_ao=False, light=0.25)
    w, l = CAR_WIDTH, CAR_LENGTH
    m.add(blob((0, 1.0, 0), (w / 2, 0.55, l / 2), (0.3, 0.22), nu=28, nv=12), body_paint(seams=(0.6, -1.4)), tint=True)
    m.add(blob((0, 1.78, -0.35), (w * 0.43, 0.5, l * 0.26), (0.35, 0.35), nu=24, nv=10),
          glass() + bands((0.16, 0.16, 0.18), [(0.0, 0.25)]) + stripes((0.16, 0.16, 0.18), 4, 0.12, axis="u"))
    m.add(blob((0, 2.18, -0.4), (w * 0.4, 0.13, l * 0.21), (0.3, 0.4)), body_paint(), tint=True)
    bumper(m, l / 2)
    bumper(m, -l / 2)
    m.add(blob((0, 0.95, l / 2 + 0.02), (0.9, 0.18, 0.05), (0.2, 0.2)), color((0.12, 0.12, 0.13)) + stripes((0.4, 0.4, 0.42), 4, 0.3, axis="v"))
    wheels(m, (l / 2 - 1.55, -l / 2 + 1.55))
    lights(m, l / 2 + 0.02, -l / 2 - 0.02, 1.15)
    m.write()


def make_van():
    m = Model("van", ground_ao=False, light=0.25)
    w, l = CAR_WIDTH, VAN_LENGTH
    m.add(blob((0, 1.9, -0.65), (w / 2, 1.35, (l - 1.3) / 2), (0.18, 0.18), nu=26, nv=12),
          body_paint(seams=(1.0, -1.2, -3.6)), tint=True)
    m.add(blob((0, 1.05, l / 2 - 0.85), (w / 2, 0.6, 0.85), (0.35, 0.3)), body_paint(), tint=True)
    m.add(plane((-w / 2 * 0.86, 1.95, l / 2 - 1.18), (w * 0.86, 0, 0), (0, 0.85, -0.45)), glass())
    for side in (1, -1):
        x = side * (w / 2 + 0.02)
        a, b = ((0, 0, -1.3), (0, 0.8, 0)) if side > 0 else ((0, 0, 1.3), (0, 0.8, 0))
        start = (x, 2.15, l / 2 - 1.55) if side > 0 else (x, 2.15, l / 2 - 2.85)
        m.add(plane(start, a, b), glass())
    bumper(m, l / 2)
    bumper(m, -l / 2 + 0.05)
    wheels(m, (l / 2 - 1.6, -l / 2 + 1.7), radius=0.66)
    lights(m, l / 2 + 0.02, -l / 2 + 0.05, 1.2)
    m.write()


def make_truck():
    m = Model("truck", ground_ao=False, light=0.25, size=1024)
    w, l = CAR_WIDTH, TRUCK_LENGTH
    cab, front = 3.4, l / 2
    m.add(blob((0, 0.8, 0), (w * 0.38, 0.22, l / 2 - 0.3), (0.2, 0.2)), color((0.2, 0.2, 0.22)))
    m.add(blob((0, 2.15, front - cab / 2), (w / 2, 1.45, cab / 2), (0.18, 0.2), nu=22, nv=12), body_paint(seams=(front - 1.9,)), tint=True)
    m.add(blob((0, 3.55, front - cab / 2 - 0.2), (w * 0.44, 0.3, cab / 2 - 0.5), (0.4, 0.4)), body_paint(), tint=True)
    m.add(plane((-w * 0.42, 2.25, front + 0.03), (w * 0.84, 0, 0), (0, 0.95, -0.05)), glass())
    for side in (1, -1):
        x = side * (w / 2 + 0.03)
        start = (x, 2.3, front - 0.4) if side > 0 else (x, 2.3, front - 1.6)
        m.add(plane(start, (0, 0, -1.2 * side), (0, 0.85, 0)), glass())
    trailer = l - cab - 0.5
    tz = -l / 2 + trailer / 2

    def trailer_paint(ctx):
        out = _varied(ctx, (0.92, 0.91, 0.88), 0.04, 0.8)
        ribs = (np.sin(ctx.p[..., 2] * 2.4) > 0.92) * (np.abs(ctx.n[..., 1]) < 0.5) * 0.12
        band = (np.abs(ctx.p[..., 1] - 2.8) < 0.25) * (np.abs(ctx.n[..., 0]) > 0.5)
        out = out * (1 - ribs)[..., None]
        out = out * (1 - band[..., None]) + band[..., None] * np.array([0.85, 0.2, 0.15])
        return out * (1 - smoothstep(1.4, 0.8, ctx.p[..., 1]) * 0.25)[..., None]
    m.add(box((0, 2.45, tz), (w + 0.1, 3.4, trailer)), painted(trailer_paint) + edges(0.12, 0.08, dark=True))
    bumper(m, front + 0.05)
    m.add(blob((0, 0.85, -l / 2 + 0.05), (w / 2, 0.15, 0.12), (0.3, 0.3)), color((0.2, 0.2, 0.22)))
    wheels(m, (front - 1.3, front - cab - 1.4, -l / 2 + 2.6, -l / 2 + 1.2), radius=0.66, width=0.62)
    lights(m, front + 0.03, -l / 2 - 0.03, 1.0)
    m.write()


def make_bus():
    m = Model("bus", ground_ao=False, light=0.25, size=1024)
    w, l = CAR_WIDTH, BUS_LENGTH
    m.add(blob((0, 2.15, 0), (w / 2, 1.6, l / 2), (0.15, 0.12), nu=28, nv=12), body_paint(seams=(l / 2 - 2.0, -l / 2 + 4.0)), tint=True)
    m.add(blob((0, 3.75, 0), (w * 0.46, 0.18, l * 0.47), (0.3, 0.2)), body_paint(lightness=0.85), tint=True)
    m.add(plane((-w * 0.44, 1.95, l / 2 + 0.03), (w * 0.88, 0, 0), (0, 1.35, -0.05)), glass())
    for side in (1, -1):
        x = side * (w / 2 + 0.03)
        a = (0, 0, -(l - 4.2)) if side > 0 else (0, 0, l - 4.2)
        start = (x, 2.25, l / 2 - 2.6) if side > 0 else (x, 2.25, -l / 2 + 1.6)
        m.add(plane(start, a, (0, 1.15, 0)), glass() + stripes((0.15, 0.15, 0.17), 7, 0.06, axis="u"))
        m.add(plane((x, 1.3, start[2] + (0.0 if side > 0 else 0)), a, (0, 0.3, 0)), color((0.15, 0.15, 0.17)))
    bumper(m, l / 2 + 0.03)
    bumper(m, -l / 2 - 0.03)
    wheels(m, (l / 2 - 2.4, -l / 2 + 3.2), radius=0.72, width=0.62)
    lights(m, l / 2 + 0.03, -l / 2 - 0.03, 1.05)
    m.write()


#
# The wall between the road and the pavement: a concrete barrier with a yellow band
#


def make_wall():
    m = Model("wall", ground_ao=True, light=0.3)
    hw = WALL_WIDTH / 2
    prof = [(-hw, 0.0), (-hw, 0.45), (-hw * 0.78, 0.6), (-hw * 0.42, 1.7), (-hw * 0.36, WALL_HEIGHT - 0.2), (-hw * 0.3, WALL_HEIGHT),
            (hw * 0.3, WALL_HEIGHT), (hw * 0.36, WALL_HEIGHT - 0.2), (hw * 0.42, 1.7), (hw * 0.78, 0.6), (hw, 0.45), (hw, 0.0)]
    L = WALL_SEGMENT / 2

    def concrete(ctx):
        out = _varied(ctx, (0.74, 0.72, 0.68), 0.08, 0.9)
        y, z = ctx.p[..., 1], ctx.p[..., 2]
        band = (np.abs(y - 2.6) < 0.18).astype(float) * (np.abs(ctx.n[..., 0]) > 0.3)
        out = out * (1 - band[..., None]) + band[..., None] * _varied(ctx, (0.96, 0.75, 0.15), 0.06, 3)
        joint = smoothstep(0.07, 0.0, L - np.abs(z)) * 0.4
        pits = smoothstep(0.66, 0.72, fbm(ctx.p, 7, 2, 9)) * 0.15
        dirt = smoothstep(1.2, 0.0, y) * 0.3 * (0.6 + 0.4 * fbm(ctx.p, 2, 3, 4))
        return out * (1 - joint - pits - dirt)[..., None]
    m.add(extrude(prof, -L, L), painted(concrete))
    m.add(plane((-hw * 0.3, WALL_HEIGHT, L), (hw * 0.6, 0, 0), (0, 0, -2 * L)), painted(concrete))
    m.write()


#
# The city around the field
#


def _cells(x, y, spacing, floor_h, first, lu, lv):
    cols = max(1, int(lu / spacing))
    x0 = (lu - cols * spacing) / 2
    col = np.floor((x - x0) / spacing)
    row = np.floor((y - first) / floor_h)
    floors = max(1, int((lv - first - 0.6) / floor_h))
    ok = (col >= 0) & (col < cols) & (row >= 0) & (row < floors)
    cx = x0 + (col + 0.5) * spacing
    cy = first + row * floor_h + floor_h * 0.5
    return col, row, cx, cy, ok


def facade(wall, spacing=3.0, floor_h=3.2, first=1.2, win=(1.5, 1.9), lit=0.15, seed=1, trim=(0.85, 0.82, 0.74),
           sills=True, curtains=True):
    """A wall with a grid of windows painted on it, on a face of a box (v up). wall is a painter for the wall"""
    def fn(ctx):
        out = wall(ctx)
        x, y = ctx.u * ctx.lu, ctx.v * ctx.lv
        col, row, cx, cy, ok = _cells(x, y, spacing, floor_h, first, ctx.lu, ctx.lv)
        dx, dy = np.abs(x - cx), np.abs(y - cy)
        hw, hh = win[0] / 2, win[1] / 2
        face = int(abs(ctx.n[0, 0, 0] * 3 + ctx.n[0, 0, 2] * 7) * 10)
        h = _hash3(col.astype(np.int64), row.astype(np.int64), np.full(ctx.shape, face, np.int64), seed)
        h2 = _hash3(col.astype(np.int64), row.astype(np.int64), np.full(ctx.shape, face + 1, np.int64), seed + 3)
        # Grime running down from the sills
        drip = ok & (dx < hw) & (y < cy - hh) & (y > cy - hh - 1.6)
        out = out * (1 - drip * 0.12 * smoothstep(cy - hh - 1.6, cy - hh, y))[..., None]
        frame = ok & (dx < hw + 0.16) & (dy < hh + 0.16)
        out = np.where(frame[..., None], _varied(ctx, trim, 0.05, 3) * 0.92, out)
        if sills:
            sill = ok & (dx < hw + 0.32) & (y < cy - hh - 0.05) & (y > cy - hh - 0.3)
            out = np.where(sill[..., None], _varied(ctx, trim, 0.05, 3) * 1.05, out)
        pane = ok & (dx < hw) & (dy < hh)
        sky = (0.18 + 0.22 * smoothstep(-hh, hh, y - cy))[..., None] * np.array([0.7, 0.85, 1.0])
        streak = (smoothstep(0.7, 0.95, np.sin((x - cx + y - cy) * 2.2) * 0.5 + 0.5) * 0.18)[..., None]
        glass_c = np.array([0.12, 0.16, 0.24]) + sky + streak
        warm = np.array([1.0, 0.82, 0.48]) * (0.85 + 0.15 * smoothstep(-hh, hh, cy - y))[..., None]
        is_lit = (h < lit)[..., None]
        g = np.where(is_lit, warm, glass_c)
        if curtains:
            cur = (h2 < 0.35)[..., None] & ((np.abs(x - cx) > hw * 0.55)[..., None])
            g = np.where(cur, np.array([0.75, 0.3, 0.3]) * (0.7 + 0.5 * is_lit), g)
        cross = (np.abs(x - cx) < 0.05) | (np.abs(y - cy - hh * 0.25) < 0.05)
        g = np.where(cross[..., None], np.array(trim) * 0.8, g)
        return np.where(pane[..., None], g, out)
    return Paint(fn)


def bricks(c=(0.62, 0.3, 0.2), mortar=(0.78, 0.74, 0.66), brick=(0.5, 0.22)):
    def fn(ctx):
        x, y = ctx.u * ctx.lu, ctx.v * ctx.lv
        row = np.floor(y / brick[1])
        bx = x / brick[0] + 0.5 * (row % 2)
        bi = np.floor(bx)
        h = _hash3(bi.astype(np.int64), row.astype(np.int64), np.zeros(ctx.shape, np.int64), 5)
        base = _varied(ctx, c, 0.06, 1.0) * (0.85 + 0.3 * h)[..., None]
        fx, fy = bx - bi, y / brick[1] - row
        m = (fx < 0.06) | (fy < 0.12)
        return np.where(m[..., None], _varied(ctx, mortar, 0.05, 2), base)
    return Paint(fn)


def panels(c=(0.72, 0.7, 0.66), w=4.0, h=3.2):
    def fn(ctx):
        x, y = ctx.u * ctx.lu, ctx.v * ctx.lv
        base = _varied(ctx, c, 0.07, 0.6)
        seam = ((x % w) < 0.06) | ((y % h) < 0.06)
        streak = fbm(np.stack([x * 3, y * 0.3, np.zeros_like(x)], -1), 1, 3, 17) * 0.1
        return base * (1 - 0.25 * seam - streak + 0.05)[..., None]
    return Paint(fn)


def plaster(c=(0.9, 0.84, 0.7)):
    return Paint(lambda ctx: _varied(ctx, c, 0.08, 0.7) * (1 - smoothstep(0.62, 0.75, fbm(ctx.p, 1.5, 3, 23)) * 0.12)[..., None])


def curtain_wall(c=(0.2, 0.3, 0.42), mullion=(0.7, 0.72, 0.75), w=2.0, h=3.0):
    """An office tower all of glass, in a grid of metal"""
    def fn(ctx):
        x, y = ctx.u * ctx.lu, ctx.v * ctx.lv
        col, row = np.floor(x / w), np.floor(y / h)
        hsh = _hash3(col.astype(np.int64), row.astype(np.int64), np.zeros(ctx.shape, np.int64), 9)
        sky = smoothstep(0, ctx.lv, y)[..., None] * np.array([0.25, 0.3, 0.35])
        g = np.array(c) * (0.8 + 0.4 * hsh)[..., None] + sky
        g = np.where((hsh > 0.88)[..., None], np.array([0.95, 0.85, 0.55]), g)
        streak = (smoothstep(0.75, 0.95, np.sin((x + y * 0.6) * 0.5) * 0.5 + 0.5) * 0.2)[..., None]
        g = g + streak
        m = ((x % w) < 0.12) | ((y % h) < 0.18)
        return np.where(m[..., None], _varied(ctx, mullion, 0.04, 2), g)
    return Paint(fn)


def roof(c=(0.4, 0.4, 0.42)):
    return stone(c, 2.0) + edges(0.25, 0.4)


def building(m, h, walls, top=None, plinth=None):
    faces = box((0, h / 2, 0), (BUILDING_SIZE, h, BUILDING_SIZE))
    for f in faces[:4]:
        m.add(f, walls)
    m.add(faces[4], top or roof())
    if plinth:
        for f in box((0, 0.6, 0), (BUILDING_SIZE + 0.3, 1.2, BUILDING_SIZE + 0.3))[:4]:
            m.add(f, plinth)


def roof_box(m, center, size, paint=None):
    for f in box(center, size):
        m.add(f, paint or (metal((0.6, 0.62, 0.65), 0.2) + edges(0.15, 0.1)))


def make_office():
    m = Model("building_office", size=1024, ground_ao=False, light=0.12, detail=1.0)
    h = 30.0
    building(m, h, curtain_wall() + grime(0.25, 1.5), plinth=panels((0.45, 0.47, 0.5)))
    roof_box(m, (3, h + 1.1, -2), (4, 2.2, 3))
    roof_box(m, (-4, h + 1.7, 3), (2.5, 3.4, 2.5), panels((0.62, 0.62, 0.64), 2, 2))
    m.write()


def make_brick():
    m = Model("building_brick", size=1024, ground_ao=False, light=0.12, detail=1.0)
    h = 16.0
    building(m, h, facade(bricks(), 3.2, 3.2, 1.0, (1.4, 1.9), 0.18, 2) + grime(0.3, 1.2))
    for y in (h,):
        for f in box((0, y + 0.3, 0), (BUILDING_SIZE + 0.6, 0.6, BUILDING_SIZE + 0.6))[:4]:
            m.add(f, stone((0.85, 0.8, 0.72), 3) + edges(0.2, 0.1))
    m.write()


def make_shop():
    m = Model("building_shop", size=1024, ground_ao=False, light=0.12, detail=1.0)
    h = 9.0
    walls = facade(plaster((0.92, 0.84, 0.66)), 3.2, 3.0, 4.2, (1.4, 1.6), 0.2, 3, trim=(0.95, 0.95, 0.92))

    def shopfront(ctx):
        out = walls(ctx)
        x, y = ctx.u * ctx.lu, ctx.v * ctx.lv
        cell = np.floor((x - 0.5) / 5.0)
        cx = 0.5 + (cell + 0.5) * 5.0
        win = (np.abs(x - cx) < 2.0) & (y > 0.35) & (y < 2.95) & (cell >= 0) & (cell < 3)
        frame = (np.abs(x - cx) < 2.15) & (y > 0.25) & (y < 3.05) & (cell >= 0) & (cell < 3)
        out = np.where(frame[..., None], np.array([0.22, 0.3, 0.26]), out)
        inside = np.array([0.3, 0.38, 0.42]) + (smoothstep(0.35, 2.95, y) * 0.25)[..., None] * np.array([0.6, 0.75, 0.9])
        goods = (fbm(ctx.p * np.array([4, 6, 4]), 1, 2, 5) > 0.55) & (y < 1.2)
        inside = np.where(goods[..., None], np.array([0.85, 0.6, 0.35]), inside)
        out = np.where(win[..., None], inside, out)
        sign = (y > 3.6) & (y < 4.0) & (np.abs(x - ctx.lu / 2) < 3.0)
        return np.where(sign[..., None], np.array([0.2, 0.35, 0.28]), out)
    building(m, h, painted(shopfront) + grime(0.25, 1.0), top=roof((0.45, 0.42, 0.4)))
    for f in box((0, h + 0.25, 0), (BUILDING_SIZE + 0.3, 0.5, BUILDING_SIZE + 0.3))[:4]:
        m.add(f, color((0.95, 0.95, 0.92)) + edges(0.15, 0.08, dark=True))
    awning = color((0.8, 0.16, 0.14)) + stripes((0.96, 0.95, 0.9), 6, 0.5, axis="u")
    half = BUILDING_SIZE / 2
    for rot in range(4):
        a = math.radians(rot * 90)
        ca, sa = math.cos(a), math.sin(a)

        def R(x, y, z):
            return (x * ca + z * sa, y, -x * sa + z * ca)
        o = R(-half + 0.5, 3.6, half)
        m.add(plane(o, R(half * 2 - 1.0, 0, 0), R(0, -0.6, 1.8)), awning)
    m.write()


def make_tower():
    m = Model("building_tower", size=1024, ground_ao=False, light=0.12, detail=1.0)
    h = 42.0
    building(m, h, facade(panels((0.76, 0.74, 0.7)), 2.6, 3.5, 3.5, (2.0, 2.4), 0.12, 4, trim=(0.55, 0.57, 0.6), curtains=False) + grime(0.2, 2.0))
    roof_box(m, (0, h + 1.5, 0), (BUILDING_SIZE * 0.6, 3, BUILDING_SIZE * 0.6), panels((0.55, 0.55, 0.58), 3, 3))
    m.add(cylinder((0, h + 3, 0), 0.15, 6, caps=False), metal((0.7, 0.7, 0.72)))
    m.add(sphere((0, h + 9.1, 0), 0.25), color((0.95, 0.15, 0.1)))
    m.write()


def make_lamp():
    m = Model("lamp", light=0.25)
    iron = metal((0.22, 0.25, 0.28), 0.25)
    m.add(lathe([(0, 0.0), (0, 0.38), (0.25, 0.36), (0.45, 0.2), (0.6, 0.14), (0.62, 0.0)], nu=14), iron)
    m.add(cylinder((0, 0.6, 0), 0.12, 6.0, r_top=0.09, caps=False), iron)
    m.add(tube([(0, 6.5, 0), (0.1, 7.1, 0), (0.7, 7.3, 0), (1.5, 7.15, 0)], 0.09), iron)
    m.add(blob((1.65, 7.0, 0), (0.45, 0.16, 0.3), (0.4, 0.5)), iron)
    m.add(ellipsoid((1.65, 6.86, 0), (0.36, 0.06, 0.24)), color((1.0, 0.95, 0.75), 0.02))
    m.write()


def leaves(c=(0.3, 0.55, 0.22)):
    """Painted leaves: clumps of lighter and darker green, lit on top"""
    def fn(ctx):
        base = _varied(ctx, c, 0.12, 1.2)
        clumps = fbm(ctx.p, 3.5, 3, 61)
        light = smoothstep(-0.3, 0.9, ctx.n[..., 1])
        k = 0.75 + 0.35 * clumps + 0.25 * light
        warm = smoothstep(0.6, 1.0, light * clumps)[..., None] * np.array([0.08, 0.06, -0.02])
        return base * k[..., None] + warm
    return Paint(fn)


def make_tree():
    m = Model("tree", light=0.35)
    for f in box((0, 0.35, 0), (2.4, 0.7, 2.4)):
        m.add(f, stone((0.62, 0.6, 0.56), 2) + edges(0.2, 0.08))
    m.add(plane((-1.0, 0.71, 1.0), (2.0, 0, 0), (0, 0, -2.0)), stone((0.32, 0.24, 0.16), 3))
    bark = wood((0.42, 0.3, 0.2), 6)
    m.add(tube([(0, 0.6, 0), (0.05, 2.0, 0.05), (0.15, 3.2, 0.0)], [0.3, 0.22, 0.18], nu=10), bark)
    m.add(tube([(0.1, 2.6, 0.0), (0.7, 3.4, 0.3)], [0.12, 0.07], nu=8), bark)
    m.add(tube([(0.05, 2.9, 0.0), (-0.6, 3.6, -0.4)], [0.12, 0.07], nu=8), bark)
    for (x, y, z, r) in ((0, 4.5, 0, 1.6), (0.9, 4.0, 0.5, 1.1), (-0.8, 4.2, -0.6, 1.15), (0.3, 5.3, -0.3, 1.1),
                         (-0.5, 3.8, 0.7, 0.95), (0.7, 4.8, -0.8, 0.9)):
        m.add(ellipsoid((x, y, z), (r, r * 0.85, r), nu=14, nv=9), leaves())
    m.write()


def make_bench():
    m = Model("bench", light=0.3)
    iron = metal((0.16, 0.16, 0.18), 0.2)
    for x in (-1.1, 1.1):
        m.add(tube([(x, 0.0, 0.3), (x, 0.78, 0.25), (x, 0.8, -0.35), (x, 1.5, -0.55)], 0.06, smooth=False), iron)
        m.add(tube([(x, 0.0, -0.35), (x, 0.78, -0.35)], 0.06), iron)
    plank = wood((0.6, 0.4, 0.22), 14) + edges(0.18, 0.04)
    for k in range(3):
        m.add(blob((0, 0.82, -0.3 + k * 0.3), (1.35, 0.05, 0.12), (0.2, 0.2)), plank)
    for k in range(2):
        m.add(blob((0, 1.1 + k * 0.3, -0.5 - k * 0.04), (1.35, 0.1, 0.04), (0.2, 0.2)), plank)
    m.write()


def make_hydrant():
    m = Model("hydrant", light=0.3)
    red = color((0.85, 0.15, 0.12)) + stains((0.45, 0.35, 0.3), 0.15, 4)
    m.add(lathe([(0, 0.0), (0, 0.32), (0.1, 0.32), (0.15, 0.24), (0.85, 0.24), (0.9, 0.27), (1.05, 0.2), (1.2, 0.0)], nu=14), red)
    m.add(tube([(-0.38, 0.62, 0), (0.38, 0.62, 0)], 0.1, nu=8), color((0.95, 0.9, 0.8)))
    m.add(cylinder((0, 1.15, 0), 0.06, 0.15), color((0.95, 0.9, 0.8)))
    m.write()


def make_bin():
    m = Model("bin", light=0.3)
    green = color((0.22, 0.45, 0.32)) + stripes((0.18, 0.36, 0.26), 12, 0.3, axis="u") + grime(0.2, 0.4)
    m.add(lathe([(0, 0.0), (0, 0.3), (0.05, 0.33), (0.95, 0.38), (1.0, 0.0)], nu=16), green)
    m.add(lathe([(0.95, 0.0), (0.95, 0.42), (1.05, 0.42), (1.12, 0.3), (1.15, 0.0)], nu=16), color((0.15, 0.3, 0.22)))
    m.write()


#
# Small things on the grass: kept small, so the heroes stay easy to see
#


def make_tuft():
    m = Model("tuft", size=128, ground_ao=True, light=0.3, detail=0.05)
    grass = Paint(lambda ctx: _varied(ctx, (0.34, 0.56, 0.22), 0.1, 4) * (0.7 + 0.5 * ctx.v)[..., None])
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        r = 0.12 + 0.05 * (k % 3)
        height = 0.45 + 0.12 * ((k * 5) % 3)
        x, z = math.cos(a) * r, math.sin(a) * r
        m.add(lathe([(0, 0.05), (height, 0.0)], (x, 0, z), rot=(math.degrees(math.sin(a)) * 0.25, 0, -math.degrees(math.cos(a)) * 0.25),
                    smooth=False, nu=4, nv=2), grass, share=m.surfaces[0] if m.surfaces else None)
    m.write()


def make_flower(name, petal):
    m = Model(name, size=128, light=0.3, detail=0.03)
    m.add(tube([(0, 0, 0), (0.02, 0.2, 0), (0, 0.42, 0.02)], 0.022, nu=4), color((0.3, 0.52, 0.2)))
    p = None
    for k in range(5):
        a = 2 * math.pi * k / 5
        s = m.add(ellipsoid((math.cos(a) * 0.08, 0.43, math.sin(a) * 0.08), (0.08, 0.025, 0.08), nu=8, nv=4),
                  color(petal, 0.06), share=p)
        p = p or s
    m.add(sphere((0, 0.45, 0), 0.045, nu=6, nv=4), color((0.95, 0.8, 0.2) if petal[2] > 0.5 else (0.45, 0.28, 0.1)))
    m.write()


def make_rock():
    m = Model("rock", size=128, light=0.4, detail=0.06)
    m.add(blob((0, 0.12, 0), (0.48, 0.24, 0.36), (0.7, 0.8), nu=10, nv=6), stone((0.58, 0.56, 0.52), 3))
    m.add(blob((0.32, 0.07, 0.2), (0.24, 0.14, 0.22), (0.7, 0.8), nu=8, nv=5), stone((0.46, 0.45, 0.42), 3))
    m.write()


MODELS = {name[5:]: f for name, f in dict(globals()).items() if name.startswith("make_") and callable(f) and name != "make_flower"}
MODELS["flower_yellow"] = lambda: make_flower("flower_yellow", (0.98, 0.85, 0.25))
MODELS["flower_white"] = lambda: make_flower("flower_white", (0.95, 0.95, 0.92))
MODELS["flower_purple"] = lambda: make_flower("flower_purple", (0.62, 0.4, 0.85))

if __name__ == "__main__":
    for name in sys.argv[1:] or MODELS:
        MODELS[name]()
        print("models/" + name)
