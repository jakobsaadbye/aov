#!/usr/bin/env python3
"""
Writes the models of the heroes to data/models/, with tools/sculpt.py: smooth shapes with a hand-painted texture each.

    python3 tools/make_heroes.py                 all of them
    python3 tools/make_heroes.py karl mads       only these
    python3 tools/make_heroes.py --preview       and a picture of each in the scratchpad (PREVIEW_DIR)

Most heroes are a person() of a Build: the proportions of their body, from a brute (huge shoulders and hands, short
legs, a small head pushed forward) to a slim one or an old one, bent over. Then they get their clothes, their face and
what makes them that hero: armor, a hat, a beard, what they carry. Faces are serious: eyes under heavy lids in
shadowed sockets, brows that say what they are like, and set mouths. A model is made in about the units of a 4.4 tall
person and fitted to the height of its hero (HEIGHTS, the same as the height in src/core/heroes/).
"""

import math
import os
import sys
from dataclasses import dataclass, replace

import numpy as np

from sculpt import (Model, Paint, blob, bulge, squash, horn, loft, lumps, push, bands, cloth, color, cylinder, edges, ellipsoid, fbm, fur, ghostly, glass,
                    grime, hair, knit, lathe, leather, metal, painted, patch, plane, rect, rgb, scales, skin,
                    smoothstep, snow, sphere, spots, stains, stitches, stripes, flowers, torus, tube, wood, _ellipse,
                    _over, _varied)

SKIN = (0.93, 0.72, 0.56)
SKIN_TAN = (0.8, 0.56, 0.4)
SKIN_RUDDY = (0.9, 0.62, 0.5)
SKIN_PALE = (0.96, 0.82, 0.72)
SKIN_OLIVE = (0.84, 0.66, 0.5)
WHITE = (0.93, 0.92, 0.88)
BOOT = (0.32, 0.2, 0.12)
SOLE = (0.16, 0.12, 0.1)

HEIGHTS = {
    "allan": 4.2, "ghosty": 3.4, "butcher": 6.4, "frosty": 4.6, "bjorn": 5.8, "hilda": 4.2, "mira": 4.8, "karl": 4.4,
    "birgit": 4.4, "bent": 4.8, "sigrid": 5.0, "tobias": 4.2, "mads": 4.1, "ditte": 4.3, "gudrun": 3.6, "magnus": 5.6,
    "stormy": 4.3, "hugo": 5.2, "twins": 3.0, "kenji": 4.2, "ivar": 6.0,
}


@dataclass
class Build:
    leg: float = 1.3            # From the ankle to the hip
    torso: float = 1.6          # From the hip to the neck
    hip: float = 0.55           # Half widths
    waist: float = 0.56
    chest: float = 0.74
    shoulder: float = 0.84
    depth: float = 0.66         # How deep the body is, for its width
    arm: float = 0.22           # The radius of the upper arm
    fore: float = 0.19
    arm_len: float = 1.0
    thigh: float = 0.29
    calf: float = 0.23
    hand: float = 1.0
    head: float = 1.0
    jaw: float = 1.0
    foot: float = 1.0
    hunch: float = 0.0          # How far the shoulders and head lean forward
    belly: float = 0.0
    stance: float = 0.42        # How far apart the feet are
    neck: float = 0.22
    traps: float = 0.0          # The muscles between the neck and the shoulders


HERO = Build()
ATHLETE = Build(leg=1.45, chest=0.76, shoulder=0.86, waist=0.48, hip=0.48, arm=0.21, fore=0.18, thigh=0.27, calf=0.22)
BRUTE = Build(leg=1.05, torso=1.85, hip=0.66, waist=0.74, chest=1.08, shoulder=1.22, depth=0.78, arm=0.36, fore=0.33,
              arm_len=1.05, thigh=0.4, calf=0.34, hand=1.5, head=0.82, jaw=1.35, foot=1.3, hunch=0.3, stance=0.55,
              neck=0.33, traps=1.0)
STOCKY = Build(leg=1.15, torso=1.65, hip=0.6, waist=0.64, chest=0.86, shoulder=0.96, depth=0.72, arm=0.27, fore=0.24,
               thigh=0.33, calf=0.27, hand=1.2, jaw=1.15, foot=1.1, stance=0.46, neck=0.26, traps=0.4)
STOUT = Build(leg=1.0, torso=1.65, hip=0.66, waist=0.78, chest=0.82, shoulder=0.88, depth=0.82, belly=1.0, arm=0.25,
              fore=0.22, thigh=0.34, calf=0.27, hand=1.1, jaw=1.15, neck=0.27, stance=0.46)
SLIM = Build(leg=1.6, torso=1.65, hip=0.44, waist=0.42, chest=0.58, shoulder=0.66, depth=0.6, arm=0.16, fore=0.14,
             arm_len=1.08, thigh=0.21, calf=0.17, hand=0.85, head=0.9, jaw=0.9, foot=0.85, stance=0.3, neck=0.18)
OLD = Build(leg=0.95, torso=1.45, hip=0.6, waist=0.58, chest=0.62, shoulder=0.66, depth=0.72, arm=0.17, fore=0.15,
            thigh=0.25, calf=0.19, hand=0.9, head=1.02, jaw=0.95, hunch=0.55, belly=0.35, stance=0.34, neck=0.18)
KID = Build(leg=0.95, torso=1.15, hip=0.44, waist=0.45, chest=0.54, shoulder=0.6, arm=0.16, fore=0.14, thigh=0.21,
            calf=0.18, hand=0.85, head=1.18, jaw=0.85, foot=0.85, stance=0.3, neck=0.17)


#
# The face: painted on the cranium (eyes), the jaw (mouth, stubble) and the brow ridge (brows)
#


def eyes(v=0.5, spacing=0.18, size=0.075, iris=(0.35, 0.28, 0.2), lid=0.3, tilt=0.0, socket=0.35, look=(0, 0),
         white=(0.92, 0.88, 0.8), glow=None):
    """Almond eyes under heavy lids, in shadowed sockets. lid is how much of the eye the upper lid covers, tilt > 0
    lifts the outer corners, look moves the irises. glow paints the whole eye in a color, e.g a ghost's"""
    def fn(ctx, base):
        out = base
        for side in (1, -1):
            u0 = 0.5 + side * spacing / ctx.lu
            du = ((ctx.u - u0 + 0.5) % 1.0 - 0.5) * ctx.lu
            dv = (ctx.v - v) * ctx.lv
            sock = np.exp(-((du / (size * 2.3)) ** 2 + ((dv - size * 0.4) / (size * 1.8)) ** 2))
            out = out * (1 - socket * sock)[..., None]
            xn = du / (size * 1.35)
            outward = xn * side
            yn = (dv - tilt * size * 0.45 * outward) / (size * 0.78)
            r2 = xn ** 2 + yn ** 2 * (1 + 0.25 * xn ** 2)
            top = 1 - 1.7 * lid
            eye = smoothstep(1.06, 0.94, r2) * smoothstep(top + 0.08, top - 0.04, yn)
            lidline = smoothstep(1.25, 1.0, r2) * smoothstep(top - 0.2, top - 0.02, yn) * smoothstep(top + 0.45, top + 0.2, yn)
            lower = smoothstep(1.2, 1.0, r2) * smoothstep(-0.7, -0.95, yn) * 0.5
            out = _over(out, base * 0.78, smoothstep(1.3, 1.0, r2) * (yn > top) * 1.0)
            if glow is not None:
                out = _over(out, rgb(glow), eye)
            else:
                out = _over(out, rgb(white), eye)
                ix = du - look[0] * size * 0.4
                iy = dv - (look[1] - 0.05) * size
                ir = np.sqrt(ix ** 2 + iy ** 2) / (size * 0.62)
                out = _over(out, rgb(iris) * (0.8 + 0.4 * smoothstep(1, 0.3, ir))[..., None], smoothstep(1.08, 0.92, ir) * eye)
                out = _over(out, (0.04, 0.03, 0.03), smoothstep(0.5, 0.4, ir) * eye)
                hl = np.sqrt((ix - size * 0.2) ** 2 + (iy - size * 0.18) ** 2) / (size * 0.16)
                out = _over(out, (1, 1, 1), smoothstep(1.1, 0.8, hl) * eye * 0.9)
            out = _over(out, (0.14, 0.07, 0.05), np.clip(lidline, 0, 1))
            out = _over(out, (0.3, 0.16, 0.12), lower)
        return out
    return fn


def mouth(kind="line", v=0.58, width=0.15, lips=(0.55, 0.28, 0.24), shadow=True):
    """A mouth: line, frown, grim, grit (teeth set), snarl, wail (open), pout or smirk"""
    def fn(ctx, base):
        out = base
        du = ((ctx.u - 0.5 + 0.5) % 1.0 - 0.5) * ctx.lu
        dv = (ctx.v - v) * ctx.lv
        t = du / width
        inside = np.abs(t) < 1
        dark = rgb(lips) * 0.45
        if shadow:
            # The shadow under the lower lip and round the chin, and the lines from the nose
            out = out * (1 - 0.18 * np.exp(-(t / 0.8) ** 2 - ((dv + width * 0.5) / (width * 0.25)) ** 2))[..., None]
            for side in (1, -1):
                fold = np.abs((du - side * width * 1.15) - side * 0.35 * (dv - width * 0.2)) < width * 0.05
                fold = fold & (dv > -width * 0.2) & (dv < width * 0.7)
                out = out * (1 - 0.18 * fold)[..., None]
        if kind in ("line", "frown", "grim", "smirk", "pout"):
            k = {"line": -0.08, "frown": -0.35, "grim": -0.22, "smirk": 0.0, "pout": -0.15}[kind] * width
            curve = k * t ** 2
            if kind == "smirk":
                curve = width * 0.18 * np.clip(t, 0, 1) ** 2 - width * 0.05 * np.clip(-t, 0, 1)
            thick = width * (0.09 if kind != "grim" else 0.13)
            a = (np.abs(dv - curve) < thick) & inside
            out = _over(out, dark, a.astype(float))
            lip = (dv - curve < -thick) & (dv - curve > -thick * 3.0) & (np.abs(t) < 0.7)
            out = _over(out, rgb(lips), lip.astype(float) * 0.45)
        elif kind in ("grit", "snarl"):
            h = width * (0.22 if kind == "grit" else 0.32)
            curve = (width * 0.15 * t ** 2) if kind == "snarl" else 0
            box = (np.abs(dv - curve) < h) & (np.abs(t) < 0.85)
            out = _over(out, dark * 0.6, box.astype(float))
            teeth = (np.abs(dv - curve) < h * 0.7) & (np.abs(t) < 0.78)
            out = _over(out, (0.9, 0.86, 0.74), teeth.astype(float))
            gaps = teeth & ((np.abs(dv - curve) < h * 0.06) | (np.abs(((t * 4) % 1) - 0.5) < 0.06))
            out = _over(out, (0.45, 0.35, 0.3), gaps.astype(float))
        elif kind == "wail":
            r = np.sqrt((du / (width * 0.55)) ** 2 + ((dv + width * 0.2) / (width * 0.8)) ** 2)
            out = _over(out, (0.08, 0.06, 0.12), smoothstep(1.05, 0.95, r))
        return out
    return fn


def stubble(c=(0.25, 0.18, 0.14), amount=0.5, below=0.62):
    def fn(ctx, base):
        speck = (fbm(ctx.p, 60, 1, 91) > 0.5).astype(float) * 0.6 + 0.4
        a = smoothstep(below, below - 0.15, ctx.v) * amount * speck
        return _over(base, rgb(c), a * 0.6)
    return fn


def brows(c=(0.25, 0.16, 0.1), tilt=0.5, thick=0.7, spacing=0.2, length=0.17, v=0.62, gap=1.0):
    """Brows on the brow ridge: tilt > 0 is angry (inner ends down), < 0 worried, thick 0..1"""
    def fn(ctx, base):
        out = base
        for side in (1, -1):
            u0 = 0.5 + side * spacing * gap / ctx.lu
            du = ((ctx.u - u0 + 0.5) % 1.0 - 0.5) * ctx.lu
            dv = (ctx.v - v) * ctx.lv
            t = du * side / length               # -1 at the inner end, 1 at the outer
            centre = -tilt * 0.35 * ctx.lv * (-t) * 0.25
            half = (0.07 + 0.09 * thick) * ctx.lv * (1 - 0.35 * np.clip(t, 0, 1)) * 0.5
            a = (np.abs(t) < 1) & (np.abs(dv - centre) < half * 2)
            streak = 0.75 + 0.25 * (fbm(np.stack([ctx.u * 300, ctx.v * 20, ctx.u * 0], -1), 1, 2, 7))
            out = _over(out, rgb(c) * streak[..., None], a.astype(float))
        return out
    return fn


#
# The body
#


class Body:
    pass


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def _norm(d):
    n = math.sqrt(sum(c * c for c in d)) or 1.0
    return tuple(c / n for c in d)


def person(m, bd, top, legs, shoes=None, arms=None, hands=None, skin_c=SKIN, head_paint=None, eyes_kw=None,
           mouth_kw=None, brows_kw=None, jaw_paint=None, hair_paint=None, hair_style=None, skirt=None,
           arm_pose="down", x=0.0, nose="round", ears=True, sole=None, cuffs=None, neck_paint=None, pecs=False,
           boots=True, face_weight=3.0):
    """A person standing on y = 0, looking at +z, of the proportions of the Build bd. The paints are of its clothes.
    skirt is a paint for a skirt or a long coat over the legs. arm_pose: down, out, forward, up, ready, akimbo, or a
    pair (right, left). Returns where its parts are, for what is added to it"""
    b = Body()
    b.bd, b.x = bd, x
    shoes = shoes or leather(BOOT)
    arms = arms or top
    hands = hands or skin(skin_c)
    eyes_kw, mouth_kw, brows_kw = eyes_kw or {}, mouth_kw or {}, brows_kw or {}

    ankle = 0.3 * bd.foot
    hip = ankle + bd.leg
    neck_y = hip + bd.torso
    sh_y = neck_y - 0.22
    waist_y = hip + bd.torso * 0.28
    chest_y = hip + bd.torso * 0.68

    def lean(y):
        return bd.hunch * 0.65 * min(max((y - waist_y) / (neck_y - waist_y), 0.0), 1.2) ** 2

    b.hip_y, b.waist_y, b.chest_y, b.neck_y, b.sh_y = hip, waist_y, chest_y, neck_y, sh_y
    b.lean = lean

    # Feet: a boot with a darker sole, and a cuff round the ankle
    fs = bd.foot
    for side in (1, -1):
        fx = x + side * bd.stance
        m.add(blob((fx, 0.21 * fs, 0.12 * fs), (0.26 * fs, 0.19 * fs, 0.42 * fs), (0.55, 0.7), rot=(0, side * 7, 0)), shoes)
        m.add(blob((fx, 0.06 * fs, 0.12 * fs), (0.28 * fs, 0.07 * fs, 0.45 * fs), (0.3, 0.6), rot=(0, side * 7, 0)),
              leather(sole or SOLE))
        if boots:
            m.add(torus((fx, ankle + 0.06, 0.0), bd.calf * 0.8, 0.07 * fs), cuffs or shoes)
    # Legs: calf, knee and thigh
    for side in (1, -1):
        fx, hx = x + side * bd.stance, x + side * bd.hip * 0.55
        L = bd.leg
        pts = [(fx, ankle + 0.02, 0.0), (_lerp((fx, 0, 0), (hx, 0, 0), 0.3)[0], ankle + L * 0.3, -0.03),
               (_lerp((fx, 0, 0), (hx, 0, 0), 0.5)[0], ankle + L * 0.5, 0.04), (_lerp((fx, 0, 0), (hx, 0, 0), 0.78)[0], ankle + L * 0.78, 0.0),
               (hx, hip + 0.05, 0.0)]
        m.add(tube(pts, [bd.calf * 0.72, bd.calf * 1.05, bd.calf * 0.85, bd.thigh, bd.thigh * 0.95], nu=12), legs, crease=0.2)
    # The torso
    belly = bd.belly
    prof = [(hip - 0.25, 0.0), (hip - 0.2, bd.hip, 0.0), (hip + 0.08, bd.hip * 1.03, belly * 0.1),
            (waist_y, bd.waist * (1 + 0.18 * belly), belly * 0.35 + lean(waist_y)),
            (hip + bd.torso * 0.48, bd.waist * (1 + 0.28 * belly) * 1.04, belly * 0.4 + lean(hip + bd.torso * 0.48)),
            (chest_y, bd.chest, 0.06 + belly * 0.1 + lean(chest_y)), (sh_y - 0.04, bd.shoulder * 0.9, lean(sh_y)),
            (sh_y + 0.13, bd.shoulder * 0.6, lean(sh_y + 0.13)), (neck_y, bd.neck * 1.35, lean(neck_y)), (neck_y + 0.04, 0.0, lean(neck_y))]
    b.torso = m.add(lathe(prof, (x, 0, 0), sz=bd.depth + belly * 0.1, nu=24, nv=18), top, crease=0.15)
    b.depth_at = lambda y: bd.depth
    if bd.traps:
        m.add(ellipsoid((x, sh_y + 0.05, lean(sh_y) - 0.05), (bd.shoulder * 0.72, 0.26 * bd.traps, 0.42)), top)
    if pecs:
        for side in (1, -1):
            m.add(ellipsoid((x + side * bd.chest * 0.42, chest_y + 0.05, lean(chest_y) + bd.chest * bd.depth * 0.78),
                            (bd.chest * 0.42, 0.26, 0.16)), skin(skin_c), crease=0.1)
    if skirt is not None:
        m.add(lathe([(0.65, 0.0), (0.66, bd.hip * 1.55), (hip * 0.6, bd.hip * 1.35), (hip + 0.15, bd.hip * 1.12), (hip + 0.32, 0.0)],
                    (x, 0, 0), sz=0.82, nu=26), skirt, crease=0.12)
    # Neck
    m.add(tube([(x, sh_y, lean(sh_y)), (x, neck_y + 0.35 * bd.head, lean(neck_y) + bd.hunch * 0.2)], bd.neck, caps=False, nu=10),
          neck_paint or skin(skin_c))

    # Arms: a round shoulder, a bulging upper arm, the elbow, the forearm, and a fist
    b.hands, b.wrists, b.elbows, b.shoulders = [], [], [], []
    upper, fore = bd.torso * 0.42 * bd.arm_len, bd.torso * 0.4 * bd.arm_len
    poses = arm_pose if isinstance(arm_pose, tuple) else (arm_pose, "down" if arm_pose in ("forward", "up", "ready") else arm_pose)
    if arm_pose == "both_up":
        poses = ("up", "up")
    for side, pose in zip((1, -1), poses):
        sh = (x + side * bd.shoulder * 0.98, sh_y - 0.08, lean(sh_y))
        if pose == "down":
            elbow = _add(sh, (side * 0.2, -upper * 0.96, -0.04))
            wrist = _add(elbow, (side * 0.06, -fore * 0.9, 0.24))
        elif pose == "out":
            elbow = _add(sh, (side * 0.42, -upper * 0.82, 0.0))
            wrist = _add(elbow, (side * 0.32, -fore * 0.62, 0.32))
        elif pose == "forward":
            elbow = _add(sh, (side * 0.24, -upper * 0.88, 0.1))
            wrist = _add(elbow, (-side * 0.06, 0.06, fore * 0.96))
        elif pose == "ready":
            elbow = _add(sh, (side * 0.32, -upper * 0.85, 0.1))
            wrist = _add(elbow, (-side * 0.18, 0.12, fore * 0.9))
        elif pose == "akimbo":
            elbow = _add(sh, (side * 0.6, -upper * 0.68, -0.12))
            wrist = (x + side * (bd.waist + 0.12), waist_y + 0.05, 0.1)
        else:  # up
            elbow = _add(sh, (side * 0.32, upper * 0.62, 0.06))
            wrist = _add(elbow, (-side * 0.06, fore * 0.96, 0.12))
        bicep = _add(_lerp(sh, elbow, 0.45), (side * 0.02, 0, 0.02))
        mid = _lerp(elbow, wrist, 0.38)
        m.add(tube([sh, bicep, elbow, mid, wrist], [bd.arm * 1.05, bd.arm * 1.14, bd.fore * 0.92, bd.fore * 1.1, bd.fore * 0.72], nu=12),
              arms, crease=0.12)
        m.add(sphere(sh, bd.arm * 1.3), top)
        d = _norm(tuple(wrist[i] - elbow[i] for i in range(3)))
        hs = bd.hand
        palm = _add(wrist, tuple(c * 0.15 * hs for c in d))
        m.add(ellipsoid(palm, (0.16 * hs, 0.18 * hs, 0.17 * hs)), hands)
        lat = (1.0, 0.0, 0.0) if abs(d[0]) < 0.9 else (0.0, 0.0, 1.0)
        for k in range(4):
            kp = _add(palm, tuple(c * 0.13 * hs for c in d))
            kp = _add(kp, tuple(c * (k - 1.5) * 0.075 * hs for c in lat))
            kp = _add(kp, (0, 0, 0.05 * hs))
            m.add(sphere(kp, 0.065 * hs), hands)
        m.add(ellipsoid(_add(palm, (-side * 0.11 * hs, 0.03 * hs, 0.09 * hs)), (0.06 * hs, 0.09 * hs, 0.06 * hs)), hands)
        b.hands.append(_add(palm, tuple(c * 0.08 * hs for c in d)))
        b.wrists.append(wrist)
        b.elbows.append(elbow)
        b.shoulders.append(sh)
    b.right, b.left = b.hands
    b.forearm_dir = [_norm(tuple(b.wrists[i][k] - b.elbows[i][k] for k in range(3))) for i in range(2)]

    # The head: a cranium, a jaw, a brow ridge, a nose and ears
    hs = bd.head
    hy = neck_y + 0.5 * hs
    hz = lean(neck_y) + bd.hunch * 0.3 + 0.04
    b.head = (x, hy, hz)
    b.head_r = (0.56 * hs, 0.6 * hs, 0.54 * hs)
    b.hs = hs
    face_paint = head_paint or (skin(skin_c) + eyes(**eyes_kw))
    b.cranium = m.add(ellipsoid(b.head, b.head_r, nu=24, nv=14), face_paint, weight=face_weight)
    jw = bd.jaw
    b.jaw_c = (x, hy - 0.3 * hs, hz + 0.12 * hs)
    b.jaw_r = (0.45 * jw * hs, 0.32 * hs * (0.9 + 0.15 * jw), 0.42 * hs)
    m.add(ellipsoid(b.jaw_c, b.jaw_r, nu=20, nv=12), jaw_paint or (skin(skin_c) + mouth(**mouth_kw)), weight=face_weight)
    m.add(ellipsoid((x, hy + 0.13 * hs, hz + 0.39 * hs), (0.44 * hs, 0.085 * hs, 0.17 * hs), nu=16, nv=6),
          skin(skin_c) + brows(**brows_kw), weight=face_weight)
    nz = hz + 0.52 * hs
    ny = hy - 0.07 * hs
    sk = skin(skin_c)
    if nose == "round":
        m.add(ellipsoid((x, ny, nz), (0.1 * hs, 0.12 * hs, 0.11 * hs)), sk)
    elif nose == "big":
        m.add(ellipsoid((x, ny - 0.02, nz + 0.02), (0.14 * hs, 0.15 * hs, 0.14 * hs)), sk)
    elif nose == "long":
        m.add(tube([(x, ny + 0.12 * hs, nz - 0.06), (x, ny - 0.04, nz + 0.12 * hs)], [0.07 * hs, 0.06 * hs]), sk)
    elif nose == "hook":
        m.add(tube([(x, ny + 0.12 * hs, nz - 0.08), (x, ny + 0.02, nz + 0.25 * hs), (x, ny - 0.16 * hs, nz + 0.32 * hs)],
                   [0.08 * hs, 0.07 * hs, 0.03 * hs]), sk)
    elif nose == "broad":
        m.add(ellipsoid((x, ny - 0.03, nz - 0.01), (0.15 * hs, 0.11 * hs, 0.1 * hs)), sk)
        m.add(ellipsoid((x, ny + 0.08 * hs, nz - 0.03), (0.07 * hs, 0.1 * hs, 0.07 * hs)), sk)
    elif nose == "crooked":
        m.add(ellipsoid((x + 0.03, ny, nz), (0.12 * hs, 0.13 * hs, 0.12 * hs), rot=(0, 0, 18)), sk)
    if ears:
        for side in (1, -1):
            m.add(ellipsoid((x + side * 0.55 * hs, hy - 0.02, hz - 0.03), (0.07 * hs, 0.15 * hs, 0.11 * hs), rot=(0, side * 20, 0)), sk)
    b.top = hy + 0.6 * hs
    if hair_paint is not None and hair_style:
        hair_on(m, b, hair_paint, hair_style)
    return b


def hair_on(m, b, paint, style):
    hx, hy, hz = b.head
    rx, ry, rz = b.head_r
    hs = b.hs
    if style in ("short", "long", "ponytail", "bun", "slick"):
        m.add(ellipsoid((hx, hy + 0.04 * hs, hz - 0.05 * hs), (rx * 1.07, ry * 1.04, rz * 1.08), vrange=(0.48, 1.0), nu=22, nv=8), paint)
        # Sides and back, open at the face
        for ur in ((0.0, 0.32), (0.68, 1.0)):
            m.add(ellipsoid((hx, hy - 0.04 * hs, hz - 0.1 * hs), (rx * 1.05, ry * 0.96, rz * 1.0), urange=ur, vrange=(0.25, 0.7)), paint)
    if style == "short":
        m.add(ellipsoid((hx, hy + 0.4 * hs, hz + 0.3 * hs), (rx * 0.72, 0.18 * hs, 0.22 * hs), rot=(-12, 0, 0)), paint)
    elif style == "slick":
        m.add(ellipsoid((hx, hy + 0.42 * hs, hz + 0.18 * hs), (rx * 0.85, 0.16 * hs, 0.3 * hs), rot=(-18, 0, 0)), paint)
    elif style == "long":
        for ur in ((0.0, 0.36), (0.64, 1.0)):
            m.add(lathe([(hy - 1.0 * hs, 0.42 * hs), (hy - 0.5 * hs, 0.6 * hs), (hy, 0.64 * hs), (hy + 0.3 * hs, 0.58 * hs)],
                        (hx, 0, hz - 0.12 * hs), sz=0.85, urange=ur), paint)
        m.add(ellipsoid((hx, hy + 0.38 * hs, hz + 0.28 * hs), (rx * 0.8, 0.2 * hs, 0.24 * hs), rot=(-10, 0, 0)), paint)
    elif style == "ponytail":
        m.add(tube([(hx, hy + 0.3 * hs, hz - 0.5 * hs), (hx, hy - 0.1 * hs, hz - 0.85 * hs), (hx, hy - 0.75 * hs, hz - 0.75 * hs)],
                   [0.18 * hs, 0.15 * hs, 0.05 * hs]), paint)
        m.add(torus((hx, hy + 0.3 * hs, hz - 0.5 * hs), 0.15 * hs, 0.05 * hs, rot=(70, 0, 0)), color((0.75, 0.15, 0.2)))
    elif style == "bun":
        m.add(sphere((hx, hy + 0.6 * hs, hz - 0.32 * hs), 0.28 * hs), paint)
    elif style == "spiky":
        m.add(ellipsoid((hx, hy + 0.04 * hs, hz - 0.04 * hs), (rx * 1.06, ry * 1.04, rz * 1.06), vrange=(0.5, 1.0), nu=22, nv=8), paint)
        for k in range(8):
            a = (k - 3.5) * 0.3
            m.add(lathe([(0, 0.17 * hs), (0.42 * hs, 0.0)], (hx + math.sin(a) * 0.38 * hs, hy + 0.5 * hs, hz + 0.1 * hs - abs(a) * 0.12),
                        rot=(-30 + abs(a) * 12, 0, -a * 55), smooth=False, nu=8, nv=4), paint)
    elif style == "mohawk":
        m.add(blob((hx, hy + 0.62 * hs, hz - 0.05), (0.09 * hs, 0.28 * hs, 0.55 * hs), (0.5, 0.6)), paint)


def beard(m, b, paint, length=0.7, moustache=True, width=1.0):
    jx, jy, jz = b.jaw_c
    rx, ry, rz = b.jaw_r
    m.add(lathe([(jy - ry - length, 0.0), (jy - ry - length * 0.6, rx * 0.6 * width), (jy - ry * 0.4, rx * 1.02 * width),
                 (jy + ry * 0.35, rx * 1.05 * width)], (jx, 0, jz + 0.03), sz=1.0, urange=(0.2, 0.8)), paint)
    if moustache:
        for side in (1, -1):
            m.add(ellipsoid((jx + side * rx * 0.38, jy + ry * 0.3, jz + rz * 0.95), (rx * 0.42, ry * 0.18, rz * 0.2),
                            rot=(0, 0, side * 15)), paint)


def belt(m, b, paint=None, buckle=None, y=None, width=0.11):
    bd = b.bd
    y = y if y is not None else b.waist_y - 0.05
    r = bd.waist * (1 + 0.18 * bd.belly) * 1.02
    m.add(torus((b.x, y, b.lean(y) + bd.belly * 0.3), r, width, sz=(bd.depth + bd.belly * 0.1) * 1.05, nu=26), paint or leather((0.3, 0.18, 0.1)))
    z = b.lean(y) + bd.belly * 0.3 + r * (bd.depth + bd.belly * 0.1) * 1.05 + width * 0.6
    m.add(blob((b.x, y, z), (0.16, 0.13, 0.05), (0.3, 0.3)), buckle or metal((0.85, 0.7, 0.35)) + edges(0.3, 0.03))


def pauldrons(m, b, paint, size=1.0, rim=None, spikes=0):
    for i, side in enumerate((1, -1)):
        sx, sy, sz = b.shoulders[i]
        r = b.bd.arm * 1.9 * size
        m.add(ellipsoid((sx + side * 0.05, sy + 0.1, sz), (r, r * 0.85, r * 1.05), vrange=(0.35, 1.0)), paint)
        m.add(torus((sx + side * 0.05, sy + 0.1 - r * 0.38, sz), r * 0.95, 0.06, rot=(0, 0, side * 15), sz=1.1), rim or metal((0.75, 0.62, 0.3)))
        for k in range(spikes):
            a = (k - (spikes - 1) / 2) * 0.6
            m.add(lathe([(0, 0.1), (0.35, 0.0)], (sx + side * (0.15 + r * 0.4), sy + r * 0.6, sz + a * 0.3), rot=(0, 0, -side * 30),
                        smooth=False, nu=8, nv=3), metal((0.8, 0.8, 0.82)))


