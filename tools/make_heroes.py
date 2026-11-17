#!/usr/bin/env python3
"""
Writes the models of the heroes to data/models/, with tools/sculpt.py: smooth shapes with a hand-painted texture each,
in chunky proportions (big heads, hands and boots, short legs) so they read from high above.

    python3 tools/make_heroes.py                 all of them
    python3 tools/make_heroes.py karl mads       only these
    python3 tools/make_heroes.py --preview       and a picture of each in the scratchpad (PREVIEW_DIR)

Most heroes are a person() in their clothes, with what makes them that hero added: a hat, a beard, what they carry.
Each is made about 4.2 tall and then fitted to the height of the hero in src/core/heroes/.
"""

import math
import os
import sys

from sculpt import (Model, blob, stains, painted, smoothstep, bands, checks, cloth, color, cylinder, edges, ellipsoid, face, flowers, fur, ghostly,
                    glass, hair, knit, lathe, leather, metal, patch, plane, rect, skin, snow, sphere, spots, stripes,
                    tube, wood, rgb)

SKIN = (0.95, 0.74, 0.58)
SKIN_TAN = (0.82, 0.58, 0.42)
SKIN_DARK = (0.6, 0.4, 0.28)
SKIN_PALE = (0.98, 0.84, 0.74)
WHITE = (0.95, 0.94, 0.9)
BLACK = (0.12, 0.11, 0.12)
BOOT = (0.32, 0.2, 0.12)

HEIGHTS = {
    "allan": 4.2, "ghosty": 3.2, "butcher": 4.6, "frosty": 4.3, "bjorn": 4.8, "hilda": 4.4, "mira": 5.2, "karl": 4.3,
    "birgit": 4.4, "bent": 4.3, "sigrid": 5.0, "tobias": 4.2, "mads": 4.2, "ditte": 4.4, "gudrun": 4.0, "magnus": 4.4,
    "stormy": 4.4, "hugo": 5.0, "twins": 3.3, "kenji": 4.2, "ivar": 4.6,
}


class Body:
    """Where the parts of a person() are, for what is added to it"""
    pass


def person(m, top, legs, shoes=None, arms=None, hands=None, head=None, hair_paint=None, hair_style="short",
           width=1.0, belly=0.0, legs_len=1.0, x=0.0, face_kw=None, skin_c=SKIN, skirt=None, arm_pose="down",
           neck=None, nose=1.0, ears=True):
    """A chunky person standing on y = 0, looking at +z, about 4.2 tall. The paints are of its clothes. skirt is a paint
    for a skirt or a long coat, over the legs. arm_pose: down, out, forward (right hand forward), up (right hand up)"""
    b = Body()
    w = width
    shoes = shoes or leather(BOOT)
    arms = arms or top
    hands = hands or skin(skin_c)
    face_kw = face_kw or {}
    leg_top = 1.05 + 0.4 * legs_len
    b.x = x

    # Boots, big and round, toes out a little
    for side in (1, -1):
        m.add(blob((x + side * 0.4 * w, 0.2, 0.14), (0.3 * w, 0.22, 0.46), (0.55, 0.7), rot=(0, side * 8, 0)), shoes)
    # Legs
    for side in (1, -1):
        m.add(tube([(x + side * 0.38 * w, 0.3, 0.02), (x + side * 0.37 * w, (0.3 + leg_top) / 2, 0.0),
                    (x + side * 0.36 * w, leg_top, 0)], [0.23 * w, 0.26 * w, 0.32 * w], nu=12), legs, crease=0.25)
    # The torso, wider at the chest, with a belly when it has one
    torso = lathe([(leg_top - 0.25, 0.0), (leg_top - 0.22, 0.58 * w), (leg_top + 0.1, 0.68 * w, belly * 0.3),
                   (1.95, (0.66 + belly * 0.25) * w, belly * 0.4), (2.35, 0.78 * w, belly * 0.15), (2.7, 0.8 * w),
                   (2.88, 0.55 * w), (2.98, 0.25)], (x, 0, 0), sz=0.68 + belly * 0.1, nu=22, nv=16)
    b.torso = m.add(torso, top, crease=0.2)
    if skirt is not None:
        m.add(lathe([(0.75, 0.0), (0.76, 0.82 * w), (1.4, 0.72 * w), (leg_top + 0.2, 0.62 * w), (leg_top + 0.35, 0.0)],
                    (x, 0, 0), sz=0.8, nu=28), skirt, crease=0.15)
    # Neck
    m.add(cylinder((x, 2.8, 0.0), 0.24, 0.35, caps=False), neck or skin(skin_c))

    # Arms: shoulders, upper and lower arm in one tube, and big hands
    b.hands = []
    for side in (1, -1):
        sh = (x + side * 0.84 * w, 2.66, 0.0)
        pose = arm_pose if side == 1 else ("down" if arm_pose in ("forward", "up") else arm_pose)
        if pose == "both_up":
            pose = "up"
        if pose == "down":
            elbow, wrist = (x + side * 1.08 * w, 2.12, 0.04), (x + side * 1.12 * w, 1.62, 0.26)
        elif pose == "out":
            elbow, wrist = (x + side * 1.25 * w, 2.25, 0.05), (x + side * 1.5 * w, 1.85, 0.3)
        elif pose == "forward":
            elbow, wrist = (x + side * 1.1 * w, 2.2, 0.2), (x + side * 1.05 * w, 2.15, 0.85)
        else:  # up
            elbow, wrist = (x + side * 1.22 * w, 3.1, 0.1), (x + side * 1.18 * w, 3.7, 0.25)
        m.add(tube([sh, elbow, wrist], [0.25 * w, 0.21 * w, 0.18 * w], nu=12), arms, crease=0.15)
        m.add(sphere(sh, 0.3 * w), arms)
        d = [wrist[i] - elbow[i] for i in range(3)]
        n = math.sqrt(sum(c * c for c in d))
        hand = tuple(wrist[i] + d[i] / n * 0.18 for i in range(3))
        m.add(ellipsoid(hand, (0.21, 0.25, 0.23)), hands)
        m.add(ellipsoid((hand[0] - side * 0.04, hand[1] + 0.05, hand[2] + 0.17), (0.08, 0.11, 0.08)), hands)
        b.hands.append(hand)
    b.right, b.left = b.hands[0], b.hands[1]

    # The head: big, with a big nose and ears
    b.head = (x, 3.5, 0.04)
    b.head_r = (0.6, 0.64, 0.58)
    head_paint = head or (skin(skin_c) + face(**face_kw))
    b.head_surface = m.add(ellipsoid(b.head, b.head_r, nu=24, nv=14), head_paint)
    if nose:
        m.add(ellipsoid((x, 3.4, 0.6), (0.11 * nose, 0.13 * nose, 0.13 * nose)), skin(skin_c))
    if ears:
        for side in (1, -1):
            m.add(ellipsoid((x + side * 0.58, 3.48, 0.0), (0.07, 0.15, 0.12)), skin(skin_c))
    b.top = 3.5 + 0.64
    if hair_paint is not None:
        hair_on(m, b, hair_paint, hair_style)
    return b


