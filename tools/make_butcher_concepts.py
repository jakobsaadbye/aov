#!/usr/bin/env python3
"""
Concepts for the Butcher: three directions, each a rigged model with clips, drawn as a sheet of sketches (front,
three quarters, side, back and an action pose) and a painted render, to pick a style from before it is applied to all
the heroes. The models go to the scratchpad, not to data/.

    PREVIEW_DIR=... python3 tools/make_butcher_concepts.py          all three
    PREVIEW_DIR=... python3 tools/make_butcher_concepts.py a        only one
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from sculpt import (Model, Paint, blob, bands, bulge, cloth, color, cylinder, edges, ellipsoid, fbm, fur, hair, horn,
                    leather, loft, lumps, metal, painted, patch, push, rect, scales, skin, smoothstep, sphere, spots,
                    squash, stains, stitches, stripes, torus, tube, wood, _ellipse, _over, _varied, rgb)
from rig import Rig, clip, render, skinned_mesh, write_glb
from sculpt import mirror_bone_name
from make_heroes import eyes, mouth, brows, stubble

OUT = os.environ.get("PREVIEW_DIR", ".")
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fonts")


#
# A brute's skeleton and body, from where its joints are
#


def joints(**over):
    j = dict(hips=(0, 1.45, 0), spine=(0, 2.0, 0.08), chest=(0, 2.75, 0.2), neck=(0, 3.45, 0.5), head=(0, 3.7, 0.72),
             shoulder_r=(1.3, 3.25, 0.3), elbow_r=(1.72, 2.35, 0.5), wrist_r=(1.62, 1.55, 0.98), hand_end_r=(1.6, 1.15, 1.25),
             hip_r=(0.55, 1.38, 0.0), knee_r=(0.68, 0.82, 0.18), ankle_r=(0.74, 0.3, 0.02), toe_r=(0.76, 0.1, 0.62))
    j.update(over)
    return {k: np.asarray(v, dtype=float) for k, v in j.items()}


def make_rig(J):
    r = Rig()
    up = np.array([0, 0.4, 0])
    r.bone("hips", J["hips"], J["spine"])
    r.bone("spine", J["spine"], J["chest"], "hips")
    r.bone("chest", J["chest"], J["neck"], "spine")
    r.bone("neck", J["neck"], J["head"], "chest")
    r.bone("head", J["head"], J["head"] + up, "neck")
    r.bone("upper_r", J["shoulder_r"], J["elbow_r"], "chest")
    r.bone("fore_r", J["elbow_r"], J["wrist_r"], "upper_r")
    r.bone("hand_r", J["wrist_r"], J["hand_end_r"], "fore_r")
    r.bone("thigh_r", J["hip_r"], J["knee_r"], "hips")
    r.bone("shin_r", J["knee_r"], J["ankle_r"], "thigh_r")
    r.bone("foot_r", J["ankle_r"], J["toe_r"], "shin_r")
    r.mirror()
    return r


def L(p):
    """A point on the left side, mirrored from the right"""
    return np.array([-p[0], p[1], p[2]])


def clips():
    def walk(phase):
        s = 1 if phase == 0 else -1
        return {"thigh_r": (-26 * s, 0, 0), "thigh_l": (22 * s, 0, 0), "shin_r": (8 if s > 0 else 34, 0, 0),
                "shin_l": (34 if s > 0 else 8, 0, 0), "upper_r": (20 * s, 0, 6), "upper_l": (-20 * s, 0, -6),
                "fore_r": (-25, 0, 0), "fore_l": (-25, 0, 0), "spine": (6, 6 * s, 0), "chest": (4, 4 * s, 0),
                "hips": {"rot": (0, -6 * s, 3 * s), "pos": (0, -0.06, 0)}, "head": (-8, -6 * s, 0)}

    def passing(s):
        return {"thigh_r": (-4 if s > 0 else 0, 0, 0), "thigh_l": (0 if s > 0 else -4, 0, 0),
                "shin_r": (12 if s > 0 else 38, 0, 0), "shin_l": (38 if s > 0 else 12, 0, 0),
                "upper_r": (0, 0, 6), "upper_l": (0, 0, -6), "fore_r": (-25, 0, 0), "fore_l": (-25, 0, 0),
                "spine": (6, 0, 0), "chest": (4, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.06, 0)}, "head": (-8, 0, 0)}

    idle0 = {"chest": (0, 0, 0), "upper_r": (0, 0, 4), "upper_l": (0, 0, -4), "fore_r": (-20, 0, 0), "fore_l": (-20, 0, 0),
             "hips": {"rot": (0, 0, 0), "pos": (0, 0, 0)}}
    idle1 = {"chest": (-3, 0, 0), "spine": (-1, 0, 0), "upper_r": (0, 0, 7), "upper_l": (0, 0, -7), "fore_r": (-24, 0, 0),
             "fore_l": (-24, 0, 0), "head": (3, 0, 0), "hips": {"rot": (0, 0, 0), "pos": (0, 0.03, 0)}}
    windup = {"upper_r": (-150, 0, 25), "fore_r": (-50, 0, 0), "chest": (-10, -20, 0), "spine": (-6, -10, 0),
              "upper_l": (-30, 0, -15), "fore_l": (-40, 0, 0), "head": (-12, 10, 0), "thigh_r": (-10, 0, 0), "shin_r": (10, 0, 0)}
    slam = {"upper_r": (-55, 0, 8), "fore_r": (-15, 0, 0), "chest": (18, 18, 0), "spine": (10, 8, 0), "upper_l": (10, 0, -10),
            "fore_l": (-30, 0, 0), "head": (5, -5, 0), "thigh_r": (-25, 0, 0), "shin_r": (20, 0, 0), "thigh_l": (15, 0, 0),
            "hips": {"rot": (0, 0, 0), "pos": (0, -0.12, 0.1)}}
    return {"idle": clip(2.0, (0.0, idle0), (1.0, idle1)), "walk": clip(1.0, (0.0, walk(0)), (0.25, passing(1)), (0.5, walk(1)), (0.75, passing(-1))),
            "cast": clip(0.9, (0.0, idle0), (0.35, windup), (0.55, slam), (0.8, idle0))}


MENACE = {"upper_r": (-115, 0, 22), "fore_r": (-70, 0, 0), "chest": (6, -14, 0), "spine": (4, -6, 0), "head": (-14, 8, 0),
          "upper_l": (-35, 0, -18), "fore_l": (-35, 0, 0), "thigh_r": (-14, 0, 0), "shin_r": (12, 0, 0), "thigh_l": (12, 0, 0),
          "shin_l": (6, 0, 0)}


def skin_paint(c, veins=None, scars=0.0, warts=0.0):
    def fn(ctx):
        base = _varied(ctx, c, 0.07, 2.5)
        mottle = (fbm(ctx.p, 1.2, 3, 41) - 0.5) * 0.18
        out = base * (1 + mottle)[..., None]
        out += smoothstep(0.55, 0.85, fbm(ctx.p, 2.0, 3, 9))[..., None] * np.array([0.06, -0.01, -0.02])
        if veins is not None:
            v = np.abs(fbm(ctx.p * np.array([1, 3, 1]), 3.0, 3, 77) - 0.5) < 0.012
            out = _over(out, rgb(veins), v.astype(float) * 0.5)
        if scars:
            sc = np.abs(fbm(ctx.p * np.array([3, 1, 3]), 1.5, 2, 13) - 0.5) < 0.006 * scars
            out = _over(out, out * 0.6 + np.array([0.25, 0.1, 0.1]), sc.astype(float))
        if warts:
            w = smoothstep(0.78, 0.82, fbm(ctx.p, 12, 1, 51)) * warts
            out = out * (1 - 0.25 * w)[..., None] + w[..., None] * np.array([0.05, 0.05, 0.0])
        return out
    return Paint(fn)


def brute_body(m, J, skin_p, legs_p, boot_p, gut=1.0, shoulders=1.0, forearm=1.0, legs_thick=1.0, chest_p=None,
               arms_p=None, hand_p=None, bones=True, right_hand=True):
    """The body of a brute: a huge wedge of a torso with a gut, a hump of muscle over the shoulders, massive forearms,
    big hands, short thick legs and big feet"""
    chest_p = chest_p or skin_p
    arms_p = arms_p or skin_p
    hand_p = hand_p or skin_p
    lump = lumps(0.025, 2.2, 3)
    # Torso: pelvis, gut, a broad chest wedge, up into a hunched neck. Squarish sections, a groove down the chest
    sp = [J["hips"] + [0, -0.2, -0.05], J["spine"] + [0, 0, 0.05], J["chest"], (J["chest"] + J["neck"]) / 2 + [0, 0, 0.05], J["neck"] + [0, 0.1, -0.05]]
    sec = [dict(w=0.78, d=0.58, e=2.8), dict(w=0.92 * (0.85 + 0.15 * gut), d=0.8 * (0.75 + 0.35 * gut), e=2.4, oy=0.18 * gut),
           dict(w=1.22 * shoulders, d=0.82, e=3.0, oy=0.08 * gut), dict(w=1.08 * shoulders, d=0.66, e=3.2), dict(w=0.42, d=0.4, e=2.4)]
    c = J["chest"]
    m.add(loft(sp, sec, nu=28, nv=26).deform(
        lump, bulge(c + [0.45, 0.25, 0.75], 0.55, 0.12), bulge(c + [-0.45, 0.25, 0.75], 0.55, 0.12), push(c + [0, 0.2, 0.9], 0.3, (0, 0, -0.1)),
        push(c + [0, -0.45, 0.75], 0.35, (0, -0.05, 0.05))), chest_p, bones=["hips", "spine", "chest"])
    # The hump of muscle between the neck and the shoulders
    sh, shl = J["shoulder_r"], L(J["shoulder_r"])
    top = (J["neck"] + J["chest"]) / 2 + [0, 0.62, -0.12]
    m.add(loft([shl + [0.15, 0.08, -0.08], top, sh + [-0.15, 0.08, -0.08]], [(0.3 * shoulders, 0.48, 3.0), (0.44 * shoulders, 0.56, 2.6), (0.3 * shoulders, 0.48, 3.0)],
               nu=18, nv=16).deform(lump), skin_p, bones=["chest"])
    # Arms: a deltoid cap, an upper arm with the bicep forward and the triceps back, a knotted elbow, and a forearm that
    # flares out below the elbow and narrows hard to the wrist
    e, w = J["elbow_r"], J["wrist_r"]
    path = [sh + [0.05, 0.05, 0], sh + (e - sh) * 0.3, sh + (e - sh) * 0.62, e, e + (w - e) * 0.3, e + (w - e) * 0.65, w]
    secs = [dict(w=0.44 * shoulders, d=0.46, e=2.6), dict(w=0.38, d=0.42, e=2.6, oy=0.04), dict(w=0.34, d=0.4, e=2.6, oy=0.07),
            dict(w=0.27, d=0.3, e=3.0), dict(w=0.42 * forearm, d=0.36 * forearm, e=2.8, ox=0.04), dict(w=0.36 * forearm, d=0.3 * forearm, e=3.0),
            dict(w=0.24, d=0.2, e=3.2)]
    arm = m.add(loft(path, secs, facing=(0.2, 0, 1), nu=16, nv=28).deform(lump), arms_p, bones=["upper_r", "fore_r"])
    m.mirror(arm)
    m.mirror(m.add(loft([sh + [-0.25, 0.25, 0], sh + [0.12, 0.22, 0.02], sh + [0.35, -0.1, 0.02]], [(0.32, 0.4, 2.6), (0.42, 0.48, 2.4), (0.3, 0.38, 2.6)],
                        facing=(0, 0, 1), nu=14, nv=12).deform(lump), skin_p, bones=["upper_r"]))
    # Hands: a broad palm, four thick fingers curled round a grip, a thumb
    hand(m, J, hand_p, right=right_hand)
    # Legs and feet
    hp, kn, an = J["hip_r"], J["knee_r"], J["ankle_r"]
    leg = m.add(loft([hp + [0, 0.1, 0], (hp + kn) / 2, kn, (kn + an) / 2 + [0, 0, -0.04], an],
                     [(0.5 * legs_thick, 0.52 * legs_thick, 2.3), (0.46 * legs_thick, 0.48, 2.3), (0.34, 0.36, 2.3), (0.4 * legs_thick, 0.4, 2.3), (0.28, 0.28, 2.3)],
                     nu=14, nv=18).deform(lump), legs_p, bones=["thigh_r", "shin_r"])
    m.mirror(leg)
    toe = J["toe_r"]
    foot = m.add(loft([an + [0, 0.05, -0.25], an + [0, -0.05, 0.1], toe + [0, 0.05, 0.05]], [(0.32, 0.26, 3.0), (0.36, 0.24, 3.2), (0.3, 0.16, 2.6)],
                      facing=(0, 1, 0), nu=14, nv=12), boot_p, bones=["foot_r"])
    m.mirror(foot)
    sole = m.add(loft([an + [0, -0.17, -0.3], toe + [0, -0.07, 0.12]], [(0.36, 0.06, 4), (0.32, 0.06, 4)], facing=(0, 1, 0), nu=12, nv=6, caps="flat"),
                 leather((0.15, 0.11, 0.09)), bones=["foot_r"])
    m.mirror(sole)


def wrap_apron(m, J, paint, gut=1.0, low=1.0, wide=1.0, bones=("spine", "hips")):
    """An apron that wraps round the front of the body and the gut, from the chest down to below the knees"""
    sp = [J["hips"] + [0, -low, 0.1], J["hips"] + [0, -0.3, 0.12], J["spine"] + [0, 0, 0.12], J["chest"] + [0, 0.25, 0.05]]
    secs = [dict(w=1.0 * wide, d=0.9 + 0.1 * gut, e=2.4, oy=0.22 * gut), dict(w=0.96 * wide, d=0.92 + 0.12 * gut, e=2.4, oy=0.26 * gut),
            dict(w=1.02 * wide, d=0.96 + 0.16 * gut, e=2.4, oy=0.22 * gut), dict(w=1.28 * wide, d=0.92, e=3.0, oy=0.08 * gut)]
    return m.add(loft(sp, secs, nu=16, nv=18, caps=None, urange=(0.3, 0.7)).deform(lumps(0.02, 3, 6)), paint, bones=list(bones))


def hand(m, J, paint, grip=True, right=True):
    """A big fist, on both sides (or only the left, right=False)"""
    w, he = J["wrist_r"], J["hand_end_r"]
    d = (he - w) / np.linalg.norm(he - w)
    palm = w + d * 0.22

    def both(srf):
        if right:
            m.mirror(srf)
        else:
            # Only the left one: the surface itself moved over to the other side
            srf.F = np.diag([-1.0, 1.0, 1.0]) @ srf.F
            srf.orient = -srf.orient
            srf.bones = [mirror_bone_name(b) for b in srf.bones]
    h = m.add(blob(palm, (0.26, 0.3, 0.24), (0.6, 0.6)).deform(lumps(0.015, 4, 7)), paint, bones=["hand_r"])
    both(h)
    side = np.array([0, 0, 1.0])
    for k in range(4):
        base = palm + d * 0.2 + side * (k - 1.5) * 0.12 + [0.08, 0, 0]
        f = m.add(loft([base, base + d * 0.12 + [0.12, 0, 0], base + d * 0.12 + [0.02, -0.1, 0], base + [-0.08, -0.12, 0]],
                       [(0.075, 0.075, 2.2), (0.07, 0.07, 2.2), (0.065, 0.065, 2.2), (0.06, 0.06, 2.2)], nu=8, nv=8), paint, bones=["hand_r"])
        both(f)
    t = m.add(loft([palm + [-0.12, 0.05, 0.15], palm + [-0.08, -0.08, 0.3], palm + [0.0, -0.18, 0.32]], [(0.08, 0.08, 2.2), (0.075, 0.075, 2.2), (0.06, 0.06, 2.2)],
                   nu=8, nv=8), paint, bones=["hand_r"])
    both(t)


def chain(m, a, b, links=8, r=0.07, paint=None, bones=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    paint = paint or metal((0.5, 0.5, 0.52), 0.4)
    first = None
    for k in range(links):
        p = a + (b - a) * (k + 0.5) / links
        rot = (90, 0, 0) if k % 2 else (0, 0, 90)
        s = m.add(torus(p, r, r * 0.3, rot=rot, nu=10, nv=6), paint, bones=bones, share=first)
        first = first or s


#
# Option A: the Slaughterhouse Brute
#


def option_a():
    """A huge hunched half-ogre: a small bald head sunk between his shoulders with a topknot, an underbite with two
    tusks, a pig skull on his shoulder, a leather apron plated with iron, a cleaver like a door, a hook on a chain
    wrapped round his arm"""
    m = Model("butcher_a", size=1024, light=0.5, ao=1.6, detail=0.09)
    J = joints()
    m.rig = make_rig(J)
    sk = (0.56, 0.44, 0.36)
    skin_p = skin_paint(sk, veins=(0.36, 0.26, 0.26), scars=1.0)
    trousers = cloth((0.32, 0.25, 0.2), folds=6) + stitches((0.2, 0.15, 0.12), [0.3, 0.7], axis="u") + stains((0.4, 0.06, 0.05), 0.12, 3)
    boots = leather((0.3, 0.2, 0.13)) + stitches((0.55, 0.42, 0.25), [0.4]) + edges(0.2, 0.05)
    brute_body(m, J, skin_p, trousers, boots, gut=1.1, chest_p=skin_p + bands((0.32, 0.25, 0.2), [(0.0, 0.2)]))
    # Head: small and boxy, pushed forward, with a heavy brow, an underbite and tusks
    hd = J["head"]
    m.add(blob(hd + [0, 0.12, -0.04], (0.4, 0.42, 0.42), (0.75, 0.8)).deform(lumps(0.02, 3, 5)),
          skin_paint(sk, scars=2.0) + eyes(v=0.5, spacing=0.15, size=0.06, iris=(0.95, 0.72, 0.15), lid=0.4, tilt=0.35, socket=0.35,
                                           white=(0.85, 0.78, 0.6)), bones="head", weight=3)
    m.add(blob(hd + [0, -0.17, 0.12], (0.47, 0.27, 0.42), (0.6, 0.7)).deform(push(hd + [0, -0.25, 0.5], 0.4, (0, 0, 0.12))),
          skin_paint(sk) + mouth("grim", v=0.62, width=0.2) + stubble((0.2, 0.14, 0.12), 0.5, 0.7), bones="head", weight=3)
    m.add(blob(hd + [0, 0.27, 0.3], (0.38, 0.09, 0.14), (0.5, 0.7)), skin_paint(sk) + brows((0.3, 0.2, 0.15), 0.9, 0.15, spacing=0.16, length=0.09, v=0.62),
          bones="head", weight=2)
    m.add(blob(hd + [0, 0.05, 0.42], (0.13, 0.11, 0.1), (0.7, 0.7)), skin_paint(sk) + patch((0.22, 0.12, 0.1), 0.43, 0.3, 0.025, 0.02) + patch((0.22, 0.12, 0.1), 0.57, 0.3, 0.025, 0.02),
          bones="head")
    tusk = color((0.92, 0.88, 0.74)) + bands((0.6, 0.55, 0.42), [(0.0, 0.2)])
    for s in (1, -1):
        m.add(horn(hd + [s * 0.24, -0.08, 0.52], (s * 0.25, 1, 0.25), 0.34, 0.065, curl=(s * 0.1, 0, 0.12)), tusk, bones="head")
        m.add(horn(hd + [s * 0.38, 0.12, -0.05], (s * 1, 0.6, -0.4), 0.22, 0.08, curl=(0, 0.2, 0)), skin_paint(sk), bones="head")
    m.add(tube([hd + [0, 0.5, -0.25], hd + [0, 0.75, -0.35], hd + [0, 0.7, -0.65], hd + [0, 0.4, -0.75]], [0.1, 0.12, 0.08, 0.03]), hair((0.15, 0.12, 0.1)), bones="head")
    m.add(torus(hd + [0, 0.52, -0.27], 0.1, 0.04, rot=(70, 0, 0)), metal((0.7, 0.6, 0.3)), bones="head")
    # The apron, wrapped round the gut, with an iron plaque riveted on and a ragged hem
    apron = leather((0.42, 0.28, 0.16)) + stains((0.32, 0.05, 0.04), 0.14, 2.6) + stitches((0.6, 0.45, 0.3), [0.06, 0.94]) + edges(0.25, 0.06, dark=True)
    wrap_apron(m, J, apron, gut=1.1)
    y = J["spine"][1] + 0.05
    m.add(loft([(-0.32, y, 1.24), (0, y + 0.02, 1.3), (0.32, y, 1.24)], [(0.22, 0.03, 6), (0.24, 0.03, 6), (0.22, 0.03, 6)], nu=10, nv=8, caps="flat"),
          metal((0.48, 0.45, 0.42), 0.3) + spots((0.75, 0.72, 0.68), 0.03, 0.5, 3) + edges(0.35, 0.05) + stains((0.45, 0.25, 0.15), 0.3, 4), bones=["spine"])
    m.add(torus(J["hips"] + [0, 0.15, 0.25], 1.02, 0.1, sz=0.85), leather((0.25, 0.15, 0.1)) + stitches((0.5, 0.4, 0.25), [0.5]), bones="hips")
    m.add(blob(J["hips"] + [0, 0.15, 1.14], (0.2, 0.17, 0.06), (0.3, 0.3)), metal((0.6, 0.5, 0.3), 0.4) + edges(0.3, 0.03), bones="hips")
    # A pig skull on his left shoulder, strapped on
    s0 = L(J["shoulder_r"]) + [-0.1, 0.55, 0.05]
    bone_c = color((0.74, 0.68, 0.55)) + stains((0.4, 0.32, 0.22), 0.3, 4) + edges(0.2, 0.05, dark=True)
    m.add(blob(s0, (0.34, 0.28, 0.34), (0.7, 0.8)), bone_c + patch((0.1, 0.08, 0.08), 0.42, 0.55, 0.06, 0.06) + patch((0.1, 0.08, 0.08), 0.58, 0.55, 0.06, 0.06), bones="chest")
    m.add(blob(s0 + [0, -0.1, 0.32], (0.18, 0.14, 0.2), (0.6, 0.7)), bone_c, bones="chest")
    for s in (1, -1):
        m.add(horn(s0 + [s * 0.15, -0.2, 0.45], (s * 0.4, 1, 0.3), 0.3, 0.05, curl=(0, 0, -0.1)), tusk, bones="chest")
    m.add(tube([s0 + [0.3, -0.3, 0.3], J["chest"] + [0, 0.1, 1.0], J["shoulder_r"] + [-0.4, -0.5, 0.4]], 0.05, flat=0.4), leather((0.25, 0.15, 0.1)), bones=["chest"])
    # Wraps round the wrists, a chain wound round the right forearm
    for wr, el in ((J["wrist_r"], J["elbow_r"]),):
        d = wr - el
        for k in range(3):
            p = wr - d * (0.1 + k * 0.12)
            r = m.add(torus(p, 0.36 - k * 0.0, 0.05, rot=(55, 0, -20)), metal((0.45, 0.45, 0.48), 0.3), bones="fore_r")
    m.mirror(m.add(tube([J["wrist_r"] - (J["wrist_r"] - J["elbow_r"]) * 0.05, J["wrist_r"] - (J["wrist_r"] - J["elbow_r"]) * 0.32], [0.33, 0.38], nu=12, caps=False),
                   cloth((0.6, 0.52, 0.4)) + stripes((0.45, 0.38, 0.28), 6, 0.2, axis="v", angle=30) + stains((0.4, 0.06, 0.05), 0.2, 4), bones="fore_r"))
    # The cleaver
    gp = J["hand_end_r"] + [0.05, 0.05, 0.0]
    m.add(loft([gp + [0, -0.3, -0.1], gp + [0, 0.15, 0.05], gp + [0, 0.45, 0.15]], [(0.09, 0.09, 2), (0.08, 0.08, 2), (0.1, 0.1, 2)], nu=10),
          wood((0.35, 0.2, 0.1)) + stripes((0.2, 0.12, 0.08), 6, 0.3, axis="v", angle=40), bones="hand_r")
    blade = metal((0.46, 0.46, 0.5), 0.45) + edges(0.6, 0.07) + stains((0.36, 0.05, 0.04), 0.15, 3) + stains((0.35, 0.22, 0.12), 0.18, 5, 11)
    m.add(loft([gp + [0, 0.45, 0.15], gp + [0, 0.7, 0.9], gp + [0, 0.62, 1.7]], [dict(w=0.05, d=0.55, e=5), dict(w=0.045, d=0.75, e=6), dict(w=0.04, d=0.7, e=5)],
               facing=(0, 1, 0), nu=12, nv=10, caps="flat"), blade, bones="hand_r")
    m.add(torus(gp + [0, 1.15, 1.5], 0.1, 0.035, rot=(0, 0, 90)), metal((0.5, 0.5, 0.52)), bones="hand_r")
    # The hook on its chain in his left hand
    lh = L(J["hand_end_r"])
    chain(m, lh + [0, 0.05, 0], lh + [0, -0.75, 0.15], 7, bones=["hand_l"])
    m.add(horn(lh + [0, -0.8, 0.15], (0, -1, 0.2), 0.55, 0.07, curl=(0, 1.0, 0.7), tip=0.01), metal((0.6, 0.6, 0.62), 0.5) + stains((0.45, 0.05, 0.05), 0.3, 5), bones="hand_l")
    m.default_bones = None
    m.clips = clips()
    return m


#
# Option B: the Hooded Carver
#


def option_b():
    """A towering executioner of a butcher: a black leather hood with eye slits, long powerful arms, an apron to his
    ankles, a bandolier of cleavers across his chest, a spiked iron collar, a great cleaver-axe, hooks on a chain"""
    m = Model("butcher_b", size=1024, light=0.5, ao=1.6, detail=0.09)
    J = joints(hips=(0, 1.75, 0), spine=(0, 2.35, 0.05), chest=(0, 3.05, 0.12), neck=(0, 3.75, 0.35), head=(0, 4.0, 0.5),
               shoulder_r=(1.2, 3.55, 0.2), elbow_r=(1.6, 2.5, 0.35), wrist_r=(1.6, 1.5, 0.75), hand_end_r=(1.6, 1.08, 0.95),
               hip_r=(0.5, 1.7, 0), knee_r=(0.6, 0.98, 0.12), ankle_r=(0.66, 0.32, 0.0), toe_r=(0.68, 0.1, 0.58))
    m.rig = make_rig(J)
    sk = (0.72, 0.64, 0.6)
    skin_p = skin_paint(sk, scars=1.5)
    hide = leather((0.16, 0.13, 0.12)) + stitches((0.4, 0.32, 0.25), [0.2, 0.8])
    brute_body(m, J, skin_p, cloth((0.2, 0.18, 0.18), folds=7), leather((0.16, 0.13, 0.12)) + edges(0.2, 0.05), gut=0.6, shoulders=1.0, forearm=0.9,
               chest_p=skin_p + bands((0.2, 0.18, 0.18), [(0.0, 0.2)]), arms_p=skin_p, hand_p=leather((0.2, 0.15, 0.12)))
    hd = J["head"]
    hood = leather((0.12, 0.1, 0.1)) + stitches((0.35, 0.28, 0.22), [0.5], axis="u")

    def hood_paint(ctx):
        out = hood(ctx)
        out = eyes(v=0.5, spacing=0.14, size=0.065, iris=(0.95, 0.85, 0.5), lid=0.1, socket=0.0, white=(0.05, 0.03, 0.03), glow=None)(ctx, out)
        return out
    m.add(loft([hd + [0, -0.5, -0.05], hd + [0, -0.1, 0.0], hd + [0, 0.35, -0.08], hd + [0, 0.75, -0.3], hd + [0, 0.95, -0.6]],
               [(0.5, 0.5, 2.2), (0.44, 0.47, 2.2), (0.4, 0.42, 2.2), (0.24, 0.24, 2.2), (0.04, 0.04, 2)], nu=20, nv=18).deform(lumps(0.015, 4, 3)),
          Paint(hood_paint), bones="head", weight=3)
    m.add(blob(hd + [0, -0.38, 0.32], (0.32, 0.18, 0.2), (0.6, 0.7)), skin_paint(sk) + mouth("grit", v=0.55, width=0.15) + stubble((0.25, 0.2, 0.18), 0.6), bones="head", weight=2)
    # The spiked iron collar
    m.add(torus(J["neck"] + [0, -0.1, -0.05], 0.55, 0.12, sz=0.9), metal((0.35, 0.34, 0.36), 0.3) + edges(0.3, 0.05), bones="chest")
    for k in range(8):
        a = k * math.pi / 4
        p = J["neck"] + [math.sin(a) * 0.62, -0.1, -0.05 + math.cos(a) * 0.56]
        m.add(horn(p, (math.sin(a), 0.3, math.cos(a)), 0.22, 0.05), metal((0.55, 0.55, 0.58), 0.4), bones="chest")
    # The long apron
    apron = leather((0.55, 0.45, 0.35)) + stains((0.36, 0.04, 0.04), 0.16, 2.4) + stitches((0.3, 0.22, 0.15), [0.04, 0.96]) + edges(0.2, 0.06, dark=True)
    wrap_apron(m, J, apron, gut=0.6, low=1.45, wide=0.95)
    m.add(torus(J["hips"] + [0, 0.2, 0.1], 0.88, 0.09, sz=0.8), hide, bones="hips")
    # A bandolier of little cleavers across his chest
    a0, a1 = J["shoulder_r"] + [-0.3, 0.1, 0.55], L(J["hips"] + [0.7, 0.4, 0.9])
    m.add(tube([a0, (a0 + a1) / 2 + [0, 0, 0.35], a1], 0.07, flat=0.35), hide, bones=["chest", "spine"])
    for k in range(4):
        p = a0 + (a1 - a0) * (0.18 + k * 0.2) + [0, 0, 0.32]
        m.add(loft([p, p + [0, -0.38, 0.05]], [dict(w=0.025, d=0.16, e=5), dict(w=0.02, d=0.2, e=5)], facing=(1, 0, 0), nu=8, nv=4, caps="flat"),
              metal((0.6, 0.6, 0.62), 0.5) + edges(0.4, 0.05), bones="chest")
    # The cleaver-axe in his right hand, its head over his shoulder
    gp = J["hand_end_r"]
    haft = wood((0.3, 0.18, 0.1)) + bands((0.15, 0.12, 0.1), [(0.4, 0.55), (0.0, 0.08)])
    m.add(loft([gp + [0, -0.5, 0], gp + [0, 1.5, -0.2], gp + [0, 3.0, -0.5]], [(0.08, 0.08, 2), (0.075, 0.075, 2), (0.08, 0.08, 2)], nu=10), haft, bones="hand_r")
    blade = metal((0.55, 0.55, 0.58), 0.5) + edges(0.5, 0.1) + stains((0.5, 0.04, 0.04), 0.3, 3)
    m.add(loft([gp + [0, 2.3, -0.4], gp + [0, 2.7, 0.3], gp + [0, 2.6, 1.0]], [dict(w=0.05, d=0.5, e=5), dict(w=0.045, d=0.75, e=6), dict(w=0.04, d=0.95, e=4)],
               facing=(0, 1, 0), nu=12, nv=10, caps="flat"), blade, bones="hand_r")
    # Hooks on a chain at his left hip
    hp = L(J["hips"] + [0.75, 0.1, 0.4])
    chain(m, hp, hp + [-0.05, -0.9, 0.05], 8, bones=["hips"])
    for k, off in enumerate(((0, 0, 0), (0.15, 0.25, 0.05), (-0.12, 0.45, -0.05))):
        m.add(horn(hp + [-0.05, -0.95, 0.05] + np.array(off), (0, -1, 0.2), 0.42, 0.05, curl=(0, 0.9, 0.5), tip=0.01),
              metal((0.6, 0.6, 0.62), 0.5) + stains((0.45, 0.05, 0.05), 0.3, 5), bones="hips")
    m.clips = clips()
    return m


#
# Option C: the Marsh Monger
#


def option_c():
    """A squat swamp brute of a fishmonger-butcher: as wide as he is tall, warty olive skin, a wide frog mouth with a
    snaggletooth, long drooping ears, one eye under a patch, a crude hide apron, shell pauldrons, an iron hook for a
    right hand, a stone cleaver, eels and fish hanging from a rope belt"""
    m = Model("butcher_c", size=1024, light=0.5, ao=1.6, detail=0.09)
    J = joints(hips=(0, 1.15, 0), spine=(0, 1.75, 0.15), chest=(0, 2.4, 0.25), neck=(0, 2.95, 0.55), head=(0, 3.2, 0.8),
               shoulder_r=(1.45, 2.75, 0.3), elbow_r=(1.95, 1.8, 0.45), wrist_r=(1.95, 0.95, 0.75), hand_end_r=(1.95, 0.55, 0.95),
               hip_r=(0.65, 1.1, 0.0), knee_r=(0.85, 0.65, 0.2), ankle_r=(0.9, 0.25, 0.05), toe_r=(0.95, 0.08, 0.7))
    m.rig = make_rig(J)
    sk = (0.4, 0.44, 0.3)
    skin_p = skin_paint(sk, warts=1.0, veins=(0.3, 0.38, 0.28))
    brute_body(m, J, skin_p, cloth((0.38, 0.32, 0.22), folds=5) + stains((0.25, 0.3, 0.15), 0.25, 3), skin_p, gut=1.6, shoulders=1.1, forearm=1.15, legs_thick=1.15,
               chest_p=skin_p + bands((0.38, 0.32, 0.22), [(0.0, 0.2)]), right_hand=False)
    hd = J["head"]
    m.add(blob(hd + [0, 0.05, -0.05], (0.55, 0.38, 0.5), (0.7, 0.75)).deform(lumps(0.03, 3, 8)),
          skin_paint(sk, warts=1.2) + eyes(v=0.62, spacing=0.2, size=0.07, iris=(0.95, 0.75, 0.1), lid=0.35, tilt=-0.2, socket=0.5), bones="head", weight=3)
    m.add(blob(hd + [0, -0.2, 0.12], (0.62, 0.24, 0.5), (0.5, 0.6)).deform(push(hd + [0, -0.2, 0.6], 0.5, (0, 0, 0.08))),
          skin_paint(sk, warts=0.6) + mouth("frown", v=0.55, width=0.35), bones="head", weight=3)
    m.add(horn(hd + [0.18, -0.12, 0.6], (0.1, 1, 0.3), 0.18, 0.05, curl=(0, 0, 0.08)), color((0.85, 0.8, 0.6)), bones="head")
    for s in (1, -1):
        m.add(loft([hd + [s * 0.45, 0.12, -0.05], hd + [s * 0.85, 0.05, -0.05], hd + [s * 1.2, -0.25, -0.05]], [(0.2, 0.07, 2.4), (0.22, 0.07, 2.4), (0.06, 0.04, 2)],
                   facing=(0, 1, 0), nu=10, nv=10), skin_paint(sk, warts=0.5), bones="head")
    # The patch over one eye and its strap
    m.add(blob(hd + [-0.2, 0.15, 0.48], (0.13, 0.11, 0.05), (0.5, 0.5)), leather((0.15, 0.1, 0.08)), bones="head")
    m.add(torus(hd + [0, 0.2, -0.03], 0.56, 0.02, rot=(-25, 0, 28), sz=0.95), leather((0.15, 0.1, 0.08)), bones="head")
    # A crude hide apron and a rope belt with fish
    apron = fur((0.48, 0.4, 0.3)) + stains((0.3, 0.35, 0.18), 0.3, 2) + stains((0.45, 0.05, 0.05), 0.15, 3, 5) + stitches((0.25, 0.18, 0.12), [0.08, 0.92])
    wrap_apron(m, J, apron, gut=1.6, low=0.8, wide=1.15)
    m.add(torus(J["hips"] + [0, 0.25, 0.35], 1.25, 0.07, sz=0.85), color((0.62, 0.52, 0.32)) + stripes((0.42, 0.34, 0.2), 30, 0.4, axis="u", angle=45), bones="hips")
    for k, (x, kind) in enumerate(((1.05, "fish"), (0.75, "eel"), (-0.95, "fish"))):
        top = np.array([x * 1.15, J["hips"][1] + 0.25, 0.55 + 0.1 * abs(x)])
        if kind == "fish":
            m.add(loft([top, top + [0, -0.35, 0.05], top + [0, -0.85, 0.05], top + [0, -1.05, 0.02]], [(0.05, 0.04, 2), (0.11, 0.24, 2), (0.08, 0.2, 2), (0.03, 0.17, 1.2)],
                       facing=(0, 0, 1), nu=10, nv=10), color((0.6, 0.68, 0.72)) + scales((0.5, 0.58, 0.62), 0.05) + patch((0.1, 0.1, 0.1), 0.5, 0.9, 0.02, 0.02), bones="hips")
        else:
            m.add(tube([top, top + [0.08, -0.4, 0.1], top + [-0.05, -0.8, 0.05], top + [0.06, -1.05, 0.1]], [0.05, 0.07, 0.05, 0.02]),
                  color((0.3, 0.32, 0.22)) + stripes((0.55, 0.52, 0.35), 2, 0.3, axis="u"), bones="hips")
    # Shell pauldrons
    for i, s in enumerate((1, -1)):
        p = (J["shoulder_r"] if s > 0 else L(J["shoulder_r"])) + [s * 0.05, 0.3, 0]
        sh = m.add(ellipsoid(p, (0.62, 0.42, 0.62), vrange=(0.4, 1.0)).deform(lumps(0.03, 4, 11)),
                   color((0.72, 0.66, 0.55)) + stripes((0.55, 0.45, 0.35), 7, 0.3, axis="u") + edges(0.2, 0.08, dark=True), bones="chest" if True else None)
    # The hook for a right hand, on a wooden socket
    w, he = J["wrist_r"], J["hand_end_r"]
    m.add(loft([w + [0, 0.25, -0.05], w, w + (he - w) * 0.6], [(0.34, 0.34, 2.2), (0.3, 0.3, 2.2), (0.24, 0.24, 2.2)], nu=12, caps="flat"),
          wood((0.42, 0.28, 0.15)) + bands((0.4, 0.4, 0.42), [(0.1, 0.25), (0.75, 0.9)]), bones="fore_r")
    m.add(horn(w + (he - w) * 0.6, (0, -1, 0.2), 0.75, 0.08, curl=(0, 1.2, 0.8), tip=0.015), metal((0.45, 0.45, 0.48), 0.4) + stains((0.35, 0.25, 0.15), 0.3, 4), bones="fore_r")
    # The stone cleaver in his left hand
    gp = L(J["hand_end_r"])
    m.add(loft([gp + [0, -0.25, 0], gp + [0, 0.4, 0.05]], [(0.08, 0.08, 2), (0.08, 0.08, 2)], nu=10), wood((0.4, 0.3, 0.2)), bones="hand_l")
    m.add(loft([gp + [0, 0.4, 0.05], gp + [0, 0.6, 0.6], gp + [0, 0.45, 1.15]], [dict(w=0.09, d=0.45, e=3), dict(w=0.08, d=0.55, e=3), dict(w=0.06, d=0.42, e=2.5)],
               facing=(0, 1, 0), nu=12, nv=10, caps="flat").deform(lumps(0.03, 5, 4)),
          color((0.5, 0.5, 0.48)) + edges(0.35, 0.06) + stains((0.3, 0.32, 0.2), 0.2, 4), bones="hand_l")
    m.clips = clips()
    return m


#
# The sheets
#


def sheet(m, title, subtitle, notes):
    m.fit_height(6.4)
    m.write(OUT)
    glb = write_glb(m, OUT)
    mesh = skinned_mesh(m)
    tex = np.asarray(Image.open(os.path.join(OUT, m.name + ".png")).convert("RGB"), dtype=float) / 255
    S = 420
    views = [(0, 6, None), (35, 12, None), (90, 6, None), (180, 6, None)]
    frame = None
    tiles = []
    for yaw, pitch, pose in views:
        img, fr = render(mesh, tex, pose, S, yaw, pitch, sketch=True, background=(0.93, 0.89, 0.8), frame=None)
        tiles.append(img)
    action, _ = render(mesh, tex, MENACE, S + 160, 28, 14, sketch=True, background=(0.93, 0.89, 0.8))
    painted_img, _ = render(mesh, tex, MENACE, S + 160, 28, 14, sketch=False, background=(0.2, 0.22, 0.26))
    W = S * 4
    H = 90 + S + S + 160 + 120
    out = Image.new("RGB", (W, H), (236, 228, 208))
    d = ImageDraw.Draw(out)
    try:
        ft = ImageFont.truetype(os.path.join(FONT, "Cinzel-Bold.ttf"), 44)
        fs = ImageFont.truetype(os.path.join(FONT, "FiraSans-SemiBold.ttf"), 20)
    except OSError:
        ft = fs = ImageFont.load_default()
    d.text((24, 16), title, fill=(60, 30, 20), font=ft)
    d.text((26, 66), subtitle, fill=(90, 70, 55), font=fs)
    for i, t in enumerate(tiles):
        out.paste(t, (i * S, 90))
    for i, label in enumerate(("Front", "Three quarters", "Side", "Back")):
        d.text((i * S + 14, 96), label, fill=(120, 95, 75), font=fs)
    out.paste(action, (0, 90 + S))
    out.paste(painted_img, (S + 160, 90 + S))
    d.text((14, 96 + S), "Action pose (rigged)", fill=(120, 95, 75), font=fs)
    d.text((S + 174, 96 + S), "Painted, in the same pose", fill=(200, 190, 170), font=fs)
    x0 = 2 * (S + 160) + 20
    y = 110 + S
    for line in notes:
        d.text((x0, y), "- " + line, fill=(70, 50, 40), font=fs)
        y += 30
    path = os.path.join(OUT, f"concept_{m.name}.png")
    out.save(path)
    print(path, glb)
    return mesh, tex


def walk_gif(mesh, tex, name, clip_, frames=16, size=300):
    from rig import sample
    imgs = []
    fr = None
    for k in range(frames):
        t = clip_["duration"] * k / frames
        img, fr = render(mesh, tex, sample(clip_, t), size, 35, 12, sketch=False, background=(0.2, 0.22, 0.26), frame=fr)
        imgs.append(img)
    path = os.path.join(OUT, f"{name}.gif")
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=int(clip_["duration"] * 1000 / frames), loop=0)
    print(path)


OPTIONS = {
    "a": (option_a, "A · The Slaughterhouse Brute", "A hunched half-ogre: tusks, a pig skull pauldron, an iron-plated apron, a cleaver like a door",
          ["Hulking, low and forward-leaning", "Earthy: grey-olive skin, leather, rust", "Cleaver right, hook on a chain left",
           "Small head sunk between the shoulders", "Asymmetric: skull on one shoulder only"]),
    "b": (option_b, "B · The Hooded Carver", "A towering executioner: hood with eye slits, spiked collar, long apron, a cleaver-axe",
          ["Tall and broad, long reaching arms", "Dark: black leather, pale skin, blood red", "Great cleaver-axe over the shoulder",
           "Menace through what you don't see", "Bandolier of small cleavers, hooks at the hip"]),
    "c": (option_c, "C · The Marsh Monger", "A squat swamp brute: warty olive skin, frog mouth, an iron hook for a hand, fish on his belt",
          ["As wide as he is tall, knuckles low", "Swampy: olive, bone, wet browns", "Hook for a hand, stone cleaver",
           "Grotesque and a bit funny", "Shell pauldrons, eye patch, drooping ears"]),
}

if __name__ == "__main__":
    which = sys.argv[1:] or list(OPTIONS)
    for k in which:
        make, title, sub, notes = OPTIONS[k]
        m = make()
        mesh, tex = sheet(m, title, sub, notes)
        if "--gif" in sys.argv or True:
            walk_gif(mesh, tex, f"walk_{m.name}", m.clips["walk"])
