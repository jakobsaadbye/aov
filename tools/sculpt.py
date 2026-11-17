#!/usr/bin/env python3
"""
Sculpt: models out of smooth parametric surfaces, with a hand-painted texture each.

A model is a set of surfaces: ellipsoids, superellipsoids (rounded boxes), lathes (a profile turned around y), tubes
(a circle swept along a curve) and planes. Each is a function from (u, v) in [0, 1] to a point, so the same function
gives both the mesh (sampled coarsely) and the texture (sampled once for every texel of its part of the texture). A
painter colors the texels from where they are on the model: their position, their normal and (u, v), so noise and
patterns run on across the surfaces without seams, and the light, the dark creases and the worn edges of a hand-painted
texture are worked out from the shape itself.

    m = Model("allan")
    head = m.add(ellipsoid((0, 3.6, 0), (0.6, 0.66, 0.58)), skin(SKIN) + face())
    m.write()                       # data/models/allan.obj, .mtl and .png

Conventions (the same as the rest of the game): units are the units of the game, y is up, a model looks towards +z and
stands on y = 0 with its middle at x = z = 0. On a surface of revolution u goes around (u = 0.5 faces +z) and v goes
from the bottom (0) to the top (1); on a tube v goes along its path.

A part made with tint=True is in the material 'body', which is pure white (Kd 1 1 1): the game colors it, e.g the body
of each car. Its painting should be light and grey, so the color the game multiplies it by shows. Everything else is in
the material 'paint'. The texture is <name>.png next to the OBJ, and the game puts it on every material of the model.

    python3 tools/sculpt.py preview data/models/allan.obj     a picture of a model, from the front, to the scratchpad
"""

import math
import os

import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "models")

#
# Noise: value noise in 3D, on the positions on the model, so it is seamless across surfaces
#


def _hash3(ix, iy, iz, seed):
    h = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263 + iz.astype(np.int64) * 1440865169 +
         seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0xFFFFFF)


def noise3(p, seed=0):
    """Smooth noise in [0, 1] at points p (..., 3)"""
    f = np.floor(p)
    t = p - f
    t = t * t * (3 - 2 * t)
    i = f.astype(np.int64)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = ((t[..., 0] if dx else 1 - t[..., 0]) * (t[..., 1] if dy else 1 - t[..., 1]) *
                     (t[..., 2] if dz else 1 - t[..., 2]))
                out = out + w * _hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def fbm(p, scale=1.0, octaves=4, seed=0):
    """Fractal noise in about [0, 1]: big blotches with finer ones in them"""
    total, amp, norm = 0, 1.0, 0
    q = np.asarray(p) * scale
    for o in range(octaves):
        total = total + amp * noise3(q, seed + o * 17)
        norm += amp
        amp *= 0.5
        q = q * 2.03
    return total / norm


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) else t
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def rgb(c):
    """A color from 0..1 floats or 0..255 ints"""
    c = np.asarray(c, dtype=float)
    return c / 255.0 if c.max() > 1.0 else c


#
# Surfaces
#


def rotation(rx=0.0, ry=0.0, rz=0.0):
    """A rotation matrix from angles in degrees: first around z, then x, then y"""
    a, b, c = math.radians(rx), math.radians(ry), math.radians(rz)
    X = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Y = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Z = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Y @ X @ Z


class Surface:
    """A function of (u, v) to points, placed in the model by a rotation and an offset"""

    def __init__(self, fn, nu, nv, pos=(0, 0, 0), rot=(0, 0, 0), urange=(0, 1), vrange=(0, 1), wrap_u=False):
        self.fn = fn
        self.nu, self.nv = nu, nv
        self.M = rotation(*rot)
        self.t = np.asarray(pos, dtype=float)
        self.urange, self.vrange = urange, vrange
        self.wrap_u = wrap_u and urange == (0, 1)
        self.orient = 1             # -1 once mirrored: the normals of the function point in
        self.paint = None
        self.tint = False
        self.share = None           # A surface whose part of the texture this one uses too
        self.crease = 0.0           # How much darker it is towards its ends (v = 0 and 1), where it meets others
        self.region = None

    def copy(self):
        s = Surface.__new__(Surface)
        s.__dict__.update(self.__dict__)
        return s

    def points(self, u, v):
        uu = self.urange[0] + (self.urange[1] - self.urange[0]) * u
        vv = self.vrange[0] + (self.vrange[1] - self.vrange[0]) * v
        p = self.fn(uu, vv)
        return p @ self.M.T + self.t

    def frame(self, u, v):
        """The points and their outward normals"""
        p = self.points(u, v)
        e = 1e-3
        vc = np.clip(v, 2e-3, 1 - 2e-3)
        if self.wrap_u:
            du = (self.points(u + e, vc) - self.points(u - e, vc))
        else:
            uc = np.clip(u, e, 1 - e)
            du = (self.points(uc + e, vc) - self.points(uc - e, vc))
        dv = (self.points(u, np.clip(vc + e, 0, 1)) - self.points(u, np.clip(vc - e, 0, 1)))
        n = np.cross(du, dv) * self.orient
        length = np.linalg.norm(n, axis=-1, keepdims=True)
        n = n / np.maximum(length, 1e-12)
        return p, n

    def lengths(self):
        """How long it is around (u) and along (v), on average"""
        g = np.linspace(0, 1, 17)
        u, v = np.meshgrid(g, g)
        p = self.points(u, v)
        lu = np.linalg.norm(np.diff(p, axis=1), axis=-1).sum(axis=1).mean()
        lv = np.linalg.norm(np.diff(p, axis=0), axis=-1).sum(axis=0).mean()
        return max(lu, 1e-3), max(lv, 1e-3)


def _spow(x, e):
    return np.sign(x) * np.abs(x) ** e