def hair_on(m, b, paint, style):
    hx, hy, hz = b.head
    rx, ry, rz = b.head_r
    if style == "short":
        # A cap over the top and the back, open at the face
        m.add(ellipsoid((hx, hy + 0.04, hz - 0.04), (rx * 1.06, ry * 1.04, rz * 1.06), vrange=(0.45, 1.0), nu=22, nv=8),
              paint)
        m.add(ellipsoid((hx, hy - 0.05, hz - 0.12), (rx * 1.04, ry * 0.95, rz * 0.98), urange=(0.0, 0.3), vrange=(0.25, 0.75)), paint)
        m.add(ellipsoid((hx, hy - 0.05, hz - 0.12), (rx * 1.04, ry * 0.95, rz * 0.98), urange=(0.7, 1.0), vrange=(0.25, 0.75)), paint)
        # A fringe
        m.add(ellipsoid((hx, hy + 0.36, hz + 0.32), (rx * 0.75, 0.22, 0.25)), paint)
    elif style == "long":
        m.add(ellipsoid((hx, hy + 0.04, hz - 0.04), (rx * 1.07, ry * 1.05, rz * 1.07), vrange=(0.45, 1.0), nu=22, nv=8), paint)
        m.add(lathe([(hy - 1.0, 0.45), (hy - 0.5, 0.62), (hy, 0.66), (hy + 0.3, 0.6)], (hx, 0, hz - 0.1), sz=0.85,
                    urange=(0.0, 0.36)), paint)
        m.add(lathe([(hy - 1.0, 0.45), (hy - 0.5, 0.62), (hy, 0.66), (hy + 0.3, 0.6)], (hx, 0, hz - 0.1), sz=0.85,
                    urange=(0.64, 1.0)), paint)
        m.add(ellipsoid((hx, hy + 0.38, hz + 0.3), (rx * 0.8, 0.22, 0.26)), paint)
    elif style == "bun":
        m.add(ellipsoid((hx, hy + 0.06, hz - 0.04), (rx * 1.05, ry * 1.03, rz * 1.05), vrange=(0.5, 1.0), nu=22, nv=8), paint)
        m.add(sphere((hx, hy + 0.62, hz - 0.3), 0.3), paint)
    elif style == "spiky":
        m.add(ellipsoid((hx, hy + 0.04, hz - 0.04), (rx * 1.06, ry * 1.04, rz * 1.06), vrange=(0.5, 1.0), nu=22, nv=8), paint)
        for k in range(7):
            a = (k - 3) * 0.32
            m.add(lathe([(0, 0.18), (0.45, 0.0)], (hx + math.sin(a) * 0.4, hy + 0.5, hz + 0.15 - abs(a) * 0.1),
                        rot=(-25 + abs(a) * 10, 0, -a * 50), smooth=False, nu=8, nv=4), paint)


def beard(m, b, paint, length=0.7, moustache=True):
    hx, hy, hz = b.head
    m.add(lathe([(hy - 0.35 - length, 0.0), (hy - 0.3 - length * 0.7, 0.35), (hy - 0.45, 0.56), (hy - 0.1, 0.6)],
                (hx, 0, hz + 0.12), sz=0.75, urange=(0.18, 0.82)), paint)
    if moustache:
        for side in (1, -1):
            m.add(ellipsoid((hx + side * 0.17, hy - 0.22, hz + 0.56), (0.22, 0.08, 0.1), rot=(0, 0, side * 12)), paint)


def finish(m, name):
    m.fit_height(HEIGHTS[name])
    tris = m.write()
    print(f"models/{name}.obj  {tris} triangles")


#
# The heroes
#


def make_allan():
    """A runner: a red tracksuit with white stripes, a sweatband, and big white running shoes"""
    m = Model("allan")
    red = (0.84, 0.16, 0.14)
    suit = cloth(red) + bands(WHITE, [(0.0, 0.06)])
    sleeves = cloth(red) + stripes(WHITE, 2, 0.3, axis="u")
    b = person(m, cloth(red) + bands(WHITE, [(0.88, 0.95)]) + patch(WHITE, 0.5, 0.7, 0.15, 0.15),
               cloth(red) + stripes(WHITE, 2, 0.25, axis="u"),
               shoes=color(WHITE) + bands((0.85, 0.15, 0.12), [(0.35, 0.55)]) + bands((0.3, 0.3, 0.32), [(0.0, 0.25)]),
               arms=sleeves, hair_paint=hair((0.45, 0.28, 0.14)), hair_style="spiky",
               face_kw=dict(mouth="grin", brow_tilt=0.3, eye=(0.3, 0.5, 0.25)))
    hx, hy, hz = b.head
    m.add(lathe([(hy + 0.12, 0.62), (hy + 0.32, 0.6)], (hx, 0, hz), smooth=False, nu=28), color(WHITE) + bands(red, [(0.4, 0.6)]))
    finish(m, "allan")



def top_hat(m, b, paint, band=None, height=0.9, tilt=0.0):
    hx, hy, hz = b.head
    y = b.top - 0.22
    m.add(cylinder((hx, y, hz - 0.02), 0.82, 0.08, rot=(tilt, 0, 0)), paint)
    m.add(lathe([(0, 0.0), (0.0, 0.48), (height * 0.5, 0.5), (height, 0.54), (height, 0.0)], (hx, y, hz - 0.02), rot=(tilt, 0, 0),
                smooth=False, nu=20), paint + bands(band, [(0.12, 0.3)]) if band else paint)


def cap(m, b, paint, peak_paint=None, back=False, height=0.36):
    """A cap with a peak, forwards or backwards"""
    hx, hy, hz = b.head
    m.add(ellipsoid((hx, hy + 0.12, hz - 0.02), (0.64, height + 0.5, 0.62), vrange=(0.55, 1.0), nu=20, nv=6), paint)
    d = -1 if back else 1
    m.add(blob((hx, hy + 0.28, hz + d * 0.62), (0.42, 0.05, 0.3), (0.3, 0.8)), peak_paint or paint)