def bracers(m, b, paint, length=0.45, studs=None):
    for i in range(2):
        w, d = b.wrists[i], b.forearm_dir[i]
        a = _add(w, tuple(-c * length for c in d))
        m.add(tube([a, w], [b.bd.fore * 1.25, b.bd.fore * 1.0], nu=12, caps=False), paint)
        m.add(torus(w, b.bd.fore * 1.0, 0.035, rot=_aim(d)), studs or metal((0.7, 0.6, 0.35)))


def collar(m, b, paint, r=None, t=0.1):
    r = r or b.bd.neck * 1.5
    m.add(torus((b.x, b.neck_y - 0.05, b.lean(b.neck_y)), r, t, sz=0.9), paint)


def _aim(d):
    """The angles (for rot) that turn y towards the direction d"""
    dx, dy, dz = _norm(d)
    return (math.degrees(math.acos(max(-1, min(1, dy)))), math.degrees(math.atan2(dx, dz)), 0)


def top_hat(m, b, paint, band=None, height=0.9, tilt=0.0, brim=0.82):
    hx, hy, hz = b.head
    y = b.top - 0.22 * b.hs
    hs = b.hs
    m.add(torus((hx, y + 0.02, hz - 0.02), brim * hs * 0.85, 0.05 * hs, rot=(tilt, 0, 0)), paint)
    m.add(cylinder((hx, y - 0.02, hz - 0.02), brim * hs * 0.85, 0.06, rot=(tilt, 0, 0)), paint)
    m.add(lathe([(0, 0.0), (0.0, 0.47 * hs), (height * 0.5 * hs, 0.49 * hs), (height * hs, 0.53 * hs), (height * hs, 0.0)], (hx, y, hz - 0.02),
                rot=(tilt, 0, 0), smooth=False, nu=20), paint + bands(band, [(0.08, 0.25)]) if band else paint)


def cap(m, b, paint, peak_paint=None, back=False, height=0.4, badge=None):
    hx, hy, hz = b.head
    hs = b.hs
    m.add(ellipsoid((hx, hy + 0.1 * hs, hz - 0.02), (0.63 * hs, (height + 0.48) * hs, 0.61 * hs), vrange=(0.56, 1.0), nu=20, nv=6), paint)
    m.add(torus((hx, hy + 0.32 * hs, hz - 0.02), 0.6 * hs, 0.05 * hs, sz=1.0), peak_paint or paint)
    d = -1 if back else 1
    m.add(blob((hx, hy + 0.3 * hs, hz + d * 0.62 * hs), (0.42 * hs, 0.045, 0.3 * hs), (0.3, 0.8), rot=(d * 8, 0, 0)), peak_paint or paint)
    if badge:
        m.add(blob((hx, hy + 0.55 * hs, hz + 0.6 * hs), (0.12 * hs, 0.1 * hs, 0.03), (0.4, 0.4)), badge)


def pointy_hat(m, b, paint, brim=1.0, height=1.8, bend=0.35, band=None):
    hx, hy, hz = b.head
    hs = b.hs
    y = b.top - 0.3 * hs
    m.add(lathe([(0, 0.0), (0.03, 1.05 * brim * hs), (0.09, 0.98 * brim * hs), (0.06, 0.6 * hs), (0.1, 0.0)], (hx, y, hz), smooth=True, nu=22), paint)
    m.add(tube([(hx, y, hz), (hx, y + height * 0.5 * hs, hz - 0.05), (hx, y + height * 0.85 * hs, hz - bend), (hx + 0.1, y + height * hs, hz - bend * 1.9)],
               [0.55 * hs, 0.33 * hs, 0.14 * hs, 0.03], nu=14, caps=False), paint)
    if band:
        m.add(torus((hx, y + 0.12 * hs, hz), 0.55 * hs, 0.06 * hs), band)


def glasses(m, b, frame=(0.2, 0.2, 0.22), r=0.15, sun=False):
    hx, hy, hz = b.head
    hs = b.hs
    y = hy + 0.01 * hs
    lens = color((0.1, 0.1, 0.14)) + edges(0.2, 0.02) if sun else glass((0.55, 0.7, 0.8))
    for side in (1, -1):
        c = (hx + side * 0.19 * hs, y, hz + 0.56 * hs)
        m.add(cylinder(c, r * hs, 0.03, rot=(90, 0, 0)), lens)
        m.add(torus(c, r * hs, 0.022, rot=(90, 0, 0)), color(frame))
        m.add(tube([(hx + side * 0.34 * hs, y, hz + 0.52 * hs), (hx + side * 0.56 * hs, y + 0.02, hz + 0.05)], 0.022), color(frame))
    m.add(tube([(hx - 0.05 * hs, y + 0.02, hz + 0.58 * hs), (hx + 0.05 * hs, y + 0.02, hz + 0.58 * hs)], 0.02), color(frame))


def finish(m, name):
    m.fit_height(HEIGHTS[name])
    tris = m.write()
    print(f"models/{name}.obj  {tris} triangles")


def hero_model(name):
    return Model(name, size=1024, light=0.32, ao=1.1, detail=0.11)


def tunic(c, trim=None, folds=5, hem=(0.0, 0.06), seams=True):
    p = cloth(c, folds=folds)
    if trim:
        p = p + bands(trim, [hem])
    if seams:
        p = p + stitches(tuple(np.array(c) * 0.6), [hem[1] + 0.02, 0.97])
    return p


#
# The heroes
#


def make_allan():
    """A runner: lean, a red tracksuit with white stripes and a zip, a sweatband, wristbands, big running shoes, and
    the set face of someone who means to make it across"""
    m = hero_model("allan")
    red = (0.78, 0.14, 0.12)
    jacket = cloth(red) + bands(WHITE, [(0.86, 0.92)]) + rect((0.85, 0.85, 0.82), 0.495, 0.505, 0.1, 0.95) + stitches((0.5, 0.08, 0.07), [0.1, 0.84])
    b = person(m, ATHLETE, jacket, cloth(red) + stripes(WHITE, 2, 0.22, axis="u"),
               shoes=color(WHITE) + bands((0.8, 0.14, 0.12), [(0.3, 0.5)]) + stitches((0.6, 0.6, 0.6), [0.62]), sole=(0.25, 0.25, 0.27),
               arms=cloth(red) + stripes(WHITE, 2, 0.22, axis="u"), arm_pose=("ready", "down"), hair_paint=hair((0.42, 0.26, 0.13)), hair_style="spiky",
               eyes_kw=dict(iris=(0.3, 0.45, 0.22), lid=0.35, tilt=-0.1), mouth_kw=dict(kind="line"), brows_kw=dict(c=(0.35, 0.2, 0.1), tilt=0.45),
               cuffs=color(WHITE), nose="long")
    hx, hy, hz = b.head
    m.add(torus((hx, hy + 0.22 * b.hs, hz - 0.02), 0.58 * b.hs, 0.07, sz=1.0), knit(WHITE) + bands((0.8, 0.14, 0.12), [(0.4, 0.6)]))
    collar(m, b, cloth(red) + bands(WHITE, [(0.3, 0.7)]), t=0.08)
    for i in range(2):
        m.add(torus(b.wrists[i], b.bd.fore * 0.95, 0.07, rot=_aim(b.forearm_dir[i])), knit(WHITE))
    finish(m, "allan")


def make_ghosty():
    """A ghost in a torn sheet: a bell that rips into tatters at the hem, reaching arms, hollow glowing eyes and a
    wailing mouth"""
    m = Model("ghosty", size=1024, light=0.45, ao=0.8, detail=0.1)

    def sheet_paint(ctx):
        base = ghostly()(ctx)
        hollow = smoothstep(0.6, 0.0, ctx.p[..., 1]) * 0.25
        return base * (1 - hollow)[..., None] + hollow[..., None] * np.array([0.25, 0.3, 0.6]) * 0.5

    sheet = painted(sheet_paint)
    face_paint = sheet + eyes(v=0.76, spacing=0.22, size=0.13, glow=(0.55, 0.9, 1.0), lid=0.0, socket=0.6) + \
        mouth("wail", v=0.67, width=0.2, shadow=False)
    prof = [(0.6, 0.0), (0.58, 0.95), (0.9, 0.93), (1.5, 0.86), (2.2, 0.8), (2.9, 0.7), (3.35, 0.45), (3.55, 0.0)]
    m.add(lathe(prof, sz=0.9, nu=28, nv=22), face_paint, weight=2.0)
    for k in range(10):
        a = k * math.pi / 5
        length = 0.55 + 0.25 * ((k * 7) % 3)
        m.add(tube([(math.sin(a) * 0.9, 0.75, math.cos(a) * 0.82), (math.sin(a) * 1.0, 0.75 - length * 0.6, math.cos(a) * 0.92),
                    (math.sin(a + 0.15) * 1.05, 0.75 - length, math.cos(a + 0.15) * 0.95)], [0.24, 0.16, 0.03], nu=8, flat=0.5), sheet)
    for side in (1, -1):
        m.add(tube([(side * 0.72, 2.4, 0.1), (side * 1.2, 2.25, 0.45), (side * 1.45, 2.05, 0.85), (side * 1.55, 1.9, 1.05)],
                   [0.26, 0.2, 0.13, 0.04]), sheet)
        for f in range(3):
            m.add(tube([(side * 1.5, 1.95, 1.0), (side * (1.6 + f * 0.05), 1.85 - f * 0.08, 1.25)], [0.05, 0.015], nu=6), sheet)
    m.fit_height(HEIGHTS["ghosty"])
    m.write()
    print("models/ghosty.obj")



#
# A sculpted face with bones: eyeballs under lids that blink, brows that frown and lift, a jaw that opens on teeth.
# Its clips are layered over the clips of the body (rig.layered)
#


def eyeball(center, look=(0, -0.1, 1), iris=(0.9, 0.6, 0.08), sclera=(0.86, 0.8, 0.52), iris_size=40, pupil_size=13):
    """An eye: yellowed white with red at its edges, a big iris that is lighter at its middle, a pupil, a glint"""
    c = np.asarray(center, float)
    f = np.asarray(look, float)
    f = f / np.linalg.norm(f)
    g = f + np.array([-0.35, 0.4, 0.0])
    g = g / np.linalg.norm(g)
    ci, cp, cg = math.cos(math.radians(iris_size)), math.cos(math.radians(pupil_size)), math.cos(math.radians(9))

    def fn(ctx):
        d = ctx.p - c
        d = d / np.maximum(np.linalg.norm(d, axis=-1, keepdims=True), 1e-9)
        k = d @ f
        out = np.ones(ctx.shape + (3,)) * rgb(sclera)
        veins = smoothstep(0.3, -0.2, k) * 0.5 + (fbm(ctx.p, 30, 2, 5) > 0.62) * smoothstep(0.6, 0.2, k) * 0.5
        out = out * (1 - 0.35 * veins[..., None]) + veins[..., None] * np.array([0.25, 0.02, 0.0])
        t = np.clip((k - ci) / (1 - ci), 0, 1)
        iris_c = rgb(iris) * (0.55 + 0.75 * t)[..., None]
        streak = 0.85 + 0.3 * fbm(np.stack([np.arctan2(d[..., 1], d[..., 0]) * 6, k * 2, k * 0], -1), 1, 2, 3)
        out = np.where((k > ci)[..., None], iris_c * streak[..., None], out)
        ring = (k > ci) & (k < ci + 0.04)
        out = np.where(ring[..., None], rgb(iris) * 0.25, out)
        out = np.where((k > cp)[..., None], np.array([0.03, 0.02, 0.02]), out)
        out = np.where(((d @ g) > cg)[..., None], np.array([1.0, 1.0, 0.95]), out)
        return out
    return Paint(fn)


def wrinkles(hd, eyes_x=0.2, eye_y=0.08, eye_z=0.36, brow_y=0.24, furrows=3, depth=0.35):
    """The lines of a face that scowls: shadowed sockets, furrows across the forehead that dip at the middle, two
    creases between the brows, and folds from the nose to the corners of the mouth, all lit on their upper edge"""
    h = np.asarray(hd, float)

    def fn(ctx, base):
        p = ctx.p - h
        front = smoothstep(0.0, 0.5, ctx.n[..., 2])
        out = base
        for ex in (eyes_x, -eyes_x):
            d = np.linalg.norm(p - np.array([ex, eye_y, eye_z]), axis=-1)
            out = out * (1 - 0.5 * np.exp(-(d / 0.16) ** 2) * front)[..., None]
        dark = np.zeros(ctx.shape)
        light = np.zeros(ctx.shape)
        ax = np.abs(p[..., 0])
        for k in range(furrows):
            y0 = brow_y + 0.07 + k * 0.055
            line = p[..., 1] - (y0 + 0.07 * ax - 0.03 * ax * ax)
            span = smoothstep(0.32, 0.2, ax)
            dark = np.maximum(dark, smoothstep(0.012, 0.0, np.abs(line)) * span)
            light = np.maximum(light, smoothstep(0.02, 0.008, np.abs(line - 0.016)) * span * 0.6)
        for sx in (0.04, -0.04):
            crease = smoothstep(0.012, 0.0, np.abs(p[..., 0] - sx - 0.15 * (p[..., 1] - brow_y))) * smoothstep(brow_y - 0.04, brow_y + 0.02, p[..., 1]) * \
                smoothstep(brow_y + 0.17, brow_y + 0.1, p[..., 1])
            dark = np.maximum(dark, crease)
        for side in (1, -1):
            t = np.clip((eye_y - 0.1 - p[..., 1]) / 0.22, 0, 1)
            x = side * (0.17 + 0.13 * t)
            fold = smoothstep(0.016, 0.0, np.abs(p[..., 0] - x)) * (t > 0) * (t < 1)
            dark = np.maximum(dark, fold * 0.8)
        out = out * (1 - depth * dark * front)[..., None] + (light * front * 0.12)[..., None]
        return out
    return fn


def lash_line(at_bottom=True, c=(0.12, 0.08, 0.05), width=0.14):
    """A dark rim along the edge of an eyelid (the bottom of an upper lid, the top of a lower one)"""
    def fn(ctx, base):
        v = ctx.v if at_bottom else 1 - ctx.v
        return _over(base, rgb(c), smoothstep(width, width * 0.5, v))
    return fn


def face_pose(jaw=4, brow=10, lid=22, drop=0.0, lift=0.0):
    """The face: how far the jaw is open, how much the brows frown (degrees, inner ends down), how far the lids are
    closed (degrees), and how far the brows are dropped or lifted"""
    return {"jaw": (jaw, 0, 0), "brow_r": {"rot": (0, 0, brow), "pos": (0, lift - drop, 0)},
            "brow_l": {"rot": (0, 0, -brow), "pos": (0, lift - drop, 0)}, "lid_r": (lid, 0, 0), "lid_l": (lid, 0, 0)}


def face_clips():
    """What the face does in each clip of the body"""
    from rig import clip
    from anatomy import once
    calm, chew, blink = face_pose(), face_pose(jaw=11, brow=12, lid=26), face_pose(lid=88)
    sneer = face_pose(jaw=6, brow=18, lid=30, drop=0.015)
    scowl, roar = face_pose(jaw=0, brow=30, lid=42, drop=0.03), face_pose(jaw=36, brow=24, lid=4, lift=0.01)
    grimace = face_pose(jaw=3, brow=34, lid=58, drop=0.035)
    pant0, pant1 = face_pose(jaw=7, brow=18, lid=28), face_pose(jaw=13, brow=18, lid=28)
    return {
        "idle": clip(2.0, (0.0, calm), (0.5, chew), (0.8, calm), (1.3, sneer), (1.6, calm), (1.72, calm), (1.77, blink), (1.84, calm)),
        "walk": clip(1.0, (0.0, pant0), (0.25, pant1), (0.5, pant0), (0.75, pant1)),
        "cast": once(0.9, (0.0, calm), (0.3, scowl), (0.5, roar), (0.75, face_pose(jaw=20, brow=20, lid=12)), (0.9, calm)),
        "hook": once(0.75, (0.0, scowl), (0.1, roar), (0.4, face_pose(jaw=22, brow=22, lid=10)), (0.75, calm)),
        "heave": once(0.9, (0.0, calm), (0.2, grimace), (0.42, roar), (0.6, face_pose(jaw=24, brow=22, lid=10)), (0.9, calm)),
    }


def swamp_face(m, hd, sk, rig_, S=1.3):
    """The Butcher's head: a wide, low skull with drooping ears; big amber eyes deep under heavy, fleshy brows; fat
    cheeks; a broad snout; a wide frog's mouth with an overhanging upper lip, and an underbite whose tusks stand up
    over it; a dark mouth and a tongue behind the teeth. S scales it. Adds the bones of the face to the rig"""
    from anatomy import skin_paint
    h = np.asarray(hd, float)

    def P(x, y, z):
        return h + S * np.array([x, y, z], float)

    def R(*r):
        return tuple(S * v for v in r)
    E = 0.2                                         # How far apart the eyes are, from the middle
    eye_r = P(E, 0.07, 0.4)
    detail = m.detail
    m.detail = 0.03                                 # The face is looked at: smooth, not faceted
    rig_.bone("jaw", P(0, -0.1, -0.1), P(0, -0.28, 0.5), "head")
    rig_.bone("brow_r", P(0.06, 0.2, 0.46), P(0.36, 0.25, 0.36), "head")
    rig_.bone("lid_r", eye_r, eye_r + S * np.array([0, 0, 0.12]), "head")
    rig_.mirror()
    sp = skin_paint(sk, warts=0.4) + flush(h, S)
    dark_sk = tuple(c * 0.82 for c in sk)
    W = 4                                           # Texels: the face gets many
    wr = wrinkles(h, eyes_x=E * S, eye_y=0.07 * S, eye_z=0.38 * S, brow_y=0.21 * S)
    # The skull, with its wrinkles and sockets
    m.add(blob(P(0, 0.06, -0.06), R(0.5, 0.4, 0.48), (0.7, 0.75)).deform(lumps(0.01, 4, 3)), skin_paint(sk, warts=0.5) + flush(h, S) + wr, bones="head", weight=W)
    # Eyes, the lids over them, and the lower lids
    m.mirror(m.add(sphere(eye_r, 0.105 * S, nu=18, nv=12), eyeball(eye_r, look=(0.08, 0.05, 1), iris_size=42), bones="head", weight=W))
    m.mirror(m.add(ellipsoid(eye_r, R(0.122, 0.122, 0.122), vrange=(0.55, 1.0), nu=18, nv=6), sp + lash_line(True), bones="lid_r", weight=W))
    m.mirror(m.add(ellipsoid(eye_r + S * np.array([0, -0.004, 0.004]), R(0.126, 0.114, 0.124), vrange=(0.0, 0.3), nu=18, nv=5),
                   sp + lash_line(False, width=0.2), bones="head", weight=W))
    # The brows: heavy ridges of flesh from beside the nose out over the eyes, that the brow bones turn
    brow = skin_paint(sk, warts=0.2) + flush(h, S) + bristles((0.15, 0.16, 0.08))
    m.mirror(m.add(loft([P(0.05, 0.19, 0.47), P(0.16, 0.215, 0.47), P(0.28, 0.235, 0.42), P(0.38, 0.24, 0.32)],
                        [(0.05, 0.075, 2.2), (0.065, 0.085, 2.2), (0.06, 0.08, 2.2), (0.035, 0.05, 2.2)], facing=(0, 0.2, 1), nu=12, nv=12),
                   brow, bones="brow_r", weight=W))
    # Cheeks, low and round, and the snout with its nostrils
    m.mirror(m.add(ellipsoid(P(0.29, -0.06, 0.3), R(0.16, 0.12, 0.13)).deform(lumps(0.008, 6, 2)), sp + wr, bones="head", weight=W))
    m.add(blob(P(0, 0.0, 0.5), R(0.15, 0.1, 0.12), (0.7, 0.7)), sp, bones="head", weight=W)
    for side in (1, -1):
        m.add(torus(P(side * 0.07, -0.03, 0.6), 0.035 * S, 0.016 * S, rot=(75, 0, 0)), color(dark_sk), bones="head")
        m.add(ellipsoid(P(side * 0.07, -0.03, 0.598), R(0.03, 0.02, 0.012)), color((0.08, 0.06, 0.04)), bones="head")
    m.add(ellipsoid(P(0, 0.12, 0.47), R(0.06, 0.07, 0.06)), sp, bones="head", weight=W)
    # The mouth: a dark inside, the upper lip over it, fangs down from it
    m.add(ellipsoid(P(0, -0.17, 0.26), R(0.36, 0.08, 0.24)), color((0.22, 0.04, 0.05)), bones="head")
    lip_c = skin_paint((sk[0] * 0.92, sk[1] * 0.8, sk[2] * 0.75)) + flush(h, S, 0.05)
    m.add(loft([P(-0.37, -0.18, 0.22), P(-0.22, -0.14, 0.43), P(0, -0.128, 0.5), P(0.22, -0.14, 0.43), P(0.37, -0.18, 0.22)],
               [(0.025, 0.035, 2.2), (0.055, 0.075, 2.2), (0.065, 0.085, 2.2), (0.055, 0.075, 2.2), (0.025, 0.035, 2.2)], facing=(0, 0, 1), nu=14, nv=20),
          lip_c, bones="head", weight=W)
    tooth = color((0.86, 0.79, 0.55)) + bands((0.55, 0.45, 0.3), [(0.0, 0.25)])
    for x in (0.12, -0.24):
        m.add(horn(P(x, -0.15, 0.5 - abs(x) * 0.3), (0, -1, 0.1), 0.06 * S, 0.022 * S), tooth, bones="head")
    # The jaw, its lower lip, its teeth and tusks, a tongue: all turned by the jaw bone
    m.add(blob(P(0, -0.27, 0.12), R(0.47, 0.16, 0.4), (0.5, 0.6)).deform(push(P(0, -0.3, 0.5), 0.3 * S, (0, -0.01 * S, 0.04 * S))),
          skin_paint(sk, warts=0.4) + wr, bones="jaw", weight=W)
    m.add(loft([P(-0.35, -0.21, 0.24), P(-0.2, -0.19, 0.46), P(0, -0.185, 0.53), P(0.2, -0.19, 0.46), P(0.35, -0.21, 0.24)],
               [(0.025, 0.035, 2.2), (0.05, 0.07, 2.2), (0.058, 0.08, 2.2), (0.05, 0.07, 2.2), (0.025, 0.035, 2.2)], facing=(0, 0, 1), nu=14, nv=20),
          lip_c, bones="jaw", weight=W)
    m.add(ellipsoid(P(0, -0.21, 0.3), R(0.22, 0.035, 0.18)), color((0.58, 0.24, 0.24)), bones="jaw")
    for x, length, lean in ((-0.26, 0.07, -0.15), (-0.13, 0.055, 0.1), (-0.02, 0.06, -0.05), (0.08, 0.05, 0.12)):
        m.add(horn(P(x, -0.185, 0.53 - abs(x) * 0.35), (lean, 1, 0.05), length * S, 0.026 * S), tooth, bones="jaw")
    for x, length in ((0.21, 0.22), (-0.33, 0.14)):
        m.add(horn(P(x, -0.18, 0.5 - abs(x) * 0.25), (0.12 * np.sign(x), 1, 0.2), length * S, 0.05 * S, curl=(0.04 * np.sign(x), 0, 0.06)),
              tooth, bones="jaw")
    # Warts
    for p_ in ((0.32, -0.01, 0.4), (-0.34, -0.08, 0.36), (0.09, 0.05, 0.58), (-0.1, -0.32, 0.47), (0.4, 0.18, 0.24)):
        m.add(sphere(P(*p_), 0.025 * S, nu=6, nv=4), color(dark_sk), bones="jaw" if p_[1] < -0.25 else "head")
    # Drooping ears with a notch
    for side in (1, -1):
        m.add(loft([P(side * 0.44, 0.12, -0.05), P(side * 0.82, 0.05, -0.07), P(side * 1.12, -0.22, -0.07)],
                   [(0.19, 0.06, 2.4), (0.21, 0.06, 2.4), (0.06, 0.035, 2)], facing=(0, 1, 0), nu=10, nv=10),
              skin_paint(sk) + patch(dark_sk, 0.5, 0.62, 0.04, 0.04), bones="head")
    m.detail = detail