def ellipsoid(center, radii, rot=(0, 0, 0), nu=16, nv=10, **kw):
    rx, ry, rz = radii

    def fn(u, v):
        th = 2 * np.pi * (u - 0.5)
        ph = np.pi * (v - 0.5)
        return np.stack([rx * np.cos(ph) * np.sin(th), ry * np.sin(ph), rz * np.cos(ph) * np.cos(th)], axis=-1)
    return Surface(fn, nu, nv, center, rot, wrap_u=True, **kw)


def sphere(center, r, **kw):
    return ellipsoid(center, (r, r, r), **kw)


def blob(center, radii, e=(0.5, 0.5), rot=(0, 0, 0), nu=20, nv=12, **kw):
    """A superellipsoid: a rounded box. e near 0 is a box with sharp edges, 1 an ellipsoid. e[0] is how square it is
    seen from the side, e[1] from above"""
    rx, ry, rz = radii
    e1, e2 = e

    def fn(u, v):
        th = 2 * np.pi * (u - 0.5)
        ph = np.pi * (v - 0.5)
        c = _spow(np.cos(ph), e1)
        return np.stack([rx * c * _spow(np.sin(th), e2), ry * _spow(np.sin(ph), e1), rz * c * _spow(np.cos(th), e2)],
                        axis=-1)
    return Surface(fn, nu, nv, center, rot, wrap_u=True, **kw)


def _densify(points, smooth, per=24):
    """A dense polyline through the points: a Catmull-Rom curve when smooth"""
    pts = np.asarray(points, dtype=float)
    if not smooth or len(pts) < 3:
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            for k in range(1, per + 1):
                out.append(a + (b - a) * k / per)
        return np.array(out)
    ext = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return np.array(out)


def _by_length(dense):
    """The arc length at each point of a dense polyline, from 0 to 1"""
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=-1))])
    return d / max(d[-1], 1e-9)


def lathe(profile, pos=(0, 0, 0), rot=(0, 0, 0), sx=1.0, sz=1.0, smooth=True, nu=20, nv=None, **kw):
    """A profile of (y, radius) or (y, radius, dz) points from the bottom up, turned around y. sx and sz squash it, e.g a
    torso is wider than it is deep. dz moves that height forward. A radius of 0 at an end closes it"""
    prof = np.array([p if len(p) == 3 else (p[0], p[1], 0.0) for p in profile], dtype=float)
    dense = _densify(prof, smooth)
    s = _by_length(dense[:, :2])
    if nv is None:
        nv = max(6, len(profile) * 3)

    def fn(u, v):
        y = np.interp(v, s, dense[:, 0])
        r = np.maximum(np.interp(v, s, dense[:, 1]), 0)
        dz = np.interp(v, s, dense[:, 2])
        th = 2 * np.pi * (u - 0.5)
        return np.stack([r * sx * np.sin(th), y, r * sz * np.cos(th) + dz], axis=-1)
    return Surface(fn, nu, nv, pos, rot, wrap_u=True, **kw)


def cylinder(pos, r, h, rot=(0, 0, 0), r_top=None, caps=True, **kw):
    """Standing on pos, h tall (along y before rot)"""
    rt = r if r_top is None else r_top
    prof = [(0, r), (h, rt)]
    if caps:
        b = min(r, rt, h) * 0.06
        prof = [(0, 0), (0, r - b), (b * 0.3, r), (h - b * 0.3, rt), (h, rt - b), (h, 0)]
    return lathe(prof, pos, rot, smooth=False, nv=len(prof) * 2 + 2, **kw)


def tube(path, radii, nu=10, nv=None, caps=True, flat=1.0, smooth=True, **kw):
    """A circle swept along a curve through the points of path, as thick as radii (one, or one for each point). caps
    rounds off its ends. flat < 1 flattens it across, e.g a strap"""
    pts = np.asarray(path, dtype=float)
    rad = np.broadcast_to(np.asarray(radii, dtype=float), (len(pts),))
    dense = _densify(np.column_stack([pts, rad]), smooth)
    c, r = dense[:, :3], dense[:, 3]
    if caps:
        t0 = c[0] - c[1]
        t0 /= np.linalg.norm(t0)
        t1 = c[-1] - c[-2]
        t1 /= np.linalg.norm(t1)
        k = np.linspace(0, 1, 7)[1:]
        start = [c[0] + t0 * r[0] * kk for kk in k[::-1]]
        start_r = [r[0] * math.sqrt(max(0.0, 1 - kk * kk)) for kk in k[::-1]]
        end = [c[-1] + t1 * r[-1] * kk for kk in k]
        end_r = [r[-1] * math.sqrt(max(0.0, 1 - kk * kk)) for kk in k]
        c = np.vstack([start, c, end])
        r = np.concatenate([start_r, r, end_r])
    s = _by_length(c)
    # Frames carried along the curve without twisting
    tang = np.gradient(c, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=-1, keepdims=True), 1e-12)
    up = np.array([0, 1, 0]) if abs(tang[0][1]) < 0.9 else np.array([1, 0, 0])
    n = np.cross(up, tang[0])
    n /= np.linalg.norm(n)
    normals = [n]
    for i in range(1, len(c)):
        n = normals[-1] - tang[i] * np.dot(normals[-1], tang[i])
        n /= max(np.linalg.norm(n), 1e-12)
        normals.append(n)
    normals = np.array(normals)
    binormals = np.cross(tang, normals)
    if nv is None:
        nv = max(8, len(pts) * 4)

    def at(v, arr):
        return np.stack([np.interp(v, s, arr[:, k]) for k in range(3)], axis=-1)

    def fn(u, v):
        a = 2 * np.pi * u
        cc, nn, bb = at(v, c), at(v, normals), at(v, binormals)
        rr = np.interp(v, s, r)[..., None]
        return cc + rr * (np.cos(a)[..., None] * nn + flat * np.sin(a)[..., None] * bb)
    return Surface(fn, nu, nv, wrap_u=True, **kw)