def pointy_hat(m, b, paint, brim=1.0, height=1.8, bend=0.35):
    hx, hy, hz = b.head
    y = b.top - 0.3
    m.add(lathe([(0, 0.0), (0.02, 1.0 * brim), (0.06, 0.95 * brim), (0.1, 0.0)], (hx, y, hz), smooth=False, nu=22), paint)
    m.add(tube([(hx, y, hz), (hx, y + height * 0.5, hz - 0.05), (hx, y + height * 0.85, hz - bend), (hx, y + height, hz - bend * 1.8)],
               [0.55, 0.32, 0.14, 0.03], nu=14, caps=False), paint)


def glasses(m, b, frame=(0.2, 0.2, 0.22), y=None, r=0.17, sun=False):
    hx, hy, hz = b.head
    y = y if y is not None else hy + 0.06
    lens = color((0.1, 0.1, 0.14)) if sun else glass((0.6, 0.75, 0.85))
    for side in (1, -1):
        m.add(cylinder((hx + side * 0.21, y, hz + 0.55), r, 0.04, rot=(90, 0, 0)), lens)
        m.add(tube([(hx + side * 0.04, y, hz + 0.6), (hx + side * 0.06, y + 0.02, hz + 0.6)], 0.03), color(frame))
        m.add(tube([(hx + side * 0.38, y, hz + 0.5), (hx + side * 0.58, y + 0.02, hz + 0.05)], 0.03), color(frame))


def make_ghosty():
    """A ghost in a sheet: a bell that ripples out at the hem, little arms, big dark eyes and a round mouth"""
    m = Model("ghosty", light=0.45)
    sheet = ghostly()
    prof = [(0.25, 0.0), (0.22, 1.05), (0.6, 0.98), (1.4, 0.88), (2.2, 0.82), (2.9, 0.72), (3.4, 0.45), (3.62, 0.0)]
    m.add(lathe(prof, sz=0.92, nu=28, nv=20), sheet + face(eye=(0.05, 0.05, 0.1), v=0.83, spacing=0.22, size=0.15,
                                                          mouth="o", brow=None, blush=False))
    # The ripples of the hem
    for k in range(8):
        a = k * math.pi / 4
        m.add(ellipsoid((math.sin(a) * 0.95, 0.28, math.cos(a) * 0.88), (0.28, 0.22, 0.28)), sheet)
    for side in (1, -1):
        m.add(tube([(side * 0.75, 2.2, 0.1), (side * 1.15, 2.0, 0.35), (side * 1.25, 1.75, 0.55)], [0.26, 0.2, 0.14]), sheet)
    m.fit_height(HEIGHTS["ghosty"])
    m.write()
    print("models/ghosty.obj")


def make_butcher():
    """A huge butcher: a striped shirt with the sleeves rolled up, a bloody white apron, a bald head with a big
    moustache, and a cleaver"""
    m = Model("butcher")
    shirt = cloth((0.75, 0.82, 0.92)) + stripes((0.25, 0.4, 0.7), 10, 0.35, axis="u")
    apron = cloth((0.95, 0.94, 0.9), folds=3) + stains((0.6, 0.06, 0.05), 0.22, 2.2) + bands((0.85, 0.84, 0.8), [(0.93, 1.0)])
    b = person(m, shirt, cloth((0.2, 0.2, 0.24)), arms=skin(SKIN) + bands((0.75, 0.82, 0.92), [(0.0, 0.35)]),
               width=1.28, belly=1.0, face_kw=dict(mouth="grin", brow_tilt=0.6, eye=(0.35, 0.25, 0.15), size=0.1), nose=1.3)
    # The apron over the belly
    m.add(lathe([(0.85, 0.82), (1.4, 0.98, 0.25), (1.9, 1.08, 0.5), (2.35, 0.98, 0.3), (2.6, 0.82)], sz=0.82,
                urange=(0.28, 0.72), nu=14), apron)
    m.add(tube([(-0.55, 2.62, 0.45), (0, 3.0, 0.3), (0.55, 2.62, 0.45)], 0.05), color((0.85, 0.84, 0.8)))
    beard(m, b, hair((0.25, 0.15, 0.1)), length=0.0)
    # The cleaver in his right hand
    hx, hy, hz = b.right
    m.add(tube([(hx, hy - 0.05, hz), (hx, hy - 0.05, hz + 0.55)], 0.08), wood((0.4, 0.24, 0.12)))
    m.add(blob((hx, hy + 0.15, hz + 1.0), (0.05, 0.42, 0.5), (0.2, 0.2)), metal((0.78, 0.8, 0.84)) + edges(0.3, 0.05))
    finish(m, "butcher")


def make_frosty():
    """A snowman: three snowballs, coal eyes and buttons, a carrot nose, a top hat, a striped scarf and stick arms"""
    m = Model("frosty", light=0.4)
    s = snow()
    m.add(sphere((0, 0.95, 0), 1.0, nu=24, nv=14), s)
    m.add(sphere((0, 2.3, 0), 0.78, nu=22, nv=12), s + patch((0.08, 0.08, 0.1), 0.5, 0.62, 0.09, 0.09) + patch((0.08, 0.08, 0.1), 0.5, 0.42, 0.09, 0.09))
    head = m.add(sphere((0, 3.4, 0), 0.6, nu=22, nv=12),
                 s + face(eye=(0.05, 0.05, 0.05), v=0.58, spacing=0.17, size=0.08, mouth="smile", brow=None, lips=(0.1, 0.1, 0.1)))
    m.add(lathe([(0, 0.13), (0.7, 0.0)], (0, 3.36, 0.52), rot=(90, 0, 0), smooth=False, nu=10, nv=4), color((0.98, 0.5, 0.1)))
    scarf = knit((0.85, 0.15, 0.15)) + stripes((0.15, 0.55, 0.25), 6, 0.4, axis="u")
    m.add(lathe([(2.82, 0.5), (2.92, 0.64), (3.08, 0.6), (3.15, 0.45)], nu=20), scarf)
    m.add(tube([(0.3, 2.95, 0.5), (0.4, 2.5, 0.65), (0.45, 2.1, 0.6)], [0.14, 0.13, 0.12], flat=0.5), scarf)
    class B: pass
    b = B()
    b.head, b.top = (0, 3.4, 0), 4.0
    top_hat(m, b, color((0.12, 0.11, 0.13)), band=(0.75, 0.12, 0.12), height=0.75)
    for side in (1, -1):
        stick = wood((0.4, 0.26, 0.14))
        m.add(tube([(side * 0.6, 2.4, 0), (side * 1.2, 2.75, 0.1), (side * 1.7, 3.15, 0.2)], [0.07, 0.06, 0.04]), stick)
        m.add(tube([(side * 1.45, 2.95, 0.15), (side * 1.6, 2.85, 0.4)], 0.035), stick)
        m.add(tube([(side * 1.7, 3.15, 0.2), (side * 1.95, 3.35, 0.15)], 0.03), stick)
    finish(m, "frosty")