def ogre_face(m, hd, sk, rig_, style="brute", S=1.3):
    """An ogre's head with bones for its face: a low, sloping skull; small eyes deep under a heavy shelf of a brow; a
    broad nose; a massive underbite of a jaw with tusks. style: brute (a bony brow, beady eyes, a flat nose, big tusks),
    boar (a pig's snout, small red eyes, curved tusks, pointed ears), scarred (a scar over a milky eye, a broken nose,
    a chipped tusk, stubble) or warlord (old: deep wrinkles, jowls, warts, bushy grey brows, gaps in his teeth)"""
    from anatomy import skin_paint
    h = np.asarray(hd, float)

    def P(x, y, z):
        return h + S * np.array([x, y, z], float)

    def R(*r):
        return tuple(S * v for v in r)
    E = 0.19
    eye_r = P(E, 0.05, 0.372)
    eye_size = 0.078 if style != "warlord" else 0.08
    rig_.bone("jaw", P(0, -0.1, -0.1), P(0, -0.28, 0.5), "head")
    rig_.bone("brow_r", P(0.02, 0.18, 0.46), P(0.4, 0.2, 0.32), "head")
    rig_.bone("lid_r", eye_r, eye_r + S * np.array([0, 0, 0.1]), "head")
    rig_.mirror()
    detail = m.detail
    m.detail = 0.03
    warts = {"brute": 0.3, "boar": 0.4, "scarred": 0.2, "warlord": 0.9}[style]
    sp = skin_paint(sk, warts=warts) + flush(h, S, 0.12)
    dark_sk = tuple(c * 0.6 for c in sk)
    W = 4
    wr = wrinkles(h, eyes_x=E * S, eye_y=0.05 * S, eye_z=0.355 * S, brow_y=0.19 * S, furrows=4 if style == "warlord" else 2,
                  depth=0.5 if style == "warlord" else 0.35)
    scar = None
    if style == "scarred":
        def scar(ctx, base):
            p = (ctx.p - h) / S
            d = np.abs((p[..., 0] + 0.19) * 0.8 + (p[..., 1] - 0.05) * 0.6)
            a = smoothstep(0.018, 0.006, d) * (np.abs(p[..., 1] - 0.05) < 0.22) * (ctx.n[..., 2] > 0.2)
            return _over(base, (0.62, 0.42, 0.38), a)
    face_p = sp + wr + (scar if scar else (lambda ctx, b: b))
    # The skull: low and sloping back, the forehead pushed back over the brow
    m.add(blob(P(0, 0.02, -0.08), R(0.52, 0.37, 0.48), (0.65, 0.7)).deform(lumps(0.012, 4, 3), push(P(0, 0.3, 0.3), 0.3 * S, (0, -0.04 * S, -0.06 * S))),
          face_p, bones="head", weight=W)
    # Small eyes, deep: dirty whites, small irises, a tight lid with a dark crease, a pouch under each
    irises = {"brute": (1.0, 0.82, 0.15), "boar": (1.0, 0.3, 0.1), "scarred": (1.0, 0.78, 0.2), "warlord": (0.95, 0.9, 0.55)}
    for side in (1, -1):
        c = eye_r if side > 0 else eye_r * np.array([-1, 1, 1]) + np.array([2 * h[0], 0, 0])
        milky = style == "scarred" and side < 0
        iris = (0.7, 0.72, 0.7) if milky else irises[style]
        m.add(sphere(c, eye_size * S, nu=16, nv=12), eyeball(c, look=(0, -0.05, 1), iris=iris, sclera=(0.74, 0.66, 0.44), iris_size=40,
                                                            pupil_size=0 if milky else 11), bones="head", weight=W)
    crease = lash_line(True, c=dark_sk, width=0.1)
    m.mirror(m.add(ellipsoid(eye_r, R(eye_size * 1.12, eye_size * 1.12, eye_size * 1.12), vrange=(0.55, 1.0), nu=16, nv=6), sp + crease,
                   bones="lid_r", weight=W))
    bag = 1.25 if style == "warlord" else 1.0
    m.mirror(m.add(ellipsoid(eye_r + S * np.array([0, -0.045 * bag, 0.02]), R(0.1, 0.045 * bag, 0.07)), sp + wr, bones="head", weight=W))
    # The brow: two heavy wedges of bone that meet over the nose, a shelf the eyes sit in the shadow of
    if style == "warlord":
        brow = skin_paint(sk, warts=0.3) + bristles((0.72, 0.72, 0.68))
    elif style == "boar":
        brow = skin_paint(sk, warts=0.3) + bristles((0.12, 0.1, 0.07))
    else:
        brow = skin_paint(sk, warts=0.2) + wr + (scar if scar else (lambda ctx, b: b))
    m.mirror(m.add(loft([P(0.0, 0.16, 0.45), P(0.13, 0.18, 0.46), P(0.27, 0.19, 0.42), P(0.4, 0.16, 0.3)],
                        [(0.07, 0.11, 2.6), (0.09, 0.125, 2.6), (0.08, 0.11, 2.6), (0.05, 0.07, 2.4)], facing=(0, 0.35, 1), nu=12, nv=12).deform(lumps(0.008, 7, 9)),
                   brow, bones="brow_r", weight=W))
    # Cheeks: flat and hard
    m.mirror(m.add(blob(P(0.3, -0.07, 0.27), R(0.15, 0.1, 0.12), (0.7, 0.7)), sp + wr, bones="head", weight=W))
    # The nose
    nostril = color((0.07, 0.05, 0.04))
    if style == "boar":
        snout = P(0, -0.02, 0.48)
        m.add(loft([snout, snout + S * np.array([0, 0.03, 0.17])], [(0.15, 0.11, 2.6), (0.14, 0.1, 2.8)], facing=(0, 1, 0), nu=16, caps="flat"),
              sp + patch((0.5, 0.36, 0.3), 0.5, 0.95, 0.12, 0.08), bones="head", weight=W)
        for side in (1, -1):
            m.add(ellipsoid(snout + S * np.array([side * 0.055, 0.03, 0.172]), R(0.03, 0.04, 0.01)), nostril, bones="head")
    elif style == "scarred":
        m.add(blob(P(0.02, 0.0, 0.5), R(0.16, 0.1, 0.11), (0.7, 0.7), rot=(0, 0, 14)), sp + wr, bones="head", weight=W)
        m.add(ellipsoid(P(-0.01, 0.1, 0.47), R(0.06, 0.05, 0.05)), sp, bones="head", weight=W)
        for side in (1, -1):
            m.add(ellipsoid(P(side * 0.07 + 0.02, -0.05, 0.585), R(0.03, 0.02, 0.012)), nostril, bones="head")
    elif style == "warlord":
        m.add(blob(P(0, -0.03, 0.5), R(0.15, 0.13, 0.13), (0.85, 0.85)), sp + patch(dark_sk, 0.6, 0.6, 0.02, 0.02), bones="head", weight=W)
        for side in (1, -1):
            m.add(ellipsoid(P(side * 0.07, -0.09, 0.58), R(0.03, 0.02, 0.012)), nostril, bones="head")
    else:
        m.add(blob(P(0, -0.01, 0.48), R(0.2, 0.09, 0.11), (0.65, 0.7)), sp, bones="head", weight=W)
        for side in (1, -1):
            m.add(torus(P(side * 0.09, -0.04, 0.575), 0.036 * S, 0.016 * S, rot=(75, 0, 0)), color(tuple(c * 0.85 for c in sk)), bones="head")
            m.add(ellipsoid(P(side * 0.09, -0.04, 0.573), R(0.03, 0.02, 0.012)), nostril, bones="head")
    # The mouth: a dark inside, a thick upper lip over it, fangs down from it
    m.add(ellipsoid(P(0, -0.17, 0.26), R(0.36, 0.08, 0.24)), color((0.2, 0.04, 0.04)), bones="head")
    lip_c = skin_paint((sk[0] * 0.85, sk[1] * 0.75, sk[2] * 0.68)) + wr
    m.add(loft([P(-0.36, -0.18, 0.22), P(-0.21, -0.14, 0.42), P(0, -0.13, 0.49), P(0.21, -0.14, 0.42), P(0.36, -0.18, 0.22)],
               [(0.03, 0.04, 2.4), (0.06, 0.08, 2.4), (0.07, 0.09, 2.4), (0.06, 0.08, 2.4), (0.03, 0.04, 2.4)], facing=(0, 0, 1), nu=14, nv=20),
          lip_c, bones="head", weight=W)
    tooth = color((0.8, 0.72, 0.48)) + bands((0.5, 0.4, 0.26), [(0.0, 0.3)]) + stains((0.45, 0.35, 0.2), 0.15, 8)
    for x in (0.13, -0.15):
        m.add(horn(P(x, -0.15, 0.47 - abs(x) * 0.3), (0, -1, 0.1), 0.06 * S, 0.024 * S), tooth, bones="head")
    # The jaw: wide and jutting, its thick lower lip, its teeth and its tusks
    # Its top is flat, a floor of the mouth just under the lower lip, dark with the tongue on it, so the mouth opens
    # wide when the jaw drops rather than showing the skin of the jaw
    floor_y, lip_z = -0.2, 0.46

    def mouth_floor(p):
        out = p.copy()
        y = (p[..., 1] - h[1]) / S
        q = (p - h) / S
        inside = (q[..., 2] < lip_z) & ((q[..., 0] / 0.38) ** 2 + ((q[..., 2] - 0.12) / 0.36) ** 2 < 1)
        out[..., 1] = np.where(inside & (y > floor_y), h[1] + S * (floor_y + (y - floor_y) * 0.1), p[..., 1])
        return out

    def mouth_paint(ctx, base):
        q = (ctx.p - h) / S
        a = smoothstep(floor_y - 0.03, floor_y - 0.005, q[..., 1]) * smoothstep(lip_z + 0.02, lip_z - 0.04, q[..., 2]) * (ctx.n[..., 1] > 0.3)
        a = a * smoothstep(1.0, 0.8, (q[..., 0] / 0.38) ** 2 + ((q[..., 2] - 0.12) / 0.36) ** 2)
        back = smoothstep(0.45, 0.0, q[..., 2])
        inside = np.array([0.36, 0.08, 0.07]) * (1 - 0.7 * back)[..., None]
        tongue = smoothstep(0.17, 0.1, np.abs(q[..., 0]))[..., None] * np.array([0.22, 0.1, 0.09]) * (1 - back)[..., None]
        return _over(base, inside + tongue, a)
    m.add(blob(P(0, -0.28, 0.13), R(0.5, 0.18, 0.44), (0.5, 0.6)).deform(push(P(0, -0.33, 0.52), 0.32 * S, (0, -0.02 * S, 0.06 * S)), mouth_floor),
          skin_paint(sk, warts=warts) + wr + mouth_paint, bones="jaw", weight=W)
    if style == "warlord":
        for side in (1, -1):
            m.add(ellipsoid(P(side * 0.36, -0.33, 0.12), R(0.16, 0.14, 0.2)), skin_paint(sk, warts=0.9) + wr, bones="jaw", weight=W)
    m.add(loft([P(-0.36, -0.21, 0.23), P(-0.2, -0.19, 0.45), P(0, -0.185, 0.53), P(0.2, -0.19, 0.45), P(0.36, -0.21, 0.23)],
               [(0.03, 0.04, 2.4), (0.06, 0.08, 2.4), (0.07, 0.09, 2.4), (0.06, 0.08, 2.4), (0.03, 0.04, 2.4)], facing=(0, 0, 1), nu=14, nv=20),
          lip_c, bones="jaw", weight=W)
    m.add(ellipsoid(P(0, -0.21, 0.3), R(0.22, 0.035, 0.18)), color((0.5, 0.2, 0.2)), bones="jaw")
    gaps = style == "warlord"
    for k, (x, length, lean) in enumerate(((-0.24, 0.07, -0.15), (-0.12, 0.055, 0.1), (-0.02, 0.06, -0.05), (0.08, 0.05, 0.12))):
        if gaps and k % 2:
            continue
        m.add(horn(P(x, -0.185, 0.52 - abs(x) * 0.35), (lean, 1, 0.05), length * S, 0.026 * S), tooth, bones="jaw")
    tusks = {"brute": ((0.22, 0.3, 0.06), (-0.22, 0.28, 0.06)), "boar": ((0.24, 0.4, 0.055), (-0.24, 0.4, 0.055)),
             "scarred": ((0.22, 0.3, 0.06), (-0.22, 0.12, 0.06)), "warlord": ((0.22, 0.2, 0.05), (-0.25, 0.16, 0.05))}[style]
    for x, length, r in tusks:
        sx = np.sign(x)
        curl = (0.25 * sx, 0, 0.0) if style == "boar" else (0.05 * sx, 0, 0.06)
        m.add(horn(P(x, -0.18, 0.47 - abs(x) * 0.22), (0.1 * sx, 1, 0.2), length * S, r * S, curl=curl, tip=0.012 if length > 0.15 else 0.04),
              tooth, bones="jaw")
    # Warts
    n_warts = {"brute": 3, "boar": 4, "scarred": 2, "warlord": 9}[style]
    spots_at = ((0.32, -0.01, 0.38), (-0.33, -0.09, 0.34), (0.09, 0.06, 0.52), (-0.1, -0.33, 0.46), (0.4, 0.15, 0.22),
                (-0.25, 0.1, 0.38), (0.2, -0.36, 0.42), (-0.4, -0.2, 0.25), (0.05, 0.26, 0.38))
    for p_ in spots_at[:n_warts]:
        m.add(sphere(P(*p_), 0.026 * S, nu=6, nv=4), color(tuple(c * 0.8 for c in sk)), bones="jaw" if p_[1] < -0.25 else "head")
    # Ears
    for side in (1, -1):
        if style == "boar":
            m.add(loft([P(side * 0.4, 0.2, -0.08), P(side * 0.58, 0.42, -0.12), P(side * 0.66, 0.62, -0.18)],
                       [(0.12, 0.05, 2.4), (0.1, 0.045, 2.4), (0.02, 0.02, 2)], facing=(0, 0, 1), nu=10, nv=10), skin_paint(sk) + patch(dark_sk, 0.5, 0.5, 0.05, 0.08),
                  bones="head")
        else:
            m.add(loft([P(side * 0.43, 0.1, -0.05), P(side * 0.8, 0.03, -0.07), P(side * 1.08, -0.22, -0.07)],
                       [(0.18, 0.06, 2.4), (0.2, 0.06, 2.4), (0.06, 0.035, 2)], facing=(0, 1, 0), nu=10, nv=10),
                  skin_paint(sk) + patch(dark_sk, 0.5, 0.62, 0.04, 0.04), bones="head")
    m.detail = detail


def flush(hd, S=1.0, amount=0.18):
    """Warmer, redder skin on the snout, the cheeks and the lips, where the blood is near"""
    h = np.asarray(hd, float)

    def fn(ctx, base):
        p = (ctx.p - h) / S
        a = np.exp(-(np.linalg.norm(p - np.array([0, -0.02, 0.5]), axis=-1) / 0.16) ** 2)
        for side in (1, -1):
            a = np.maximum(a, 0.7 * np.exp(-(np.linalg.norm(p - np.array([side * 0.3, -0.08, 0.35]), axis=-1) / 0.13) ** 2))
        a = np.maximum(a, 0.6 * np.exp(-((p[..., 1] + 0.16) / 0.06) ** 2) * (p[..., 2] > 0.3))
        top = smoothstep(0.3, 0.9, ctx.n[..., 1]) * 0.1
        return base * (1 + top)[..., None] + (a * amount)[..., None] * np.array([0.9, 0.15, -0.1])
    return fn


def bristles(c):
    """Coarse hairs along a brow: fine streaks that run its length, thickest on its top"""
    def fn(ctx, base):
        hairs = fbm(np.stack([ctx.u * 90, ctx.v * 5, ctx.u * 0], -1), 1, 3, 17)
        top = smoothstep(-0.1, 0.6, ctx.n[..., 1])
        a = (0.55 + 0.45 * smoothstep(0.4, 0.65, hairs)) * top
        return _over(base, rgb(c) * (0.8 + 0.4 * hairs)[..., None], a * 0.9)
    return fn


def make_butcher(face="boar"):
    """The Butcher, a swamp brute of a butcher-monger: as wide as he is tall, olive skin, a wide frog mouth with a
    snaggletooth, drooping ears, a bloodied hide apron round his gut, a shell on one shoulder, a big fish on his belt,
    an iron meat hook for a right hand and a cleaver in his left. Simple, bold shapes, painted broadly. He is rigged,
    with clips for standing, walking, throwing his hook and heaving a car, written as models/butcher.glb too"""
    from anatomy import joints, make_rig, clips, skin_paint, brute_body, wrap_apron, L
    from rig import write_glb
    m = Model("butcher", size=1024, light=0.55, ao=1.5, detail=0.1)
    J = joints(hips=(0, 1.15, 0), spine=(0, 1.75, 0.15), chest=(0, 2.4, 0.25), neck=(0, 2.95, 0.55), head=(0, 3.2, 0.8),
               shoulder_r=(1.45, 2.75, 0.3), elbow_r=(1.95, 1.8, 0.45), wrist_r=(1.95, 0.95, 0.75), hand_end_r=(1.95, 0.55, 0.95),
               hip_r=(0.65, 1.1, 0.0), knee_r=(0.85, 0.65, 0.2), ankle_r=(0.9, 0.25, 0.05), toe_r=(0.95, 0.08, 0.7))
    m.rig = make_rig(J)
    sk = (0.42, 0.46, 0.3)
    skin_p = skin_paint(sk, warts=0.4)
    trousers = (0.3, 0.25, 0.2)
    brute_body(m, J, skin_p, cloth(trousers, folds=4), skin_p, gut=1.6, shoulders=1.1, forearm=1.15, legs_thick=1.15,
               chest_p=skin_p + bands(trousers, [(0.0, 0.2)]), right_hand=False)
    ogre_face(m, J["head"] + np.array([0, 0.08, 0.18]), sk, m.rig, face)
    # The apron: hide, light and stained, wrapped round the gut, on a strap round his neck, and a thick belt
    apron = leather((0.6, 0.48, 0.34)) + stains((0.45, 0.07, 0.05), 0.32, 1.0) + stains((0.32, 0.26, 0.16), 0.2, 2.2, 21) + edges(0.35, 0.12, dark=True)
    wrap_apron(m, J, apron, gut=1.6, low=0.8, wide=1.15)
    c = J["chest"]
    m.add(tube([c + [0.55, 0.4, 0.95], J["neck"] + [0, 0.15, 0.25], c + [-0.55, 0.4, 0.95]], 0.07, flat=0.45), leather((0.35, 0.24, 0.15)), bones="chest")
    m.add(torus(J["hips"] + [0, 0.25, 0.35], 1.25, 0.11, sz=0.85), leather((0.3, 0.2, 0.13)), bones="hips")
    m.add(blob(J["hips"] + [0, 0.25, 1.45], (0.24, 0.2, 0.07), (0.3, 0.3)), metal((0.55, 0.5, 0.42), 0.4) + edges(0.4, 0.04), bones="hips")
    # A big fish hanging from his belt
    top = np.array([-1.15, J["hips"][1] + 0.25, 0.65])
    m.add(loft([top, top + [0, -0.35, 0.05], top + [0, -0.95, 0.06], top + [0, -1.2, 0.02]], [(0.06, 0.05, 2), (0.13, 0.28, 2), (0.1, 0.22, 2), (0.03, 0.2, 1.2)],
               facing=(0, 0, 1), nu=12, nv=12), color((0.55, 0.64, 0.68)) + bands((0.38, 0.45, 0.5), [(0.6, 1.0)], axis="u") +
          patch((0.08, 0.08, 0.08), 0.5, 0.88, 0.025, 0.025), bones="hips")
    # A great shell on his left shoulder
    p = L(J["shoulder_r"]) + [-0.05, 0.32, 0]
    m.add(ellipsoid(p, (0.7, 0.45, 0.7), vrange=(0.4, 1.0)), color((0.74, 0.66, 0.52)) + stripes((0.52, 0.42, 0.32), 6, 0.3, axis="u") + edges(0.25, 0.1, dark=True),
          bones="chest")
    # The meat hook for a right hand, on a wooden socket bound with iron
    w, he = J["wrist_r"], J["hand_end_r"]
    m.add(loft([w + [0, 0.28, -0.05], w, w + (he - w) * 0.6], [(0.36, 0.36, 2.2), (0.32, 0.32, 2.2), (0.25, 0.25, 2.2)], nu=12, caps="flat"),
          wood((0.42, 0.28, 0.15)) + bands((0.42, 0.42, 0.45), [(0.1, 0.28), (0.72, 0.9)]), bones="fore_r")
    # The hook: as long as his arm, a heavy collar where it goes into the socket. A part of its own, which the game
    # leaves out while he has thrown it
    base = w + (he - w) * 0.6
    meat_hook(m, base, (0, -1, 0.25), (0, 0, 1), 0.95, hook_steel(), bones="fore_r", part="hook")
    # The cleaver in his left hand
    gp = L(J["hand_end_r"])
    m.add(loft([gp + [0, -0.25, 0], gp + [0, 0.45, 0.05]], [(0.08, 0.08, 2), (0.08, 0.08, 2)], nu=10), wood((0.35, 0.22, 0.12)), bones="hand_l")
    m.add(loft([gp + [0, 0.4, 0.05], gp + [0, 0.52, 0.42], gp + [0, 0.45, 0.8]], [dict(w=0.05, d=0.3, e=5), dict(w=0.045, d=0.38, e=5), dict(w=0.04, d=0.34, e=4)],
               facing=(0, 1, 0), nu=12, nv=10, caps="flat"), metal((0.55, 0.55, 0.58), 0.45) + edges(0.5, 0.07) + stains((0.42, 0.06, 0.05), 0.15, 3),
          bones="hand_l")
    m.add(tube([gp + (L(J["elbow_r"]) - gp) * 0.15, gp + (L(J["elbow_r"]) - gp) * 0.38], [0.36, 0.42], nu=12, caps=False),
          leather((0.36, 0.25, 0.15)) + stripes((0.25, 0.17, 0.1), 5, 0.2, axis="v", angle=30), bones="fore_l")
    from rig import layered, clip
    body, face = clips(), face_clips()
    m.clips = {name: layered(body[name], face[name]) for name in body}
    # For the portrait: the face of each clip on a body that stands still, so nothing swings in front of it
    still = body["idle"]["keys"][0][1]
    for name in body:
        stand = clip(body[name]["duration"], (0.0, still))
        stand["once"] = body[name].get("once", False)
        m.clips[name + "_face"] = layered(stand, face[name])
    finish(m, "butcher")
    print(write_glb(m, fps=30))


def meat_hook(m, origin, along, side, s, paint, bones=None, part=None):
    """A heavy meat hook: a collar, a thick shank along along, a broad belly that bends round towards side, and a point
    that comes back towards the collar with a barb on it, s long-ish units big. It lies in the plane of along and side,
    blade-like: wider in that plane than across it, so it reads as a hook from above"""
    o = np.asarray(origin, float)
    a = np.asarray(along, float)
    a /= np.linalg.norm(a)
    b = np.asarray(side, float)
    b = b - a * (b @ a)
    b /= np.linalg.norm(b)
    across = np.cross(a, b)
    P = lambda x, y: o + (a * x + b * y) * s
    # The shank, round the belly, and back up to the point
    path, secs = [P(0.2, 0), P(0.75, 0), P(1.3, 0)], [(0.17, 0.15, 2.5), (0.19, 0.16, 2.5), (0.22, 0.17, 2.5)]
    R, cy = 0.56, 0.56
    for k in range(1, 9):
        t = math.pi * k / 8
        path.append(P(1.3 + R * math.sin(t), cy - R * math.cos(t)))
        w = 0.22 + 0.06 * math.sin(t) - 0.06 * k / 8
        secs.append((w, 0.17 - 0.03 * k / 8, 2.3))
    path += [P(1.08, 1.14), P(0.82, 1.06), P(0.58, 0.92)]
    secs += [(0.17, 0.11, 1.8), (0.1, 0.06, 1.5), (0.015, 0.015, 1.4)]
    m.add(loft(path, [(w * s, d * s, e) for w, d, e in secs], facing=across, nu=14, nv=40, caps="round"),
          paint, bones=bones, part=part)
    # A heavy collar where the chain or the socket holds it, and a barb on the inside of the point
    m.add(loft([P(-0.05, 0), P(0.12, 0), P(0.28, 0)], [(0.24 * s, 0.22 * s, 3), (0.27 * s, 0.25 * s, 3), (0.2 * s, 0.19 * s, 3)],
               facing=across, nu=14, caps="flat"), metal((0.3, 0.3, 0.33), 0.3) + edges(0.4, 0.08), bones=bones, part=part)
    m.add(horn(P(0.98, 1.0), b * -0.7 + a * 0.5, 0.45 * s, 0.12 * s, curl=tuple(a * 0.2), e=1.6, tip=0.012 * s, facing=across),
          paint, bones=bones, part=part)


def hook_steel():
    return metal((0.36, 0.36, 0.4), 0.35) + edges(0.35, 0.06) + stains((0.32, 0.05, 0.04), 0.12, 2.0) + stains((0.33, 0.2, 0.1), 0.12, 4, 9)


def make_meat_hook():
    """The Butcher's hook as it flies: the same hook as on his arm, big. The chain is tied on at the origin, and it
    points along +z, bending round towards +x"""
    m = Model("meat_hook", size=512, ground_ao=False, light=0.35, ao=0.6, detail=0.08)
    m.add(chain_link_shape((0, 0, -0.45), upright=True), metal((0.3, 0.3, 0.33), 0.3) + edges(0.3, 0.1))
    meat_hook(m, (0, 0, 0), (0, 0, 1), (1, 0, 0), 2.1, hook_steel())
    tris = m.write()
    print(f"models/meat_hook.obj  {tris} triangles")


def chain_link_shape(c, upright=False, r=0.22, straight=0.2, t=0.12):
    """An oval link round c, along z: a ring r round, t thick, pulled out by straight at each end. Flat in the xz
    plane, or upright in the yz plane"""
    c = np.asarray(c, float)

    def stretch(p):
        z = p[..., 2] - c[2]
        out = p.copy()
        out[..., 2] += straight * np.clip(z / (0.5 * r), -1, 1)
        return out
    return torus(c, r, t, rot=(0, 0, 90) if upright else (0, 0, 0), nu=28, nv=10).deform(stretch)


def make_chain_link():
    """A link of the hook's chain: a heavy oval of dark iron, along z, flat in the xz plane. The game turns every other
    one a quarter round, so they hang in each other"""
    m = Model("chain_link", size=256, ground_ao=False, light=0.35, ao=0.0, detail=0.06)
    m.add(chain_link_shape((0, 0, 0)),
          metal((0.3, 0.29, 0.31), 0.45) + stains((0.4, 0.22, 0.1), 0.2, 6, 3))
    tris = m.write()
    print(f"models/chain_link.obj  {tris} triangles")


def frosty_clips():
    """Frosty: he sways and bobs on the spot, waddles when he walks, claps his mittens over his head and flings them
    out for his cold snap, and crouches and hugs himself as his igloo goes up round him. The face of each, and the
    swing of his pompom and his scarf"""
    from rig import clip, layered
    from anatomy import once
    stand = {"upper_r": (0, 0, 12), "upper_l": (0, 0, -12), "fore_r": (-20, 0, 0), "fore_l": (-20, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0, 0)}}
    sway_r = {"upper_r": (-6, 0, 16), "upper_l": (6, 0, -8), "fore_r": (-26, 0, 0), "fore_l": (-14, 0, 0), "spine": (0, 0, -4), "chest": (0, 0, -3),
              "head": (4, 0, 8), "hips": {"rot": (0, 0, -2), "pos": (0.03, 0.04, 0)}}
    sway_l = {"upper_r": (6, 0, 8), "upper_l": (-6, 0, -16), "fore_r": (-14, 0, 0), "fore_l": (-26, 0, 0), "spine": (0, 0, 4), "chest": (0, 0, 3),
              "head": (4, 0, -8), "hips": {"rot": (0, 0, 2), "pos": (-0.03, 0.0, 0)}}

    def step(s):
        return {"thigh_r": (-30 * s, 0, 0), "thigh_l": (30 * s, 0, 0), "shin_r": (10, 0, 0), "shin_l": (10, 0, 0),
                "upper_r": (28 * s, 0, 18), "upper_l": (-28 * s, 0, -18), "fore_r": (-30, 0, 0), "fore_l": (-30, 0, 0),
                "spine": (6, 0, 6 * s), "chest": (2, 0, 4 * s), "head": (-4, 0, -8 * s), "hips": {"rot": (0, -6 * s, 8 * s), "pos": (0.06 * s, -0.04, 0)}}

    def lift(s):
        return {"thigh_r": (-35 if s > 0 else 5, 0, 0), "thigh_l": (5 if s > 0 else -35, 0, 0), "shin_r": (30 if s > 0 else 5, 0, 0),
                "shin_l": (5 if s > 0 else 30, 0, 0), "upper_r": (0, 0, 22), "upper_l": (0, 0, -22), "fore_r": (-30, 0, 0), "fore_l": (-30, 0, 0),
                "spine": (6, 0, 0), "chest": (2, 0, 0), "head": (-4, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.1, 0)}}
    # Cold snap: up on his toes, mittens clapped over his head, then flung out wide as the cold goes out
    clap = {"upper_r": (-160, 0, -42), "upper_l": (-160, 0, 42), "fore_r": (-25, 0, -20), "fore_l": (-25, 0, 20), "spine": (-6, 0, 0), "chest": (-8, 0, 0),
            "head": (-14, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.14, 0)}}
    fling = {"upper_r": (-30, 0, 85), "upper_l": (-30, 0, -85), "fore_r": (-5, 0, 0), "fore_l": (-5, 0, 0), "spine": (8, 0, 0), "chest": (6, 0, 0),
             "head": (6, 0, 0), "thigh_r": (-10, 0, 8), "thigh_l": (-10, 0, -8), "shin_r": (14, 0, 0), "shin_l": (14, 0, 0),
             "hips": {"rot": (0, 0, 0), "pos": (0, -0.12, 0)}}
    # Igloo: down on his haunches, his arms round himself
    hug = {"upper_r": (-60, 0, -35), "upper_l": (-60, 0, 35), "fore_r": (-80, 0, 0), "fore_l": (-80, 0, 0), "spine": (14, 0, 0), "chest": (8, 0, 0),
           "head": (-10, 0, 0), "thigh_r": (-40, 0, 0), "thigh_l": (-40, 0, 0), "shin_r": (50, 0, 0), "shin_l": (50, 0, 0),
           "hips": {"rot": (8, 0, 0), "pos": (0, -0.25, 0)}}
    body = {
        "idle": clip(2.4, (0.0, stand), (0.6, sway_r), (1.2, stand), (1.8, sway_l)),
        "walk": clip(0.8, (0.0, step(1)), (0.2, lift(-1)), (0.4, step(-1)), (0.6, lift(1))),
        "freeze": once(0.8, (0.0, stand), (0.18, clap), (0.26, clap), (0.4, fling), (0.62, fling), (0.8, stand)),
        "igloo": once(0.5, (0.0, stand), (0.25, hug), (0.5, hug)),
    }
    calm, blink = face_pose(jaw=0, brow=0, lid=-25), face_pose(jaw=0, brow=0, lid=100)
    happy = face_pose(jaw=8, brow=-12, lid=-20, lift=0.03)
    puff, blow = face_pose(jaw=0, brow=10, lid=40), face_pose(jaw=18, brow=-6, lid=-25, lift=0.03)
    cosy = face_pose(jaw=4, brow=-10, lid=90, lift=0.02)
    face = {
        "idle": clip(2.4, (0.0, calm), (0.9, calm), (0.95, blink), (1.02, calm), (1.6, happy), (2.0, happy), (2.3, calm)),
        "walk": clip(0.8, (0.0, happy), (0.4, face_pose(jaw=5, brow=-8, lid=-20, lift=0.02))),
        "freeze": once(0.8, (0.0, calm), (0.18, puff), (0.4, blow), (0.62, blow), (0.8, happy)),
        "igloo": once(0.5, (0.0, calm), (0.25, cosy), (0.5, cosy)),
    }
    # The pompom and the scarf lag behind him
    flap = {
        "idle": clip(2.4, (0.0, {"pompom": (0, 0, 0), "scarf_1": (0, 0, 0)}), (0.7, {"pompom": (0, 0, -12), "scarf_1": (4, 0, -6), "scarf_2": (0, 0, -8)}),
                     (1.3, {"pompom": (0, 0, 0), "scarf_1": (0, 0, 0)}), (1.9, {"pompom": (0, 0, 12), "scarf_1": (4, 0, 6), "scarf_2": (0, 0, 8)})),
        "walk": clip(0.8, (0.0, {"pompom": (10, 0, -16), "scarf_1": (-10, 0, -10), "scarf_2": (-14, 0, -6)}), (0.2, {"pompom": (-12, 0, 0), "scarf_1": (-20, 0, 0), "scarf_2": (-8, 0, 0)}),
                     (0.4, {"pompom": (10, 0, 16), "scarf_1": (-10, 0, 10), "scarf_2": (-14, 0, 6)}), (0.6, {"pompom": (-12, 0, 0), "scarf_1": (-20, 0, 0), "scarf_2": (-8, 0, 0)})),
        "freeze": once(0.8, (0.0, {"pompom": (0, 0, 0)}), (0.18, {"pompom": (20, 0, 0), "scarf_1": (10, 0, 0)}), (0.4, {"pompom": (-25, 0, 0), "scarf_1": (-30, 0, 0), "scarf_2": (-20, 0, 0)}),
                       (0.8, {"pompom": (0, 0, 0), "scarf_1": (0, 0, 0), "scarf_2": (0, 0, 0)})),
        "igloo": once(0.5, (0.0, {"pompom": (0, 0, 0)}), (0.25, {"pompom": (-20, 0, 0), "scarf_1": (15, 0, 0)}), (0.5, {"pompom": (-10, 0, 0), "scarf_1": (10, 0, 0)})),
    }
    clips_ = {name: layered(body[name], face[name], flap[name]) for name in body}
    for name in body:
        still = clip(body[name]["duration"], (0.0, stand))
        still["once"] = body[name].get("once", False)
        clips_[name + "_face"] = layered(still, face[name], flap["idle"])
    return clips_