def extrude(profile, z0, z1, smooth=False, nv=None, **kw):
    """A profile of (x, y) points pulled along z from z0 to z1, e.g a concrete barrier. The profile goes up its left
    side (-x), over the top and down its right side, so it faces out. u goes along z"""
    prof = np.asarray(profile, dtype=float)
    dense = _densify(prof, smooth, 12)
    s = _by_length(dense)
    if nv is None:
        nv = max(4, len(profile) * 2)

    def fn(u, v):
        x = np.interp(v, s, dense[:, 0])
        y = np.interp(v, s, dense[:, 1])
        return np.stack([x, y, z0 + (z1 - z0) * u], axis=-1)
    return Surface(fn, 2, nv, **kw)


def plane(origin, a, b, nu=2, nv=2, **kw):
    """A parallelogram from origin along a (u) and b (v). It faces a x b"""
    o, a, b = (np.asarray(x, dtype=float) for x in (origin, a, b))

    def fn(u, v):
        return o + u[..., None] * a + v[..., None] * b
    return Surface(fn, nu, nv, **kw)


def box(center, size, rot=(0, 0, 0), bottom=False, divide=1):
    """The faces of a box, each a plane with its own part of the texture, so facades get as many texels as they need.
    v goes up on the sides, and towards +z on the top. Returns the faces: [front, back, right, left, top(, bottom)]"""
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    M = rotation(*rot)
    c = np.array(center, dtype=float)

    def P(x, y, z):
        return c + M @ np.array([x, y, z], dtype=float)

    def D(x, y, z):
        return M @ np.array([x, y, z], dtype=float)
    faces = [
        plane(P(-sx, -sy, sz), D(2 * sx, 0, 0), D(0, 2 * sy, 0), divide, divide),     # front (+z)
        plane(P(sx, -sy, -sz), D(-2 * sx, 0, 0), D(0, 2 * sy, 0), divide, divide),    # back
        plane(P(sx, -sy, sz), D(0, 0, -2 * sz), D(0, 2 * sy, 0), divide, divide),     # right (+x)
        plane(P(-sx, -sy, -sz), D(0, 0, 2 * sz), D(0, 2 * sy, 0), divide, divide),    # left
        plane(P(-sx, sy, sz), D(2 * sx, 0, 0), D(0, 0, -2 * sz), divide, divide),     # top
    ]
    if bottom:
        faces.append(plane(P(-sx, -sy, -sz), D(2 * sx, 0, 0), D(0, 0, 2 * sz), divide, divide))
    return faces


#
# Painters: a painter makes the colors of the texels of a surface, from a Context of where they are. Paint objects add
# up: a base painter + decals, each of which paints over what is there
#


class Context:
    def __init__(self, u, v, p, n, lu, lv, seed):
        self.u, self.v, self.p, self.n = u, v, p, n
        self.lu, self.lv = lu, lv           # How long the surface is around and along, in model units
        self.seed = seed

    @property
    def shape(self):
        return self.u.shape

    def noise(self, scale=1.0, octaves=4, seed=0):
        return fbm(self.p, scale, octaves, self.seed + seed)


class Paint:
    def __init__(self, fn, decals=()):
        self.fn = fn
        self.decals = list(decals)

    def __add__(self, decal):
        return Paint(self.fn, self.decals + [decal])

    def __call__(self, ctx):
        out = self.fn(ctx)
        for d in self.decals:
            out = d(ctx, out)
        return np.clip(out, 0, 1)


def _varied(ctx, c, var, scale, warm=0.03):
    """A color with blotches of lighter and darker in it, the lighter a bit warmer and the darker a bit cooler"""
    c = rgb(c)
    k = (ctx.noise(scale) - 0.5) * 2 * var
    fine = (ctx.noise(scale * 6, 2, 5) - 0.5) * var * 0.6
    out = c[None, None, :] * (1 + k + fine)[..., None]
    shift = np.array([warm, 0, -warm])
    return out + shift * k[..., None] * 4


def color(c, var=0.07, scale=2.0):
    return Paint(lambda ctx: _varied(ctx, c, var, scale))


def skin(c, var=0.05):
    def fn(ctx):
        base = _varied(ctx, c, var, 3.0)
        flush = smoothstep(0.55, 0.8, ctx.noise(1.7, 3, 9))[..., None] * np.array([0.05, -0.01, -0.02])
        return base + flush
    return Paint(fn)


def cloth(c, folds=5, depth=0.12, var=0.06, weave=0.04):
    """Fabric: soft folds running along v, a bit of weave"""
    def fn(ctx):
        base = _varied(ctx, c, var, 2.5)
        warp = ctx.noise(1.5, 2, 3) * 1.5
        fold = np.sin(2 * np.pi * (ctx.u * folds + warp))
        fold = fold * smoothstep(0.0, 0.25, ctx.v) * smoothstep(1.0, 0.75, ctx.v) * 0.5 + fold * 0.5
        w = (np.sin(ctx.u * ctx.lu * 90) * np.sin(ctx.v * ctx.lv * 90)) * weave
        return base * (1 + depth * fold + w)[..., None]
    return Paint(fn)


def knit(c, rows=40):
    """Knitted wool: rows of little v shapes"""
    def fn(ctx):
        base = _varied(ctx, c, 0.05, 3)
        x = ctx.u * ctx.lu * rows / 2
        y = ctx.v * ctx.lv * rows
        stitch = np.abs(((x * 2) % 2) - 1) * 0.5 + (y % 1)
        k = np.sin(stitch * np.pi * 2) * 0.12
        return base * (1 + k)[..., None]
    return Paint(fn)


def leather(c):
    def fn(ctx):
        base = _varied(ctx, c, 0.1, 3)
        crack = smoothstep(0.48, 0.5, ctx.noise(14, 2, 7)) * smoothstep(0.52, 0.5, ctx.noise(14, 2, 7))
        return base * (1 - 0.18 * crack)[..., None] * (0.92 + 0.16 * ctx.noise(5, 2, 2))[..., None]
    return Paint(fn)