def make_bjorn():
    """A viking shieldbearer: broad, a big braided beard, a horned helmet, fur on his shoulders and a round shield"""
    m = Model("bjorn")
    tunic = cloth((0.3, 0.42, 0.26)) + bands((0.65, 0.5, 0.2), [(0.0, 0.06), (0.86, 0.9)])
    b = person(m, tunic, cloth((0.4, 0.3, 0.2)) + stripes((0.3, 0.22, 0.14), 6, 0.4, axis="v", angle=30),
               shoes=fur((0.45, 0.33, 0.2)), arms=skin(SKIN) + bands((0.4, 0.3, 0.2), [(0.0, 0.25)]), width=1.22,
               face_kw=dict(mouth=None, brow_tilt=0.5, eye=(0.2, 0.45, 0.7), size=0.1), arm_pose="down")
    beard_c = hair((0.85, 0.42, 0.12))
    beard(m, b, beard_c, length=0.85)
    hx, hy, hz = b.head
    for side in (1, -1):
        m.add(tube([(hx + side * 0.18, hy - 1.2, hz + 0.45), (hx + side * 0.2, hy - 1.6, hz + 0.45)], 0.09), beard_c)
    # Fur round the shoulders, and a belt
    m.add(lathe([(2.45, 0.86), (2.62, 1.05), (2.8, 0.95), (2.95, 0.5)], sz=0.75, nu=22), fur((0.55, 0.42, 0.28)))
    m.add(lathe([(1.42, 0.72), (1.6, 0.74)], sz=0.72, smooth=False, nu=22), leather((0.3, 0.18, 0.1)))
    # The helmet with its horns
    helm = metal((0.6, 0.6, 0.64)) + bands((0.7, 0.55, 0.25), [(0.0, 0.12)])
    m.add(ellipsoid((hx, hy + 0.1, hz - 0.02), (0.66, 0.68, 0.64), vrange=(0.52, 1.0), nu=22, nv=8), helm)
    m.add(blob((hx, hy + 0.05, hz + 0.6), (0.06, 0.28, 0.06), (0.4, 0.4)), metal((0.6, 0.6, 0.64)))
    for side in (1, -1):
        m.add(tube([(hx + side * 0.55, hy + 0.35, hz), (hx + side * 0.95, hy + 0.55, hz + 0.05), (hx + side * 1.05, hy + 1.0, hz + 0.1)],
                   [0.16, 0.1, 0.02]), color((0.92, 0.88, 0.75)) + bands((0.6, 0.55, 0.45), [(0.0, 0.12)]))
    # The round shield on his left arm, facing forward
    lx, ly, lz = b.left
    c = (lx + 0.05, ly + 0.5, lz + 0.3)
    m.add(cylinder(c, 1.0, 0.14, rot=(90, 0, 0)),
          wood((0.62, 0.36, 0.18)) + stripes((0.75, 0.14, 0.1), 3, 0.5, axis="u") + edges(0.15, 0.1, dark=True))
    m.add(tube([(c[0] + math.sin(a) * 1.0, c[1] + math.cos(a) * 1.0, c[2] + 0.07) for a in [k * math.pi / 12 for k in range(25)]],
               0.07, nu=8, caps=False), metal((0.55, 0.55, 0.58)))
    m.add(ellipsoid((c[0], c[1], c[2] + 0.16), (0.24, 0.24, 0.14)), metal((0.78, 0.66, 0.35)))
    finish(m, "bjorn")


def make_hilda():
    """A crossing guard: a long hi-vis coat with silver bands, a white peaked cap, and the stop sign on its pole"""
    m = Model("hilda")
    hivis = cloth((0.98, 0.86, 0.12), folds=4) + bands((0.85, 0.87, 0.9), [(0.3, 0.36), (0.62, 0.68)])
    b = person(m, hivis, cloth((0.2, 0.22, 0.3)), arms=hivis, skirt=cloth((0.98, 0.86, 0.12)) + bands((0.85, 0.87, 0.9), [(0.15, 0.25)]),
               hair_paint=hair((0.75, 0.75, 0.78)), hair_style="bun", arm_pose="up",
               face_kw=dict(mouth="open", brow_tilt=0.4, eye=(0.35, 0.3, 0.25)), skin_c=SKIN_PALE)
    cap(m, b, color((0.95, 0.95, 0.95)) + bands((0.15, 0.15, 0.2), [(0.0, 0.3)]), color((0.12, 0.12, 0.16)))
    hx, hy, hz = b.right
    m.add(cylinder((hx, hy - 1.6, hz), 0.07, 2.9), metal((0.85, 0.85, 0.88)))
    c = (hx, hy + 1.55, hz + 0.05)

    def sign(ctx):
        x, y = ctx.p[..., 0] - c[0], ctx.p[..., 1] - c[1]
        r = (x * x + y * y) ** 0.5
        out = color((0.86, 0.1, 0.08))(ctx)
        white = (smoothstep(0.62, 0.6, r) * smoothstep(0.52, 0.54, r) + (abs(y) < 0.12) * (abs(x) < 0.42) * (r < 0.56))
        front = (ctx.n[..., 2] > 0.5)
        white = white * front
        return out * (1 - white[..., None]) + 0.97 * white[..., None]
    m.add(cylinder(c, 0.72, 0.08, rot=(90, 0, 0)), painted(sign))
    finish(m, "hilda")