def make_frosty():
    """Frosty, a little snow golem: a big round belly of packed snow on two stubby snowball feet, a big round head with
    shiny coal eyes, rosy cheeks, a short carrot nose, twig brows and a smile of coal pebbles, chunky snow arms in green
    mittens, a red bobble hat with a pompom that bounces, a long knitted scarf whose tail swings, and shards of blue ice
    growing out of his back, where his cold comes from. Rigged, with clips for standing, waddling, his cold snap and
    his igloo, written as models/frosty.glb too"""
    from anatomy import joints, make_rig
    from rig import write_glb
    m = Model("frosty", size=1024, light=0.5, ao=1.2, detail=0.07)
    J = joints(hips=(0, 1.0, 0), spine=(0, 1.45, 0.02), chest=(0, 1.95, 0.02), neck=(0, 2.25, 0.02), head=(0, 2.4, 0.03),
               shoulder_r=(0.86, 1.85, 0.05), elbow_r=(1.25, 1.5, 0.18), wrist_r=(1.42, 1.12, 0.34), hand_end_r=(1.48, 0.88, 0.44),
               hip_r=(0.42, 0.62, 0.0), knee_r=(0.45, 0.42, 0.05), ankle_r=(0.46, 0.22, 0.04), toe_r=(0.48, 0.06, 0.5))
    m.rig = make_rig(J)
    s_ = snow()
    lump = lumps(0.025, 2.0, 11)
    # The belly, the feet and the legs that hide in it
    m.add(blob((0, 1.28, 0), (1.05, 0.98, 1.0), (0.85, 0.88), nu=28, nv=16).deform(lump), s_, bones=["hips", "spine", "chest"])
    for side in (1, -1):
        hp = J["hip_r"] * np.array([side, 1, 1])
        m.add(loft([hp + [0, 0.15, 0], hp + [0, -0.3, 0.02]], [(0.26, 0.26, 2.2), (0.24, 0.24, 2.2)], nu=12), s_, bones=["thigh_" + ("r" if side > 0 else "l"), "shin_" + ("r" if side > 0 else "l")])
    foot = m.add(blob(J["ankle_r"] + [0, -0.04, 0.16], (0.3, 0.2, 0.38), (0.75, 0.75)).deform(lumps(0.02, 3, 4)), s_, bones=["foot_r"])
    m.mirror(foot)
    # Coal buttons down his belly
    coal = color((0.09, 0.09, 0.11)) + edges(0.2, 0.3)
    for y in (1.75, 1.4, 1.05):
        z = math.sqrt(max(1.0 - ((y - 1.28) / 0.98) ** 2, 0)) * 1.0
        m.add(sphere((0, y, z - 0.02), 0.085, nu=10, nv=8), coal, bones="spine" if y > 1.3 else "hips")
    # Arms: chunky snow, in green mittens with a thumb
    sh, e, w = J["shoulder_r"], J["elbow_r"], J["wrist_r"]
    arm = m.add(loft([sh + [-0.15, 0.05, 0], sh, e, w], [(0.26, 0.26, 2.2), (0.25, 0.25, 2.2), (0.22, 0.22, 2.2), (0.19, 0.19, 2.2)], nu=14, nv=18).deform(lumps(0.02, 3, 8)),
                s_, bones=["upper_r", "fore_r"])
    m.mirror(arm)
    mitt = knit((0.14, 0.5, 0.24)) + stripes((0.92, 0.92, 0.88), 2, 0.25, axis="v")
    d = (J["hand_end_r"] - w) / np.linalg.norm(J["hand_end_r"] - w)
    palm = w + d * 0.18
    m.mirror(m.add(blob(palm, (0.22, 0.26, 0.22), (0.7, 0.7)), mitt, bones=["hand_r"]))
    m.mirror(m.add(blob(palm + [-0.17, 0.08, 0.12], (0.08, 0.12, 0.08), (0.75, 0.75), rot=(0, 0, -25)), mitt, bones=["hand_r"]))
    m.mirror(m.add(torus(w + d * 0.02, 0.2, 0.06, rot=(0, 0, 20)), knit((0.92, 0.92, 0.88)), bones=["hand_r", "fore_r"]))
    # Shards of blue ice out of his upper back and shoulder
    ice = color((0.62, 0.86, 1.0)) + edges(0.5, 0.15) + stripes((0.85, 0.97, 1.0), 3, 0.2, axis="v")
    for base, d_, l_ in (((0.3, 2.0, -0.75), (0.3, 0.8, -0.5), 0.75), ((-0.1, 2.05, -0.85), (-0.15, 0.9, -0.4), 0.95), ((-0.5, 1.85, -0.65), (-0.6, 0.7, -0.4), 0.6),
                         ((0.72, 2.0, -0.2), (0.7, 0.8, -0.2), 0.45)):
        b_ = np.array(base, float)
        for k, (off, scale) in enumerate((((0, 0, 0), 1.0), ((0.12, -0.08, 0.05), 0.6), ((-0.1, -0.1, 0.06), 0.5))):
            m.add(horn(b_ + off, np.array(d_) + np.array(off) * 3, l_ * scale, 0.17 * scale, curl=(0, 0, 0), e=1.3, segments=3, tip=0.015), ice, bones="chest")
    # The head: big and round, with its face
    hd = np.array([0, 2.95, 0.06])
    R_ = 0.82
    rig_ = m.rig
    eye = hd + np.array([0.26, 0.08, 0.7])
    rig_.bone("jaw", hd + [0, -0.15, 0.2], hd + [0, -0.45, 0.7], "head")
    rig_.bone("brow_r", hd + [0.14, 0.3, 0.72], hd + [0.42, 0.32, 0.6], "head")
    rig_.bone("lid_r", eye, eye + [0, 0, 0.12], "head")
    rig_.mirror()

    def cheeks(ctx, base):
        out = base
        for sx in (1, -1):
            dd = np.linalg.norm(ctx.p - (hd + np.array([sx * 0.45, -0.18, 0.6])), axis=-1)
            out = _over(out, (1.0, 0.62, 0.66), np.exp(-(dd / 0.16) ** 2) * 0.8)
        return out
    detail = m.detail
    m.detail = 0.03
    m.add(sphere(hd, R_, nu=28, nv=18).deform(lumps(0.015, 2.5, 21)), s_ + cheeks, bones="head", weight=3)
    # Eyes: big, round and shiny black, with a glint; snow lids that blink
    for sx in (1, -1):
        c = eye * np.array([sx, 1, 1])
        m.add(ellipsoid(c, (0.145, 0.185, 0.08), nu=18, nv=12), eyeball(c, look=(0, 0.05, 1), iris=(0.06, 0.06, 0.1), sclera=(0.08, 0.08, 0.12),
                                                                  iris_size=70, pupil_size=0), bones="head", weight=3)
        m.add(sphere(c + np.array([-0.05, 0.08, 0.065]), 0.035, nu=8, nv=6), color((1, 1, 1)), bones="head")
        m.add(sphere(c + np.array([0.04, -0.06, 0.07]), 0.016, nu=6, nv=4), color((1, 1, 1)), bones="head")
    lid = m.add(ellipsoid(eye, (0.16, 0.2, 0.1), vrange=(0.78, 1.0), nu=18, nv=6), s_, bones="lid_r", weight=3)
    m.mirror(lid)
    # Twig brows
    twig = wood((0.4, 0.26, 0.14), 4) + edges(0.3, 0.1, dark=True)
    m.mirror(m.add(loft([hd + [0.13, 0.31, 0.73], hd + [0.27, 0.34, 0.69], hd + [0.4, 0.31, 0.6]], [(0.025, 0.025, 2), (0.03, 0.03, 2), (0.02, 0.02, 2)], nu=8, nv=10),
                   twig, bones="brow_r"))
    # A short carrot nose
    m.add(horn(hd + [0, -0.04, 0.8], (0.05, -0.08, 1), 0.3, 0.085, curl=(0.0, -0.06, 0), tip=0.02, facing=(0, 1, 0)),
          color((0.98, 0.5, 0.1)) + stripes((0.78, 0.36, 0.06), 5, 0.12, axis="v"), bones="head")
    # The mouth: dark inside, a chin of snow that drops open, with a smile of coal pebbles on it
    m.add(ellipsoid(hd + [0, -0.33, 0.68], (0.15, 0.06, 0.1)), color((0.16, 0.08, 0.1)), bones="head")
    m.add(blob(hd + [0, -0.37, 0.57], (0.25, 0.1, 0.23), (0.8, 0.8)), s_ + cheeks, bones="jaw", weight=3)
    for k in range(5):
        t = (k - 2) / 2
        y = -0.25 + 0.07 * t * t
        p_ = hd + np.array([t * 0.2, y, math.sqrt(R_ * R_ - y * y - (t * 0.2) ** 2) + 0.01])
        m.add(sphere(p_, 0.04, nu=8, nv=6), coal, bones="head")
    m.detail = detail
    # A red bobble hat with a white band, and a pompom on a bone of its own
    hat = knit((0.82, 0.14, 0.14)) + stripes((0.95, 0.93, 0.9), 2, 0.3, axis="v")
    m.add(ellipsoid(hd + [0, 0.28, -0.05], (0.75, 0.62, 0.74), vrange=(0.5, 1.0), rot=(-10, 0, 0), nu=24, nv=10), hat, bones="head")
    m.add(torus(hd + [0, 0.33, -0.03], 0.75, 0.11, rot=(-10, 0, 0), nu=28), knit((0.95, 0.93, 0.9)), bones="head")
    top = hd + np.array([0, 0.98, -0.18])
    rig_.bone("pompom", top + [0, -0.2, 0], top + [0, 0.2, 0], "head")
    m.add(sphere(top + [0, 0.08, 0], 0.22, nu=14, nv=10).deform(lumps(0.03, 8, 2)), fur((0.95, 0.94, 0.9)), bones="pompom")
    # The scarf: round his neck, and a tail on two bones that hangs over his front and swings
    scarf = knit((0.12, 0.45, 0.22)) + stripes((0.82, 0.14, 0.14), 6, 0.4, axis="u")
    m.add(torus(np.array([0, 2.22, 0.02]), 0.72, 0.17, sz=0.95, nu=30), scarf, bones=["chest", "head"])
    s0 = np.array([0.35, 2.15, 0.72])
    s1 = s0 + np.array([0.08, -0.5, 0.2])
    s2 = s1 + np.array([0.02, -0.45, 0.05])
    rig_.bone("scarf_1", s0, s1, "chest")
    rig_.bone("scarf_2", s1, s2, "scarf_1")
    m.add(loft([s0, s1, s2], [(0.17, 0.05, 3), (0.16, 0.05, 3), (0.15, 0.05, 3)], facing=(0, 0, 1), nu=12, nv=14, caps="flat"),
          scarf + stripes((0.95, 0.93, 0.9), 1, 0.06, axis="v"), bones=["scarf_1", "scarf_2"])
    for k in range(4):
        m.add(tube([s2 + [(k - 1.5) * 0.08, 0, 0], s2 + [(k - 1.5) * 0.09, -0.14, 0.01]], 0.022), knit((0.12, 0.45, 0.22)), bones="scarf_2")
    m.clips = frosty_clips()
    finish(m, "frosty")
    print(write_glb(m, fps=30))
    return m


def make_igloo():
    """Frosty's igloo: a dome of packed snow blocks, rows of them laid round and staggered, a low tunnel out of it with
    a dark doorway towards +x (the game turns it to the side he is going), and icicles along its edge. As wide as
    IglooRadius (2.4), and as tall as he is crouched"""
    m = Model("igloo", size=1024, ground_ao=True, light=0.45, ao=1.0, detail=0.08)
    R, H = 2.45, 2.9

    def blocks(ctx):
        base = snow()(ctx)
        p = ctx.p
        el = np.clip(p[..., 1] / H, 0, 1)
        row = el * 6.5
        r_i = np.floor(row)
        az = (np.arctan2(p[..., 2], p[..., 0]) / (2 * np.pi) + 0.5) * (14 - r_i * 1.5) + r_i * 0.5
        seam_h = smoothstep(0.08, 0.0, np.abs(row - np.round(row)))
        seam_v = smoothstep(0.06, 0.0, np.abs(az - np.round(az)))
        groove = np.maximum(seam_h, seam_v * (el < 0.93))
        out = base * (1 - 0.28 * groove)[..., None] + groove[..., None] * np.array([-0.06, -0.02, 0.04])
        face = 0.94 + 0.08 * fbm(np.stack([np.round(row), np.round(az), np.zeros_like(az)], -1), 3, 1, 9)
        return out * face[..., None]
    paint = Paint(blocks)
    m.add(ellipsoid((0, 0, 0), (R, H, R), vrange=(0.5, 1.0), nu=40, nv=16).deform(lumps(0.03, 1.5, 4)), paint, weight=2)
    # The tunnel to the door: half a tube of blocks, with a dark doorway at its end
    m.add(loft([(R * 0.7, 0, 0), (R + 0.75, 0, 0)], [dict(w=0.85, d=1.35, e=2.2), dict(w=0.82, d=1.3, e=2.2)], facing=(0, 1, 0), nu=24, caps=None,
               urange=(0.25, 0.75)).deform(lumps(0.03, 2, 6)), paint)
    m.add(loft([(R + 0.7, 0, 0), (R + 0.76, 0, 0)], [dict(w=0.6, d=1.0, e=2.2), dict(w=0.6, d=1.0, e=2.2)], facing=(0, 1, 0), nu=20, caps="flat", urange=(0.25, 0.75)),
          color((0.12, 0.16, 0.26)) + patch((0.3, 0.4, 0.6), 0.5, 0.3, 0.2, 0.3))
    # Icicles hanging from the edge of the tunnel and round the bottom of the dome
    ice = color((0.7, 0.9, 1.0)) + edges(0.5, 0.2)
    for k in range(5):
        z = (k - 2) * 0.32
        top = (R + 0.78, math.sqrt(max(1 - (z / 0.85) ** 2, 0)) * 1.3, z)
        m.add(horn(top, (0, -1, 0), 0.25 + 0.12 * (k % 2), 0.05, curl=(0, 0, 0), tip=0.005), ice)
    for k in range(16):
        a = k / 16 * 2 * math.pi + 0.2
        if math.cos(a) > 0.8:
            continue
        y = 0.9 + 0.25 * (k % 3)
        rr = R * math.sqrt(max(1 - (y / H) ** 2, 0)) + 0.02
        m.add(horn((rr * math.cos(a), y, rr * math.sin(a)), (0, -1, 0), 0.18 + 0.08 * (k % 2), 0.04, curl=(0, 0, 0), tip=0.005), ice)
    tris = m.write()
    print(f"models/igloo.obj  {tris} triangles")


def make_bjorn():
    """A viking shieldbearer: huge, in mail under a fur mantle, a horned helmet with a nose guard, a long braided red
    beard with iron rings, bracers, and a round shield with an iron rim and boss"""
    m = hero_model("bjorn")
    bd = replace(BRUTE, hunch=0.2, belly=0.3, head=0.86)
    mail = scales((0.55, 0.56, 0.6), 0.1)
    tunic_p = cloth((0.3, 0.38, 0.24)) + scales((0.55, 0.56, 0.6), 0.1) + bands((0.32, 0.4, 0.25), [(0.0, 0.12)]) + bands((0.7, 0.55, 0.22), [(0.12, 0.15)])
    b = person(m, bd, tunic_p, cloth((0.38, 0.28, 0.18)) + stripes((0.28, 0.2, 0.12), 7, 0.4, axis="v", angle=35),
               shoes=fur((0.42, 0.3, 0.18)), arms=skin(SKIN_RUDDY) + bands((0.3, 0.38, 0.24), [(0.75, 1.0)]), skin_c=SKIN_RUDDY,
               eyes_kw=dict(iris=(0.25, 0.45, 0.65), lid=0.4, size=0.07, socket=0.5), mouth_kw=dict(kind="grim"),
               brows_kw=dict(c=(0.75, 0.35, 0.1), tilt=0.6, thick=1.0), nose="broad", arm_pose=("ready", "ready"), cuffs=fur((0.5, 0.38, 0.24)))
    beard_c = hair((0.82, 0.38, 0.1))
    beard(m, b, beard_c, length=0.9, width=1.1)
    jx, jy, jz = b.jaw_c
    for side in (1, -1):
        m.add(tube([(jx + side * 0.17, jy - 0.9, jz + 0.35), (jx + side * 0.2, jy - 1.35, jz + 0.38)], [0.1, 0.06]), beard_c)
        m.add(torus((jx + side * 0.17, jy - 0.95, jz + 0.35), 0.1, 0.04), metal((0.6, 0.6, 0.62)))
    # A fur mantle round the shoulders and a cloak behind
    m.add(lathe([(b.sh_y - 0.3, bd.shoulder * 1.05), (b.sh_y, bd.shoulder * 1.15), (b.sh_y + 0.22, bd.shoulder * 0.8), (b.neck_y + 0.1, bd.neck * 1.5)],
                (0, 0, b.lean(b.sh_y)), sz=0.85, nu=24), fur((0.55, 0.42, 0.28)))
    m.add(lathe([(0.6, bd.hip * 1.6), (b.hip_y, bd.waist * 1.45), (b.sh_y - 0.2, bd.shoulder * 1.05)], (0, 0, b.lean(b.waist_y) - 0.05), sz=0.9,
                urange=(0.0, 0.25)), cloth((0.6, 0.15, 0.1), folds=6) + bands((0.75, 0.6, 0.25), [(0.0, 0.05)]))
    m.add(lathe([(0.6, bd.hip * 1.6), (b.hip_y, bd.waist * 1.45), (b.sh_y - 0.2, bd.shoulder * 1.05)], (0, 0, b.lean(b.waist_y) - 0.05), sz=0.9,
                urange=(0.75, 1.0)), cloth((0.6, 0.15, 0.1), folds=6) + bands((0.75, 0.6, 0.25), [(0.0, 0.05)]))
    belt(m, b, leather((0.3, 0.18, 0.1)) + stitches((0.6, 0.45, 0.25), [0.3, 0.7]), buckle=metal((0.8, 0.65, 0.3)))
    bracers(m, b, leather((0.35, 0.22, 0.12)) + stitches((0.6, 0.45, 0.25), [0.2, 0.8]))
    # The helmet with its horns and nose guard
    hx, hy, hz = b.head
    hs = b.hs
    helm = metal((0.58, 0.58, 0.62), 0.45) + bands((0.72, 0.56, 0.25), [(0.0, 0.14)]) + spots((0.8, 0.8, 0.82), 0.025, 0.25, 4)
    m.add(ellipsoid((hx, hy + 0.08 * hs, hz - 0.02), (0.64 * hs, 0.68 * hs, 0.62 * hs), vrange=(0.5, 1.0), nu=22, nv=8), helm)
    m.add(blob((hx, hy - 0.02, hz + 0.6 * hs), (0.06 * hs, 0.3 * hs, 0.06 * hs), (0.4, 0.4)), metal((0.6, 0.6, 0.64)))
    m.add(blob((hx, hy + 0.5 * hs, hz), (0.06 * hs, 0.18 * hs, 0.6 * hs), (0.4, 0.5)), metal((0.65, 0.55, 0.3)))
    for side in (1, -1):
        m.add(tube([(hx + side * 0.55 * hs, hy + 0.32 * hs, hz), (hx + side * 0.98 * hs, hy + 0.52 * hs, hz + 0.08), (hx + side * 1.12 * hs, hy + 1.0 * hs, hz + 0.15)],
                   [0.17 * hs, 0.11 * hs, 0.02]), color((0.9, 0.85, 0.7)) + stripes((0.7, 0.65, 0.52), 6, 0.2, axis="v") + bands((0.55, 0.5, 0.42), [(0.0, 0.14)]))
    # The shield on his left arm, facing forward
    lx, ly, lz = b.left
    c = (lx - 0.25, ly + 0.4, lz + 0.4)
    m.add(cylinder(c, 0.92, 0.14, rot=(90, 0, 0)),
          wood((0.6, 0.35, 0.17)) + stripes((0.72, 0.13, 0.1), 3, 0.5, axis="u") + edges(0.2, 0.12, dark=True) + stains((0.3, 0.2, 0.12), 0.15, 3))
    m.add(torus((c[0], c[1], c[2] + 0.07), 0.92, 0.08, rot=(90, 0, 0), nu=28), metal((0.5, 0.5, 0.54)) + spots((0.75, 0.75, 0.78), 0.025, 0.5, 3))
    m.add(ellipsoid((c[0], c[1], c[2] + 0.16), (0.27, 0.27, 0.16)), metal((0.78, 0.66, 0.35), 0.5))
    for k in range(6):
        a = k * math.pi / 3
        m.add(sphere((c[0] + math.cos(a) * 0.5, c[1] + math.sin(a) * 0.5, c[2] + 0.15), 0.055), metal((0.72, 0.72, 0.75)))
    finish(m, "bjorn")


def make_hilda():
    """A crossing guard: a long hi-vis coat with silver bands and pockets, a white peaked cap with a badge, grey hair in
    a bun, a stern frown, and the stop sign held up on its pole"""
    m = hero_model("hilda")
    bd = replace(HERO, hip=0.6, belly=0.2)
    hivis = cloth((0.98, 0.84, 0.1), folds=4) + bands((0.82, 0.84, 0.88), [(0.32, 0.38), (0.62, 0.68)]) + stitches((0.6, 0.5, 0.05), [0.3, 0.4, 0.6, 0.7]) + \
        rect((0.9, 0.76, 0.08), 0.36, 0.46, 0.15, 0.25) + rect((0.9, 0.76, 0.08), 0.54, 0.64, 0.15, 0.25)
    b = person(m, bd, hivis, cloth((0.2, 0.22, 0.3)), arms=cloth((0.98, 0.84, 0.1)) + bands((0.82, 0.84, 0.88), [(0.4, 0.48)]),
               skirt=cloth((0.98, 0.84, 0.1), folds=6) + bands((0.82, 0.84, 0.88), [(0.12, 0.22)]) + stitches((0.6, 0.5, 0.05), [0.1, 0.24]),
               hair_paint=hair((0.72, 0.72, 0.75)), hair_style="bun", arm_pose=("up", "akimbo"), skin_c=SKIN_PALE,
               eyes_kw=dict(iris=(0.35, 0.3, 0.25), lid=0.35, size=0.07), mouth_kw=dict(kind="frown"), brows_kw=dict(c=(0.6, 0.6, 0.62), tilt=0.7),
               nose="long")
    cap(m, b, color((0.95, 0.95, 0.95)) + bands((0.15, 0.15, 0.2), [(0.0, 0.3)]), color((0.12, 0.12, 0.16)), badge=metal((0.85, 0.7, 0.3)))
    hx, hy, hz = b.right
    m.add(cylinder((hx, hy - 1.7, hz), 0.07, 3.1), metal((0.85, 0.85, 0.88)) + stripes((0.75, 0.1, 0.1), 6, 0.3, axis="v"))
    c = (hx, hy + 1.45, hz + 0.05)

    def sign(ctx):
        x, y = ctx.p[..., 0] - c[0], ctx.p[..., 1] - c[1]
        r = (x * x + y * y) ** 0.5
        out = color((0.86, 0.1, 0.08))(ctx)
        white = (smoothstep(0.62, 0.6, r) * smoothstep(0.52, 0.54, r) + (abs(y) < 0.12) * (abs(x) < 0.42) * (r < 0.56))
        white = white * (ctx.n[..., 2] > 0.5)
        return out * (1 - white[..., None]) + 0.97 * white[..., None]
    m.add(cylinder(c, 0.72, 0.08, rot=(90, 0, 0)), painted(sign), weight=1.5)
    m.add(torus((c[0], c[1], c[2] + 0.04), 0.72, 0.04, rot=(90, 0, 0)), metal((0.8, 0.8, 0.82)))
    finish(m, "hilda")


def mira_clips():
    """Mira: she stands with her staff planted, breathes, and now and then glances up at the hourglass on it; walks
    with long, unhurried steps; for Reverse her left hand sweeps a circle backwards through the air and pushes out; for
    Rewind she twirls once as she comes back; for Time lock she swings the staff back over her shoulder and thrusts the
    hourglass at her enemy. Her face for each, and the swing of her hair and the tip of her hat"""
    from rig import clip, layered
    from anatomy import once

    def staff(upper, fore, tilt=0.0):
        """The right hand turned so the staff tilts forward by tilt degrees, whatever the arm does: the staff is upright
        in the rest pose, along the arm"""
        return {"upper_r": upper, "fore_r": (fore, 0, 0), "hand_r": (tilt - upper[0] - fore, 0, 0)}

    def pose(arm, **rest):
        p = dict(arm)
        for k, v in rest.items():
            p[k] = v
        return p
    hold = staff((-12, 0, 8), -42)
    stand = pose(hold, upper_l=(-4, 0, -6), fore_l=(-34, 0, 0), hand_l=(0, -20, 0), hips={"rot": (0, 0, 0), "pos": (0, 0, 0)})
    breathe = pose(staff((-14, 0, 9), -44), upper_l=(-6, 0, -8), fore_l=(-38, 0, 0), hand_l=(0, -20, 0), chest=(-3, 0, 0), head=(2, 0, 0),
                   hips={"rot": (0, 0, 0), "pos": (0, 0.02, 0)})
    glance = pose(hold, upper_l=(-4, 0, -6), fore_l=(-34, 0, 0), hand_l=(0, -20, 0), head=(-18, -24, 0), chest=(-2, -6, 0),
                  hips={"rot": (0, 0, 0), "pos": (0, 0.01, 0)})

    def walk(s):
        return pose(staff((-12 + 10 * s, 0, 8), -42 + 6 * s), thigh_r=(-22 * s, 0, 0), thigh_l=(20 * s, 0, 0), shin_r=(8 if s > 0 else 32, 0, 0),
                    shin_l=(32 if s > 0 else 8, 0, 0), foot_r=(6 * s, 0, 0), foot_l=(-6 * s, 0, 0), upper_l=(-18 * s, 0, -8), fore_l=(-30, 0, 0),
                    hand_l=(0, -20, 0), spine=(3, 5 * s, 0), chest=(2, 4 * s, 0), head=(-2, -5 * s, 0), hips={"rot": (0, -6 * s, 3 * s), "pos": (0, -0.04, 0)})

    def passing(s):
        return pose(staff((-12, 0, 8), -42), thigh_r=(-2 if s > 0 else 2, 0, 0), thigh_l=(2 if s > 0 else -2, 0, 0), shin_r=(8 if s > 0 else 38, 0, 0),
                    shin_l=(38 if s > 0 else 8, 0, 0), upper_l=(-2, 0, -8), fore_l=(-30, 0, 0), hand_l=(0, -20, 0), spine=(3, 0, 0), chest=(2, 0, 0),
                    head=(-2, 0, 0), hips={"rot": (0, 0, 0), "pos": (0, 0.04, 0)})
    # Reverse: the staff up, and the left hand sweeps a circle backwards (up and out to her left, over her head, across to
    # the right), then pushes out flat towards the lanes
    up = staff((-55, 0, 10), -30)
    sweep_out = pose(up, upper_l=(-80, 0, -70), fore_l=(-15, 0, 0), hand_l=(-20, 0, 0), chest=(-4, 16, 0), spine=(0, 6, 0), head=(-8, 14, 0))
    sweep_top = pose(up, upper_l=(-165, 0, -15), fore_l=(-10, 0, 0), hand_l=(-30, 0, 0), chest=(-8, 6, 0), head=(-14, 4, 0),
                     hips={"rot": (0, 0, 0), "pos": (0, 0.05, 0)})
    sweep_in = pose(up, upper_l=(-95, 0, 35), fore_l=(-25, 0, 0), hand_l=(-10, 0, 0), chest=(0, -14, 0), spine=(0, -6, 0), head=(-6, -10, 0))
    push_ = pose(staff((-50, 0, 10), -30), upper_l=(-82, 0, -6), fore_l=(-4, 0, 0), hand_l=(-70, 0, 0), chest=(8, -4, 0), spine=(4, 0, 0),
                 head=(-4, 0, 0), thigh_l=(-18, 0, 0), shin_l=(14, 0, 0), thigh_r=(10, 0, 0), hips={"rot": (0, 0, 0), "pos": (0, -0.05, 0.08)})
    # Rewind: she twirls once on the spot as she comes back, the staff held high, her robe swinging out
    def twirl(angle, out=1.0):
        return pose(staff((-130, 0, 14), -20), upper_l=(-10, 0, -75 * out), fore_l=(-10, 0, 0), hand_l=(0, 0, 0), chest=(-6, 0, 0), head=(-8, 0, 0),
                    thigh_r=(0, 0, 10 * out), thigh_l=(0, 0, -10 * out), hips={"rot": (0, angle, 0), "pos": (0, 0.06 * out, 0)})
    # Time lock: the staff swung back over her shoulder, then thrust out, the hourglass at the enemy, with a step into it
    back = pose(staff((-160, 0, 16), -25, tilt=-35), upper_l=(-40, 0, -30), fore_l=(-40, 0, 0), chest=(-10, 18, 0), spine=(-4, 8, 0),
                head=(-6, -10, 0), thigh_r=(8, 0, 0), thigh_l=(-12, 0, 0), shin_l=(12, 0, 0), hips={"rot": (0, 8, 0), "pos": (0, -0.03, -0.04)})
    thrust = pose(staff((-84, 0, 4), -8, tilt=55), upper_l=(18, 0, -28), fore_l=(-20, 0, 0), hand_l=(-40, 0, 0), chest=(10, -12, 0), spine=(6, -6, 0),
                  head=(-6, 8, 0), thigh_r=(-26, 0, 0), shin_r=(20, 0, 0), thigh_l=(14, 0, 0), hips={"rot": (0, -8, 0), "pos": (0, -0.08, 0.14)})
    body = {
        "idle": clip(3.6, (0.0, stand), (1.0, breathe), (1.6, stand), (2.0, glance), (2.7, glance), (3.1, stand)),
        "walk": clip(1.0, (0.0, walk(1)), (0.25, passing(1)), (0.5, walk(-1)), (0.75, passing(-1))),
        "reverse": once(1.1, (0.0, stand), (0.15, sweep_out), (0.3, sweep_top), (0.45, sweep_in), (0.62, push_), (0.85, push_), (1.1, stand)),
        "rewind": once(0.8, (0.0, twirl(0, 0.3)), (0.2, twirl(-120)), (0.4, twirl(-240)), (0.58, twirl(-360, 0.5)), (0.8, pose(stand, hips={"rot": (0, -360, 0), "pos": (0, 0, 0)}))),
        "time_lock": once(0.9, (0.0, stand), (0.14, back), (0.3, thrust), (0.6, thrust), (0.9, stand)),
    }
    calm, blink = face_pose(jaw=1, brow=-2, lid=4), face_pose(jaw=1, brow=-2, lid=85)
    knowing = face_pose(jaw=2, brow=-8, lid=12, lift=0.008)
    wonder = face_pose(jaw=6, brow=-10, lid=4, lift=0.015)
    focus, chant = face_pose(jaw=2, brow=14, lid=30), face_pose(jaw=12, brow=8, lid=18)
    delight = face_pose(jaw=8, brow=-12, lid=10, lift=0.014)
    stern = face_pose(jaw=0, brow=22, lid=34, drop=0.01)
    command = face_pose(jaw=16, brow=18, lid=20)
    face = {
        "idle": clip(3.6, (0.0, calm), (0.7, calm), (0.75, blink), (0.82, calm), (2.0, wonder), (2.6, knowing), (3.1, calm), (3.3, calm), (3.35, blink), (3.42, calm)),
        "walk": clip(1.0, (0.0, knowing), (0.5, face_pose(jaw=2, brow=-6, lid=8, lift=0.006))),
        "reverse": once(1.1, (0.0, calm), (0.15, focus), (0.45, chant), (0.62, face_pose(jaw=14, brow=12, lid=14)), (0.85, focus), (1.1, knowing)),
        "rewind": once(0.8, (0.0, delight), (0.4, delight), (0.8, knowing)),
        "time_lock": once(0.9, (0.0, calm), (0.14, stern), (0.3, command), (0.6, stern), (0.9, knowing)),
    }
    # Her hair and the tip of her hat swing a moment after her
    flow = {
        "idle": clip(3.6, (0.0, {"hair_1": (2, 0, 0), "hair_2": (2, 0, 0), "hat_tip": (0, 0, 0)}),
                     (1.0, {"hair_1": (4, 0, 2), "hair_2": (3, 0, 2), "hat_tip": (-4, 0, 3)}), (2.0, {"hair_1": (1, 0, -2), "hair_2": (2, 0, -2), "hat_tip": (4, 0, -6)}),
                     (2.7, {"hair_1": (3, 0, -1), "hair_2": (4, 0, 0), "hat_tip": (2, 0, -4)})),
        "walk": clip(1.0, (0.0, {"hair_1": (12, 0, 6), "hair_2": (10, 0, 8), "hat_tip": (-10, 0, 6)}), (0.25, {"hair_1": (8, 0, 0), "hair_2": (16, 0, 0), "hat_tip": (-14, 0, 0)}),
                     (0.5, {"hair_1": (12, 0, -6), "hair_2": (10, 0, -8), "hat_tip": (-10, 0, -6)}), (0.75, {"hair_1": (8, 0, 0), "hair_2": (16, 0, 0), "hat_tip": (-14, 0, 0)})),
        "reverse": once(1.1, (0.0, {"hair_1": (2, 0, 0)}), (0.3, {"hair_1": (-10, 0, 12), "hair_2": (-6, 0, 16), "hat_tip": (8, 0, -12)}),
                        (0.62, {"hair_1": (14, 0, -10), "hair_2": (12, 0, -14), "hat_tip": (-12, 0, 10)}), (1.1, {"hair_1": (2, 0, 0), "hair_2": (2, 0, 0), "hat_tip": (0, 0, 0)})),
        "rewind": once(0.8, (0.0, {"hair_1": (6, 0, 0)}), (0.2, {"hair_1": (30, 0, 40), "hair_2": (20, 0, 30), "hat_tip": (-10, 0, 25)}),
                       (0.58, {"hair_1": (30, 0, 40), "hair_2": (20, 0, 30), "hat_tip": (-10, 0, 25)}), (0.8, {"hair_1": (2, 0, -6), "hair_2": (2, 0, -8), "hat_tip": (0, 0, -6)})),
        "time_lock": once(0.9, (0.0, {"hair_1": (2, 0, 0)}), (0.14, {"hair_1": (-14, 0, 0), "hair_2": (-8, 0, 0), "hat_tip": (14, 0, 0)}),
                          (0.3, {"hair_1": (24, 0, 0), "hair_2": (20, 0, 0), "hat_tip": (-22, 0, 0)}), (0.9, {"hair_1": (2, 0, 0), "hair_2": (2, 0, 0), "hat_tip": (0, 0, 0)})),
    }
    clips_ = {name: layered(body[name], face[name], flow[name]) for name in body}
    # For the portrait: the face of each clip on a body that stands still
    for name in body:
        still = clip(body[name]["duration"], (0.0, stand))
        still["once"] = body[name].get("once", False)
        clips_[name + "_face"] = layered(still, face[name], flow["idle"])
    return clips_