def metal(c, shine=0.35):
    """Brushed metal that catches the light on its top"""
    def fn(ctx):
        base = _varied(ctx, c, 0.05, 2)
        streak = (ctx.noise(1, 3, 4) - 0.5) * 0.25
        band = smoothstep(0.2, 0.9, ctx.n[..., 1]) * shine
        scratches = (fbm(ctx.p * np.array([40, 2, 40]), 1, 2, 11) - 0.5) * 0.1
        return base * (0.8 + streak + scratches)[..., None] + band[..., None] * 0.6
    return Paint(fn)


def wood(c, rings=10.0):
    """Planks with grain along v"""
    def fn(ctx):
        base = _varied(ctx, c, 0.08, 1.5)
        g = ctx.u * ctx.lu * rings + ctx.noise(1.2, 3, 8) * 3
        grain = (np.sin(g * np.pi * 2) * 0.5 + 0.5) ** 3
        knot = smoothstep(0.82, 0.9, ctx.noise(3, 2, 12))
        return base * (1 - 0.18 * grain - 0.25 * knot)[..., None]
    return Paint(fn)


def hair(c, strands=60):
    """Hair, or fur: streaks along v, lighter where it catches the light"""
    def fn(ctx):
        base = _varied(ctx, c, 0.06, 2)
        s = fbm(np.stack([ctx.u * strands, ctx.v * 2, np.zeros_like(ctx.u)], -1), 1, 3, ctx.seed + 21)
        streak = (s - 0.5) * 0.5
        sheen = smoothstep(0.3, 0.9, ctx.n[..., 1]) * 0.25
        return base * (0.9 + streak + sheen)[..., None]
    return Paint(fn)


def fur(c):
    def fn(ctx):
        base = _varied(ctx, c, 0.08, 2)
        tufts = (ctx.noise(9, 3, 31) - 0.5) * 0.55
        return base * (0.95 + tufts)[..., None]
    return Paint(fn)


def stone(c, scale=1.0):
    def fn(ctx):
        base = _varied(ctx, c, 0.12, 0.8 * scale)
        pits = smoothstep(0.62, 0.7, ctx.noise(6 * scale, 3, 41)) * 0.25
        return base * (1 - pits)[..., None]
    return Paint(fn)


def glass(c=(0.16, 0.24, 0.34)):
    """Window glass: dark, with a lighter sky reflected in its top, and a streak of shine"""
    def fn(ctx):
        c0 = rgb(c)
        sky = smoothstep(-0.2, 0.9, ctx.n[..., 1])[..., None] * 0.25
        d = ctx.p[..., 0] * 0.6 + ctx.p[..., 1] * 1.0 + ctx.p[..., 2] * 0.4
        streak = (smoothstep(0.75, 0.95, np.sin(d * 1.3) * 0.5 + 0.5) * 0.3)[..., None]
        return c0[None, None] + sky * np.array([0.5, 0.65, 0.8]) + streak
    return Paint(fn)


def snow(c=(0.94, 0.96, 1.0)):
    def fn(ctx):
        base = _varied(ctx, c, 0.04, 2)
        blue = smoothstep(0.4, -0.6, ctx.n[..., 1])[..., None] * np.array([-0.12, -0.05, 0.02])
        sparkle = (ctx.noise(30, 1, 77) > 0.86)[..., None] * 0.08
        return base + blue + sparkle
    return Paint(fn)


def ghostly(c=(0.88, 0.92, 1.0)):
    def fn(ctx):
        base = _varied(ctx, c, 0.05, 1.5)
        swirl = np.sin(ctx.v * 12 + ctx.noise(2, 3, 5) * 6) * 0.05
        return base * (1 + swirl)[..., None] + smoothstep(0.3, -0.5, ctx.p[..., 1] - 1.0)[..., None] * np.array([-0.1, -0.05, 0.05])
    return Paint(fn)


def tinted(lightness=0.92, var=0.05):
    """For a part the game colors (tint=True): light grey, with the shading painted in"""
    return Paint(lambda ctx: _varied(ctx, (lightness,) * 3, var, 1.5, warm=0))


#
# Decals: they paint over what is there. Most take places in (u, v) of the surface, and sizes in model units
#


def _ellipse(ctx, u0, v0, ru, rv, soft=0.12):
    """How much of each texel is in an ellipse around (u0, v0), with radii in model units"""
    du = (ctx.u - u0)
    if du.size and True:
        du = (du + 0.5) % 1.0 - 0.5          # Across the seam of a closed surface
    d = np.sqrt((du * ctx.lu / ru) ** 2 + ((ctx.v - v0) * ctx.lv / rv) ** 2)
    return smoothstep(1 + soft, 1 - soft, d)


def _over(base, c, a):
    c = rgb(c) if not isinstance(c, np.ndarray) or c.ndim == 1 else c
    return base * (1 - a[..., None]) + c * a[..., None]


def bands(c, ranges, axis="v", soft=0.01):
    """Stripes of a color across the surface, at ranges [(from, to)] of v (or u)"""
    def fn(ctx, base):
        t = ctx.v if axis == "v" else ctx.u
        a = 0
        for lo, hi in ranges:
            a = np.maximum(a, smoothstep(lo - soft, lo + soft, t) * smoothstep(hi + soft, hi - soft, t))
        return _over(base, _varied(ctx, c, 0.05, 3), a)
    return fn


def stripes(c, count, width=0.5, axis="v", angle=0.0):
    """Regular stripes, e.g a scarf or a striped shirt"""
    def fn(ctx, base):
        x = ctx.v * ctx.lv if axis == "v" else ctx.u * ctx.lu
        y = ctx.u * ctx.lu if axis == "v" else ctx.v * ctx.lv
        t = (x + y * math.tan(math.radians(angle))) * count / (ctx.lv if axis == "v" else ctx.lu)
        f = t % 1.0
        a = smoothstep(width + 0.04, width - 0.04, f) * smoothstep(-0.04, 0.04, f)
        return _over(base, _varied(ctx, c, 0.05, 3), a)
    return fn