def make_mira():
    """A timekeeper: a long starry robe and a pointed hat, and a staff with an hourglass on top"""
    m = Model("mira")
    robe = cloth((0.42, 0.28, 0.7), folds=6) + spots((0.98, 0.9, 0.5), 0.05, 0.25, 11) + bands((0.85, 0.7, 0.3), [(0.0, 0.05)])
    b = person(m, robe, robe, arms=robe, skirt=robe, hair_paint=hair((0.95, 0.95, 0.98)), hair_style="long",
               face_kw=dict(mouth="smile", eye=(0.55, 0.3, 0.8)), skin_c=SKIN_PALE, arm_pose="forward")
    pointy_hat(m, b, cloth((0.42, 0.28, 0.7), folds=3) + spots((0.98, 0.9, 0.5), 0.05, 0.3, 12), brim=1.15, height=1.7)
    hx, hy, hz = b.right
    m.add(cylinder((hx, 0.05, hz), 0.08, 3.6), wood((0.45, 0.3, 0.16)))
    top = 3.65
    gold = metal((0.85, 0.68, 0.3))
    m.add(cylinder((hx, top, hz), 0.34, 0.08), gold)
    m.add(cylinder((hx, top + 0.95, hz), 0.34, 0.08), gold)
    m.add(lathe([(0, 0.3), (0.4, 0.05), (0.45, 0.05), (0.85, 0.3)], (hx, top + 0.08, hz), smooth=True, nu=16), glass((0.55, 0.7, 0.85)))
    m.add(lathe([(0, 0.24), (0.25, 0.04), (0.28, 0.0)], (hx, top + 0.08, hz), nu=12), color((0.95, 0.8, 0.45)))
    for k in range(3):
        a = k * 2 * math.pi / 3
        m.add(cylinder((hx + math.sin(a) * 0.3, top, hz + math.cos(a) * 0.3), 0.04, 1.0), gold)
    finish(m, "mira")


def make_karl():
    """A mechanic in blue overalls with a red cap, a moustache, oil on his sleeves and a big wrench"""
    m = Model("karl")
    overalls = cloth((0.2, 0.36, 0.62)) + stains((0.08, 0.07, 0.07), 0.15, 2.5)
    b = person(m, overalls + rect((0.16, 0.3, 0.5), 0.4, 0.6, 0.55, 0.75), overalls, arms=cloth((0.85, 0.85, 0.82)) + stains((0.1, 0.1, 0.1), 0.2, 3),
               width=1.08, face_kw=dict(mouth="smile", eye=(0.4, 0.3, 0.2), brow_tilt=0.2))
    cap(m, b, color((0.8, 0.16, 0.14)))
    beard(m, b, hair((0.3, 0.2, 0.12)), length=0.0)
    for side in (1, -1):
        m.add(tube([(side * 0.42, 2.0, 0.42), (side * 0.42, 2.7, 0.35), (side * 0.38, 2.9, -0.1)], 0.08, flat=0.4), color((0.16, 0.3, 0.52)))
    hx, hy, hz = b.right
    steel = metal((0.72, 0.74, 0.78))
    m.add(tube([(hx, hy, hz), (hx, hy - 1.0, hz + 0.1)], 0.09), steel)
    m.add(lathe([(0, 0.0), (0, 0.28), (0.14, 0.28), (0.14, 0.0)], (hx, hy - 1.15, hz + 0.1), rot=(90, 0, 0), smooth=False, nu=8), steel)
    finish(m, "karl")


def make_birgit():
    """A builder: an orange hi-vis vest with silver stripes, a yellow hard hat, a tool belt, a braid and a plank"""
    m = Model("birgit")
    vest = cloth((0.98, 0.48, 0.08)) + bands((0.88, 0.9, 0.92), [(0.35, 0.42), (0.62, 0.69)])
    b = person(m, vest, cloth((0.3, 0.3, 0.34)), arms=cloth((0.35, 0.36, 0.4)), hair_paint=hair((0.88, 0.6, 0.25)),
               hair_style="short", face_kw=dict(mouth="grin", eye=(0.3, 0.55, 0.35)))
    hx, hy, hz = b.head
    m.add(tube([(hx, hy, hz - 0.55), (hx, hy - 0.6, hz - 0.65), (hx, hy - 1.2, hz - 0.55)], [0.14, 0.12, 0.08]), hair((0.88, 0.6, 0.25)))
    hat = color((0.98, 0.84, 0.1)) + bands((0.85, 0.7, 0.05), [(0.4, 0.45)])
    m.add(ellipsoid((hx, hy + 0.15, hz), (0.68, 0.7, 0.66), vrange=(0.5, 1.0), nu=22, nv=8), hat)
    m.add(blob((hx, hy + 0.17, hz + 0.1), (0.78, 0.04, 0.8), (0.3, 1.0)), hat)
    m.add(lathe([(1.4, 0.74), (1.6, 0.76)], sz=0.72, smooth=False, nu=22), leather((0.45, 0.28, 0.14)))
    for x in (0.45, -0.45):
        m.add(blob((x, 1.3, 0.48), (0.18, 0.2, 0.1), (0.4, 0.4)), leather((0.4, 0.25, 0.12)))
    m.add(tube([(0.42, 1.25, 0.55), (0.45, 1.6, 0.6)], 0.05), wood((0.5, 0.32, 0.18)))
    m.add(blob((-0.9, 3.05, -0.1), (0.18, 0.1, 1.5), (0.1, 0.1), rot=(10, 0, 0)), wood((0.78, 0.58, 0.34)))
    finish(m, "birgit")


def make_bent():
    """A bus driver: a green uniform with a tie and brass buttons, a peaked cap, a round belly and a moustache"""
    m = Model("bent")
    green = (0.18, 0.45, 0.3)
    uni = cloth(green) + rect((0.95, 0.95, 0.92), 0.46, 0.54, 0.6, 0.98) + rect((0.75, 0.15, 0.12), 0.48, 0.52, 0.45, 0.92)
    uni = uni + patch((0.9, 0.75, 0.3), 0.44, 0.4, 0.04, 0.04) + patch((0.9, 0.75, 0.3), 0.44, 0.25, 0.04, 0.04)
    b = person(m, uni, cloth((0.15, 0.3, 0.2)), arms=cloth(green) + bands((0.9, 0.75, 0.3), [(0.05, 0.1)]), width=1.15, belly=0.8,
               face_kw=dict(mouth="smile", eye=(0.4, 0.3, 0.2)), hair_paint=hair((0.55, 0.55, 0.58)), hair_style="short")
    beard(m, b, hair((0.55, 0.55, 0.58)), length=0.0)
    cap(m, b, color(green) + bands((0.9, 0.75, 0.3), [(0.0, 0.25)]), color((0.1, 0.1, 0.12)), height=0.45)
    finish(m, "bent")