def make_mira():
    """Mira the Timekeeper: tall and slender in a long robe of deep violet, scattered with gold stars, with gold trim at
    the hem and down the front, and wide bell sleeves. Long silver-white hair down her back, violet eyes, pale, ageless skin, a
    tall pointed hat with a crescent moon on it whose tip flops back, a clock brooch at her collar and a pocket watch on
    a chain at her sash. Her staff, in her right hand, carries an hourglass in a gold frame, its sand running. Her left
    hand is open, for casting. Rigged like the Butcher, with clips for standing, walking, Reverse, Rewind and Time lock,
    written as models/mira.glb too"""
    from anatomy import human_joints, human_body, make_rig, grip_point, skin_paint
    from rig import write_glb
    m = Model("mira", size=1024, light=0.5, ao=1.3, detail=0.07)
    J = human_joints(shoulder_r=(0.6, 3.17, 0.0), elbow_r=(0.78, 2.5, -0.06), wrist_r=(0.86, 1.88, 0.1), hand_end_r=(0.89, 1.62, 0.18),
                     hip_r=(0.27, 1.84, 0.0), knee_r=(0.31, 1.05, 0.06), ankle_r=(0.34, 0.3, -0.02), toe_r=(0.36, 0.08, 0.48))
    m.rig = make_rig(J)
    sk = (1.0, 0.88, 0.8)
    skin_p = skin_paint(sk)
    gold = (0.9, 0.72, 0.3)
    violet = (0.34, 0.2, 0.58)
    star_c = (1.0, 0.9, 0.5)
    robe_p = cloth(violet, folds=6) + spots(star_c, 0.055, 0.07, 11) + spots((0.8, 0.72, 1.0), 0.02, 0.06, 23) + edges(0.2, 0.05, dark=True)
    sleeve_p = cloth(violet, folds=4) + spots(star_c, 0.05, 0.07, 12)
    slipper_p = leather((0.3, 0.16, 0.4)) + edges(0.3, 0.08, dark=True)
    gold_p = metal(gold, 0.45) + edges(0.4, 0.06)
    h, s, c, n = J["hips"], J["spine"], J["chest"], J["neck"]
    human_body(m, J, robe_p + bands(gold, [(0.495, 0.505)], axis="u"), sleeve_p, skin_p, cloth(tuple(v * 0.7 for v in violet), folds=2), skin_p, slipper_p,
               chest=0.94, hips=0.98, bust=0.55, arm=0.86, leg=0.86, rolled=False, left_open=True)
    # The skirt of the robe: from the waist to the ground, flaring, with a gold hem. On the hips and the legs, so it
    # follows her steps
    skirt_p = robe_p + bands(gold, [(0.93, 0.965)]) + bands(star_c, [(0.97, 0.98)]) + bands(gold, [(0.497, 0.503)], axis="u")
    path = [h + [0, 0.1, 0.0], h + [0, -0.45, 0.0], (0, 1.0, 0.02), (0, 0.5, 0.03), (0, 0.04, 0.04)]
    secs = [dict(w=0.54, d=0.38, e=2.4), dict(w=0.6, d=0.46, e=2.3), dict(w=0.72, d=0.6, e=2.2), dict(w=0.86, d=0.74, e=2.2), dict(w=0.98, d=0.86, e=2.2)]
    m.add(loft(path, secs, facing=(0, 0, 1), nu=32, nv=24, caps=None).deform(lumps(0.012, 2, 4)), skirt_p,
          bones=["hips", "thigh_r", "thigh_l", "shin_r", "shin_l"])
    # A sash at the waist, and a pocket watch on a gold chain hanging from it at her left hip
    m.add(torus(h + [0, 0.12, 0.0], 0.55, 0.06, sz=0.72, nu=28), cloth((0.62, 0.42, 0.85), folds=2) + edges(0.3, 0.08, dark=True), bones="hips")
    watch = h + [-0.42, -0.32, 0.3]
    m.add(tube([h + [-0.3, 0.1, 0.38], h + [-0.38, -0.1, 0.38], watch + [0, 0.1, 0.02]], 0.012), gold_p, bones="hips")
    m.add(cylinder(watch, 0.1, 0.035, rot=(90, 0, 15)), gold_p, bones="hips")
    m.add(cylinder(watch + [0, 0, 0.034], 0.08, 0.01, rot=(90, 0, 15)), color((0.96, 0.92, 0.82)) + edges(0.5, 0.15, dark=True), bones="hips")
    # Bell sleeves: wide from the elbow, open past the wrist, gold at the rim
    sh, e, w = J["shoulder_r"], J["elbow_r"], J["wrist_r"]
    d = (w - e) / np.linalg.norm(w - e)
    m.mirror(m.add(lathe([(0, 0.15), (0.35, 0.22), (0.62, 0.34), (0.66, 0.35)], e + d * 0.1, rot=_aim(d), nu=18, urange=(0, 1)),
                   sleeve_p + bands(gold, [(0.88, 0.96)]), bones=["upper_r", "fore_r"]))
    # A high collar, and a clock brooch at its front
    m.add(lathe([(0, 0.2), (0.16, 0.24), (0.24, 0.3)], n + [0, -0.12, -0.02], nu=20), robe_p + bands(gold, [(0.8, 1.0)]), bones=["chest", "neck"])
    brooch = c + [0, 0.32, 0.34]
    m.add(cylinder(brooch, 0.1, 0.04, rot=(90, 0, 0)), gold_p, bones="chest")
    m.add(cylinder(brooch + [0, 0, 0.04], 0.075, 0.01, rot=(90, 0, 0)), color((0.96, 0.92, 0.82)) + edges(0.5, 0.2, dark=True), bones="chest")
    m.add(tube([brooch + [0, 0, 0.052], brooch + [0, 0.055, 0.052]], 0.008), color((0.2, 0.12, 0.3)), bones="chest")
    # The head: pale, ageless, big violet eyes, silver brows, rosy lips
    hd = J["head"] + np.array([0, 0.28, 0.08])
    P = human_face(m, hd, sk, m.rig, S=0.96, iris=(0.55, 0.3, 0.82), brow_c=(0.86, 0.86, 0.92), lips=(0.82, 0.46, 0.55), nose="button")
    silver = (0.9, 0.9, 0.95)
    hair_p = hair(silver) + stripes((0.75, 0.75, 0.84), 16, 0.3, axis="u")
    m.add(ellipsoid(P(0, 0.05, -0.05), (0.39, 0.39, 0.39), vrange=(0.3, 1.0), nu=20, nv=10), hair_p, bones="head", weight=3)
    # A parting, with the hair swept down over the sides of her face to her shoulders
    for side in (1, -1):
        m.add(loft([P(side * 0.2, 0.2, 0.22), P(side * 0.34, 0.0, 0.18), P(side * 0.36, -0.3, 0.1), P(side * 0.4, -0.6, 0.04)],
                   [(0.12, 0.06, 2.2), (0.12, 0.07, 2.2), (0.11, 0.06, 2.2), (0.06, 0.03, 2.2)], facing=(side, 0, 0.3), nu=12, nv=14), hair_p, bones="head")
    # Long hair down her back, on two bones of its own, so it swings
    top = P(0, -0.02, -0.34)
    mid = top + np.array([0, -0.6, -0.12])
    end = mid + np.array([0, -0.65, -0.02])
    m.rig.bone("hair_1", top, mid, "head")
    m.rig.bone("hair_2", mid, end, "hair_1")
    m.add(loft([top + [0, 0.2, 0.06], top, mid, (mid + end) / 2, end], [(0.34, 0.12, 2.4), (0.36, 0.12, 2.4), (0.38, 0.1, 2.4), (0.33, 0.08, 2.4), (0.18, 0.04, 2.4)],
               facing=(0, 0, -1), nu=16, nv=18).deform(lumps(0.01, 6, 3)), hair_p, bones=["head", "hair_1", "hair_2"])
    # The hat: a wide brim, a tall cone that bends back, its upper half on a bone of its own (it flops), a gold band, and
    # a gold crescent moon on the front
    hat_c = (0.28, 0.16, 0.5)
    hat_p = cloth(hat_c, folds=3) + spots(star_c, 0.05, 0.08, 31) + edges(0.25, 0.06, dark=True)
    m.add(lathe([(0, 0.78), (0.02, 0.76), (0.05, 0.4), (0.06, 0.38)], P(0, 0.2, 0.0), nu=32, smooth=True).deform(squash(P(0, 0.2, 0), (0, 1, 0), 0.4)),
          hat_p, bones="head")
    base, bend = P(0, 0.24, -0.02), P(0, 0.85, -0.1)
    tip = P(0, 1.45, -0.42)
    m.rig.bone("hat_tip", bend, tip, "head")
    m.add(loft([base, (base + bend) / 2, bend, (bend + tip) / 2 + np.array([0, 0.02, 0.04]), tip],
               [(0.38, 0.38, 2.2), (0.3, 0.3, 2.2), (0.21, 0.21, 2.2), (0.12, 0.12, 2.2), (0.015, 0.015, 2.2)], facing=(0, 0, 1), nu=20, nv=20),
          hat_p, bones=["head", "hat_tip"])
    m.add(torus(P(0, 0.33, -0.02), 0.37, 0.04, nu=28), gold_p + bands((0.5, 0.25, 0.75), [(0.45, 0.55)]), bones="head")
    # The crescent: an arc of 240 degrees on the front of the cone, thick in its middle and tapering to its tips
    moon_c, moon_r = P(0, 0.62, 0.27), 0.13
    arc = [moon_c + np.array([math.cos(a) * moon_r, math.sin(a) * moon_r, 0.02 * math.cos(a)]) for a in np.radians(np.linspace(60, 300, 9))]
    widths = [0.012, 0.03, 0.045, 0.055, 0.058, 0.055, 0.045, 0.03, 0.012]
    m.add(loft(arc, [(w_, 0.025, 2.2) for w_ in widths], facing=(0, 0, 1), nu=10, nv=18), gold_p, bones="head")
    # The staff: a long dark wood shaft through her right fist, wound with gold, and the hourglass on top in a gold
    # frame: two plates, three posts, two bulbs of glass, the sand running from the top into a heap in the bottom, and
    # a violet gem over it all
    g = grip_point(J)
    up = np.array([0.0, 1.0, 0.0])
    foot, head_at = g - up * 1.55, g + up * 1.62
    wood_p = wood((0.32, 0.2, 0.14)) + bands(gold, [(0.58, 0.61), (0.9, 0.93)])
    m.add(loft([foot, g, head_at], [(0.045, 0.045, 2.2), (0.05, 0.05, 2.2), (0.055, 0.055, 2.2)], nu=10, caps="round"), wood_p, bones="hand_r")
    m.add(horn(head_at + up * 0.02, (0, 1, 0), 0.06, 0.08, curl=(0, 0, 0), tip=0.07), gold_p, bones="hand_r")
    hg = head_at + up * 0.08
    H = 0.7
    m.add(cylinder(hg, 0.24, 0.06), gold_p, bones="hand_r")
    m.add(cylinder(hg + up * H, 0.24, 0.06), gold_p, bones="hand_r")
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.4
        post = hg + np.array([math.sin(a) * 0.2, 0, math.cos(a) * 0.2])
        m.add(tube([post, post + up * (H * 0.5) + np.array([math.sin(a) * 0.02, 0, math.cos(a) * 0.02]), post + up * H], 0.022), gold_p, bones="hand_r")
    # The glass: the sand is seen through it, a heap at the bottom of the lower bulb and what is left in the neck of the
    # upper one, and a thread of it running down between
    sand_c = (0.98, 0.78, 0.38)
    m.add(lathe([(0.03, 0.03), (0.08, 0.17), (0.3, 0.12), (0.35, 0.03), (0.4, 0.12), (0.62, 0.17), (0.67, 0.03)], hg, smooth=True, nu=18),
          glass((0.72, 0.84, 1.0)) + bands(sand_c, [(0.0, 0.3), (0.5, 0.62)]) + bands((0.85, 0.62, 0.28), [(0.27, 0.3), (0.5, 0.52)]), bones="hand_r")
    m.add(tube([hg + up * 0.36, hg + up * 0.12], 0.012), color(sand_c), bones="hand_r")
    m.add(sphere(hg + up * (H + 0.16), 0.09), color((0.7, 0.45, 1.0)) + edges(0.5, 0.3), bones="hand_r")
    m.clips = mira_clips()
    finish(m, "mira")
    print(write_glb(m, fps=30))
    return m


def make_time_lock_clock():
    """The clock over a hero Mira locks in time: a round face of old ivory with gold hour marks and a ring of smaller
    ones, a gold bezel, a violet back with gears showing at its edge, and a little bell on a ring at the top. Its face
    looks towards +z, its middle at the origin, 2.2 across. The hands are a model of their own (clock_hand), which the
    game turns backwards over it"""
    m = Model("time_lock_clock", size=512, light=0.45, ao=0.8, detail=0.06)
    R = 1.1
    gold_p = metal((0.92, 0.74, 0.32), 0.45) + edges(0.4, 0.08)

    def face(ctx):
        p = ctx.p
        r = np.hypot(p[..., 0], p[..., 1]) / R
        a = np.arctan2(p[..., 0], p[..., 1]) / (2 * np.pi) * 60
        # Hour marks: bold violet bars, a gold one at twelve; a dot for each minute; a ring inside them
        arc = r * 2 * np.pi * R / 60                                     # The length of a minute along the circle here
        minute = smoothstep(0.035, 0.015, np.abs(a - np.round(a)) * arc) * smoothstep(0.012, 0.0, np.abs(r - 0.84))
        hour_off = np.abs(a / 5 - np.round(a / 5)) * 5 * arc
        hour = smoothstep(0.05, 0.03, hour_off) * (r > 0.64) * (r < 0.86)
        twelve = hour * (np.abs(a) < 2.5)
        ring = smoothstep(0.01, 0.0, np.abs(r - 0.6))
        base = np.zeros(p.shape[:-1] + (3,)) + np.array([0.95, 0.9, 0.78])
        base = base * (0.95 + 0.06 * fbm(p, 4, 2, 5))[..., None]
        base = _over(base, (0.28, 0.16, 0.42), np.clip(minute + ring * 0.7 + hour, 0, 1))
        base = _over(base, (0.9, 0.7, 0.28), np.clip(twelve, 0, 1))
        return base * (1 - 0.25 * smoothstep(0.75, 1.0, r))[..., None]
    m.add(cylinder((0, 0, 0.0), R * 0.92, 0.04, rot=(90, 0, 0)), Paint(face), weight=3)
    m.add(torus((0, 0, 0.0), R * 0.96, 0.09, rot=(90, 0, 0), nu=40), gold_p)
    m.add(cylinder((0, 0, -0.18), R * 0.98, 0.16, rot=(90, 0, 0)), color((0.32, 0.2, 0.48)) + edges(0.3, 0.1, dark=True))
    for k in range(8):
        a = k * 2 * math.pi / 8
        m.add(cylinder((math.sin(a) * R * 0.92, math.cos(a) * R * 0.92, -0.22), 0.1, 0.05, rot=(90, 0, 0)), gold_p)
    m.add(torus((0, R + 0.16, 0), 0.12, 0.03, nu=16), gold_p)
    m.add(sphere((0, R + 0.32, 0), 0.12), gold_p)
    tris = m.write()
    print(f"models/time_lock_clock.obj  {tris} triangles")


def make_clock_hand():
    """A hand of the clock, pointing up +y from its pivot at the origin, 0.9 long, a spade near its tip, a gold cap
    over the pivot. Lying just in front of the clock's face (+z)"""
    m = Model("clock_hand", size=256, light=0.45, ao=0.6, detail=0.04)
    dark = color((0.22, 0.12, 0.32)) + edges(0.4, 0.1)
    m.add(loft([(0, -0.18, 0.1), (0, 0.6, 0.1)], [(0.05, 0.02, 2.0), (0.025, 0.02, 2.0)], facing=(0, 0, 1), nu=10, caps="flat"), dark)
    m.add(blob((0, 0.68, 0.1), (0.1, 0.14, 0.02), (0.5, 0.9)), dark)
    m.add(loft([(0, 0.78, 0.1), (0, 0.92, 0.1)], [(0.03, 0.02, 2.0), (0.004, 0.01, 2.0)], facing=(0, 0, 1), nu=8, caps="flat"), dark)
    m.add(cylinder((0, 0, 0.12), 0.09, 0.05, rot=(90, 0, 0)), metal((0.92, 0.74, 0.32), 0.45) + edges(0.4, 0.08))
    tris = m.write()
    print(f"models/clock_hand.obj  {tris} triangles")


def make_car_jack():
    """Karl's jack, that a car he lifts stands on at each end: a scissor jack of red steel arms in a diamond, a long screw
    through it with a crank eye at one end, a wide base and a ridged saddle on top. It is drawn stretched up as the car
    goes up, so it is made open, JackModelHeight (2.85) tall"""
    m = Model("car_jack", size=512, ground_ao=True, light=0.4, ao=0.8, detail=0.05)
    red = color((0.8, 0.12, 0.08)) + edges(0.35, 0.08, dark=True) + stains((0.2, 0.15, 0.1), 0.15, 4)
    steel = metal((0.6, 0.62, 0.66), 0.5) + edges(0.3, 0.05)
    H, W = 2.85, 0.75
    m.add(beam((-0.75, 0.05, 0), (0.75, 0.05, 0), 0.12, 0.4, facing=(0, 0, 1)), color((0.25, 0.25, 0.28)) + edges(0.3, 0.1))
    mid = H * 0.5
    for z in (-0.18, 0.18):
        for x in (-W, W):
            m.add(beam((0, 0.18, z), (x, mid, z), 0.07, 0.04, facing=(0, 0, 1), e=4.0), red)
            m.add(beam((x, mid, z), (0, H - 0.2, z), 0.07, 0.04, facing=(0, 0, 1), e=4.0), red)
    m.add(tube([(-W - 0.35, mid, 0), (W + 0.15, mid, 0)], 0.05, nu=8), steel)
    m.add(torus((-W - 0.45, mid, 0), 0.1, 0.035, rot=(0, 0, 90), nu=12), steel)
    for x in (-W, W, 0):
        y = mid if x else 0.18
        m.add(sphere((x, y, 0.24), 0.06, nu=8, nv=6), steel)
    m.add(beam((-0.45, H - 0.15, 0), (0.45, H - 0.15, 0), 0.12, 0.3, facing=(0, 0, 1)), red)
    for k in range(4):
        x = -0.3 + k * 0.2
        m.add(beam((x, H - 0.02, -0.25), (x, H - 0.02, 0.25), 0.03, 0.025, facing=(0, 1, 0)), steel)
    tris = m.write()
    print(f"models/car_jack.obj  {tris} triangles")


def karl_clips():
    """Karl: he stands with his wrench and his oil can, shakes the can to hear how much is in it, plods along, crouches
    and cranks to jack up a car, and swings his can round to sling its oil"""
    from rig import clip, layered
    from anatomy import once
    stand = {"upper_r": (-6, 0, 8), "fore_r": (-30, 0, 0), "upper_l": (-6, 0, -8), "fore_l": (-35, 0, 0), "head": (4, 0, 0),
             "hips": {"rot": (0, 0, 0), "pos": (0, 0, 0)}}
    breathe = dict(stand, chest=(-3, 0, 0), head=(2, 0, 0))
    breathe["hips"] = {"rot": (0, 0, 0), "pos": (0, 0.02, 0)}
    shake0 = {"upper_r": (-6, 0, 8), "fore_r": (-30, 0, 0), "upper_l": (-30, 0, -20), "fore_l": (-95, 0, 0), "hand_l": (0, 0, 15), "head": (8, 0, -12),
              "chest": (0, 10, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0, 0)}}
    shake1 = dict(shake0, hand_l=(0, 0, -15), fore_l=(-100, 0, 0))

    def walk(s):
        return {"thigh_r": (-24 * s, 0, 0), "thigh_l": (22 * s, 0, 0), "shin_r": (8 if s > 0 else 34, 0, 0), "shin_l": (34 if s > 0 else 8, 0, 0),
                "upper_r": (18 * s, 0, 8), "upper_l": (-18 * s, 0, -8), "fore_r": (-30, 0, 0), "fore_l": (-35, 0, 0),
                "spine": (6, 6 * s, 0), "chest": (2, 5 * s, 0), "hips": {"rot": (0, -6 * s, 4 * s), "pos": (0, -0.05, 0)}, "head": (-4, -6 * s, 0)}

    def passing(s):
        return {"thigh_r": (-4 if s > 0 else 0, 0, 0), "thigh_l": (0 if s > 0 else -4, 0, 0), "shin_r": (12 if s > 0 else 40, 0, 0),
                "shin_l": (40 if s > 0 else 12, 0, 0), "upper_r": (0, 0, 8), "upper_l": (0, 0, -8), "fore_r": (-30, 0, 0), "fore_l": (-35, 0, 0),
                "spine": (6, 0, 0), "chest": (2, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.05, 0)}, "head": (-4, 0, 0)}
    # The jack: down on his haunches, the wrench at the crank, round and round
    squat = {"thigh_r": (-70, 0, 12), "thigh_l": (-60, 0, -12), "shin_r": (90, 0, 0), "shin_l": (80, 0, 0), "spine": (30, 0, 0), "chest": (10, 0, 0),
             "head": (-25, 0, 0), "upper_l": (-40, 0, -25), "fore_l": (-60, 0, 0), "hips": {"rot": (10, 0, 0), "pos": (0, -0.6, 0.05)}}

    def crank(a):
        pose = dict(squat)
        pose["upper_r"] = (-55 + 25 * math.sin(a), 0, 10 + 15 * math.cos(a))
        pose["fore_r"] = (-40 + 25 * math.cos(a), 0, 0)
        pose["hand_r"] = (0, 0, 30 * math.sin(a))
        return pose
    # The oil: the can back low, then swung round and up, tipped, the oil flying out of it
    back = {"upper_l": (50, 0, -18), "fore_l": (-25, 0, 0), "hand_l": (-30, 0, 0), "upper_r": (-20, 0, 12), "fore_r": (-40, 0, 0), "chest": (4, -26, 0),
            "spine": (4, -10, 0), "head": (-4, 14, 0), "thigh_r": (-14, 0, 0), "shin_r": (16, 0, 0), "hips": {"rot": (0, -12, 0), "pos": (0, -0.1, 0)}}
    sling = {"upper_l": (-120, 0, -12), "fore_l": (-10, 0, 0), "hand_l": (60, 0, 0), "upper_r": (10, 0, 14), "fore_r": (-35, 0, 0), "chest": (-6, 22, 0),
             "spine": (-2, 8, 0), "head": (-8, -10, 0), "thigh_l": (-30, 0, 0), "shin_l": (22, 0, 0), "thigh_r": (14, 0, 0), "hips": {"rot": (0, 10, 0), "pos": (0, -0.04, 0.14)}}
    body = {
        "idle": clip(3.4, (0.0, stand), (0.9, breathe), (1.6, stand), (1.9, shake0), (2.05, shake1), (2.2, shake0), (2.35, shake1), (2.5, shake0), (2.9, stand)),
        "walk": clip(1.0, (0.0, walk(1)), (0.25, passing(1)), (0.5, walk(-1)), (0.75, passing(-1))),
        "jack": once(1.0, (0.0, stand), (0.15, crank(0)), (0.3, crank(2.1)), (0.45, crank(4.2)), (0.6, crank(6.3)), (0.75, crank(8.4)), (1.0, stand)),
        "oil_change": once(0.8, (0.0, stand), (0.15, back), (0.32, sling), (0.55, sling), (0.8, stand)),
    }
    calm, blink = face_pose(jaw=1, brow=6, lid=24), face_pose(jaw=1, brow=6, lid=88)
    listen = face_pose(jaw=4, brow=-4, lid=30, lift=0.01)
    effort, grunt = face_pose(jaw=3, brow=20, lid=40, drop=0.01), face_pose(jaw=10, brow=22, lid=36)
    grin = face_pose(jaw=12, brow=-6, lid=18, lift=0.01)
    face = {
        "idle": clip(3.4, (0.0, calm), (1.1, calm), (1.15, blink), (1.22, calm), (1.9, listen), (2.6, listen), (2.9, calm)),
        "walk": clip(1.0, (0.0, face_pose(jaw=2, brow=8, lid=26)), (0.5, face_pose(jaw=3, brow=8, lid=26))),
        "jack": once(1.0, (0.0, calm), (0.15, effort), (0.4, grunt), (0.6, effort), (0.8, grunt), (1.0, calm)),
        "oil_change": once(0.8, (0.0, calm), (0.15, effort), (0.32, grin), (0.6, grin), (0.8, calm)),
    }
    clips_ = {name: layered(body[name], face[name]) for name in body}
    for name in body:
        still = clip(body[name]["duration"], (0.0, stand))
        still["once"] = body[name].get("once", False)
        clips_[name + "_face"] = layered(still, face[name])
    return clips_