def checks(c, size=0.25):
    def fn(ctx, base):
        x = np.floor(ctx.u * ctx.lu / size) + np.floor(ctx.v * ctx.lv / size)
        a = (x % 2 == 0).astype(float) * 0.85
        return _over(base, _varied(ctx, c, 0.05, 3), a)
    return fn


def spots(c, size=0.12, density=0.3, seed=3):
    """Round spots or flowers scattered over it"""
    def fn(ctx, base):
        cell = size * 3
        g = np.stack([ctx.u * ctx.lu / cell, ctx.v * ctx.lv / cell], -1)
        f = np.floor(g)
        a = np.zeros(ctx.shape)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                ci = f + np.array([ox, oy])
                h = _hash3(ci[..., 0].astype(np.int64), ci[..., 1].astype(np.int64), np.zeros(ctx.shape, np.int64), seed)
                h2 = _hash3(ci[..., 0].astype(np.int64), ci[..., 1].astype(np.int64), np.ones(ctx.shape, np.int64), seed)
                center = ci + 0.5 + (np.stack([h, h2], -1) - 0.5) * 0.6
                d = np.linalg.norm((g - center) * cell, axis=-1) / size
                keep = (h < density).astype(float)
                a = np.maximum(a, smoothstep(1.1, 0.9, d) * keep)
        return _over(base, _varied(ctx, c, 0.06, 3), a)
    return fn


def flowers(petal, middle=(1.0, 0.85, 0.2), size=0.16, density=0.35, seed=5):
    """A flower print, e.g a Hawaiian shirt"""
    def fn(ctx, base):
        cell = size * 2.6
        g = np.stack([ctx.u * ctx.lu / cell, ctx.v * ctx.lv / cell], -1)
        f = np.floor(g)
        out = base
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                ci = f + np.array([ox, oy])
                ix, iy = ci[..., 0].astype(np.int64), ci[..., 1].astype(np.int64)
                h = _hash3(ix, iy, np.zeros(ctx.shape, np.int64), seed)
                h2 = _hash3(ix, iy, np.ones(ctx.shape, np.int64), seed)
                rot = _hash3(ix, iy, np.full(ctx.shape, 2, np.int64), seed) * 6.28
                center = ci + 0.5 + (np.stack([h, h2], -1) - 0.5) * 0.5
                d = (g - center) * cell
                r = np.linalg.norm(d, axis=-1)
                ang = np.arctan2(d[..., 1], d[..., 0]) + rot
                petals = size * (0.55 + 0.45 * np.abs(np.cos(ang * 2.5)))
                keep = (h < density)
                a_p = smoothstep(petals + 0.015, petals - 0.015, r) * keep
                a_m = smoothstep(size * 0.25, size * 0.18, r) * keep
                out = _over(out, rgb(petal), a_p)
                out = _over(out, rgb(middle), a_m)
        return out
    return fn


def stains(c, amount=0.25, scale=2.5, seed=7):
    """Irregular smears of a color, e.g blood or oil"""
    def fn(ctx, base):
        n = fbm(ctx.p, scale, 4, ctx.seed + seed)
        lo = 1 - amount - 0.15
        a = smoothstep(lo, lo + 0.06, n) * (0.75 + 0.25 * ctx.noise(scale * 4, 2, seed + 3))
        return _over(base, _varied(ctx, c, 0.15, 4), a)
    return fn


def painted(fn):
    """A painter from a function of the Context to colors, e.g colors by where on the model"""
    return Paint(fn)


def patch(c, u0, v0, ru, rv, soft=0.12, var=0.05):
    """An ellipse of a color, e.g a badge, a stain, a cheek"""
    def fn(ctx, base):
        return _over(base, _varied(ctx, c, var, 3), _ellipse(ctx, u0, v0, ru, rv, soft))
    return fn


def rect(c, u0, u1, v0, v1, soft=0.01):
    """A rectangle in (u, v), e.g a window or a pocket"""
    def fn(ctx, base):
        a = (smoothstep(u0 - soft, u0 + soft, ctx.u) * smoothstep(u1 + soft, u1 - soft, ctx.u) *
             smoothstep(v0 - soft, v0 + soft, ctx.v) * smoothstep(v1 + soft, v1 - soft, ctx.v))
        return _over(base, _varied(ctx, c, 0.04, 3), a)
    return fn


def edges(amount=0.18, width=0.06, dark=False):
    """Worn, lighter edges (or darker grime) near the borders of a plane, or the ends of a surface"""
    def fn(ctx, base):
        wu = width / max(ctx.lu, 1e-3)
        wv = width / max(ctx.lv, 1e-3)
        e = np.maximum(smoothstep(wu, 0, ctx.u) + smoothstep(1 - wu, 1, ctx.u), smoothstep(wv, 0, ctx.v) + smoothstep(1 - wv, 1, ctx.v))
        e = np.clip(e, 0, 1) * (0.6 + 0.4 * ctx.noise(8, 2, 13))
        k = -amount if dark else amount
        return base * (1 + k * e)[..., None]
    return fn


def grime(amount=0.25, height=0.6):
    """Darker towards the ground, and in blotches"""
    def fn(ctx, base):
        low = smoothstep(height, 0, ctx.p[..., 1]) * amount
        blot = smoothstep(0.55, 0.75, ctx.noise(2.5, 3, 19)) * amount * 0.6
        return base * (1 - low - blot)[..., None]
    return fn