def make_sigrid():
    """A witch: a long black dress, a tall pointed hat with a wide brim, a purple scarf, wild grey hair, a hooked nose"""
    m = Model("sigrid")
    dress = cloth((0.16, 0.14, 0.2), folds=7) + bands((0.4, 0.2, 0.5), [(0.0, 0.05)])
    b = person(m, dress, dress, arms=dress, skirt=dress, hair_paint=hair((0.72, 0.72, 0.7)), hair_style="long",
               face_kw=dict(mouth="grin", brow_tilt=0.7, eye=(0.45, 0.75, 0.2)), skin_c=(0.78, 0.86, 0.66), nose=0)
    hx, hy, hz = b.head
    m.add(tube([(hx, hy - 0.02, hz + 0.5), (hx, hy - 0.1, hz + 0.85), (hx, hy - 0.3, hz + 0.95)], [0.13, 0.08, 0.03]), skin((0.78, 0.86, 0.66)))
    pointy_hat(m, b, cloth((0.14, 0.12, 0.18), folds=2) + bands((0.5, 0.25, 0.6), [(0.05, 0.13)]), brim=1.4, height=2.2, bend=0.45)
    m.add(lathe([(2.78, 0.48), (2.9, 0.62), (3.05, 0.5)], nu=20), knit((0.5, 0.22, 0.6)))
    m.add(tube([(0.25, 2.85, 0.48), (0.35, 2.4, 0.62), (0.3, 1.9, 0.55)], 0.12, flat=0.45), knit((0.5, 0.22, 0.6)))
    finish(m, "sigrid")


def make_tobias():
    """A tourist: a pink flowered shirt, khaki shorts, socks in sandals, a sun hat, a bum bag and his camera"""
    m = Model("tobias")
    shirt = cloth((0.95, 0.55, 0.65)) + flowers((0.98, 0.95, 0.85), (0.98, 0.7, 0.2), 0.14, 0.4)
    legs = skin(SKIN_PALE) + bands((0.82, 0.72, 0.5), [(0.55, 1.0)]) + bands(WHITE, [(0.0, 0.18)])
    b = person(m, shirt, legs, shoes=leather((0.5, 0.33, 0.2)) + bands(WHITE, [(0.0, 0.6)]), arms=skin(SKIN_PALE) + bands((0.95, 0.55, 0.65), [(0.6, 1.0)]),
               skin_c=SKIN_PALE, face_kw=dict(mouth="grin", eye=(0.3, 0.5, 0.8)), belly=0.4, arm_pose="forward")
    glasses(m, b, sun=True)
    hx, hy, hz = b.head
    hat = cloth((0.92, 0.86, 0.62), folds=8) + bands((0.4, 0.6, 0.85), [(0.05, 0.25)])
    m.add(lathe([(0, 0.0), (0.0, 1.05), (0.08, 0.95), (0.12, 0.62), (0.45, 0.6), (0.55, 0.0)], (hx, b.top - 0.32, hz), nu=22), hat)
    m.add(lathe([(1.4, 0.74), (1.52, 0.76)], sz=0.75, smooth=False, nu=20), color((0.2, 0.5, 0.75)))
    m.add(blob((0.3, 1.38, 0.55), (0.3, 0.18, 0.14), (0.5, 0.5)), color((0.2, 0.5, 0.75)))
    # The camera in his hand, on its strap
    hx, hy, hz = b.right
    m.add(blob((hx - 0.25, hy + 0.15, hz + 0.25), (0.35, 0.22, 0.18), (0.3, 0.3)), color((0.15, 0.15, 0.17)) + bands((0.6, 0.6, 0.62), [(0.75, 0.85)]))
    m.add(cylinder((hx - 0.25, hy + 0.12, hz + 0.4), 0.14, 0.25, rot=(90, 0, 0)), metal((0.3, 0.3, 0.33)))
    m.add(tube([(-0.5, 2.85, 0.35), (0, 2.4, 0.62), (hx - 0.35, hy + 0.3, hz + 0.2)], 0.035), color((0.15, 0.15, 0.17)))
    finish(m, "tobias")


def make_mads():
    """A skater on his board: a baggy orange hoodie, wide grey jeans and a cap on backwards"""
    m = Model("mads")
    hoodie = cloth((0.98, 0.42, 0.12), folds=6) + rect((0.88, 0.36, 0.1), 0.4, 0.6, 0.12, 0.32) + patch((0.98, 0.95, 0.85), 0.5, 0.68, 0.1, 0.1)
    b = person(m, hoodie, cloth((0.5, 0.52, 0.56), folds=6), shoes=color((0.15, 0.15, 0.18)) + bands(WHITE, [(0.0, 0.3)]),
               arms=cloth((0.98, 0.42, 0.12)), width=1.05, face_kw=dict(mouth="smile", eye=(0.35, 0.25, 0.15), look=(0.4, 0)),
               hair_paint=hair((0.2, 0.14, 0.1)))
    cap(m, b, color((0.15, 0.4, 0.75)), back=True)
    # The hood, down on his back
    m.add(ellipsoid((0, 2.85, -0.45), (0.55, 0.32, 0.3)), cloth((0.9, 0.38, 0.1)))
    for s in m.surfaces:
        s.t = s.t + [0, 0.32, 0]
    board = wood((0.85, 0.65, 0.35)) + bands((0.15, 0.6, 0.85), [(0.2, 0.8)], axis="v")
    m.add(blob((0, 0.24, 0.1), (0.5, 0.06, 1.3), (0.2, 0.6)), board)
    for z in (-0.75, 0.95):
        for x in (0.32, -0.32):
            m.add(cylinder((x - 0.1 * (1 if x > 0 else -1), 0.1, z), 0.11, 0.18, rot=(0, 0, 90)), color((0.98, 0.9, 0.5)))
    finish(m, "mads")


def make_ditte():
    """A paramedic: a green and yellow uniform with reflective stripes, a white cross, a radio and a ponytail"""
    m = Model("ditte")
    uni = (cloth((0.15, 0.55, 0.35)) + bands((0.98, 0.88, 0.15), [(0.4, 0.62)]) + bands((0.88, 0.9, 0.92), [(0.48, 0.54)])
           + rect((0.97, 0.97, 0.97), 0.42, 0.58, 0.72, 0.78) + rect((0.97, 0.97, 0.97), 0.47, 0.53, 0.66, 0.84))
    b = person(m, uni, cloth((0.15, 0.4, 0.28)) + bands((0.88, 0.9, 0.92), [(0.35, 0.42)]), arms=cloth((0.15, 0.55, 0.35)) + bands((0.88, 0.9, 0.92), [(0.3, 0.38)]),
               hair_paint=hair((0.3, 0.2, 0.12)), hair_style="short", face_kw=dict(mouth="smile", eye=(0.3, 0.5, 0.35)))
    hx, hy, hz = b.head
    m.add(tube([(hx, hy + 0.3, hz - 0.55), (hx, hy - 0.2, hz - 0.85), (hx, hy - 0.8, hz - 0.75)], [0.2, 0.16, 0.06]), hair((0.3, 0.2, 0.12)))
    m.add(blob((-0.55, 2.6, 0.42), (0.14, 0.24, 0.08), (0.4, 0.4)), color((0.15, 0.15, 0.17)))
    m.add(tube([(-0.6, 2.84, 0.42), (-0.6, 3.1, 0.42)], 0.025), color((0.15, 0.15, 0.17)))
    finish(m, "ditte")