def make_karl():
    """Karl the Mechanic: stocky, in brown canvas bib overalls with straps, brass buttons and oil stains over a white
    undershirt rolled up at the arms, greasy forearms and hands, heavy work boots, an olive trucker cap, a thick grey
    walrus moustache and stubble, a big nose and a tired squint, a red rag hanging from his back pocket, a big adjustable
    wrench in his right fist and a dented oil can with a long spout in his left. Rigged like the Butcher, with clips for
    standing, walking, cranking up a car on his jack and slinging oil from his can, written as models/karl.glb too"""
    from anatomy import human_joints, human_body, make_rig, grip_point, skin_paint, L
    from rig import write_glb
    m = Model("karl", size=1024, light=0.5, ao=1.3, detail=0.07)
    J = human_joints(hips=(0, 1.75, 0), spine=(0, 2.22, 0.06), chest=(0, 2.8, 0.08), neck=(0, 3.25, 0.08), head=(0, 3.45, 0.12),
                     shoulder_r=(0.74, 3.08, 0.0), elbow_r=(0.96, 2.4, -0.04), wrist_r=(1.04, 1.78, 0.12), hand_end_r=(1.07, 1.5, 0.2),
                     hip_r=(0.34, 1.72, 0.0), knee_r=(0.38, 0.98, 0.08), ankle_r=(0.42, 0.3, -0.02), toe_r=(0.44, 0.08, 0.54))
    m.rig = make_rig(J)
    sk = (0.9, 0.68, 0.54)
    grease = (0.08, 0.07, 0.06)
    skin_p = skin_paint(sk)
    blue = (0.55, 0.38, 0.2)        # Brown canvas
    white = (0.86, 0.84, 0.8)
    c_y = J["chest"][1]

    def overalls_top(ctx):
        # The bib over his chest and the straps over his shoulders are the overalls; the rest of his top is the undershirt
        y, x, z = ctx.p[..., 0] * 0 + ctx.p[..., 1], ctx.p[..., 0], ctx.p[..., 2]
        shirt = rgb(white) * (0.94 + 0.08 * fbm(ctx.p, 4, 2, 3))[..., None]
        denim = rgb(blue) * (0.9 + 0.15 * fbm(ctx.p * np.array([1, 4, 1]), 6, 2, 8))[..., None]
        below = smoothstep(J["spine"][1] + 0.12, J["spine"][1] + 0.08, y)
        bib = smoothstep(0.34, 0.3, np.abs(x)) * smoothstep(c_y + 0.25, c_y + 0.2, y) * (z > 0)
        strap = smoothstep(0.07, 0.05, np.abs(np.abs(x) - 0.3 + 0.08 * np.clip((y - c_y) / 0.5, 0, 1) * np.sign(z)))
        cover = np.clip(np.maximum(np.maximum(below, bib), strap), 0, 1)
        out = shirt * (1 - cover)[..., None] + denim * cover[..., None]
        stains_ = smoothstep(0.7, 0.76, fbm(ctx.p, 3.5, 3, 41)) * 0.55
        return out * (1 - stains_)[..., None] + np.array(grease) * stains_[..., None]
    trousers = cloth(blue, folds=4) + stains(grease, 0.2, 2.5) + stitches((0.8, 0.62, 0.3), [0.2, 0.8], axis="u")
    boots = leather((0.3, 0.2, 0.13)) + edges(0.25, 0.06, dark=True) + stains(grease, 0.2, 4)
    hands = skin_paint(sk) + stains(grease, 0.35, 5)
    pads = cloth((0.45, 0.3, 0.16), folds=2) + stitches((0.8, 0.62, 0.3), [0.1, 0.9], axis="u")
    human_body(m, J, Paint(overalls_top), cloth(white, folds=3) + stains(grease, 0.12, 3), skin_p + stains(grease, 0.25, 4), trousers, hands, boots,
               chest=1.12, hips=1.12, bust=0.0, arm=1.12, leg=1.1, cuff_p=cloth(white, folds=2), knee_p=pads)
    h, c = J["hips"], J["chest"]
    # Brass buttons on the bib, a pocket with a pencil, a belly over the belt
    for x in (0.27, -0.27):
        m.add(sphere(c + [x, 0.22, 0.38], 0.05, nu=8, nv=6), metal((0.85, 0.66, 0.25), 0.6), bones="chest")
    m.add(blob(c + [0.0, 0.0, 0.42], (0.16, 0.12, 0.03), (0.4, 0.4)), cloth((0.45, 0.3, 0.16), folds=2) + edges(0.3, 0.1, dark=True), bones="chest")
    m.add(tube([c + [0.06, 0.02, 0.44], c + [0.08, 0.2, 0.44]], 0.018), color((0.95, 0.75, 0.15)), bones="chest")
    m.add(blob(J["spine"] + [0, -0.05, 0.14], (0.36, 0.28, 0.2), (0.85, 0.85)), trousers, bones=["spine", "hips"])
    # A red rag hanging out of his back pocket
    m.add(loft([h + [0.25, -0.15, -0.36], h + [0.3, -0.45, -0.4], h + [0.27, -0.7, -0.36]], [(0.1, 0.02, 3), (0.12, 0.02, 3), (0.09, 0.02, 3)],
               facing=(0, 0, 1), nu=10, nv=10, caps="flat"), cloth((0.8, 0.18, 0.12), folds=3) + stains(grease, 0.3, 5), bones="hips")
    # The head: tired eyes, a big nose, stubble
    hd = J["head"] + np.array([0, 0.3, 0.1])
    S = 1.05
    P = human_face(m, hd, sk, m.rig, S=S, iris=(0.42, 0.3, 0.2), brow_c=(0.45, 0.42, 0.4), lips=(0.75, 0.5, 0.44), freckles=0.0, nose="button")
    m.add(blob(P(0, -0.06, 0.39), (0.08 * S, 0.075 * S, 0.075 * S), (0.85, 0.85)), skin_paint((0.92, 0.62, 0.52)), bones="head", weight=4)
    grey = (0.55, 0.52, 0.5)
    m.mirror(m.add(loft([P(0.05, 0.13, 0.37), P(0.15, 0.15, 0.36), P(0.24, 0.12, 0.31)], [(0.025 * S, 0.03 * S, 2.2), (0.03 * S, 0.035 * S, 2.2), (0.02 * S, 0.02 * S, 2.2)],
                        facing=(0, 0.3, 1), nu=10, nv=10), hair(grey), bones="brow_r"))
    # The walrus moustache, drooping over his mouth
    tash = hair(grey) + stripes((0.4, 0.38, 0.36), 10, 0.2, axis="u")
    m.add(loft([P(-0.17, -0.2, 0.3), P(-0.09, -0.13, 0.38), P(0, -0.12, 0.41), P(0.09, -0.13, 0.38), P(0.17, -0.2, 0.3)],
               [(0.03 * S, 0.035 * S, 2.2), (0.06 * S, 0.05 * S, 2.2), (0.065 * S, 0.055 * S, 2.2), (0.06 * S, 0.05 * S, 2.2), (0.03 * S, 0.035 * S, 2.2)],
               facing=(0, 0, 1), nu=12, nv=20), tash, bones="head", weight=3)
    stubble_p = skin_paint(sk) + stubble((0.35, 0.32, 0.3), 0.6, 0.62)
    m.add(blob(P(0, -0.27, 0.16), (0.2 * S, 0.11 * S, 0.2 * S), (0.75, 0.75)), skin_paint(sk) + (lambda ctx, base: _over(base, (0.42, 0.38, 0.36),
          smoothstep(0.5, 0.58, fbm(ctx.p, 160, 1, 5)) * 0.45)), bones="jaw", weight=4)
    # Grey hair at the sides, under the cap, and the cap: red, with a bill
    m.add(ellipsoid(P(0, 0.02, -0.06), (0.4 * S, 0.36 * S, 0.4 * S), vrange=(0.35, 0.7), nu=20, nv=8), hair(grey), bones="head", weight=2)
    cap_p = color((0.36, 0.42, 0.22)) + stains(grease, 0.12, 4) + edges(0.2, 0.08, dark=True)
    front = cap_p + (lambda ctx, base: _over(base, (0.9, 0.88, 0.82), smoothstep(0.1, 0.2, ctx.n[..., 2]) * smoothstep(0.55, 0.45, np.abs(ctx.n[..., 0]))))
    m.add(ellipsoid(P(0, 0.16, -0.02), (0.42 * S, 0.33 * S, 0.43 * S), vrange=(0.5, 1.0), nu=24, nv=10), front, bones="head", weight=2)
    m.add(loft([P(0, 0.17, 0.25), P(0, 0.15, 0.62)], [dict(w=0.32 * S, d=0.03, e=2.4), dict(w=0.26 * S, d=0.03, e=2.4)], facing=(0, 1, 0), nu=16, caps="flat"),
          cap_p, bones="head")
    m.add(sphere(P(0, 0.49, 0.0), 0.04 * S, nu=8, nv=6), cap_p, bones="head")
    # The wrench in his right fist: a long handle, an open jaw with a thumb screw
    g = grip_point(J)
    along = np.array([0.0, -0.3, 1.0])
    along /= np.linalg.norm(along)
    steel = metal((0.7, 0.72, 0.76), 0.55) + edges(0.35, 0.06) + stains(grease, 0.12, 4)
    end = g + along * 0.9
    m.add(loft([g - along * 0.2, end], [(0.06, 0.035, 4.0), (0.07, 0.04, 4.0)], facing=(1, 0, 0), nu=12, caps="round"), steel, bones="hand_r")
    up = np.array([0.0, 1.0, 0.3])
    up /= np.linalg.norm(up)
    m.add(loft([end - up * 0.2, end + up * 0.08], [(0.13, 0.06, 4.0), (0.13, 0.06, 4.0)], facing=(1, 0, 0), nu=12, caps="flat"), steel, bones="hand_r")
    for side in (1, -1):
        m.add(loft([end + along * 0.05 + up * side * 0.12, end + along * 0.25 + up * side * 0.14], [(0.05, 0.05, 4.0), (0.04, 0.045, 4.0)], facing=(1, 0, 0), nu=10,
                   caps="flat"), steel, bones="hand_r")
    m.add(cylinder(end - up * 0.12 + along * 0.02, 0.05, 0.12, rot=(90, 0, 0)), metal((0.85, 0.7, 0.3), 0.5), bones="hand_r")
    # The oil can in his left fist: dented, green, a handle, a long spout
    gl = L(g)
    can_p = color((0.2, 0.42, 0.2)) + edges(0.3, 0.08, dark=True) + stains(grease, 0.25, 4) + bands((0.85, 0.75, 0.2), [(0.45, 0.55)])
    base = gl + np.array([0, -0.38, 0.12])
    m.add(lathe([(0.0, 0.0), (0.0, 0.26), (0.32, 0.26), (0.42, 0.18), (0.48, 0.06), (0.5, 0.0)], base, smooth=False, nu=20), can_p, bones="hand_l")
    m.add(tube([base + [0, 0.5, 0], base + [0.0, 0.62, 0.3], base + [0.0, 0.75, 0.75]], [0.06, 0.04, 0.025], nu=8), metal((0.6, 0.6, 0.62), 0.5), bones="hand_l")
    m.add(tube([base + [0.0, 0.42, -0.2], gl + [0, 0.05, -0.02], base + [0.0, 0.42, 0.2]], 0.03, nu=8, caps=False), metal((0.4, 0.4, 0.42), 0.4), bones="hand_l")
    m.clips = karl_clips()
    finish(m, "karl")
    print(write_glb(m, fps=30))
    return m


def human_face(m, hd, sk, rig_, S=1.0, iris=(0.3, 0.52, 0.32), brow_c=(0.55, 0.3, 0.12), lips=(0.72, 0.42, 0.38),
               freckles=0.0, nose="button"):
    """A person's head with bones for its face, like ogre_face: a skull that is a little square, big eyes under lids
    that blink (lid bones), brows that frown and lift (brow bones), a nose, round cheeks, a mouth whose chin and lower
    lip drop open (the jaw bone), and ears. No hair: that, and a hat, go on top. S scales it (1 is about 0.4 round)"""
    from anatomy import skin_paint
    h = np.asarray(hd, float)

    def P(x, y, z):
        return h + S * np.array([x, y, z], float)

    def R(*r):
        return tuple(S * v for v in r)
    E = 0.14
    eye_r = P(E, 0.03, 0.305)
    rig_.bone("jaw", P(0, -0.04, -0.05), P(0, -0.3, 0.3), "head")
    rig_.bone("brow_r", P(0.04, 0.13, 0.36), P(0.24, 0.14, 0.3), "head")
    rig_.bone("lid_r", eye_r, eye_r + S * np.array([0, 0, 0.08]), "head")
    rig_.mirror()
    detail = m.detail
    m.detail = 0.025
    W = 5

    def dots(ctx, base):
        if not freckles:
            return base
        q = (ctx.p - h) / S
        band = smoothstep(0.14, 0.04, np.abs(q[..., 1] + 0.06)) * smoothstep(0.3, 0.6, ctx.n[..., 2]) * smoothstep(0.32, 0.18, np.abs(q[..., 0]))
        f = smoothstep(0.8, 0.83, fbm(ctx.p, 140 / S, 1, 77)) * band * freckles
        return _over(base, tuple(c * 0.78 for c in sk), f * 0.8)
    sp = skin_paint(sk) + flush(h, S, 0.08) + dots
    # The skull: round at the back, a flat face, a jaw that tapers to the chin
    m.add(blob(P(0, 0.04, -0.02), R(0.36, 0.4, 0.37), (0.72, 0.8)).deform(push(P(0, -0.27, 0.25), 0.22 * S, (0, 0.01 * S, -0.05 * S))),
          sp, bones="head", weight=W)
    # Eyes, big for a hero: white, a coloured iris, a lid over each that blinks, and a crease under it
    for side in (1, -1):
        c = eye_r if side > 0 else eye_r * np.array([-1, 1, 1]) + np.array([2 * h[0], 0, 0])
        m.add(sphere(c, 0.075 * S, nu=18, nv=14), eyeball(c, look=(0, -0.03, 1), iris=iris, sclera=(0.97, 0.96, 0.94), iris_size=44, pupil_size=15),
              bones="head", weight=W)
    lid = m.add(ellipsoid(eye_r, R(0.082, 0.082, 0.082), vrange=(0.62, 1.0), nu=18, nv=6), sp + lash_line(True, c=(0.12, 0.06, 0.04), width=0.22),
                bones="lid_r", weight=W)
    m.mirror(lid)
    # Brows: thin arches of hair
    m.mirror(m.add(loft([P(0.06, 0.135, 0.37), P(0.14, 0.16, 0.365), P(0.22, 0.14, 0.32)], [(0.014, 0.02, 2.2), (0.018, 0.024, 2.2), (0.01, 0.014, 2.2)],
                        facing=(0, 0.3, 1), nu=10, nv=10), color(brow_c), bones="brow_r", weight=W))
    # Cheeks and the nose
    m.mirror(m.add(blob(P(0.16, -0.08, 0.22), R(0.09, 0.07, 0.08), (0.9, 0.9)), sp, bones="head", weight=W))
    if nose == "button":
        m.add(blob(P(0, -0.06, 0.375), R(0.05, 0.06, 0.06), (0.85, 0.85)), sp, bones="head", weight=W)
    else:
        m.add(loft([P(0, 0.06, 0.34), P(0, -0.08, 0.43)], [(0.035, 0.04, 2.2), (0.06, 0.05, 2.2)], nu=10), sp, bones="head", weight=W)
    # The mouth: dark inside, an upper lip on the head, and the chin with the lower lip on the jaw, so it opens
    m.add(ellipsoid(P(0, -0.19, 0.25), R(0.1, 0.04, 0.09)), color((0.3, 0.07, 0.07)), bones="head")
    lip_p = skin_paint(lips)
    m.add(loft([P(-0.09, -0.158, 0.31), P(-0.04, -0.17, 0.34), P(0, -0.168, 0.35), P(0.04, -0.17, 0.34), P(0.09, -0.158, 0.31)], [(0.01, 0.014, 2.2), (0.016, 0.018, 2.2), (0.017, 0.019, 2.2), (0.016, 0.018, 2.2), (0.01, 0.014, 2.2)],
               facing=(0, 0, 1), nu=10, nv=14), lip_p, bones="head", weight=W)
    m.add(blob(P(0, -0.26, 0.15), R(0.19, 0.1, 0.19), (0.75, 0.75)).deform(push(P(0, -0.31, 0.32), 0.1 * S, (0, -0.005 * S, 0.01 * S))), sp, bones="jaw", weight=W)
    m.add(loft([P(-0.07, -0.192, 0.31), P(0, -0.205, 0.335), P(0.07, -0.192, 0.31)], [(0.01, 0.014, 2.2), (0.019, 0.021, 2.2), (0.01, 0.014, 2.2)],
               facing=(0, 0, 1), nu=10, nv=12), lip_p, bones="jaw", weight=W)
    m.add(ellipsoid(P(0, -0.212, 0.24), R(0.075, 0.016, 0.07)), color((0.8, 0.78, 0.72)), bones="jaw")
    m.add(ellipsoid(P(0, -0.17, 0.25), R(0.075, 0.016, 0.07)), color((0.9, 0.88, 0.84)), bones="head")
    # Ears
    for side in (1, -1):
        m.add(blob(P(side * 0.36, -0.01, -0.02), R(0.05, 0.1, 0.07), (0.7, 0.7), rot=(0, side * 15, 0)), sp, bones="head")
    m.detail = detail
    return P


def birgit_clips():
    """Birgit: she stands with her hammer, walks with a swing in her step, slams her hammer down to build a bridge,
    and tosses a trampoline out underarm. Each with what her face does, and the swing of her braid"""
    from rig import clip, layered
    from anatomy import once
    stand = {"upper_r": (-6, 0, 6), "fore_r": (-28, 0, 0), "upper_l": (0, 0, -8), "fore_l": (-14, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0, 0)}}
    breathe = {"upper_r": (-8, 0, 7), "fore_r": (-32, 0, 0), "upper_l": (0, 0, -10), "fore_l": (-18, 0, 0), "chest": (-3, 0, 0), "head": (2, 0, 0),
               "hips": {"rot": (0, 0, 0), "pos": (0, 0.02, 0)}}
    # Now and then she tips the hammer up, checks it, and lets it down again
    check = {"upper_r": (-30, 0, 4), "fore_r": (-95, 0, 0), "hand_r": (0, 0, -20), "upper_l": (0, 0, -9), "fore_l": (-16, 0, 0), "head": (14, -18, 0),
             "chest": (-2, -6, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.01, 0)}}

    def walk(s):
        return {"thigh_r": (-28 * s, 0, 0), "thigh_l": (26 * s, 0, 0), "shin_r": (8 if s > 0 else 38, 0, 0), "shin_l": (38 if s > 0 else 8, 0, 0),
                "foot_r": (8 * s, 0, 0), "foot_l": (-8 * s, 0, 0),
                "upper_r": (24 * s, 0, 6), "upper_l": (-26 * s, 0, -8), "fore_r": (-30 - 10 * s, 0, 0), "fore_l": (-24 + 8 * s, 0, 0),
                "spine": (5, 7 * s, 0), "chest": (3, 6 * s, 0), "hips": {"rot": (0, -8 * s, 3 * s), "pos": (0, -0.05, 0)}, "head": (-6, -8 * s, 0)}

    def passing(s):
        return {"thigh_r": (-4 if s > 0 else 2, 0, 0), "thigh_l": (2 if s > 0 else -4, 0, 0), "shin_r": (10 if s > 0 else 45, 0, 0),
                "shin_l": (45 if s > 0 else 10, 0, 0), "upper_r": (0, 0, 6), "upper_l": (0, 0, -8), "fore_r": (-30, 0, 0), "fore_l": (-24, 0, 0),
                "spine": (5, 0, 0), "chest": (3, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.05, 0)}, "head": (-6, 0, 0)}
    # The footbridge: the hammer up over her head with both hands, a slam down onto the ground in front of her (the
    # bridge goes up as it lands), and back up
    raise_ = {"upper_r": (-150, 0, 10), "fore_r": (-40, 0, 0), "upper_l": (-140, 0, -10), "fore_l": (-55, 0, 0), "hand_r": (20, 0, 0),
              "spine": (-8, 0, 0), "chest": (-12, 0, 0), "head": (-14, 0, 0), "thigh_r": (-6, 0, 0), "thigh_l": (4, 0, 0),
              "hips": {"rot": (0, 0, 0), "pos": (0, 0.06, 0)}}
    slam = {"upper_r": (-82, 0, 4), "fore_r": (-4, 0, 0), "upper_l": (-80, 0, 18), "fore_l": (-12, 0, 0), "hand_r": (72, 0, 0),
            "spine": (20, 0, 0), "chest": (16, 0, 0), "head": (-18, 0, 0), "thigh_r": (-48, 0, 0), "shin_r": (55, 0, 0), "thigh_l": (14, 0, 0),
            "shin_l": (36, 0, 0), "hips": {"rot": (6, 0, 0), "pos": (0, -0.34, 0.12)}}
    settle = {"upper_r": (-30, 0, 6), "fore_r": (-30, 0, 0), "upper_l": (-10, 0, -6), "fore_l": (-30, 0, 0), "spine": (8, 0, 0), "chest": (4, 0, 0),
              "head": (-4, 0, 0), "thigh_r": (-14, 0, 0), "shin_r": (14, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, -0.06, 0.04)}}
    # The trampoline: her free hand goes back low, then flings it forward and up, a step into it
    back = {"upper_l": (55, 0, -14), "fore_l": (-20, 0, 0), "upper_r": (-20, 0, 10), "fore_r": (-40, 0, 0), "chest": (6, 24, 0), "spine": (6, 10, 0),
            "head": (-4, -16, 0), "thigh_l": (8, 0, 0), "thigh_r": (-16, 0, 0), "shin_r": (20, 0, 0), "hips": {"rot": (0, 10, 0), "pos": (0, -0.1, 0)}}
    toss = {"upper_l": (-120, 0, -10), "fore_l": (-10, 0, 0), "upper_r": (10, 0, 12), "fore_r": (-30, 0, 0), "chest": (-6, -20, 0), "spine": (-2, -8, 0),
            "head": (-8, 12, 0), "thigh_l": (-30, 0, 0), "shin_l": (20, 0, 0), "thigh_r": (14, 0, 0), "hips": {"rot": (0, -10, 0), "pos": (0, -0.04, 0.12)}}
    body = {
        "idle": clip(3.0, (0.0, stand), (0.9, breathe), (1.4, stand), (1.7, check), (2.2, check), (2.6, stand)),
        "walk": clip(0.9, (0.0, walk(1)), (0.225, passing(1)), (0.45, walk(-1)), (0.675, passing(-1))),
        "footbridge": once(0.95, (0.0, stand), (0.16, raise_), (0.3, slam), (0.6, slam), (0.95, settle)),
        "trampoline": once(0.8, (0.0, stand), (0.14, back), (0.3, toss), (0.5, toss), (0.8, stand)),
    }
    calm, blink = face_pose(jaw=1, brow=2, lid=4), face_pose(jaw=1, brow=2, lid=80)
    smirk, look = face_pose(jaw=4, brow=-6, lid=2, lift=0.01), face_pose(jaw=1, brow=10, lid=12)
    effort, shout = face_pose(jaw=6, brow=20, lid=22, drop=0.01), face_pose(jaw=22, brow=16, lid=0)
    grin = face_pose(jaw=14, brow=-8, lid=0, lift=0.012)
    face = {
        "idle": clip(3.0, (0.0, calm), (0.8, calm), (0.85, blink), (0.92, calm), (1.7, look), (2.2, look), (2.5, smirk), (2.85, calm)),
        "walk": clip(0.9, (0.0, face_pose(jaw=2, brow=6, lid=6)), (0.45, face_pose(jaw=4, brow=6, lid=6))),
        "footbridge": once(0.95, (0.0, calm), (0.16, effort), (0.3, shout), (0.6, face_pose(jaw=12, brow=12, lid=6)), (0.95, calm)),
        "trampoline": once(0.8, (0.0, calm), (0.14, look), (0.3, grin), (0.6, grin), (0.8, smirk)),
    }
    # The braid swings behind her, a moment after what she does
    braid = {
        "idle": clip(3.0, (0.0, {"braid_1": (4, 0, 2), "braid_2": (6, 0, 0)}), (1.5, {"braid_1": (6, 0, -2), "braid_2": (2, 0, 0)})),
        "walk": clip(0.9, (0.0, {"braid_1": (10, 0, 8), "braid_2": (8, 0, 10)}), (0.225, {"braid_1": (4, 0, 0), "braid_2": (14, 0, 2)}),
                     (0.45, {"braid_1": (10, 0, -8), "braid_2": (8, 0, -10)}), (0.675, {"braid_1": (4, 0, 0), "braid_2": (14, 0, -2)})),
        "footbridge": once(0.95, (0.0, {"braid_1": (4, 0, 0)}), (0.16, {"braid_1": (-20, 0, 0), "braid_2": (-10, 0, 0)}),
                           (0.3, {"braid_1": (14, 0, 0), "braid_2": (18, 0, 0)}), (0.6, {"braid_1": (-8, 0, 0), "braid_2": (10, 0, 0)}), (0.95, {"braid_1": (4, 0, 0)})),
        "trampoline": once(0.8, (0.0, {"braid_1": (4, 0, 0)}), (0.14, {"braid_1": (8, 0, 20), "braid_2": (4, 0, 14)}),
                           (0.3, {"braid_1": (14, 0, -24), "braid_2": (10, 0, -20)}), (0.8, {"braid_1": (4, 0, 0)})),
    }
    clips_ = {name: layered(body[name], face[name], braid[name]) for name in body}
    # For the portrait: the face of each clip on a body that stands still
    for name in body:
        still = clip(body[name]["duration"], (0.0, stand))
        still["once"] = body[name].get("once", False)
        clips_[name + "_face"] = layered(still, face[name], braid["idle"])
    return clips_


def make_birgit():
    """Birgit the Builder: a sturdy woman in an orange hi-vis vest with silver stripes over a rolled-up work shirt,
    cargo trousers with knee pads, steel-toed boots, a big yellow hard hat, a thick ginger braid down her back, freckles
    and a confident set to her mouth. A heavy tool belt with a tape measure, a pencil behind her ear, and a big framing
    hammer in her right fist, its head as big as her hand. Rigged like the Butcher, with clips for standing, walking,
    slamming down her hammer to raise a footbridge and tossing out a trampoline, written as models/birgit.glb too"""
    from anatomy import human_joints, human_body, make_rig, grip_point, skin_paint, L
    from rig import write_glb
    m = Model("birgit", size=1024, light=0.5, ao=1.3, detail=0.07)
    J = human_joints()
    m.rig = make_rig(J)
    sk = (0.94, 0.74, 0.6)
    skin_p = skin_paint(sk)
    shirt = (0.36, 0.42, 0.52)
    vest_c = (1.0, 0.45, 0.06)
    silver = (0.86, 0.88, 0.9)
    gloves = leather((0.78, 0.62, 0.36)) + stitches((0.5, 0.36, 0.2), [0.3, 0.7]) + edges(0.2, 0.05, dark=True)
    trousers = cloth((0.3, 0.32, 0.36), folds=4) + stains((0.55, 0.5, 0.4), 0.15, 3) + stitches((0.2, 0.2, 0.24), [0.2, 0.8], axis="u")
    boots = leather((0.58, 0.4, 0.2)) + stitches((0.35, 0.22, 0.1), [0.45]) + edges(0.25, 0.06, dark=True) + stains((0.4, 0.35, 0.28), 0.15, 4)
    pads = color((0.2, 0.2, 0.22)) + edges(0.35, 0.12)
    torso = human_body(m, J, cloth(shirt, folds=4), cloth(shirt, folds=3) + bands(tuple(c * 0.8 for c in shirt), [(0.9, 1.0)]), skin_p, trousers, gloves, boots,
                       chest=1.04, hips=1.06, bust=0.6, arm=1.05, leg=1.05, cuff_p=cloth(tuple(c * 0.85 for c in shirt), folds=2), knee_p=pads)
    h, s, c, n = J["hips"], J["spine"], J["chest"], J["neck"]
    # The vest over the shirt: bright orange with two silver bands round it, a zip down the front, a pocket with a pen
    vest_p = cloth(vest_c, folds=3) + bands(silver, [(0.4, 0.47), (0.66, 0.73)]) + bands((0.25, 0.25, 0.28), [(0.495, 0.505)], axis="u") + \
        stains((0.5, 0.35, 0.2), 0.12, 3) + edges(0.2, 0.06, dark=True)
    path = [s + [0, -0.22, 0], s, c, (c + n) / 2 + [0, 0.0, -0.02], n + [0, 0.02, -0.02]]
    secs = [dict(w=0.5, d=0.36, e=2.6), dict(w=0.48, d=0.35, e=2.5), dict(w=0.62, d=0.42, e=2.7, oy=0.02), dict(w=0.62, d=0.36, e=3.0), dict(w=0.24, d=0.22, e=2.4)]
    m.add(loft(path, secs, nu=26, nv=16, caps=None).deform(bulge(c + [0.19, -0.02, 0.34], 0.22, 0.04), bulge(c + [-0.19, -0.02, 0.34], 0.22, 0.04)),
          vest_p, bones=["hips", "spine", "chest"])
    m.add(blob(c + [-0.22, 0.12, 0.43], (0.11, 0.1, 0.03), (0.4, 0.4)), cloth(tuple(v * 0.9 for v in vest_c), folds=2) + edges(0.3, 0.1, dark=True), bones="chest")
    m.add(tube([c + [-0.18, 0.18, 0.44], c + [-0.18, 0.32, 0.44]], 0.018), color((0.15, 0.3, 0.8)), bones="chest")
    # The tool belt: thick leather, a big buckle, pouches at the front and back, a tape measure on her left hip
    belt_p = leather((0.45, 0.28, 0.14)) + stitches((0.75, 0.6, 0.35), [0.25, 0.75]) + edges(0.25, 0.05, dark=True)
    m.add(torus(h + [0, 0.02, 0.0], 0.54, 0.075, sz=0.72, nu=28), belt_p, bones="hips")
    m.add(blob(h + [0, 0.03, 0.4], (0.11, 0.08, 0.04), (0.3, 0.3)), metal((0.72, 0.66, 0.4), 0.5) + edges(0.4, 0.08), bones="hips")
    pouch = leather((0.4, 0.25, 0.12)) + stitches((0.75, 0.6, 0.35), [0.85]) + edges(0.3, 0.08, dark=True)
    for x, z in ((0.38, 0.26), (-0.36, -0.28), (0.12, -0.4)):
        m.add(blob(h + [x, -0.14, z], (0.14, 0.17, 0.09), (0.4, 0.5), rot=(0, math.degrees(math.atan2(x, z)), 0)), pouch, bones="hips")
    m.add(blob(h + [0.4, -0.02, 0.3], (0.03, 0.08, 0.03), (0.5, 0.5)), wood((0.6, 0.4, 0.2)), bones="hips")
    m.add(cylinder(h + [-0.55, -0.1, 0.12], 0.13, 0.1, rot=(0, 0, 90)), color((0.98, 0.8, 0.1)) + edges(0.3, 0.05, dark=True), bones="hips")
    m.add(blob(h + [-0.6, -0.1, 0.12], (0.03, 0.06, 0.06), (0.5, 0.5)), color((0.15, 0.15, 0.15)), bones="hips")
    # A pocket on each thigh
    m.mirror(m.add(blob(J["hip_r"] + (J["knee_r"] - J["hip_r"]) * 0.45 + [0.2, 0, 0.02], (0.06, 0.15, 0.13), (0.4, 0.5)),
                   cloth((0.27, 0.29, 0.33), folds=2) + edges(0.3, 0.08, dark=True), bones="thigh_r"))
    # The head: freckles, green eyes, a determined set to the mouth
    hd = J["head"] + np.array([0, 0.28, 0.08])
    P = human_face(m, hd, sk, m.rig, S=1.0, iris=(0.3, 0.55, 0.32), brow_c=(0.65, 0.33, 0.1), lips=(0.82, 0.52, 0.46), freckles=1.0)
    ginger = (0.86, 0.45, 0.14)
    hair_p = hair(ginger) + stripes(tuple(v * 0.75 for v in ginger), 14, 0.3, axis="u")
    # Hair under the hat: round the back and the sides, and a fringe that sticks out under the brim
    m.add(ellipsoid(P(0, 0.06, -0.06), (0.4, 0.38, 0.38), vrange=(0.3, 1.0), nu=20, nv=10), hair_p, bones="head", weight=3)
    for x in (-0.2, -0.08, 0.06, 0.18):
        m.add(horn(P(x, 0.24, 0.3), (x * 0.4, -0.6, 0.6), 0.14, 0.05, curl=(0, -0.1, 0.05), tip=0.015), hair_p, bones="head")
    # The braid: thick, from under the back of the hat down between her shoulders, tied off with a band. Two bones,
    # so it swings
    top = P(0, -0.08, -0.36)
    mid = top + np.array([0, -0.42, -0.1])
    end = mid + np.array([0, -0.45, -0.02])
    m.rig.bone("braid_1", top, mid, "head")
    m.rig.bone("braid_2", mid, end, "braid_1")
    for k in range(9):
        t = k / 8
        p_ = top + (mid - top) * min(t * 2, 1) + (end - mid) * max(t * 2 - 1, 0)
        r = 0.1 - 0.035 * t
        m.add(blob(p_ + np.array([0.025 * (1 if k % 2 else -1), 0, 0]), (r, 0.075, r * 0.8), (0.7, 0.7), rot=(0, 0, 25 if k % 2 else -25)), hair_p,
              bones=["braid_1"] if t < 0.4 else (["braid_1", "braid_2"] if t < 0.6 else ["braid_2"]))
    m.add(torus(end + np.array([0, 0.05, 0]), 0.055, 0.025), color((0.15, 0.55, 0.85)), bones="braid_2")
    m.add(horn(end + np.array([0, 0.02, 0]), (0, -1, -0.1), 0.16, 0.06, curl=(0, 0, -0.05), tip=0.03), hair_p, bones="braid_2")
    # The hard hat: big, yellow, a ridge over the top, a brim that is wider at the front, a sticker on the side
    hat = color((1.0, 0.82, 0.08)) + stains((0.55, 0.45, 0.3), 0.12, 4) + edges(0.2, 0.06, dark=True)
    m.add(ellipsoid(P(0, 0.2, 0.0), (0.47, 0.4, 0.49), vrange=(0.5, 1.0), nu=26, nv=10), hat, bones="head", weight=2)
    ridge = [P(0, 0.2 + 0.41 * math.sin(a), 0.5 * math.cos(a)) for a in np.radians(np.linspace(48, 150, 8))]
    m.add(loft(ridge, [(0.03, 0.02, 2.4)] + [(0.07, 0.035, 2.4)] * 6 + [(0.03, 0.02, 2.4)], facing=(0, 1, 0), nu=12, nv=24), hat, bones="head")
    m.add(loft([P(0, 0.2, -0.1), P(0, 0.2, 0.08)], [dict(w=0.52, d=0.5, e=2.2), dict(w=0.54, d=0.6, e=2.2, oy=0.06)], facing=(0, 0, 1), nu=28, caps="flat").deform(
        squash(P(0, 0.2, 0), (0, 1, 0), 0.12)), hat, bones="head")
    # A pencil behind her right ear
    m.add(tube([P(0.36, 0.08, 0.12), P(0.42, 0.0, -0.16)], 0.018), color((0.95, 0.75, 0.15)) + bands((0.2, 0.2, 0.2), [(0.0, 0.12)]), bones="head")
    # The hammer: a long wooden handle through her right fist, and a heavy steel head with a claw at the far end
    g = grip_point(J)
    along = np.array([0.0, -0.25, 1.0])
    along /= np.linalg.norm(along)
    butt, head_at = g - along * 0.18, g + along * 1.05
    m.add(loft([butt, g, head_at], [(0.05, 0.055, 2.4), (0.045, 0.05, 2.4), (0.05, 0.05, 2.4)], nu=10, caps="round"),
          wood((0.62, 0.4, 0.2)) + bands((0.2, 0.2, 0.22), [(0.0, 0.18)]), bones="hand_r")
    up = np.array([0.0, 1.0, 0.25])
    up /= np.linalg.norm(up)
    steel = metal((0.55, 0.56, 0.6), 0.45) + edges(0.4, 0.06)
    m.add(loft([head_at - up * 0.36, head_at + up * 0.08], [(0.13, 0.13, 3.0), (0.12, 0.12, 3.0)], facing=along, nu=14, caps="flat"), steel, bones="hand_r")
    m.add(loft([head_at - up * 0.36, head_at - up * 0.48], [(0.16, 0.16, 3.0), (0.16, 0.16, 3.0)], facing=along, nu=14, caps="flat"), steel, bones="hand_r")
    for side in (1, -1):
        m.add(horn(head_at + up * 0.05 + np.array([side * 0.04, 0, 0]), up + along * 0.5, 0.32, 0.05, curl=tuple(-along * 0.35), tip=0.012, facing=(1, 0, 0)),
              steel, bones="hand_r")
    m.clips = birgit_clips()
    finish(m, "birgit")
    print(write_glb(m, fps=30))
    return m


