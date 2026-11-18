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
from anatomy import (joints, make_rig, L, clips, MENACE, skin_paint, brute_body, wrap_apron, hand, chain)

OUT = os.environ.get("PREVIEW_DIR", ".")
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fonts")


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