def make_gudrun():
    """A grandmother: a long flowered dress, a knitted cardigan, grey hair in a bun, glasses, and her cane"""
    m = Model("gudrun")
    dress = cloth((0.55, 0.38, 0.6), folds=7) + flowers((0.95, 0.85, 0.9), (0.9, 0.7, 0.3), 0.1, 0.4)
    cardigan = knit((0.82, 0.6, 0.65))
    b = person(m, cardigan + rect((0.55, 0.38, 0.6), 0.44, 0.56, 0.0, 1.0), dress, arms=cardigan, skirt=dress,
               hair_paint=hair((0.85, 0.85, 0.88)), hair_style="bun", width=1.1, belly=0.3, skin_c=SKIN_PALE,
               face_kw=dict(mouth="smile", eye=(0.4, 0.55, 0.75), size=0.09, brow=(0.7, 0.7, 0.72)), arm_pose="out")
    glasses(m, b)
    hx, hy, hz = b.right
    m.add(tube([(hx, hy, hz), (hx + 0.05, hy * 0.5, hz + 0.05), (hx + 0.08, 0.05, hz + 0.1)], 0.06), wood((0.35, 0.2, 0.1)))
    m.add(tube([(hx, hy, hz), (hx, hy + 0.25, hz - 0.1), (hx - 0.1, hy + 0.2, hz - 0.35)], 0.07), wood((0.35, 0.2, 0.1)))
    lx, ly, lz = b.left
    m.add(sphere((lx, ly + 0.1, lz + 0.25), 0.3), knit((0.85, 0.3, 0.45)))
    finish(m, "gudrun")


def make_magnus():
    """A man of steel: a grey jumpsuit with rivets, and a big red horseshoe magnet held up in both hands"""
    m = Model("magnus")
    suit = metal((0.55, 0.57, 0.62), 0.25) + spots((0.8, 0.82, 0.86), 0.03, 0.18, 13) + bands((0.35, 0.36, 0.4), [(0.0, 0.06)]) + bands((0.85, 0.15, 0.12), [(0.45, 0.5)], axis="u")
    b = person(m, suit, suit, arms=suit, width=1.2, face_kw=dict(mouth="grin", brow_tilt=0.4, eye=(0.3, 0.3, 0.35)),
               hair_paint=hair((0.15, 0.13, 0.13)), hair_style="short", arm_pose="both_up")
    (rx, ry, rz), (lx, ly, lz) = b.right, b.left
    red = color((0.85, 0.12, 0.1)) + edges(0.2, 0.05)
    top = ry + 1.1
    m.add(tube([(rx, ry + 0.15, rz), (rx, top, rz), (0, top + 0.35, rz), (lx, top, lz), (lx, ly + 0.15, lz)], 0.24, nu=12, caps=False), red)
    for x, y, z in (b.right, b.left):
        m.add(cylinder((x, y - 0.3, z), 0.25, 0.45), metal((0.85, 0.86, 0.9)))
    finish(m, "magnus")


def make_stormy():
    """A weather girl: a blue blazer and skirt, a red umbrella over her, and a little storm cloud by her shoulder"""
    m = Model("stormy")
    blazer = cloth((0.22, 0.4, 0.8)) + rect((0.95, 0.95, 0.97), 0.45, 0.55, 0.7, 1.0)
    b = person(m, blazer, skin(SKIN), arms=cloth((0.22, 0.4, 0.8)), skirt=cloth((0.18, 0.32, 0.68)), shoes=color((0.75, 0.1, 0.12)),
               hair_paint=hair((0.95, 0.78, 0.35)), hair_style="long", face_kw=dict(mouth="grin", eye=(0.3, 0.5, 0.85)), arm_pose="up")
    hx, hy, hz = b.right
    m.add(cylinder((hx, hy - 0.4, hz), 0.05, 2.0), metal((0.3, 0.3, 0.32)))
    m.add(lathe([(0, 1.6), (0.25, 1.45), (0.6, 1.0), (0.8, 0.4), (0.85, 0.0)], (hx, hy + 1.0, hz), nu=16),
          color((0.88, 0.12, 0.12)) + stripes((0.98, 0.96, 0.95), 4, 0.5, axis="u"))
    cloud = color((0.45, 0.48, 0.58))
    for dx, dy, r in ((0, 0, 0.32), (0.3, 0.08, 0.26), (-0.28, 0.05, 0.25), (0.05, 0.2, 0.25)):
        m.add(sphere((-1.35 + dx, 3.2 + dy, 0.0), r), cloud)
    m.add(lathe([(0, 0.0), (0.0, 0.08), (-0.45, 0.0)], (-1.35, 3.05, 0.0), rot=(0, 0, 20), smooth=False, nu=6), color((1.0, 0.9, 0.3)))
    finish(m, "stormy")