def beam(a, b, w, d, facing=(0, 1, 0), e=6.0):
    """A beam from a to b, w by d (half sizes), squared off with soft edges"""
    return loft([a, b], [(w, d, e), (w, d, e)], facing=facing, nu=12, caps="flat")


def site_paints():
    """The paints of Birgit's builds: weathered planks, yellow steel with black hazard stripes, galvanised poles"""
    planks = wood((0.62, 0.43, 0.24), 14) + edges(0.3, 0.08, dark=True) + stains((0.38, 0.3, 0.2), 0.15, 3) + grime(0.2, 0.5)
    hazard = color((1.0, 0.78, 0.08)) + stripes((0.12, 0.12, 0.12), 10, 0.5, axis="v", angle=45) + edges(0.25, 0.08, dark=True)
    yellow = color((1.0, 0.8, 0.1)) + edges(0.3, 0.1, dark=True) + stains((0.5, 0.4, 0.3), 0.1, 4)
    pole = metal((0.66, 0.68, 0.7), 0.45) + edges(0.3, 0.08) + stains((0.45, 0.35, 0.25), 0.12, 5)
    return planks, hazard, yellow, pole


def footbridge_trestle(m, x, h, half, pole, hazard):
    """A scaffold under the edge of a deck at x: two poles from the ground to the deck at z = +-half, a cross brace
    between them, and base plates. Along the line between two lanes, where no car drives"""
    for z in (-half, half):
        m.add(cylinder((x, 0, z), 0.12, h - 0.25, caps=True), pole)
        m.add(cylinder((x, 0, z), 0.32, 0.08, caps=True), hazard)
    for z0, z1 in ((-half, half), (half, -half)):
        m.add(tube([(x, 0.4, z0), (x, h - 0.6, z1)], 0.06), pole)
    m.add(tube([(x, h - 0.45, -half), (x, h - 0.45, half)], 0.07), pole)


def make_footbridge_span():
    """A lane of Birgit's footbridge (the game repeats it across the lanes): a deck of thick planks across the way, on
    two beams, with a yellow railing on each side. 6 long (x, across the road), 4.4 deep (z), its deck at 3
    (BridgeHeight). It stands on the scaffolds of the ramps at its ends, so nothing is in the way of the cars"""
    m = Model("footbridge_span", size=1024, ground_ao=False, light=0.4, ao=0.8, detail=0.08)
    planks, hazard, yellow, pole = site_paints()
    H, L, D = 3.0, 3.0, 2.2
    for k in range(12):
        x = -L + 0.25 + k * 0.5
        lift = 0.02 * ((k * 7) % 3)
        m.add(beam((x, H - 0.08 + lift, -D + 0.05), (x, H - 0.08 + lift, D - 0.05), 0.23, 0.09, facing=(0, 1, 0)), planks, share=None)
    for z in (-D + 0.2, D - 0.2):
        m.add(beam((-L, H - 0.32, z), (L, H - 0.32, z), 0.16, 0.18, facing=(0, 1, 0)), planks)
    for z in (-D + 0.12, D - 0.12):
        for x in (-L + 0.15, 0.0):
            m.add(beam((x, H, z), (x, H + 1.25, z), 0.09, 0.09, facing=(0, 0, 1)), hazard)
        m.add(tube([(-L, H + 1.2, z), (L, H + 1.2, z)], 0.08, nu=10, caps=False), yellow)
        m.add(tube([(-L, H + 0.65, z), (L, H + 0.65, z)], 0.05, nu=8, caps=False), yellow)
    tris = m.write()
    print(f"models/footbridge_span.obj  {tris} triangles")


def make_footbridge_ramp():
    """The end of Birgit's footbridge: a ramp of planks with cleats to step on, from the deck (x = 0, at 3) down to the
    ground 2.5 further (x = 2.5, RampLength), with a sloping railing and the scaffold under the deck's edge"""
    m = Model("footbridge_ramp", size=1024, ground_ao=False, light=0.4, ao=0.8, detail=0.08)
    planks, hazard, yellow, pole = site_paints()
    H, R, D = 3.0, 2.5, 2.2
    slope = math.atan2(H, R)
    length = math.hypot(H, R)
    for k in range(9):
        t = (k + 0.5) / 9
        x, y = R * t, H * (1 - t)
        m.add(beam((x, y - 0.08, -D + 0.05), (x, y - 0.08, D - 0.05), 0.17, 0.08, facing=(math.sin(slope), math.cos(slope), 0)), planks)
        m.add(beam((x + 0.05, y + 0.02, -D + 0.3), (x + 0.05, y + 0.02, D - 0.3), 0.035, 0.04, facing=(0, 1, 0)), planks)
    for z in (-D + 0.2, D - 0.2):
        m.add(beam((0, H - 0.3, z), (R, -0.05, z), 0.16, 0.16, facing=(math.sin(slope), math.cos(slope), 0)), planks)
    for z in (-D + 0.12, D - 0.12):
        for t in (0.02, 0.5, 0.98):
            x, y = R * t, H * (1 - t)
            m.add(beam((x, y, z), (x, y + 1.25, z), 0.09, 0.09, facing=(0, 0, 1)), hazard)
        m.add(tube([(0, H + 1.2, z), (R, 1.2, z)], 0.08, nu=10, caps=False), yellow)
        m.add(tube([(0, H + 0.65, z), (R, 0.65, z)], 0.05, nu=8, caps=False), yellow)
    footbridge_trestle(m, 0.0, H, D - 0.2, pole, hazard)
    # Sandbags at its foot, holding it down
    for z in (-D + 0.5, D - 0.5):
        m.add(blob((R + 0.25, 0.14, z), (0.32, 0.15, 0.22), (0.6, 0.6)), cloth((0.66, 0.58, 0.42), folds=3) + stitches((0.4, 0.34, 0.24), [0.5], axis="u"))
    tris = m.write()
    print(f"models/footbridge_ramp.obj  {tris} triangles")


def make_trampoline():
    """Birgit's trampoline, without its mat (make_trampoline_mat, which the game dips when it bounces someone): a ring
    of yellow steel striped with hazard black on six bent legs, and the springs from it in to the mat. TrampolineRadius
    (1.4) round, the mat at 0.62"""
    m = Model("trampoline", size=1024, ground_ao=True, light=0.4, ao=0.8, detail=0.05)
    planks, hazard, yellow, pole = site_paints()
    R, Y = 1.4, 0.62
    ring = color((1.0, 0.8, 0.1)) + bands((0.12, 0.12, 0.12), [(k / 16, k / 16 + 0.03) for k in range(16)], axis="u") + edges(0.2, 0.1, dark=True)
    m.add(torus((0, Y, 0), R, 0.1, nu=48, nv=10), ring)
    for k in range(6):
        a = k * math.pi / 3 + 0.25
        c, s_ = math.cos(a), math.sin(a)
        top = (R * c, Y - 0.04, R * s_)
        knee = (R * 1.08 * c, Y * 0.45, R * 1.08 * s_)
        foot = (R * 1.02 * c, 0.04, R * 1.02 * s_)
        m.add(tube([top, knee, foot], 0.055, nu=8), pole)
        m.add(blob(foot, (0.12, 0.04, 0.12), (0.6, 0.6)), color((0.12, 0.12, 0.13)))
    for k in range(28):
        a = k * 2 * math.pi / 28
        c, s_ = math.cos(a), math.sin(a)
        m.add(tube([(1.12 * c, Y, 1.12 * s_), (1.36 * c, Y, 1.36 * s_)], 0.025, nu=6), metal((0.75, 0.76, 0.78), 0.55),
              share=None)
    tris = m.write()
    print(f"models/trampoline.obj  {tris} triangles")


def make_trampoline_mat():
    """The mat of Birgit's trampoline: black, with an orange ring and a bullseye to land on, at y = 0.62"""
    m = Model("trampoline_mat", size=512, ground_ao=False, light=0.4, ao=0.0, detail=0.05)

    def mat(ctx):
        r = np.linalg.norm(ctx.p[..., [0, 2]], axis=-1)
        out = np.ones(ctx.shape + (3,)) * np.array([0.1, 0.1, 0.12]) * (0.9 + 0.2 * fbm(ctx.p, 6, 2, 3))[..., None]
        ring = smoothstep(0.05, 0.03, np.abs(r - 0.82)) + smoothstep(0.05, 0.03, np.abs(r - 0.4)) + smoothstep(0.14, 0.12, r)
        return _over(out, (1.0, 0.5, 0.08), np.clip(ring, 0, 1))
    m.add(lathe([(-0.04, 0.0), (-0.04, 1.12), (0.0, 1.12), (0.0, 0.0)], (0, 0.62, 0), smooth=False, nu=40), Paint(mat))
    tris = m.write()
    print(f"models/trampoline_mat.obj  {tris} triangles")


def make_bent():
    """A bus driver: a round belly in a green uniform with brass buttons, epaulettes and a tie, a peaked cap with a
    badge, grey sideburns and moustache, and a grumpy frown"""
    m = hero_model("bent")
    green = (0.16, 0.42, 0.28)
    uni = cloth(green) + rect((0.93, 0.93, 0.9), 0.46, 0.54, 0.62, 0.98) + rect((0.72, 0.14, 0.12), 0.48, 0.52, 0.48, 0.94) + \
        stitches((0.1, 0.25, 0.16), [0.12, 0.9]) + rect((0.12, 0.32, 0.2), 0.36, 0.44, 0.62, 0.72)
    for v in (0.42, 0.3, 0.18):
        uni = uni + patch((0.88, 0.72, 0.3), 0.455, v, 0.035, 0.035)
    b = person(m, STOUT, uni, cloth((0.13, 0.28, 0.18)) + stitches((0.08, 0.2, 0.12), [0.5], axis="u"), arms=cloth(green) + bands((0.88, 0.72, 0.3), [(0.05, 0.1)]),
               hair_paint=hair((0.6, 0.6, 0.62)), hair_style="short", arm_pose=("akimbo", "down"), skin_c=SKIN_RUDDY,
               eyes_kw=dict(iris=(0.4, 0.3, 0.2), lid=0.45, size=0.065), mouth_kw=dict(kind="frown"),
               brows_kw=dict(c=(0.6, 0.6, 0.62), tilt=0.5, thick=1.0), nose="big", jaw_paint=skin(SKIN_RUDDY) + mouth("frown") + stubble((0.5, 0.5, 0.52), 0.4))
    beard(m, b, hair((0.62, 0.62, 0.64)), length=0.0)
    cap(m, b, color(green) + bands((0.88, 0.72, 0.3), [(0.0, 0.18)]), color((0.1, 0.1, 0.12)), height=0.45, badge=metal((0.88, 0.72, 0.3)))
    for i, side in enumerate((1, -1)):
        sx, sy, sz = b.shoulders[i]
        m.add(blob((sx - side * 0.15, sy + 0.25, sz), (0.32, 0.05, 0.22), (0.3, 0.3)), color(green) + stripes((0.88, 0.72, 0.3), 3, 0.3, axis="u"))
    belt(m, b, leather((0.15, 0.12, 0.1)), buckle=metal((0.85, 0.85, 0.88)))
    finish(m, "bent")


def make_sigrid():
    """A witch: thin and bent, in a long ragged black dress with patches, a tall crooked hat with a wide brim, a purple
    shawl, wild grey hair, a hooked nose with a wart, and a sly, narrow-eyed look"""
    m = hero_model("sigrid")
    bd = replace(SLIM, hunch=0.3)
    green_skin = (0.72, 0.8, 0.6)
    dress = cloth((0.14, 0.12, 0.18), folds=8) + rect((0.3, 0.2, 0.35), 0.2, 0.3, 0.3, 0.45) + rect((0.25, 0.28, 0.2), 0.62, 0.7, 0.55, 0.68) + \
        stitches((0.45, 0.35, 0.5), [0.04, 0.96])
    b = person(m, bd, dress, dress, arms=dress, skirt=dress, hands=skin(green_skin), skin_c=green_skin, hair_paint=hair((0.7, 0.7, 0.68)),
               hair_style="long", nose="hook", arm_pose=("forward", "down"),
               eyes_kw=dict(iris=(0.55, 0.8, 0.15), lid=0.55, size=0.07, tilt=0.45), mouth_kw=dict(kind="smirk"),
               brows_kw=dict(c=(0.45, 0.45, 0.42), tilt=0.8, thick=0.8))
    hx, hy, hz = b.head
    m.add(sphere((hx + 0.05, hy - 0.05, hz + 0.68 * b.hs), 0.035), skin((0.55, 0.62, 0.42)))
    # Ragged hem
    for k in range(12):
        a = k * math.pi / 6
        m.add(lathe([(0, 0.12), (0.3, 0.0)], (math.sin(a) * bd.hip * 1.5, 0.68, math.cos(a) * bd.hip * 1.5 * 0.82), rot=(180, 0, 0), smooth=False, nu=6, nv=3),
              cloth((0.14, 0.12, 0.18)))
    pointy_hat(m, b, cloth((0.13, 0.11, 0.16), folds=2) + rect((0.3, 0.22, 0.32), 0.3, 0.4, 0.5, 0.6), brim=1.45, height=2.3, bend=0.5, band=cloth((0.48, 0.2, 0.55)))
    m.add(lathe([(b.sh_y - 0.35, bd.shoulder * 1.2), (b.sh_y, bd.shoulder * 1.05), (b.neck_y, bd.neck * 1.8)], (0, 0, b.lean(b.sh_y)), sz=0.85, nu=22),
          knit((0.48, 0.2, 0.55)) + bands((0.35, 0.12, 0.4), [(0.0, 0.08)]))
    finish(m, "sigrid")


def make_tobias():
    """A tourist: a pink flowered shirt, khaki shorts with big pockets, socks in sandals, a sun hat, sunglasses, a bum
    bag, a camera on its strap, sunburnt, and lost"""
    m = hero_model("tobias")
    bd = replace(HERO, belly=0.5, arm=0.2, fore=0.17)
    shirt = cloth((0.95, 0.5, 0.62)) + flowers((0.98, 0.95, 0.85), (0.98, 0.7, 0.2), 0.13, 0.4) + rect((0.85, 0.42, 0.52), 0.495, 0.505, 0.0, 1.0)
    legs = skin(SKIN_RUDDY) + bands((0.8, 0.7, 0.5), [(0.55, 1.0)]) + bands(WHITE, [(0.0, 0.2)]) + rect((0.72, 0.62, 0.42), 0.15, 0.4, 0.62, 0.8)
    b = person(m, bd, shirt, legs, shoes=leather((0.5, 0.33, 0.2)) + bands(WHITE, [(0.0, 0.55)]), arms=skin(SKIN_RUDDY) + bands((0.95, 0.5, 0.62), [(0.62, 1.0)]),
               skin_c=SKIN_RUDDY, arm_pose=("forward", "down"), eyes_kw=dict(iris=(0.3, 0.5, 0.8), lid=0.2, size=0.075),
               mouth_kw=dict(kind="pout"), brows_kw=dict(c=(0.6, 0.45, 0.25), tilt=-0.6, thick=0.5), nose="round", boots=False)
    glasses(m, b, sun=True)
    hx, hy, hz = b.head
    hs = b.hs
    hat = cloth((0.9, 0.84, 0.6), folds=10) + bands((0.35, 0.55, 0.8), [(0.05, 0.25)])
    m.add(lathe([(0, 0.0), (0.0, 1.0 * hs), (0.08, 0.92 * hs), (0.12, 0.6 * hs), (0.45 * hs, 0.58 * hs), (0.55 * hs, 0.0)], (hx, b.top - 0.32 * hs, hz), nu=22), hat)
    belt(m, b, color((0.2, 0.5, 0.75)), y=b.hip_y + 0.12)
    m.add(blob((0.3, b.hip_y + 0.05, bd.waist * bd.depth * 1.5 + 0.2), (0.32, 0.2, 0.15), (0.5, 0.5)), color((0.2, 0.5, 0.75)) + stitches((0.1, 0.3, 0.5), [0.6]))
    rx, ry, rz = b.right
    m.add(blob((rx - 0.25, ry + 0.15, rz + 0.25), (0.36, 0.23, 0.19), (0.3, 0.3)), color((0.14, 0.14, 0.16)) + bands((0.6, 0.6, 0.62), [(0.75, 0.85)]))
    m.add(cylinder((rx - 0.25, ry + 0.12, rz + 0.42), 0.15, 0.28, rot=(90, 0, 0)), metal((0.3, 0.3, 0.33)))
    m.add(cylinder((rx - 0.25, ry + 0.12, rz + 0.69), 0.11, 0.02, rot=(90, 0, 0)), glass((0.3, 0.4, 0.55)))
    m.add(tube([(-0.5, b.sh_y + 0.1, 0.35), (0, b.chest_y - 0.1, 0.62), (rx - 0.35, ry + 0.3, rz + 0.2)], 0.035), color((0.14, 0.14, 0.16)))
    finish(m, "tobias")


def make_mads():
    """A skater on his board: lanky, a baggy orange hoodie with a pocket and strings, wide grey jeans with a torn knee,
    a cap on backwards, and a bored, half-lidded look"""
    m = hero_model("mads")
    bd = replace(SLIM, hunch=0.15, shoulder=0.72, chest=0.64, waist=0.55, hip=0.52, arm=0.19, fore=0.17, thigh=0.25, calf=0.22, foot=1.05)
    hoodie = cloth((0.95, 0.42, 0.12), folds=7) + rect((0.85, 0.36, 0.1), 0.38, 0.62, 0.15, 0.35) + stitches((0.6, 0.25, 0.05), [0.12, 0.35]) + \
        patch((0.15, 0.15, 0.16), 0.5, 0.68, 0.11, 0.11)
    jeans = cloth((0.5, 0.52, 0.56), folds=7) + patch((0.86, 0.84, 0.8), 0.5, 0.45, 0.06, 0.05) + stitches((0.75, 0.6, 0.3), [0.5], axis="u")
    b = person(m, bd, hoodie, jeans, shoes=color((0.14, 0.14, 0.16)) + bands(WHITE, [(0.0, 0.3)]) + stitches(WHITE, [0.7]), sole=(0.9, 0.9, 0.88),
               arms=cloth((0.95, 0.42, 0.12)) + bands((0.85, 0.36, 0.1), [(0.0, 0.12)]), hair_paint=hair((0.2, 0.14, 0.1)), hair_style="short",
               eyes_kw=dict(iris=(0.35, 0.25, 0.15), lid=0.6, size=0.07, look=(0.4, 0)), mouth_kw=dict(kind="line"),
               brows_kw=dict(c=(0.2, 0.14, 0.1), tilt=0.1, thick=0.6), nose="round", arm_pose=("out", "out"))
    cap(m, b, color((0.15, 0.38, 0.72)) + stitches((0.1, 0.25, 0.5), [0.3]), back=True)
    m.add(ellipsoid((0, b.sh_y + 0.05, b.lean(b.sh_y) - 0.5), (0.55, 0.3, 0.3)), cloth((0.88, 0.36, 0.1)))
    for side in (1, -1):
        m.add(tube([(side * 0.15, b.neck_y - 0.1, 0.42), (side * 0.18, b.chest_y, 0.5)], 0.025), color(WHITE))
    for s in m.surfaces:
        s.t = s.t + [0, 0.34, 0]
    board = wood((0.82, 0.62, 0.34), 18) + bands((0.15, 0.55, 0.85), [(0.2, 0.8)], axis="v") + edges(0.2, 0.05, dark=True)
    m.add(blob((0, 0.25, 0.1), (0.55, 0.06, 1.45), (0.2, 0.6)), board)
    for z in (-0.85, 1.05):
        m.add(blob((0, 0.15, z), (0.42, 0.04, 0.08), (0.3, 0.3)), metal((0.7, 0.7, 0.72)))
        for x in (0.35, -0.35):
            m.add(cylinder((x, 0.11, z), 0.11, 0.16, rot=(0, 0, 90 if x > 0 else -90)), color((0.98, 0.88, 0.45)))
    finish(m, "mads")


def make_ditte():
    """A paramedic: a green and yellow uniform with reflective stripes, a white cross, a radio on her shoulder, a
    medical bag, a ponytail and a calm, focused look"""
    m = hero_model("ditte")
    uni = (cloth((0.14, 0.52, 0.34)) + bands((0.98, 0.86, 0.14), [(0.4, 0.62)]) + bands((0.86, 0.88, 0.9), [(0.48, 0.54)])
           + rect((0.96, 0.96, 0.96), 0.42, 0.58, 0.72, 0.78) + rect((0.96, 0.96, 0.96), 0.47, 0.53, 0.66, 0.84) + stitches((0.08, 0.3, 0.2), [0.38, 0.64]))
    b = person(m, ATHLETE, uni, cloth((0.14, 0.38, 0.26)) + bands((0.86, 0.88, 0.9), [(0.35, 0.42)]),
               arms=cloth((0.14, 0.52, 0.34)) + bands((0.86, 0.88, 0.9), [(0.3, 0.38)]), hands=color((0.3, 0.45, 0.8)),
               hair_paint=hair((0.3, 0.2, 0.12)), hair_style="ponytail", arm_pose=("down", "out"),
               eyes_kw=dict(iris=(0.3, 0.5, 0.35), lid=0.35, size=0.07), mouth_kw=dict(kind="line"), brows_kw=dict(c=(0.3, 0.2, 0.12), tilt=0.3))
    sx, sy, sz = b.shoulders[1]
    m.add(blob((sx + 0.35, sy - 0.05, sz + 0.35), (0.12, 0.22, 0.08), (0.4, 0.4)), color((0.14, 0.14, 0.16)) + rect((0.3, 0.3, 0.32), 0.3, 0.7, 0.55, 0.8))
    m.add(tube([(sx + 0.38, sy + 0.17, sz + 0.35), (sx + 0.38, sy + 0.42, sz + 0.35)], 0.025), color((0.14, 0.14, 0.16)))
    belt(m, b, color((0.15, 0.15, 0.17)), buckle=metal((0.7, 0.7, 0.72)))
    lx, ly, lz = b.left
    for f in box_faces((lx, ly - 0.35, lz + 0.05), (0.7, 0.55, 0.45)):
        m.add(f, color((0.85, 0.15, 0.12)) + edges(0.2, 0.05, dark=True) + patch((0.96, 0.96, 0.96), 0.5, 0.5, 0.1, 0.1))
    finish(m, "ditte")


def box_faces(center, size):
    from sculpt import box
    return box(center, size)


def make_gudrun():
    """A grandmother: small and bent over, a long flowered dress, a knitted cardigan and shawl, grey hair in a bun,
    round glasses, a disapproving frown, her cane, and a ball of yarn with needles"""
    m = hero_model("gudrun")
    dress = cloth((0.5, 0.34, 0.55), folds=7) + flowers((0.95, 0.85, 0.9), (0.9, 0.7, 0.3), 0.09, 0.4)
    cardigan = knit((0.78, 0.55, 0.6)) + stitches((0.5, 0.3, 0.35), [0.1, 0.9])
    for v in (0.62, 0.48, 0.34):
        cardigan = cardigan + patch((0.95, 0.9, 0.8), 0.46, v, 0.03, 0.03)
    b = person(m, OLD, cardigan + rect((0.5, 0.34, 0.55), 0.47, 0.53, 0.0, 1.0), dress, arms=cardigan, skirt=dress, hair_paint=hair((0.84, 0.84, 0.87)),
               hair_style="bun", skin_c=SKIN_PALE, arm_pose=("out", "forward"),
               eyes_kw=dict(iris=(0.4, 0.55, 0.75), lid=0.45, size=0.06), mouth_kw=dict(kind="frown", width=0.13),
               brows_kw=dict(c=(0.72, 0.72, 0.74), tilt=0.6, thick=0.6), nose="long", boots=False)
    glasses(m, b, r=0.13)
    m.add(lathe([(b.sh_y - 0.4, OLD.shoulder * 1.3), (b.sh_y, OLD.shoulder * 1.1), (b.neck_y, OLD.neck * 1.8)], (0, 0, b.lean(b.sh_y)), sz=0.85, nu=22),
          knit((0.55, 0.3, 0.45)) + bands((0.85, 0.75, 0.55), [(0.0, 0.08)]))
    hx, hy, hz = b.right
    m.add(tube([(hx, hy, hz), (hx + 0.05, hy * 0.5, hz + 0.05), (hx + 0.08, 0.05, hz + 0.1)], 0.06), wood((0.33, 0.19, 0.1)))
    m.add(tube([(hx, hy, hz), (hx, hy + 0.25, hz - 0.1), (hx - 0.12, hy + 0.2, hz - 0.35)], 0.07), wood((0.33, 0.19, 0.1)))
    lx, ly, lz = b.left
    m.add(sphere((lx, ly + 0.1, lz + 0.22), 0.3), knit((0.82, 0.25, 0.4)))
    for k in (1, -1):
        m.add(tube([(lx - 0.25, ly + 0.25 + k * 0.05, lz + 0.1), (lx + 0.35, ly + 0.05 - k * 0.05, lz + 0.45)], 0.025), metal((0.8, 0.8, 0.82)))
    finish(m, "gudrun")