def face(eye=(0.25, 0.45, 0.75), v=0.52, spacing=0.19, size=0.11, mouth="smile", mouth_v=None, brow=(0.2, 0.13, 0.08),
         brow_tilt=0.0, blush=True, lips=(0.55, 0.22, 0.2), look=(0.0, 0.0), closed=False, width=1.0):
    """A cartoon face on the front of a head (u = 0.5): big eyes with a shine, brows, a mouth and pink cheeks. Sizes are
    in model units. mouth is smile, grin, open, frown, line, o, or None. brow_tilt > 0 is angry, < 0 worried"""
    def fn(ctx, base):
        out = base
        skin_c = base
        mv = mouth_v if mouth_v is not None else v - 2.6 * size / ctx.lv
        if blush:
            for side in (-1, 1):
                a = _ellipse(ctx, 0.5 + side * spacing * 1.15 / ctx.lu, mv + 0.6 * size / ctx.lv, size * 0.9, size * 0.6, 0.9) * 0.35
                out = _over(out, (0.95, 0.45, 0.42), a)
        for side in (-1, 1):
            u0 = 0.5 + side * spacing / ctx.lu
            if closed:
                du = ((ctx.u - u0) * ctx.lu) / (size * width)
                dv = (ctx.v - v) * ctx.lv / size
                arc = np.abs(dv + 0.35 * (1 - du ** 2)) < 0.18
                out = _over(out, (0.12, 0.08, 0.06), (arc & (np.abs(du) < 1)).astype(float))
            else:
                ring = _ellipse(ctx, u0, v, size * width * 1.12, size * 1.12, 0.1)
                out = _over(out, (0.12, 0.08, 0.06), ring)
                white = _ellipse(ctx, u0, v, size * width, size, 0.1)
                out = _over(out, (0.98, 0.96, 0.92), white)
                iu = u0 + (look[0] * size * 0.35 - side * size * 0.08) / ctx.lu
                iv = v + (look[1] - 0.1) * size / ctx.lv
                out = _over(out, rgb(eye), _ellipse(ctx, iu, iv, size * 0.6 * width, size * 0.66, 0.12) * white)
                out = _over(out, (0.05, 0.04, 0.05), _ellipse(ctx, iu, iv, size * 0.3 * width, size * 0.34, 0.15) * white)
                out = _over(out, (1, 1, 1), _ellipse(ctx, iu + size * 0.2 / ctx.lu, iv + size * 0.28 / ctx.lv, size * 0.14, size * 0.14, 0.2) * white)
                # The upper lid, a bit darker over the eye
                lid = _ellipse(ctx, u0, v + size * 0.55 / ctx.lv, size * width * 1.2, size * 0.55, 0.15) * white
                out = _over(out, skin_c * 0.85, lid * 0.7)
            if brow is not None:
                du = (ctx.u - u0) * ctx.lu
                tilt = -side * brow_tilt * du / (size * 1.2)
                bv = v + (size * 1.8) / ctx.lv
                dvb = (ctx.v - bv) * ctx.lv - tilt * size * 0.7
                a = (np.abs(dvb) < size * 0.22) & (np.abs(du) < size * 1.1)
                out = _over(out, rgb(brow), a.astype(float) * 0.95)
        if mouth:
            du = (ctx.u - 0.5) * ctx.lu
            dv = (ctx.v - mv) * ctx.lv
            w = size * 1.6
            t = du / w
            inside = np.abs(t) < 1
            if mouth in ("smile", "grin", "frown"):
                k = size * (0.7 if mouth != "frown" else -0.6)
                curve = k * (t ** 2) - k * 0.5
                thick = size * (0.18 if mouth != "grin" else 0.45)
                a = (np.abs(dv - curve) < thick) & inside
                out = _over(out, rgb(lips) * 0.6, a.astype(float))
                if mouth == "grin":
                    teeth = (dv - curve > -thick * 0.1) & (dv - curve < thick * 0.6) & (np.abs(t) < 0.75)
                    out = _over(out, (0.97, 0.95, 0.9), teeth.astype(float))
            elif mouth == "line":
                out = _over(out, rgb(lips) * 0.6, ((np.abs(dv) < size * 0.15) & (np.abs(t) < 0.7)).astype(float))
            elif mouth in ("open", "o"):
                r = 0.55 if mouth == "open" else 0.38
                a = _ellipse(ctx, 0.5, mv, w * r, size * (0.7 if mouth == "open" else 0.45), 0.1)
                out = _over(out, (0.35, 0.08, 0.08), a)
                if mouth == "open":
                    out = _over(out, (0.92, 0.4, 0.4), _ellipse(ctx, 0.5, mv - size * 0.3 / ctx.lv, w * 0.3, size * 0.25, 0.2) * a)
        return out
    return fn


#
# Models
#