def make_hugo():
    """A hypnotist: a black tailcoat, a purple waistcoat, a top hat, a goatee, and a swinging pocket watch"""
    m = Model("hugo")
    coat = cloth((0.12, 0.11, 0.14)) + rect((0.45, 0.2, 0.55), 0.4, 0.6, 0.3, 0.95) + rect((0.97, 0.97, 0.97), 0.47, 0.53, 0.75, 1.0)
    b = person(m, coat, cloth((0.14, 0.13, 0.16)), arms=cloth((0.12, 0.11, 0.14)), skin_c=SKIN_PALE,
               face_kw=dict(mouth="smile", brow_tilt=0.8, eye=(0.6, 0.2, 0.75)), arm_pose="forward")
    hx, hy, hz = b.head
    m.add(tube([(hx, hy - 0.42, hz + 0.5), (hx, hy - 0.72, hz + 0.45)], [0.12, 0.03]), hair((0.15, 0.12, 0.12)))
    for side in (1, -1):
        m.add(ellipsoid((hx + side * 0.2, hy - 0.22, hz + 0.56), (0.2, 0.06, 0.08), rot=(0, 0, -side * 18)), hair((0.15, 0.12, 0.12)))
    top_hat(m, b, color((0.12, 0.11, 0.14)), band=(0.5, 0.2, 0.6), height=1.0)
    # The tails of the coat
    m.add(lathe([(0.9, 0.0), (1.0, 0.62), (1.7, 0.72)], sz=0.75, urange=(0.0, 0.25)), cloth((0.12, 0.11, 0.14)))
    m.add(lathe([(0.9, 0.0), (1.0, 0.62), (1.7, 0.72)], sz=0.75, urange=(0.75, 1.0)), cloth((0.12, 0.11, 0.14)))
    rx, ry, rz = b.right
    m.add(tube([(rx, ry - 0.1, rz + 0.1), (rx + 0.05, ry - 0.7, rz + 0.25)], 0.02), metal((0.85, 0.7, 0.3)))
    m.add(cylinder((rx + 0.05, ry - 0.9, rz + 0.18), 0.22, 0.07, rot=(90, 0, 0)), metal((0.85, 0.7, 0.3)) + patch((0.95, 0.93, 0.85), 0.5, 0.5, 0.15, 0.15))
    finish(m, "hugo")


def make_twins():
    """Tim and Tom: two boys side by side in matching yellow striped shirts, holding hands"""
    m = Model("twins")
    shirt = cloth((0.98, 0.78, 0.15)) + stripes((0.2, 0.45, 0.8), 6, 0.3)
    for x, hair_c, look in ((0.82, (0.6, 0.38, 0.18), (-0.5, 0)), (-0.82, (0.6, 0.38, 0.18), (0.5, 0))):
        person(m, shirt, cloth((0.25, 0.35, 0.6)), x=x, width=0.92, hair_paint=hair(hair_c), hair_style="short",
               face_kw=dict(mouth="grin", eye=(0.35, 0.55, 0.3), look=look), arm_pose="out")
    finish(m, "twins")


def make_kenji():
    """A ninja: all in black, a mask with only his eyes showing, a red sash, a red headband with tails, a sword on
    his back"""
    m = Model("kenji")
    black = cloth((0.13, 0.13, 0.16), folds=4)
    b = person(m, black + bands((0.75, 0.12, 0.12), [(0.0, 0.12)]), black, shoes=cloth((0.1, 0.1, 0.12)), arms=black, hands=cloth((0.1, 0.1, 0.12)),
               head=cloth((0.13, 0.13, 0.16)) + rect(SKIN, 0.36, 0.64, 0.42, 0.64) + face(eye=(0.25, 0.2, 0.15), mouth=None, blush=False, brow_tilt=0.7, v=0.53),
               nose=0, ears=False)
    hx, hy, hz = b.head
    red = cloth((0.8, 0.12, 0.12))
    m.add(lathe([(hy + 0.22, 0.63), (hy + 0.42, 0.61)], (hx, 0, hz), smooth=False, nu=22), red)
    m.add(tube([(hx, hy + 0.3, hz - 0.6), (hx + 0.25, hy + 0.15, hz - 1.0), (hx + 0.4, hy - 0.25, hz - 1.2)], 0.07, flat=0.4), red)
    m.add(tube([(hx, hy + 0.3, hz - 0.6), (hx - 0.15, hy + 0.05, hz - 1.0), (hx - 0.2, hy - 0.4, hz - 1.1)], 0.07, flat=0.4), red)
    m.add(tube([(0.8, 0.9, -0.62), (-0.7, 3.3, -0.62)], 0.08), color((0.15, 0.12, 0.1)) + bands((0.75, 0.12, 0.12), [(0.82, 1.0)]))
    m.add(cylinder((-0.55, 3.05, -0.62), 0.18, 0.04, rot=(0, 0, 35)), metal((0.75, 0.65, 0.35)))
    m.add(tube([(-0.6, 3.1, -0.62), (-0.95, 3.65, -0.62)], 0.06), color((0.75, 0.12, 0.12)))
    finish(m, "kenji")


def make_ivar():
    """A berserker: a wolf pelt over his head and shoulders, a bare chest with blue war paint, a red beard and an axe"""
    m = Model("ivar")
    chest = skin(SKIN_TAN) + stripes((0.2, 0.35, 0.75), 3, 0.15, axis="u", angle=40) + bands((0.35, 0.22, 0.12), [(0.0, 0.1)])
    b = person(m, chest, fur((0.45, 0.35, 0.25)), shoes=fur((0.35, 0.26, 0.18)), arms=skin(SKIN_TAN) + bands((0.35, 0.22, 0.12), [(0.62, 0.72)]),
               width=1.25, skin_c=SKIN_TAN, face_kw=dict(mouth="grin", brow_tilt=0.9, eye=(0.75, 0.3, 0.1)), arm_pose="up")
    beard(m, b, hair((0.75, 0.25, 0.08)), length=0.7)
    hx, hy, hz = b.head
    pelt = fur((0.55, 0.52, 0.5))
    m.add(ellipsoid((hx, hy + 0.12, hz - 0.08), (0.7, 0.72, 0.7), vrange=(0.45, 1.0), nu=20, nv=8), pelt)
    m.add(ellipsoid((hx, hy + 0.5, hz + 0.45), (0.32, 0.22, 0.38)), pelt + patch((0.1, 0.1, 0.1), 0.5, 0.75, 0.06, 0.05))
    for side in (1, -1):
        m.add(lathe([(0, 0.13), (0.3, 0.0)], (hx + side * 0.35, hy + 0.7, hz - 0.1), smooth=False, nu=6), pelt)
    m.add(lathe([(2.3, 0.85), (2.6, 1.08), (2.85, 0.9), (3.0, 0.5)], sz=0.78, urange=(0.0, 0.62)), pelt)
    m.add(lathe([(2.3, 0.85), (2.6, 1.08), (2.85, 0.9), (3.0, 0.5)], sz=0.78, urange=(0.88, 1.0)), pelt)
    rx, ry, rz = b.right
    m.add(tube([(rx, ry - 0.8, rz), (rx, ry + 1.0, rz + 0.05)], 0.08), wood((0.4, 0.25, 0.12)) + bands((0.3, 0.18, 0.1), [(0.3, 0.45)]))
    m.add(lathe([(0, 0.05), (0.35, 0.12), (0.6, 0.55), (0.62, 0.0)], (rx + 0.1, ry + 0.85, rz + 0.05), rot=(0, 0, -90), sz=0.15, nu=14),
          metal((0.7, 0.72, 0.76)) + edges(0.35, 0.05))
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
