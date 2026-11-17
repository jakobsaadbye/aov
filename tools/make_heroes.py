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

from sculpt import (Model, Paint, blob, horn, loft, lumps, push, bands, cloth, color, cylinder, edges, ellipsoid, fbm, fur, ghostly, glass,
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
        "hook": once(0.8, (0.0, calm), (0.1, scowl), (0.24, roar), (0.5, face_pose(jaw=22, brow=22, lid=10)), (0.8, calm)),
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
    """Coarse hairs along a brow: dark, in streaks"""
    def fn(ctx, base):
        hairs = fbm(np.stack([ctx.v * 60, ctx.u * 6, ctx.u * 0], -1), 1, 2, 17)
        a = smoothstep(0.45, 0.6, hairs) * smoothstep(0.15, 0.4, ctx.u % 1.0) * smoothstep(0.85, 0.6, ctx.u % 1.0)
        return _over(base, rgb(c), a * 0.85)
    return fn


def make_butcher():
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
    swamp_face(m, J["head"] + np.array([0, 0.08, 0.18]), sk, m.rig)
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
    m.add(torus(base, 0.2, 0.07, rot=(20, 0, 0)), metal((0.42, 0.42, 0.46), 0.4), bones="fore_r", part="hook")
    m.add(horn(base, (0, -1, 0.3), 1.75, 0.17, curl=(0, 2.1, 1.4), tip=0.03), metal((0.52, 0.52, 0.56), 0.5) + edges(0.35, 0.06) +
          stains((0.42, 0.06, 0.05), 0.2, 2.5) + stains((0.35, 0.22, 0.12), 0.15, 4, 9), bones="fore_r", part="hook")
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


def make_frosty():
    """A snowman with a temper: lumpy snowballs, a coal scowl, a crooked carrot nose, a battered top hat, a long knitted
    scarf, mittens on his stick arms"""
    m = Model("frosty", size=1024, light=0.38, ao=1.0, detail=0.1)
    s = snow()
    m.add(blob((0, 1.0, 0), (1.05, 0.95, 1.0), (0.85, 0.9), nu=26, nv=14), s)
    m.add(blob((0, 2.35, 0), (0.8, 0.75, 0.76), (0.85, 0.9), nu=24, nv=12), s)
    m.add(sphere((0, 3.42, 0.02), 0.6, nu=24, nv=14), s, weight=2.5)
    coal = color((0.1, 0.1, 0.11))
    for k in range(5):
        t = (k - 2) / 2
        m.add(sphere((t * 0.25, 3.12 - 0.07 * (1 - t * t) * -1, 0.52 - 0.04 * abs(t)), 0.045), coal)
    for k, y in enumerate((2.6, 2.32, 2.04, 1.3, 0.95)):
        r = 0.76 if y > 1.8 else 1.0
        m.add(sphere((0, y, math.sqrt(max(r * r - (y - (2.35 if y > 1.8 else 1.0)) ** 2, 0)) * 0.95), 0.07), coal)
    # Coal eyes, set at a scowl
    for side in (1, -1):
        m.add(ellipsoid((side * 0.19, 3.53, 0.53), (0.1, 0.06, 0.06), rot=(0, side * 18, side * 22)), coal)
    m.add(tube([(0, 3.38, 0.5), (0.05, 3.33, 0.85), (0.12, 3.3, 1.1)], [0.11, 0.07, 0.02]), color((0.95, 0.48, 0.1)) + stripes((0.75, 0.35, 0.05), 6, 0.15, axis="v"))
    scarf = knit((0.75, 0.12, 0.12)) + stripes((0.12, 0.45, 0.22), 6, 0.4, axis="u")
    m.add(torus((0, 2.98, 0.0), 0.52, 0.14, sz=0.95), scarf)
    m.add(tube([(0.35, 2.95, 0.42), (0.5, 2.5, 0.62), (0.55, 2.0, 0.6), (0.6, 1.7, 0.55)], [0.15, 0.14, 0.13, 0.12], flat=0.45), scarf + stripes((0.95, 0.9, 0.85), 1, 0.08, axis="v"))
    b = Body()
    b.head, b.top, b.hs = (0, 3.42, 0.02), 4.0, 1.0
    top_hat(m, b, color((0.12, 0.11, 0.13)) + stains((0.3, 0.28, 0.26), 0.2, 3), band=(0.6, 0.1, 0.1), height=0.75, tilt=-8)
    stick = wood((0.38, 0.25, 0.14), 4)
    for side in (1, -1):
        m.add(tube([(side * 0.6, 2.45, 0), (side * 1.15, 2.6, 0.15), (side * 1.6, 2.5, 0.45)], [0.07, 0.06, 0.05]), stick)
        m.add(tube([(side * 1.3, 2.58, 0.25), (side * 1.45, 2.85, 0.35)], [0.035, 0.02]), stick)
        m.add(ellipsoid((side * 1.7, 2.48, 0.52), (0.18, 0.2, 0.2)), knit((0.12, 0.4, 0.2)))
        m.add(ellipsoid((side * 1.62, 2.58, 0.66), (0.07, 0.1, 0.07)), knit((0.12, 0.4, 0.2)))
    finish(m, "frosty")


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


def make_mira():
    """A timekeeper: tall and thin in a long starry robe with gold trim and wide sleeves, a pointed hat, long white hair,
    a calm, knowing look, and a staff with an hourglass on top"""
    m = hero_model("mira")
    purple = (0.38, 0.24, 0.62)
    robe = cloth(purple, folds=7) + spots((0.98, 0.88, 0.45), 0.04, 0.2, 11) + bands((0.85, 0.68, 0.28), [(0.0, 0.05)]) + stitches((0.85, 0.68, 0.28), [0.07])
    b = person(m, SLIM, robe + rect((0.85, 0.68, 0.28), 0.47, 0.53, 0.0, 1.0), robe, arms=robe, skirt=robe, hair_paint=hair((0.93, 0.93, 0.96)),
               hair_style="long", skin_c=SKIN_PALE, arm_pose=("forward", "down"),
               eyes_kw=dict(iris=(0.55, 0.3, 0.8), lid=0.5, size=0.07, tilt=0.2), mouth_kw=dict(kind="line"), brows_kw=dict(c=(0.85, 0.85, 0.9), tilt=0.1, thick=0.4),
               nose="long")
    for i, side in enumerate((1, -1)):
        w, d = b.wrists[i], b.forearm_dir[i]
        e = b.elbows[i]
        m.add(lathe([(0, SLIM.fore * 1.2), (0.55, SLIM.fore * 2.8), (0.62, 0.0)], _add(w, tuple(-c * 0.55 for c in d)), rot=_aim(d), nu=16, urange=(0, 1)),
              robe + bands((0.85, 0.68, 0.28), [(0.82, 0.92)]))
    pointy_hat(m, b, cloth(purple, folds=3) + spots((0.98, 0.88, 0.45), 0.05, 0.25, 12), brim=1.2, height=1.7, band=metal((0.85, 0.68, 0.28)))
    collar(m, b, metal((0.85, 0.68, 0.28)), t=0.06)
    hx, hy, hz = b.right
    m.add(tube([(hx, 0.05, hz), (hx + 0.03, 2.0, hz), (hx, 3.7, hz)], 0.07), wood((0.42, 0.28, 0.15)) + bands((0.85, 0.68, 0.28), [(0.55, 0.6)]))
    top = 3.7
    gold = metal((0.85, 0.68, 0.3), 0.5)
    m.add(cylinder((hx, top, hz), 0.34, 0.08), gold)
    m.add(cylinder((hx, top + 0.95, hz), 0.34, 0.08), gold)
    m.add(lathe([(0, 0.3), (0.4, 0.05), (0.45, 0.05), (0.85, 0.3)], (hx, top + 0.08, hz), smooth=True, nu=16), glass((0.55, 0.7, 0.85)))
    m.add(lathe([(0, 0.24), (0.25, 0.04), (0.28, 0.0)], (hx, top + 0.08, hz), nu=12), color((0.95, 0.8, 0.45)))
    for k in range(3):
        a = k * 2 * math.pi / 3
        m.add(cylinder((hx + math.sin(a) * 0.3, top, hz + math.cos(a) * 0.3), 0.04, 1.0), gold)
    m.add(sphere((hx, top + 1.12, hz), 0.12), color((0.6, 0.85, 1.0)))
    finish(m, "mira")


def make_karl():
    """A mechanic: stocky, in oil-stained blue overalls with straps, pockets and a rag, a red cap, a thick moustache, a
    tired squint, and a big wrench"""
    m = hero_model("karl")
    overalls = cloth((0.2, 0.34, 0.58)) + stains((0.08, 0.07, 0.07), 0.16, 2.5) + stitches((0.75, 0.6, 0.3), [0.15, 0.5]) + \
        rect((0.16, 0.28, 0.48), 0.42, 0.58, 0.55, 0.75)
    b = person(m, STOCKY, overalls, overalls, arms=cloth((0.82, 0.8, 0.76)) + stains((0.1, 0.1, 0.1), 0.2, 3) + bands((0.82, 0.8, 0.76), [(0.0, 0.1)]),
               hands=skin(SKIN) + stains((0.08, 0.07, 0.07), 0.3, 5), eyes_kw=dict(iris=(0.4, 0.3, 0.2), lid=0.55, size=0.065),
               mouth_kw=dict(kind="line"), brows_kw=dict(c=(0.3, 0.2, 0.12), tilt=0.2, thick=0.9), nose="big", arm_pose=("down", "akimbo"),
               jaw_paint=skin(SKIN) + mouth("line") + stubble((0.3, 0.22, 0.15), 0.5))
    cap(m, b, color((0.78, 0.15, 0.13)) + stains((0.1, 0.08, 0.08), 0.12, 4))
    beard(m, b, hair((0.3, 0.2, 0.12)), length=0.0)
    for side in (1, -1):
        m.add(tube([(side * 0.42, b.waist_y + 0.3, 0.5), (side * 0.42, b.chest_y + 0.2, 0.5), (side * 0.38, b.sh_y + 0.1, -0.1)], 0.08, flat=0.4),
              cloth((0.16, 0.28, 0.5)))
        m.add(sphere((side * 0.42, b.chest_y + 0.15, 0.56), 0.06), metal((0.8, 0.8, 0.82)))
    belt(m, b, leather((0.25, 0.16, 0.1)))
    m.add(tube([(0.5, b.waist_y - 0.15, 0.55), (0.6, b.waist_y - 0.55, 0.58), (0.55, b.waist_y - 0.8, 0.5)], 0.08, flat=0.3), cloth((0.85, 0.3, 0.2)) + stains((0.1, 0.1, 0.1), 0.3, 6))
    hx, hy, hz = b.right
    steel = metal((0.72, 0.74, 0.78), 0.5)
    m.add(tube([(hx, hy + 0.1, hz), (hx, hy - 1.05, hz + 0.1)], 0.09), steel)
    m.add(lathe([(0, 0.0), (0, 0.3), (0.15, 0.3), (0.15, 0.0)], (hx, hy - 1.2, hz + 0.1), rot=(90, 0, 0), smooth=False, nu=8), steel)
    m.add(lathe([(0, 0.0), (0, 0.22), (0.12, 0.22), (0.12, 0.0)], (hx, hy + 0.15, hz), rot=(90, 0, 0), smooth=False, nu=8), steel)
    finish(m, "karl")


def make_birgit():
    """A builder: an orange hi-vis vest with silver stripes over a work shirt, a yellow hard hat, a heavy tool belt with
    a hammer, a braid, work gloves, a focused look, and a plank on her shoulder"""
    m = hero_model("birgit")
    vest = cloth((0.98, 0.46, 0.08)) + bands((0.86, 0.88, 0.9), [(0.35, 0.42), (0.62, 0.69)]) + stitches((0.6, 0.3, 0.05), [0.33, 0.44, 0.6, 0.71])
    gloves = leather((0.75, 0.6, 0.35))
    b = person(m, ATHLETE, vest, cloth((0.3, 0.3, 0.34)) + stains((0.5, 0.45, 0.35), 0.15, 3), arms=cloth((0.36, 0.38, 0.44)) + bands((0.36, 0.38, 0.44), [(0.0, 0.1)]),
               hands=gloves, hair_paint=hair((0.85, 0.56, 0.22)), hair_style="short", arm_pose=("up", "down"),
               eyes_kw=dict(iris=(0.3, 0.5, 0.35), lid=0.35, size=0.07), mouth_kw=dict(kind="line"), brows_kw=dict(c=(0.6, 0.38, 0.15), tilt=0.4), nose="round",
               cuffs=leather((0.3, 0.2, 0.12)))
    hx, hy, hz = b.head
    hs = b.hs
    m.add(tube([(hx, hy, hz - 0.55 * hs), (hx, hy - 0.6 * hs, hz - 0.65 * hs), (hx, hy - 1.25 * hs, hz - 0.55 * hs)], [0.14 * hs, 0.12 * hs, 0.07 * hs]),
          hair((0.85, 0.56, 0.22)) + stripes((0.65, 0.4, 0.15), 8, 0.3, axis="v", angle=40))
    hat = color((0.98, 0.82, 0.1)) + bands((0.85, 0.68, 0.05), [(0.4, 0.45)]) + stains((0.5, 0.45, 0.35), 0.1, 4)
    m.add(ellipsoid((hx, hy + 0.15 * hs, hz), (0.68 * hs, 0.7 * hs, 0.66 * hs), vrange=(0.5, 1.0), nu=22, nv=8), hat)
    m.add(blob((hx, hy + 0.5 * hs, hz), (0.08 * hs, 0.22 * hs, 0.62 * hs), (0.4, 0.5)), hat)
    m.add(torus((hx, hy + 0.15 * hs, hz + 0.08), 0.74 * hs, 0.06 * hs, sz=1.1), hat)
    belt(m, b, leather((0.45, 0.28, 0.14)) + stitches((0.7, 0.55, 0.3), [0.3, 0.7]))
    for x in (0.42, -0.42, 0.0):
        m.add(blob((x, b.waist_y - 0.25, 0.5 if x else -0.55), (0.17, 0.2, 0.1), (0.4, 0.4)), leather((0.4, 0.25, 0.12)) + stitches((0.7, 0.55, 0.3), [0.85]))
    m.add(tube([(-0.45, b.waist_y - 0.1, 0.62), (-0.48, b.waist_y - 0.7, 0.66)], 0.05), wood((0.5, 0.32, 0.18)))
    m.add(blob((-0.48, b.waist_y - 0.08, 0.66), (0.22, 0.07, 0.07), (0.3, 0.3)), metal((0.5, 0.5, 0.55)))
    rx, ry, rz = b.right
    m.add(blob((rx - 0.1, ry + 0.05, rz - 0.4), (0.18, 0.1, 1.7), (0.1, 0.1), rot=(20, 0, 0)), wood((0.75, 0.55, 0.32), 16) + edges(0.15, 0.04, dark=True))
    finish(m, "birgit")


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


def make_magnus():
    """A strongman: a barrel chest in a striped wrestling singlet, huge bare arms with iron bracers, a handlebar
    moustache, slicked hair, a confident stare, and a giant horseshoe magnet held up in both hands"""
    m = hero_model("magnus")
    bd = replace(BRUTE, hunch=0.1, leg=1.2, belly=0.2, head=0.88)
    singlet = cloth((0.15, 0.15, 0.2)) + stripes((0.75, 0.12, 0.12), 6, 0.25) + stitches((0.5, 0.5, 0.55), [0.06, 0.94])
    b = person(m, bd, singlet, cloth((0.15, 0.15, 0.2)), arms=skin(SKIN_OLIVE), skin_c=SKIN_OLIVE, pecs=False,
               hair_paint=hair((0.1, 0.09, 0.09)), hair_style="slick", arm_pose="both_up",
               eyes_kw=dict(iris=(0.3, 0.3, 0.35), lid=0.35, size=0.065, socket=0.45), mouth_kw=dict(kind="line"),
               brows_kw=dict(c=(0.1, 0.09, 0.09), tilt=0.5, thick=1.0), nose="broad", cuffs=metal((0.6, 0.62, 0.66)))
    jx, jy, jz = b.jaw_c
    rx, ry, rz = b.jaw_r
    for side in (1, -1):
        m.add(tube([(jx, jy + ry * 0.3, jz + rz), (jx + side * rx * 0.6, jy + ry * 0.25, jz + rz * 0.9), (jx + side * rx * 1.05, jy + ry * 0.6, jz + rz * 0.7)],
                   [0.07, 0.06, 0.02]), hair((0.1, 0.09, 0.09)))
    bracers(m, b, metal((0.55, 0.57, 0.62), 0.4) + spots((0.8, 0.8, 0.82), 0.03, 0.3, 3), length=0.55)
    belt(m, b, leather((0.25, 0.15, 0.1)), buckle=metal((0.85, 0.7, 0.3)) + edges(0.3, 0.03))
    (rx_, ry_, rz_), (lx, ly, lz) = b.right, b.left
    red = color((0.82, 0.1, 0.08)) + edges(0.2, 0.05) + stains((0.4, 0.05, 0.05), 0.1, 4)
    top = ry_ + 1.1
    m.add(tube([(rx_, ry_ + 0.15, rz_), (rx_, top, rz_), (0, top + 0.4, rz_), (lx, top, lz), (lx, ly + 0.15, lz)], 0.27, nu=12, caps=False), red)
    for x, y, z in (b.right, b.left):
        m.add(cylinder((x, y - 0.35, z), 0.28, 0.5), metal((0.85, 0.86, 0.9), 0.6))
    finish(m, "magnus")


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