class Model:
    def __init__(self, name, size=512, ground_ao=True, light=0.3, detail=0.13):
        self.name = name
        self.detail = detail            # The shortest edges, in model units: smaller parts get fewer segments
        self.size = size
        self.surfaces = []
        self.ground_ao = ground_ao      # Darker near y = 0, where it stands on the ground
        self.light = light              # How much light and shade is painted into the texture
        self.seed = sum(ord(c) for c in name)
        self.post = (1.0, np.zeros(3))     # A scale and an offset put on the mesh when it is written (fit_height)

    def add(self, surface, paint, tint=False, crease=0.0, share=None):
        """A surface, or a list of them (a box), with a painter. share: a surface whose texture it uses too, e.g the
        second wheel"""
        if isinstance(surface, (list, tuple)):
            return [self.add(s, paint, tint, crease) for s in surface]
        # Small parts need fewer segments: no edge much shorter than detail
        lu, lv = surface.lengths()
        surface.nu = int(np.clip(round(lu / self.detail), 6, surface.nu))
        surface.nv = int(np.clip(round(lv / self.detail), 3, surface.nv))
        surface.paint = paint
        surface.tint = tint
        surface.crease = crease
        surface.share = share
        self.surfaces.append(surface)
        return surface

    def mirror(self, surface, axis=0):
        """A copy mirrored across x = 0 (or another axis), with the same part of the texture"""
        if isinstance(surface, (list, tuple)):
            return [self.mirror(s, axis) for s in surface]
        s = surface.copy()
        F = np.eye(3)
        F[axis, axis] = -1
        s.M = F @ surface.M
        s.t = F @ surface.t
        s.orient = -surface.orient
        s.share = surface.share or surface
        self.surfaces.append(s)
        return s

    def both(self, surface, paint, tint=False, crease=0.0):
        """A surface on the +x side, and its mirror on the -x side"""
        s = self.add(surface, paint, tint, crease)
        self.mirror(s)
        return s

    def bounds(self):
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        g = np.linspace(0, 1, 9)
        u, v = np.meshgrid(g, g)
        for s in self.surfaces:
            p = s.points(u, v).reshape(-1, 3)
            lo, hi = np.minimum(lo, p.min(0)), np.maximum(hi, p.max(0))
        return lo, hi

    def fit_height(self, height):
        """Makes the model as tall as height, standing on y = 0, when it is written. The painters still see the
        positions it was made with"""
        lo, hi = self.bounds()
        k = height / (hi[1] - lo[1])
        self.post = (k, np.array([0, -lo[1] * k, 0]))

    # The texture

    def _pack(self):
        owners = [s for s in self.surfaces if s.share is None]
        dims = {id(s): s.lengths() for s in owners}
        total = sum(lu * lv for lu, lv in dims.values())
        density = math.sqrt(self.size * self.size * 0.62 / max(total, 1e-6))
        pad = 3
        while True:
            rects = []
            for s in owners:
                lu, lv = dims[id(s)]
                w = int(np.clip(round(lu * density), 4, self.size - 2 * pad))
                h = int(np.clip(round(lv * density), 4, self.size - 2 * pad))
                rects.append((s, w, h))
            rects.sort(key=lambda r: -r[2])
            x = y = shelf = 0
            ok = True
            for s, w, h in rects:
                if x + w + 2 * pad > self.size:
                    x, y = 0, y + shelf
                    shelf = 0
                if y + h + 2 * pad > self.size:
                    ok = False
                    break
                s.region = (x + pad, y + pad, w, h)
                x += w + 2 * pad
                shelf = max(shelf, h + 2 * pad)
            if ok:
                break
            density *= 0.93
        for s in self.surfaces:
            if s.share is not None:
                s.region = s.share.region

    def _paint(self, s):
        x0, y0, w, h = s.region
        pad = 3
        iu = (np.arange(-pad, w + pad) + 0.5) / w
        iv = (np.arange(-pad, h + pad) + 0.5) / h
        u, v = np.meshgrid(iu, iv[::-1])       # Row 0 of the image is the top: v = 1
        if s.wrap_u:
            uu = u % 1.0
        else:
            uu = np.clip(u, 0, 1)
        vv = np.clip(v, 0, 1)
        p, n = s.frame(uu, vv)
        lu, lv = s.lengths()
        ctx = Context(uu, vv, p, n, lu, lv, self.seed + len(str(x0)))
        col = s.paint(ctx) if s.paint else np.full(u.shape + (3,), 0.8)
        # The light and shade a hand-painted texture has in it: light from above, darker underneath, in the creases and
        # near the ground, and broad strokes of lighter and darker
        k = self.light
        shade = 1 + k * (0.55 * n[..., 1] + 0.12 * n[..., 2]) - k * 0.15
        if self.ground_ao:
            shade *= 1 - 0.32 * np.exp(-np.maximum(p[..., 1], 0) / 0.35)
        if s.crease:
            d = np.minimum(vv * lv, (1 - vv) * lv)
            shade *= 1 - s.crease * np.exp(-d / 0.12)
        stroke = fbm(p * np.array([1.0, 3.0, 1.0]), 1.4, 3, self.seed + 101)
        shade *= 0.93 + 0.14 * stroke
        col = col * shade[..., None]
        # A little more saturated, as painted
        grey = col.mean(axis=-1, keepdims=True)
        col = grey + (col - grey) * 1.12
        return np.clip(col, 0, 1)

    def texture(self):
        img = np.zeros((self.size, self.size, 3))
        img[:] = 0.5
        pad = 3
        for s in self.surfaces:
            if s.share is not None:
                continue
            x0, y0, w, h = s.region
            img[y0 - pad:y0 + h + pad, x0 - pad:x0 + w + pad] = self._paint(s)
        return img

    # The mesh

    def _mesh(self, s):
        nu, nv = s.nu, s.nv
        g_u = np.linspace(0, 1, nu + 1)
        g_v = np.linspace(0, 1, nv + 1)
        u, v = np.meshgrid(g_u, g_v)
        p, n = s.frame(u, v)
        x0, y0, w, h = s.region
        tu = (x0 + u * w) / self.size
        tv = 1 - (y0 + (1 - v) * h) / self.size
        verts = p.reshape(-1, 3) * self.post[0] + self.post[1]
        norms = n.reshape(-1, 3)
        uvs = np.stack([tu, tv], -1).reshape(-1, 2)
        tris = []
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i
                b, c, d = a + 1, a + nu + 2, a + nu + 1
                for t in ((a, b, c), (a, c, d)):
                    pa, pb, pc = verts[t[0]], verts[t[1]], verts[t[2]]
                    if np.linalg.norm(np.cross(pb - pa, pc - pa)) < 1e-9:
                        continue
                    tris.append(t if s.orient > 0 else (t[0], t[2], t[1]))
        return verts, norms, uvs, tris

    def write(self, out=OUT):
        self._pack()
        os.makedirs(out, exist_ok=True)
        tex = self.texture()
        Image.fromarray((tex * 255).astype(np.uint8)).save(os.path.join(out, self.name + ".png"), optimize=True)
        groups = {"paint": [], "body": []}
        lines_v, lines_t, lines_n = [], [], []
        count = 0
        for s in self.surfaces:
            verts, norms, uvs, tris = self._mesh(s)
            for p in verts:
                lines_v.append("v " + " ".join(_num(x, 3) for x in p))
            for t in uvs:
                lines_t.append("vt " + " ".join(_num(x, 4) for x in t))
            for q in norms:
                lines_n.append("vn " + " ".join(_num(x, 2) for x in q))
            g = groups["body" if s.tint else "paint"]
            for t in tris:
                g.append("f " + " ".join(f"{count + k + 1}/{count + k + 1}/{count + k + 1}" for k in t))
            count += len(verts)
        with open(os.path.join(out, self.name + ".mtl"), "w") as f:
            f.write("# Generated by tools/sculpt.py. The texture is %s.png, which the game puts on every material\n" % self.name)
            f.write("\nnewmtl paint\nKa 0 0 0\nKd 0.9800 0.9800 0.9800\nKs 0 0 0\nd 1\nillum 1\n")
            if groups["body"]:
                f.write("\nnewmtl body\nKa 0 0 0\nKd 1.0000 1.0000 1.0000\nKs 0 0 0\nd 1\nillum 1\n")
        with open(os.path.join(out, self.name + ".obj"), "w") as f:
            f.write(f"# Generated by tools/sculpt.py\nmtllib {self.name}.mtl\no {self.name}\n")
            f.write("\n".join(lines_v) + "\n" + "\n".join(lines_t) + "\n" + "\n".join(lines_n) + "\n")
            for name, faces in groups.items():
                if faces:
                    f.write(f"usemtl {name}\n" + "\n".join(faces) + "\n")
        return sum(len(g) for g in groups.values())