def horseshoe_magnet(m, grip, forward, up, size, bones):
    """A big horseshoe magnet held by its bend at grip: two arms that reach forward along forward, red, banded, with
    bright steel poles at their ends. up is across the bend (the arms are side by side along it)"""
    f = np.asarray(forward, float)
    f /= np.linalg.norm(f)
    u = np.asarray(up, float)
    u = u - f * (u @ f)
    u /= np.linalg.norm(u)
    side = np.cross(f, u)
    r = 0.42 * size
    path = []
    for k in range(13):
        a = math.pi * k / 12
        path.append(grip + u * (r * math.cos(a)) - f * (r * math.sin(a)) + f * r * 0.15)
    a0, a1 = path[0], path[-1]
    path = [a0 + f * 0.9 * size] + path + [a1 + f * 0.9 * size]
    red = color((0.86, 0.1, 0.08)) + edges(0.35, 0.06, dark=True) + stains((0.4, 0.05, 0.05), 0.1, 4)
    w = 0.16 * size
    m.add(loft(path[::-1], [(w, w * 1.1, 5.0)] * len(path), facing=side, nu=12, nv=40, caps="flat"), red, bones=bones)
    steel = metal((0.86, 0.88, 0.92), 0.65) + edges(0.4, 0.05)
    for end in (a0, a1):
        tip = end + f * 0.9 * size
        m.add(loft([tip - f * 0.02, tip + f * 0.28 * size], [(w * 1.05, w * 1.15, 5.0)] * 2, facing=side, nu=12, caps="flat"), steel, bones=bones)
        m.add(loft([tip - f * 0.32 * size, tip - f * 0.26 * size], [(w * 1.08, w * 1.18, 5.0)] * 2, facing=side, nu=12, caps="flat"),
              color((0.95, 0.93, 0.88)) + edges(0.3, 0.1, dark=True), bones=bones)
    return path


def magnus_clips():
    """Magnus: he stands with his chest out and now and then flexes his free arm, walks heavily, holds his magnet up
    over his head and turns it round to repel the cars, and thrusts it at an enemy and heaves back to pull him in"""
    from rig import clip, layered
    from anatomy import once
    stand = {"upper_r": (-8, 0, 10), "fore_r": (-30, 0, 0), "upper_l": (0, 0, -12), "fore_l": (-18, 0, 0), "chest": (-4, 0, 0), "head": (2, 0, 0),
             "hips": {"rot": (0, 0, 0), "pos": (0, 0, 0)}}
    breathe = {"upper_r": (-10, 0, 12), "fore_r": (-34, 0, 0), "upper_l": (0, 0, -15), "fore_l": (-22, 0, 0), "chest": (-8, 0, 0), "head": (0, 0, 0),
               "hips": {"rot": (0, 0, 0), "pos": (0, 0.03, 0)}}
    flex = {"upper_r": (-8, 0, 10), "fore_r": (-30, 0, 0), "upper_l": (-10, 0, -85), "fore_l": (-120, 0, 0), "hand_l": (0, 0, -20), "chest": (-8, 12, 0),
            "head": (0, 40, 8), "hips": {"rot": (0, 0, 0), "pos": (0, 0.02, 0)}}

    def walk(s):
        return {"thigh_r": (-24 * s, 0, 0), "thigh_l": (22 * s, 0, 0), "shin_r": (8 if s > 0 else 32, 0, 0), "shin_l": (32 if s > 0 else 8, 0, 0),
                "upper_r": (16 * s, 0, 10), "upper_l": (-20 * s, 0, -12), "fore_r": (-30, 0, 0), "fore_l": (-24, 0, 0),
                "spine": (2, 8 * s, 0), "chest": (-2, 6 * s, 0), "hips": {"rot": (0, -8 * s, 4 * s), "pos": (0, -0.06, 0)}, "head": (-2, -8 * s, 0)}

    def passing(s):
        return {"thigh_r": (-4 if s > 0 else 0, 0, 0), "thigh_l": (0 if s > 0 else -4, 0, 0), "shin_r": (12 if s > 0 else 40, 0, 0),
                "shin_l": (40 if s > 0 else 12, 0, 0), "upper_r": (0, 0, 10), "upper_l": (0, 0, -12), "fore_r": (-30, 0, 0), "fore_l": (-24, 0, 0),
                "spine": (2, 0, 0), "chest": (-2, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.06, 0)}, "head": (-2, 0, 0)}
    # Repel: the magnet up over his head, then turned round, poles down, with a heave of his chest
    up = {"upper_r": (-175, 0, -5), "fore_r": (-10, 0, 0), "hand_r": (0, 0, 0), "upper_l": (-10, 0, -80), "fore_l": (-115, 0, 0), "chest": (-10, 0, 0),
          "spine": (-6, 0, 0), "head": (-22, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.05, 0)}}
    turned = dict(up, hand_r=(0, 180, 0), chest=(-4, 0, 0), head=(-14, 0, 0), thigh_r=(-14, 0, 6), thigh_l=(-14, 0, -6), shin_r=(18, 0, 0), shin_l=(18, 0, 0))
    turned["hips"] = {"rot": (0, 0, 0), "pos": (0, -0.12, 0)}
    # Attract: the magnet thrust out at the enemy, his other hand on his wrist, then a heave back with his whole weight
    aim = {"upper_r": (-88, 0, -6), "fore_r": (-4, 0, 0), "hand_r": (70, 0, 0), "upper_l": (-75, 0, 30), "fore_l": (-40, 0, 0), "chest": (10, -10, 0),
           "spine": (8, -6, 0), "head": (-6, 8, 0), "thigh_r": (-30, 0, 0), "shin_r": (25, 0, 0), "thigh_l": (14, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, -0.12, 0.15)}}
    heave = {"upper_r": (-70, 0, -4), "fore_r": (-45, 0, 0), "hand_r": (95, 0, 0), "upper_l": (-60, 0, 26), "fore_l": (-70, 0, 0), "chest": (-14, 8, 0), "spine": (-10, 4, 0),
             "head": (6, -6, 0), "thigh_r": (-10, 0, 0), "thigh_l": (-30, 0, 0), "shin_l": (30, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, -0.08, -0.2)}}
    body = {
        "idle": clip(3.2, (0.0, stand), (0.8, breathe), (1.4, stand), (1.8, flex), (2.4, flex), (2.9, stand)),
        "walk": clip(1.0, (0.0, walk(1)), (0.25, passing(1)), (0.5, walk(-1)), (0.75, passing(-1))),
        "repel": once(1.0, (0.0, stand), (0.18, up), (0.32, up), (0.5, turned), (0.75, turned), (1.0, stand)),
        "attract": once(0.9, (0.0, stand), (0.12, aim), (0.3, aim), (0.55, heave), (0.9, stand)),
    }
    calm, blink = face_pose(jaw=1, brow=4, lid=6), face_pose(jaw=1, brow=4, lid=85)
    proud = face_pose(jaw=6, brow=-10, lid=0, lift=0.02)
    strain, roar = face_pose(jaw=4, brow=24, lid=30, drop=0.01), face_pose(jaw=26, brow=16, lid=0)
    face = {
        "idle": clip(3.2, (0.0, calm), (1.0, calm), (1.05, blink), (1.12, calm), (1.8, proud), (2.4, proud), (2.9, calm)),
        "walk": clip(1.0, (0.0, face_pose(jaw=2, brow=6, lid=8)), (0.5, face_pose(jaw=3, brow=6, lid=8))),
        "repel": once(1.0, (0.0, calm), (0.18, strain), (0.5, roar), (0.75, roar), (1.0, proud)),
        "attract": once(0.9, (0.0, calm), (0.12, strain), (0.3, strain), (0.55, roar), (0.9, proud)),
    }
    clips_ = {name: layered(body[name], face[name]) for name in body}
    for name in body:
        still = clip(body[name]["duration"], (0.0, stand))
        still["once"] = body[name].get("once", False)
        clips_[name + "_face"] = layered(still, face[name])
    return clips_


def make_magnus():
    """Magnus the Magnet, a circus strongman: a barrel chest and huge bare arms, a striped red and black singlet with
    straps, black tights, laced wrestling boots, iron bracers, a belt with a big gold buckle, slicked black hair with a
    parting, a curled handlebar moustache, a cleft chin and a confident stare, and a giant red horseshoe magnet with
    steel poles in his right fist. Rigged like the Butcher, with clips for standing (and flexing), walking, turning his
    magnet round to repel the cars, and thrusting it at an enemy to pull him in, written as models/magnus.glb too"""
    from anatomy import joints, make_rig, skin_paint, brute_body, L
    from rig import write_glb
    m = Model("magnus", size=1024, light=0.5, ao=1.3, detail=0.08)
    J = joints(hips=(0, 1.5, 0), spine=(0, 2.05, 0.06), chest=(0, 2.8, 0.12), neck=(0, 3.45, 0.22), head=(0, 3.65, 0.3),
               shoulder_r=(1.3, 3.2, 0.15), elbow_r=(1.7, 2.35, 0.2), wrist_r=(1.75, 1.55, 0.5), hand_end_r=(1.75, 1.15, 0.7),
               hip_r=(0.55, 1.42, 0.0), knee_r=(0.66, 0.85, 0.12), ankle_r=(0.72, 0.3, 0.0), toe_r=(0.75, 0.1, 0.6))
    m.rig = make_rig(J)
    sk = (0.86, 0.66, 0.5)
    skin_p = skin_paint(sk)
    red, black = (0.78, 0.1, 0.1), (0.12, 0.11, 0.13)

    top_y = J["chest"][1] + 0.05

    def singlet(ctx):
        # Red and black bands up to the middle of his chest, and two black straps over his shoulders
        base = skin_p(ctx)
        y, x = ctx.p[..., 1], ctx.p[..., 0]
        band = np.floor((y - J["hips"][1]) / 0.28) % 2 == 0
        cloth_c = np.where(band[..., None], rgb(red), rgb(black)) * (0.92 + 0.12 * fbm(ctx.p, 3, 2, 5))[..., None]
        strap = smoothstep(0.1, 0.07, np.abs(np.abs(x) - 0.55))
        below = smoothstep(top_y + 0.03, top_y - 0.03, y)
        cloth_c = np.where((y > top_y)[..., None], rgb(black) * 0.95, cloth_c)
        covered = np.maximum(below, strap)
        return base * (1 - covered)[..., None] + cloth_c * covered[..., None]
    tights = cloth(black, folds=4) + stitches((0.3, 0.3, 0.32), [0.5], axis="u")
    boots = leather((0.3, 0.2, 0.14)) + stripes((0.85, 0.82, 0.75), 8, 0.12, axis="v") + edges(0.3, 0.06, dark=True)
    brute_body(m, J, skin_p, tights, boots, gut=0.5, shoulders=0.92, forearm=1.1, legs_thick=1.0, chest_p=Paint(singlet), arms_p=skin_p, hand_p=skin_p)
    h, c = J["hips"], J["chest"]
    # The belt with its gold buckle, and iron bracers on his forearms
    m.add(torus(h + [0, 0.3, 0.1], 0.98, 0.12, sz=0.78, nu=30), leather((0.28, 0.17, 0.1)) + stitches((0.6, 0.45, 0.25), [0.3, 0.7]), bones=["hips", "spine"])
    m.add(blob(h + [0, 0.3, 0.86], (0.3, 0.2, 0.06), (0.4, 0.4)), metal((0.92, 0.72, 0.25), 0.6) + edges(0.4, 0.1), bones="hips")
    e, w = J["elbow_r"], J["wrist_r"]
    iron = metal((0.5, 0.52, 0.56), 0.45) + edges(0.35, 0.08) + stains((0.45, 0.32, 0.2), 0.15, 5)
    m.mirror(m.add(loft([e + (w - e) * 0.42, e + (w - e) * 0.88], [(0.36, 0.32, 3.0), (0.3, 0.26, 3.0)], facing=(0, 0, 1), nu=14, caps="flat"), iron, bones=["fore_r"]))
    for k in range(3):
        p_ = e + (w - e) * (0.5 + 0.15 * k)
        m.mirror(m.add(sphere(p_ + [0.33, 0, 0], 0.035, nu=6, nv=4), metal((0.75, 0.76, 0.8), 0.6), bones=["fore_r"]))
    # The head: his face, with a strong jaw and a cleft chin
    S = 1.4
    hd = J["head"] + np.array([0, 0.42, 0.22])
    P = human_face(m, hd, sk, m.rig, S=S, iris=(0.35, 0.42, 0.55), brow_c=(0.1, 0.08, 0.07), lips=(0.75, 0.5, 0.44), freckles=0.0, nose="long")
    hair_c = (0.08, 0.07, 0.08)
    hair_p = hair(hair_c) + stripes((0.25, 0.25, 0.3), 16, 0.15, axis="u")
    # Slicked back hair, shining, with a parting on his left
    m.add(ellipsoid(P(0, 0.06, -0.04), (0.39 * S, 0.43 * S, 0.4 * S), vrange=(0.45, 1.0), rot=(-12, 0, 0), nu=24, nv=12),
          hair_p + rect((0.5, 0.5, 0.55), 0.38, 0.4, 0.6, 1.0), bones="head", weight=3)
    # Thick black brows, over the thin ones of the face
    m.mirror(m.add(loft([P(0.05, 0.135, 0.37), P(0.15, 0.16, 0.36), P(0.24, 0.13, 0.31)], [(0.025 * S, 0.03 * S, 2.2), (0.03 * S, 0.035 * S, 2.2), (0.018 * S, 0.02 * S, 2.2)],
                        facing=(0, 0.3, 1), nu=10, nv=10), color(hair_c), bones="brow_r"))
    # The handlebar moustache: thick under the nose, curled up at the ends
    tash = hair(hair_c) + stripes((0.2, 0.2, 0.22), 6, 0.2, axis="v")
    m.mirror(m.add(loft([P(0.0, -0.12, 0.43), P(0.1, -0.135, 0.4), P(0.2, -0.13, 0.32), P(0.26, -0.06, 0.28), P(0.24, 0.0, 0.3)],
                        [(0.04 * S, 0.035 * S, 2.2), (0.045 * S, 0.04 * S, 2.2), (0.035 * S, 0.03 * S, 2.2), (0.022 * S, 0.02 * S, 2.2), (0.012 * S, 0.012 * S, 2.2)],
                        facing=(0, 0, 1), nu=10, nv=20),
                   tash, bones="head"))
    # A square chin with a cleft
    m.add(blob(P(0, -0.33, 0.24), (0.2 * S, 0.09 * S, 0.12 * S), (0.6, 0.7)), skin_p + rect(tuple(v * 0.8 for v in sk), 0.495, 0.505, 0.4, 0.9), bones="jaw", weight=3)
    # The magnet, in his right fist, its poles forward
    w_, he = J["wrist_r"], J["hand_end_r"]
    d = (he - w_) / np.linalg.norm(he - w_)
    grip = w_ + d * 0.3 + np.array([-0.02, 0, 0.05])
    horseshoe_magnet(m, grip, forward=(0, -0.15, 1), up=d, size=1.5, bones="hand_r")
    m.clips = magnus_clips()
    finish(m, "magnus")
    print(write_glb(m, fps=30))
    return m


def make_stormy():
    """A weather girl: a fitted blue blazer and skirt, a red umbrella over her, long blonde hair, a determined look,
    and a little storm cloud by her shoulder with a bolt in it"""
    m = hero_model("stormy")
    blazer = cloth((0.2, 0.36, 0.76)) + rect((0.94, 0.94, 0.96), 0.45, 0.55, 0.7, 1.0) + stitches((0.1, 0.2, 0.45), [0.3, 0.95]) + \
        patch((0.85, 0.7, 0.3), 0.455, 0.5, 0.03, 0.03)
    b = person(m, ATHLETE, blazer, skin(SKIN), arms=cloth((0.2, 0.36, 0.76)) + bands((0.94, 0.94, 0.96), [(0.0, 0.07)]),
               skirt=cloth((0.16, 0.3, 0.64)) + stitches((0.1, 0.2, 0.45), [0.12]), shoes=color((0.72, 0.1, 0.12)), boots=False,
               hair_paint=hair((0.95, 0.76, 0.32)), hair_style="long", arm_pose=("up", "out"),
               eyes_kw=dict(iris=(0.3, 0.5, 0.85), lid=0.35, size=0.07), mouth_kw=dict(kind="line"), brows_kw=dict(c=(0.7, 0.5, 0.2), tilt=0.45), nose="round")
    hx, hy, hz = b.right
    m.add(cylinder((hx, hy - 0.4, hz), 0.05, 2.0), metal((0.3, 0.3, 0.32)))
    m.add(tube([(hx, hy - 0.4, hz), (hx, hy - 0.6, hz), (hx + 0.15, hy - 0.65, hz)], 0.05), wood((0.4, 0.25, 0.12)))
    m.add(lathe([(0, 1.65), (0.25, 1.5), (0.6, 1.05), (0.8, 0.4), (0.85, 0.0)], (hx, hy + 1.0, hz), nu=16),
          color((0.85, 0.11, 0.11)) + stripes((0.97, 0.95, 0.94), 4, 0.5, axis="u"))
    for k in range(8):
        a = k * math.pi / 4
        m.add(tube([(hx, hy + 1.85, hz), (hx + math.cos(a) * 1.6, hy + 1.0, hz + math.sin(a) * 1.6)], 0.02, caps=False), metal((0.3, 0.3, 0.32)))
    cloud = color((0.42, 0.45, 0.55))
    for dx, dy, r in ((0, 0, 0.32), (0.3, 0.08, 0.26), (-0.28, 0.05, 0.25), (0.05, 0.22, 0.25)):
        m.add(sphere((-1.4 + dx, 3.5 + dy, 0.0), r), cloud)
    m.add(lathe([(0, 0.0), (0.0, 0.08), (-0.5, 0.0)], (-1.4, 3.35, 0.0), rot=(0, 0, 20), smooth=False, nu=6), color((1.0, 0.9, 0.3)))
    finish(m, "stormy")


def make_hugo():
    """A hypnotist: tall and thin in a black tailcoat with a purple waistcoat and a cravat, a top hat, slicked hair, a
    pointed goatee and moustache, an intense stare, and a pocket watch swinging on its chain"""
    m = hero_model("hugo")
    coat = cloth((0.11, 0.1, 0.13)) + rect((0.42, 0.18, 0.52), 0.4, 0.6, 0.3, 0.95) + rect((0.96, 0.96, 0.96), 0.47, 0.53, 0.75, 1.0) + \
        stitches((0.3, 0.3, 0.35), [0.05, 0.95])
    for v in (0.7, 0.58, 0.46):
        coat = coat + patch((0.85, 0.7, 0.3), 0.5, v, 0.025, 0.025)
    b = person(m, SLIM, coat, cloth((0.13, 0.12, 0.15)) + stripes((0.25, 0.25, 0.3), 8, 0.1, axis="u"), arms=cloth((0.11, 0.1, 0.13)),
               hands=color((0.95, 0.95, 0.93)), skin_c=SKIN_PALE, hair_paint=hair((0.1, 0.09, 0.1)), hair_style="slick", arm_pose=("forward", "akimbo"),
               eyes_kw=dict(iris=(0.6, 0.15, 0.75), lid=0.25, size=0.075, socket=0.55, tilt=0.3), mouth_kw=dict(kind="smirk"),
               brows_kw=dict(c=(0.1, 0.09, 0.1), tilt=0.9, thick=0.7), nose="long")
    jx, jy, jz = b.jaw_c
    rx, ry, rz = b.jaw_r
    m.add(tube([(jx, jy - ry * 0.6, jz + rz * 0.8), (jx, jy - ry * 1.4, jz + rz * 0.85)], [0.11, 0.02]), hair((0.1, 0.09, 0.1)))
    for side in (1, -1):
        m.add(tube([(jx, jy + ry * 0.3, jz + rz), (jx + side * rx * 0.6, jy + ry * 0.25, jz + rz * 0.85), (jx + side * rx * 0.95, jy + ry * 0.55, jz + rz * 0.65)],
                   [0.05, 0.04, 0.01]), hair((0.1, 0.09, 0.1)))
    top_hat(m, b, color((0.11, 0.1, 0.13)), band=(0.45, 0.18, 0.55), height=1.05)
    for ur in ((0.0, 0.22), (0.78, 1.0)):
        m.add(lathe([(0.9, 0.0), (1.0, SLIM.hip * 1.2), (b.hip_y + 0.2, SLIM.hip * 1.2)], sz=0.8, urange=ur), cloth((0.11, 0.1, 0.13)))
    m.add(ellipsoid((0, b.neck_y - 0.1, b.lean(b.neck_y) + 0.32), (0.18, 0.14, 0.08)), cloth((0.96, 0.96, 0.96)))
    rx_, ry_, rz_ = b.right
    m.add(tube([(rx_, ry_ - 0.1, rz_ + 0.1), (rx_ + 0.05, ry_ - 0.7, rz_ + 0.25)], 0.02), metal((0.85, 0.7, 0.3)))
    m.add(cylinder((rx_ + 0.05, ry_ - 0.9, rz_ + 0.18), 0.22, 0.07, rot=(90, 0, 0)), metal((0.85, 0.7, 0.3), 0.5) + patch((0.95, 0.93, 0.85), 0.5, 0.5, 0.15, 0.15))
    finish(m, "hugo")


def make_twins():
    """Tim and Tom: two scrawny boys side by side in matching striped shirts and shorts, scuffed knees, narrowed
    eyes, up to something"""
    m = hero_model("twins")
    shirt = cloth((0.98, 0.76, 0.15)) + stripes((0.2, 0.42, 0.78), 6, 0.3) + stitches((0.6, 0.45, 0.1), [0.06])
    legs = skin(SKIN) + bands((0.25, 0.35, 0.6), [(0.6, 1.0)]) + patch((0.8, 0.5, 0.45), 0.5, 0.45, 0.06, 0.05) + bands(WHITE, [(0.0, 0.15)])
    for x, look, tilt in ((0.78, (-0.5, 0), 0.4), (-0.78, (0.5, 0), 0.6)):
        person(m, KID, shirt, legs, x=x, hair_paint=hair((0.58, 0.36, 0.17)), hair_style="short", arm_pose="out",
               eyes_kw=dict(iris=(0.35, 0.55, 0.3), lid=0.5, size=0.075, look=look), mouth_kw=dict(kind="smirk"),
               brows_kw=dict(c=(0.45, 0.28, 0.12), tilt=tilt, thick=0.6), nose="round", shoes=color((0.25, 0.25, 0.28)) + bands(WHITE, [(0.0, 0.3)]))
    finish(m, "twins")


def make_kenji():
    """A ninja: lean, all in dark wrapped cloth with bindings on his arms and legs, a mask with only his narrow eyes
    showing, a red sash and headband with long tails, and a sword on his back"""
    m = hero_model("kenji")
    black = cloth((0.12, 0.12, 0.15), folds=4)
    wraps = cloth((0.12, 0.12, 0.15)) + stripes((0.2, 0.2, 0.24), 10, 0.15, axis="v", angle=25)
    head = cloth((0.12, 0.12, 0.15)) + rect(SKIN, 0.38, 0.62, 0.44, 0.6) + eyes(iris=(0.25, 0.18, 0.12), lid=0.5, size=0.07, tilt=0.4, socket=0.3, v=0.52)
    b = person(m, ATHLETE, black + bands((0.72, 0.1, 0.1), [(0.0, 0.12)]), wraps, shoes=cloth((0.1, 0.1, 0.12)), arms=wraps, hands=cloth((0.1, 0.1, 0.12)),
               head_paint=head, jaw_paint=cloth((0.12, 0.12, 0.15)) + stitches((0.2, 0.2, 0.24), [0.6]), nose=None, ears=False,
               brows_kw=dict(c=(0.12, 0.12, 0.15), tilt=0.9, thick=0.0), arm_pose=("ready", "down"), cuffs=cloth((0.2, 0.2, 0.24)))
    hx, hy, hz = b.head
    hs = b.hs
    red = cloth((0.75, 0.1, 0.1))
    m.add(torus((hx, hy + 0.25 * hs, hz), 0.6 * hs, 0.08, sz=1.0), red)
    m.add(tube([(hx, hy + 0.3 * hs, hz - 0.6 * hs), (hx + 0.3, hy + 0.15, hz - 1.0), (hx + 0.55, hy - 0.3, hz - 1.3)], 0.07, flat=0.35), red)
    m.add(tube([(hx, hy + 0.3 * hs, hz - 0.6 * hs), (hx - 0.15, hy + 0.05, hz - 1.0), (hx - 0.25, hy - 0.45, hz - 1.15)], 0.07, flat=0.35), red)
    belt(m, b, red, buckle=red)
    m.add(tube([(0.3, b.waist_y - 0.1, 0.45), (0.45, b.waist_y - 0.6, 0.5)], 0.07, flat=0.35), red)
    bracers(m, b, cloth((0.2, 0.2, 0.24)) + stripes((0.3, 0.3, 0.34), 5, 0.2, axis="v", angle=30), length=0.6)
    m.add(tube([(0.85, 0.9, -0.62), (-0.75, 3.35, -0.62)], 0.08), color((0.15, 0.12, 0.1)) + bands((0.72, 0.1, 0.1), [(0.82, 1.0)]))
    m.add(cylinder((-0.55, 3.05, -0.62), 0.18, 0.04, rot=(0, 0, 35)), metal((0.75, 0.65, 0.35)))
    m.add(tube([(-0.6, 3.1, -0.62), (-0.98, 3.7, -0.62)], 0.06), color((0.72, 0.1, 0.1)) + stripes((0.1, 0.1, 0.1), 6, 0.3, axis="v", angle=45))
    finish(m, "kenji")


def make_ivar():
    """A berserker: enormous and bare-chested with blue war paint and scars, a wolf pelt over his head and shoulders,
    a fur kilt, iron bracers, a wild red beard, gritted teeth, and a great axe raised"""
    m = hero_model("ivar")
    bd = replace(BRUTE, hunch=0.35, belly=0.0, head=0.84)
    chest = skin(SKIN_TAN) + stripes((0.15, 0.3, 0.72), 3, 0.12, axis="u", angle=40) + patch((0.65, 0.42, 0.35), 0.62, 0.55, 0.03, 0.2) + \
        bands((0.32, 0.2, 0.1), [(0.0, 0.08)])
    b = person(m, bd, chest, fur((0.42, 0.32, 0.22)), shoes=fur((0.34, 0.25, 0.17)), arms=skin(SKIN_TAN) + stripes((0.15, 0.3, 0.72), 2, 0.1, axis="u"),
               skin_c=SKIN_TAN, pecs=True, arm_pose=("up", "ready"),
               eyes_kw=dict(iris=(0.75, 0.3, 0.1), lid=0.35, size=0.065, socket=0.6), brows_kw=dict(c=(0.7, 0.22, 0.06), tilt=1.0, thick=1.0),
               jaw_paint=skin(SKIN_TAN) + mouth("snarl", width=0.17), nose="broad", cuffs=fur((0.5, 0.42, 0.3)),
               head_paint=skin(SKIN_TAN) + eyes(iris=(0.75, 0.3, 0.1), lid=0.35, size=0.065, socket=0.6) + stripes((0.15, 0.3, 0.72), 1, 0.08, axis="v"))
    beard(m, b, hair((0.72, 0.22, 0.07)), length=0.75, width=1.15, moustache=True)
    hx, hy, hz = b.head
    hs = b.hs
    pelt = fur((0.52, 0.5, 0.48))
    m.add(ellipsoid((hx, hy + 0.1 * hs, hz - 0.08), (0.7 * hs, 0.72 * hs, 0.7 * hs), vrange=(0.45, 1.0), nu=20, nv=8), pelt)
    m.add(ellipsoid((hx, hy + 0.48 * hs, hz + 0.42 * hs), (0.32 * hs, 0.22 * hs, 0.4 * hs)), pelt + patch((0.1, 0.1, 0.1), 0.5, 0.75, 0.06, 0.05))
    for side in (1, -1):
        m.add(lathe([(0, 0.13 * hs), (0.3 * hs, 0.0)], (hx + side * 0.35 * hs, hy + 0.68 * hs, hz - 0.1), smooth=False, nu=6), pelt)
        m.add(lathe([(0, 0.05), (0.18, 0.0)], (hx + side * 0.12 * hs, hy + 0.4 * hs, hz + 0.78 * hs), rot=(180, 0, 0), smooth=False, nu=6), color((0.95, 0.92, 0.85)))
    m.add(lathe([(b.sh_y - 0.25, bd.shoulder * 1.0), (b.sh_y + 0.05, bd.shoulder * 1.12), (b.neck_y, bd.neck * 1.6)], (0, 0, b.lean(b.sh_y)), sz=0.82,
                urange=(0.62, 1.0)), pelt)
    m.add(lathe([(b.sh_y - 0.25, bd.shoulder * 1.0), (b.sh_y + 0.05, bd.shoulder * 1.12), (b.neck_y, bd.neck * 1.6)], (0, 0, b.lean(b.sh_y)), sz=0.82,
                urange=(0.0, 0.38)), pelt)
    m.add(lathe([(b.hip_y - 0.7, bd.hip * 1.35), (b.hip_y, bd.hip * 1.12), (b.waist_y, bd.waist * 1.02)], sz=0.85, nu=24), fur((0.4, 0.3, 0.2)))
    belt(m, b, leather((0.3, 0.18, 0.1)) + stitches((0.6, 0.45, 0.25), [0.5]), buckle=metal((0.6, 0.6, 0.62)) + edges(0.3, 0.03))
    bracers(m, b, metal((0.5, 0.5, 0.54), 0.4) + spots((0.75, 0.75, 0.78), 0.03, 0.35, 3))
    rx, ry, rz = b.right
    m.add(tube([(rx, ry - 1.1, rz), (rx, ry + 1.2, rz + 0.05)], 0.09), wood((0.38, 0.24, 0.12)) + bands((0.28, 0.16, 0.08), [(0.35, 0.5)]))
    for side in (1, -1):
        m.add(lathe([(0, 0.06), (0.4, 0.14), (0.75, 0.62), (0.78, 0.0)], (rx + side * 0.08, ry + 0.95, rz + 0.05), rot=(0, 0, -90 * side), sz=0.14, nu=14),
              metal((0.68, 0.7, 0.74), 0.5) + edges(0.4, 0.06) + stains((0.45, 0.06, 0.05), 0.15, 5))
    finish(m, "ivar")


HEROES = {name[5:]: f for name, f in dict(globals()).items() if name.startswith("make_") and callable(f)}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for name in args or HEROES:
        HEROES[name]()
    if "--preview" in sys.argv:
        from sculpt import preview
        out = os.path.join(os.environ.get("PREVIEW_DIR", "."), "heroes.png")
        paths = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "models", n + ".obj") for n in (args or HEROES)]
        print(preview(paths, out))