def _num(x, digits):
    """A number as short as it can be written"""
    t = f"{x:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if t in ("", "-", "-0") else t


#
# A preview: draws a model from the front and from three quarters, with its texture, in software
#


def load_obj(path):
    vs, vts, vns, faces, tint = [], [], [], [], []
    current = "paint"
    for line in open(path):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            vs.append([float(x) for x in parts[1:4]])
        elif parts[0] == "vt":
            vts.append([float(x) for x in parts[1:3]])
        elif parts[0] == "vn":
            vns.append([float(x) for x in parts[1:4]])
        elif parts[0] == "usemtl":
            current = parts[1]
        elif parts[0] == "f":
            idx = [[int(i) - 1 if i else 0 for i in p.split("/")] for p in parts[1:4]]
            faces.append(idx)
            tint.append(current == "body")
    return np.array(vs), np.array(vts) if vts else np.zeros((1, 2)), np.array(vns), faces, tint


def render(path, size=420, yaw=30.0, pitch=18.0, tint_color=(0.85, 0.2, 0.2)):
    """An image of the model of an OBJ, with its texture if there is one"""
    vs, vts, vns, faces, tint = load_obj(path)
    png = path[:-4] + ".png"
    tex = np.asarray(Image.open(png).convert("RGB"), dtype=float) / 255 if os.path.exists(png) else None
    R = rotation(pitch, yaw, 0)
    pv = vs @ R.T
    pn = vns @ R.T
    lo, hi = pv.min(0), pv.max(0)
    scale = size * 0.85 / max(hi[0] - lo[0], hi[1] - lo[1])
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    sx = (pv[:, 0] - cx) * scale + size / 2
    sy = size / 2 - (pv[:, 1] - cy) * scale
    img = np.zeros((size, size, 3))
    img[:] = (0.2, 0.22, 0.26)
    zbuf = np.full((size, size), -1e9)
    light = np.array([-0.4, 0.8, 0.5])
    light /= np.linalg.norm(light)
    for f, is_tint in zip(faces, tint):
        (a, ta, na), (b, tb, nb), (c, tc, nc) = f
        xs = np.array([sx[a], sx[b], sx[c]])
        ys = np.array([sy[a], sy[b], sy[c]])
        area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
        if area >= 0:           # Facing away (y of the screen points down)
            continue
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, size))
        y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, size))
        if x0 >= x1 or y0 >= y1:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        w0 = ((xs[1] - X) * (ys[2] - Y) - (xs[2] - X) * (ys[1] - Y)) / area
        w1 = ((xs[2] - X) * (ys[0] - Y) - (xs[0] - X) * (ys[2] - Y)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * pv[a, 2] + w1 * pv[b, 2] + w2 * pv[c, 2]
        zb = zbuf[y0:y1, x0:x1]
        m = inside & (z > zb)
        if not m.any():
            continue
        n = w0[..., None] * pn[na] + w1[..., None] * pn[nb] + w2[..., None] * pn[nc]
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        if tex is not None:
            t = w0[..., None] * vts[ta] + w1[..., None] * vts[tb] + w2[..., None] * vts[tc]
            tx = np.clip((t[..., 0] * tex.shape[1]).astype(int), 0, tex.shape[1] - 1)
            ty = np.clip(((1 - t[..., 1]) * tex.shape[0]).astype(int), 0, tex.shape[0] - 1)
            col = tex[ty, tx]
        else:
            col = np.full(n.shape, 0.8)
        if is_tint:
            col = col * np.array(tint_color)
        d = np.clip(n @ light, 0, 1)
        rim = (1 - np.clip(n[..., 2], 0, 1)) ** 3 * 0.35
        lit = col * (0.55 + 0.6 * d)[..., None] + rim[..., None] * np.array([1.0, 0.95, 0.85])
        zb[m] = z[m]
        img[y0:y1, x0:x1][m] = np.clip(lit[m], 0, 1)
    return Image.fromarray((img * 255).astype(np.uint8))


def preview(paths, out, size=300):
    """Each model from the front and from three quarters, side by side"""
    tiles = []
    for p in paths:
        tiles.append(render(p, size, yaw=0, pitch=10))
        tiles.append(render(p, size, yaw=35, pitch=22))
    cols = min(len(tiles), 8)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size, rows * size))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * size, (i // cols) * size))
    sheet.save(out)
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "preview":
        print(preview(sys.argv[2:], os.environ.get("PREVIEW", "preview.png")))
