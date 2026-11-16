#!/usr/bin/env python3
"""
Writes the models of the heroes that came after the first seven to data/models/, with the model library of
make_models.py. Each is a body (person()) and what makes it that hero: its clothes, its hat, what it carries.

    python3 tools/make_heroes.py                 all of them
    python3 tools/make_heroes.py karl mads       only these

The same rules as make_models.py: y is up, the model looks towards +z, and stands on y = 0.
"""

import math
import sys

from make_models import Model, SKIN, BLACK, eyes

SKIN_DARK = (0.62, 0.44, 0.32)
SKIN_PALE = (0.96, 0.84, 0.74)


def person(m, top, legs, shoe=(0.12, 0.1, 0.09), skin=SKIN, scale=1.0, width=1.0, arms=None, head=True):
    """A blocky person like Allan: legs, a torso, arms and a head. scale makes it taller, width wider.
    Returns the height of the top of its head"""
    s, w = scale, width
    m.material("skin", skin)
    m.material("top", top)
    m.material("legs", legs)
    m.material("shoe", shoe)
    for side in (-1, 1):
        m.box("shoe", (side * 0.33 * w, 0.15, 0.1), (0.5 * w, 0.3, 0.8))
        m.box("legs", (side * 0.33 * w, 0.95 * s, 0), (0.48 * w, 1.4 * s, 0.5 * w))
        if arms is None:
            m.box("top", (side * 0.97 * w, 2.3 * s, 0), (0.36 * w, 1.1 * s, 0.4 * w))
            m.box("skin", (side * 0.97 * w, 1.6 * s, 0), (0.3 * w, 0.32, 0.32))
    m.box("top", (0, 2.3 * s, 0), (1.55 * w, 1.4 * s, 0.78 * w))
    m.box("skin", (0, 3.1 * s, 0), (0.35, 0.2, 0.35))
    if head:
        m.box("skin", (0, 3.1 * s + 0.45, 0), (0.9, 0.85, 0.85))
        eyes(m, 3.1 * s + 0.52, 0.43, 0.2, 0.16)
    return 3.1 * s + 0.9


def make_karl():
    """A mechanic in blue overalls with a red cap, a big wrench in his hand and oil on his sleeves"""
    m = Model("karl")
    top = person(m, (0.2, 0.36, 0.6), (0.2, 0.36, 0.6), width=1.08)
    m.material("strap", (0.15, 0.27, 0.48))
    m.material("cap", (0.8, 0.16, 0.14))
    m.material("steel", (0.7, 0.7, 0.74))
    m.material("oil", (0.06, 0.05, 0.05))
    m.material("hair", (0.25, 0.18, 0.12))
    m.box("strap", (0.4, 2.6, 0.4), (0.2, 1.0, 0.04))
    m.box("strap", (-0.4, 2.6, 0.4), (0.2, 1.0, 0.04))
    m.box("oil", (0.5, 1.9, 0.41), (0.4, 0.3, 0.02))
    m.box("cap", (0, top + 0.08, -0.02), (0.96, 0.22, 0.94))
    m.box("cap", (0, top - 0.02, 0.55), (0.8, 0.06, 0.4))
    m.box("hair", (0, top - 0.5, -0.43), (0.94, 0.5, 0.1))
    m.box("hair", (0, top - 0.75, 0.44), (0.6, 0.14, 0.04))                  # Moustache
    # The wrench in his right hand
    m.box("steel", (1.05, 1.0, 0.25), (0.16, 1.2, 0.18))
    m.box("steel", (1.05, 0.38, 0.25), (0.5, 0.2, 0.18))
    m.write()


def make_birgit():
    """A builder: hi-vis orange vest, a yellow hard hat, a tool belt and a plank on her shoulder"""
    m = Model("birgit")
    top = person(m, (0.98, 0.5, 0.1), (0.3, 0.3, 0.32))
    m.material("hat", (0.98, 0.84, 0.1))
    m.material("stripe", (0.88, 0.9, 0.92))
    m.material("belt", (0.4, 0.26, 0.14))
    m.material("plank", (0.72, 0.52, 0.3))
    m.material("hair", (0.85, 0.6, 0.25))
    for y in (2.0, 2.6):
        m.box("stripe", (0, y, 0), (1.58, 0.12, 0.8))
    m.box("belt", (0, 1.62, 0), (1.6, 0.22, 0.82))
    m.box("belt", (0.55, 1.4, 0.36), (0.3, 0.35, 0.16))
    m.frustum("hat", (0, top - 0.05, 0), (1.05, 1.05), (0.75, 0.75), 0.42)
    m.box("hat", (0, top - 0.02, 0.5), (0.9, 0.06, 0.3))
    m.box("hair", (0, top - 0.7, -0.45), (0.9, 0.9, 0.14))                    # A braid down the back
    m.box("hair", (0, top - 1.35, -0.5), (0.22, 0.6, 0.12))
    m.box("plank", (-0.6, 3.35, 0), (0.3, 0.16, 3.4))
    m.write()


def make_bent():
    """A bus driver: a green uniform with a tie, a peaked cap, round belly and a moustache"""
    m = Model("bent")
    top = person(m, (0.12, 0.42, 0.28), (0.14, 0.16, 0.2), width=1.15)
    m.material("shirt", (0.9, 0.92, 0.94))
    m.material("tie", (0.75, 0.6, 0.1))
    m.material("cap", (0.1, 0.3, 0.2))
    m.material("peak", BLACK)
    m.material("badge", (0.95, 0.8, 0.2))
    m.material("hair", (0.55, 0.55, 0.58))
    m.sphere("top", (0, 2.0, 0.25), 0.75, scale=(1.1, 0.9, 0.8))             # The belly
    m.box("shirt", (0, 2.75, 0.4), (0.4, 0.5, 0.06))
    m.box("tie", (0, 2.5, 0.44), (0.16, 0.7, 0.04))
    m.box("cap", (0, top + 0.12, 0), (1.0, 0.3, 1.0))
    m.box("peak", (0, top - 0.02, 0.58), (0.9, 0.06, 0.34))
    m.box("badge", (0, top + 0.15, 0.51), (0.24, 0.16, 0.02))
    m.box("hair", (0, top - 0.75, 0.44), (0.7, 0.16, 0.05))                  # Moustache
    m.write()


def make_sigrid():
    """A witch: a long black dress, a tall pointed hat with a wide brim, a purple scarf and wild grey hair"""
    m = Model("sigrid")
    m.material("dress", (0.12, 0.08, 0.16))
    m.material("skin", SKIN_PALE)
    m.material("hat", (0.1, 0.07, 0.12))
    m.material("band", (0.55, 0.25, 0.7))
    m.material("hair", (0.72, 0.72, 0.76))
    m.material("shoe", (0.05, 0.05, 0.05))
    for side in (-1, 1):
        m.box("shoe", (side * 0.3, 0.12, 0.2), (0.38, 0.24, 0.8))
        m.box("dress", (side * 0.95, 2.4, 0), (0.34, 1.1, 0.4))
        m.box("skin", (side * 0.95, 1.7, 0), (0.28, 0.3, 0.3))
    m.frustum("dress", (0, 0.2, 0), (1.9, 1.3), (1.2, 0.75), 2.7)
    m.box("band", (0, 2.85, 0), (1.3, 0.25, 0.85))                           # Scarf
    m.box("skin", (0, 3.15, 0), (0.3, 0.2, 0.3))
    m.box("skin", (0, 3.6, 0), (0.82, 0.82, 0.8))
    eyes(m, 3.68, 0.41, 0.19, 0.15)
    m.box("skin", (0, 3.5, 0.5), (0.16, 0.3, 0.2))                            # A long nose
    m.box("hair", (0, 3.45, -0.38), (1.1, 0.95, 0.2))
    m.box("hair", (0.5, 3.35, 0), (0.2, 0.8, 0.7))
    m.box("hair", (-0.5, 3.35, 0), (0.2, 0.8, 0.7))
    m.cylinder("hat", (0, 4.05, 0), 1.25, 0.08, axis="y", segments=14)       # Brim
    m.cylinder("band", (0, 4.12, 0), 0.52, 0.18, axis="y", segments=12)
    m.cylinder("hat", (0, 4.1, 0), 0.5, 1.6, axis="y", segments=12, radius_end=0.03)
    m.write()


def make_tobias():
    """A tourist: a pink flowered shirt, khaki shorts, socks in sandals, a sun hat and a bum bag"""
    m = Model("tobias")
    top = person(m, (0.95, 0.5, 0.62), SKIN)
    m.material("shorts", (0.76, 0.68, 0.48))
    m.material("sock", (0.96, 0.96, 0.96))
    m.material("flower", (0.98, 0.9, 0.3))
    m.material("hat", (0.92, 0.88, 0.72))
    m.material("bag", (0.25, 0.5, 0.8))
    for side in (-1, 1):
        m.box("shorts", (side * 0.33, 1.4, 0), (0.52, 0.55, 0.54))
        m.box("sock", (side * 0.33, 0.42, 0), (0.5, 0.3, 0.52))
    for x, y in ((-0.4, 2.6), (0.35, 2.1), (0.1, 2.8), (-0.2, 1.9)):
        m.box("flower", (x, y, 0.4), (0.2, 0.2, 0.02))
    m.box("bag", (0, 1.65, 0.45), (0.8, 0.3, 0.2))
    m.cylinder("hat", (0, top + 0.02, 0), 0.95, 0.08, axis="y", segments=14)
    m.cylinder("hat", (0, top + 0.06, 0), 0.5, 0.42, axis="y", segments=12)
    m.write()


def make_mads():
    """A skater: a baggy orange hoodie with the hood up, wide grey jeans and a cap on backwards"""
    m = Model("mads")
    top = person(m, (0.96, 0.4, 0.15), (0.45, 0.48, 0.55), shoe=(0.9, 0.9, 0.9), width=1.05)
    m.material("cap", (0.15, 0.15, 0.18))
    m.material("pocket", (0.82, 0.32, 0.1))
    m.material("hair", (0.92, 0.82, 0.5))
    m.box("pocket", (0, 1.95, 0.4), (0.9, 0.35, 0.04))
    m.box("top", (0, 3.0, -0.35), (1.0, 0.35, 0.25))                         # The hood, down on his back
    m.box("cap", (0, top + 0.08, 0), (0.94, 0.22, 0.92))
    m.box("cap", (0, top - 0.02, -0.56), (0.8, 0.06, 0.34))                  # The peak, backwards
    m.box("hair", (0.42, top - 0.25, 0.2), (0.12, 0.3, 0.4))
    m.box("hair", (-0.42, top - 0.25, 0.2), (0.12, 0.3, 0.4))
    m.write()


def make_ditte():
    """A paramedic: a green and yellow uniform with reflective stripes, a white cross, a radio, and her hair in a
    ponytail"""
    m = Model("ditte")
    top = person(m, (0.2, 0.55, 0.3), (0.15, 0.32, 0.2))
    m.material("hivis", (0.95, 0.88, 0.15))
    m.material("stripe", (0.85, 0.88, 0.9))
    m.material("cross", (0.95, 0.95, 0.95))
    m.material("red", (0.85, 0.1, 0.12))
    m.material("radio", (0.1, 0.1, 0.12))
    m.material("hair", (0.5, 0.3, 0.15))
    m.box("hivis", (0, 2.55, 0), (1.6, 0.7, 0.82))
    m.box("stripe", (0, 2.15, 0), (1.6, 0.12, 0.82))
    m.box("cross", (0, 2.55, 0.42), (0.5, 0.14, 0.02))
    m.box("cross", (0, 2.55, 0.42), (0.14, 0.5, 0.02))
    m.box("red", (0, 2.55, 0.43), (0.36, 0.08, 0.02))
    m.box("red", (0, 2.55, 0.43), (0.08, 0.36, 0.02))
    m.box("radio", (-0.55, 2.95, 0.42), (0.2, 0.35, 0.12))
    m.box("hair", (0, top - 0.1, -0.05), (0.96, 0.25, 0.92))
    m.box("hair", (0, top - 0.6, -0.48), (0.25, 0.25, 0.3))
    m.box("hair", (0, top - 1.0, -0.6), (0.2, 0.7, 0.18))                    # Ponytail
    m.write()


def make_gudrun():
    """A grandmother: a long flowered dress, a cardigan, a headscarf, a walker in front of her and a ball of yarn"""
    m = Model("gudrun")
    m.material("skin", SKIN_PALE)
    m.material("dress", (0.55, 0.35, 0.55))
    m.material("cardigan", (0.75, 0.6, 0.45))
    m.material("scarf", (0.85, 0.3, 0.35))
    m.material("hair", (0.92, 0.92, 0.94))
    m.material("walker", (0.65, 0.68, 0.72))
    m.material("shoe", (0.15, 0.1, 0.08))
    m.material("glasses", (0.15, 0.15, 0.2))
    for side in (-1, 1):
        m.box("shoe", (side * 0.3, 0.12, 0.1), (0.4, 0.24, 0.6))
        m.box("cardigan", (side * 0.85, 2.0, 0.35), (0.32, 1.0, 0.4))
        m.box("skin", (side * 0.85, 1.55, 0.75), (0.26, 0.28, 0.28))
    m.frustum("dress", (0, 0.2, 0), (1.5, 1.0), (1.25, 0.8), 1.6)
    m.box("cardigan", (0, 2.2, -0.05), (1.4, 1.2, 0.8))                       # A little bent forward
    m.box("skin", (0, 2.95, 0.15), (0.3, 0.2, 0.3))
    m.box("skin", (0, 3.35, 0.2), (0.8, 0.78, 0.78))
    eyes(m, 3.42, 0.6, 0.18, 0.14)
    m.box("glasses", (0, 3.42, 0.6), (0.68, 0.18, 0.03))
    m.box("hair", (0, 3.75, 0.1), (0.86, 0.2, 0.86))
    m.box("scarf", (0, 3.55, -0.05), (0.92, 0.6, 0.8))
    # The walker: two frames and wheels in front of her
    for side in (-1, 1):
        m.box("walker", (side * 0.75, 0.9, 1.15), (0.08, 1.8, 0.08))
        m.box("walker", (side * 0.75, 0.9, 0.55), (0.08, 1.8, 0.08))
        m.box("walker", (side * 0.75, 1.75, 0.85), (0.08, 0.08, 0.7))
        m.cylinder("shoe", (side * 0.75, 0.12, 1.15), 0.12, 0.1, axis="x", segments=8)
    m.box("walker", (0, 1.75, 1.15), (1.5, 0.08, 0.08))
    m.write()


def make_magnus():
    """A man of metal: a steel grey jumpsuit with rivets, a big horseshoe magnet held up, red and silver"""
    m = Model("magnus")
    top = person(m, (0.45, 0.48, 0.52), (0.35, 0.37, 0.4), width=1.12)
    m.material("rivet", (0.8, 0.82, 0.86))
    m.material("red", (0.85, 0.12, 0.12))
    m.material("silver", (0.88, 0.88, 0.9))
    m.material("hair", (0.2, 0.2, 0.22))
    m.material("goggles", (0.3, 0.75, 0.85))
    for x in (-0.5, 0, 0.5):
        for y in (1.9, 2.4, 2.9):
            m.box("rivet", (x, y, 0.41), (0.1, 0.1, 0.04))
    m.box("goggles", (0, top - 0.38, 0.44), (0.8, 0.2, 0.06))
    m.box("hair", (0, top + 0.06, 0), (0.92, 0.2, 0.9))
    m.box("hair", (0, top + 0.3, 0), (0.25, 0.3, 0.8))                        # A crest
    # The magnet, held up in his right hand: a U, red with silver ends
    cx, cy = 1.0, 3.6
    m.box("red", (cx - 0.35, cy, 0.2), (0.25, 0.9, 0.3))
    m.box("red", (cx + 0.35, cy, 0.2), (0.25, 0.9, 0.3))
    m.box("red", (cx, cy - 0.5, 0.2), (0.95, 0.25, 0.3))
    m.box("silver", (cx - 0.35, cy + 0.55, 0.2), (0.25, 0.25, 0.3))
    m.box("silver", (cx + 0.35, cy + 0.55, 0.2), (0.25, 0.25, 0.3))
    m.box("top", (cx, 2.7, 0.1), (0.36, 1.0, 0.4))
    m.write()


def make_stormy():
    """A weather girl: a blue blazer and skirt, a red umbrella over her, and a little storm cloud on her shoulder"""
    m = Model("stormy")
    top = person(m, (0.2, 0.35, 0.75), (0.2, 0.35, 0.75), shoe=(0.7, 0.1, 0.1))
    m.material("blouse", (0.95, 0.95, 0.98))
    m.material("umbrella", (0.85, 0.15, 0.2))
    m.material("stick", (0.3, 0.3, 0.32))
    m.material("cloud", (0.45, 0.47, 0.55))
    m.material("bolt", (1.0, 0.85, 0.2))
    m.material("hair", (0.95, 0.75, 0.3))
    m.box("blouse", (0, 2.6, 0.4), (0.4, 0.6, 0.04))
    m.box("hair", (0, top - 0.1, -0.05), (0.98, 0.28, 0.95))
    m.box("hair", (0, top - 0.7, -0.45), (1.0, 1.1, 0.16))
    m.cylinder("stick", (0.97, 1.6, 0), 0.05, 4.0, axis="y", segments=6)
    m.cylinder("umbrella", (0.97, 5.4, 0), 1.7, 0.6, axis="y", segments=10, radius_end=0.1)
    m.sphere("cloud", (-0.9, 4.4, 0), 0.45, scale=(1.4, 0.8, 1))
    m.sphere("cloud", (-0.5, 4.5, 0), 0.4)
    m.box("bolt", (-0.75, 3.85, 0), (0.12, 0.5, 0.06))
    m.write()


def make_hugo():
    """A hypnotist: a black tailcoat, a purple waistcoat, a top hat, a pocket watch swinging from his hand"""
    m = Model("hugo")
    top = person(m, (0.08, 0.08, 0.1), (0.08, 0.08, 0.1), scale=1.08)
    m.material("waistcoat", (0.45, 0.15, 0.55))
    m.material("hat", (0.06, 0.06, 0.07))
    m.material("band", (0.5, 0.15, 0.6))
    m.material("gold", (0.95, 0.78, 0.25))
    m.material("hair", (0.1, 0.1, 0.12))
    m.box("waistcoat", (0, 2.45, 0.4), (0.7, 1.1, 0.04))
    m.box("top", (0, 1.4, -0.3), (1.4, 0.8, 0.2))                            # Coat tails
    m.box("hair", (0, top - 0.78, 0.44), (0.7, 0.1, 0.04))                    # A thin moustache
    m.box("hair", (0, top - 0.95, 0.44), (0.12, 0.2, 0.04))                   # and a goatee
    m.cylinder("hat", (0, top + 0.02, 0), 0.7, 0.08, axis="y", segments=12)
    m.cylinder("hat", (0, top + 0.06, 0), 0.45, 1.1, axis="y", segments=12)
    m.cylinder("band", (0, top + 0.1, 0), 0.47, 0.2, axis="y", segments=12)
    m.cylinder("gold", (1.0, 1.6, 0.3), 0.02, 0.6, axis="y", segments=4)
    m.cylinder("gold", (1.0, 1.25, 0.3), 0.26, 0.08, axis="z", segments=12)
    m.write()


def make_twins():
    """Tim and Tom: one model, two boys side by side in matching striped shirts, holding hands"""
    m = Model("twins")
    m.material("skin", SKIN)
    m.material("shirt", (0.95, 0.85, 0.2))
    m.material("stripe", (0.2, 0.45, 0.85))
    m.material("legs", (0.25, 0.3, 0.5))
    m.material("shoe", (0.85, 0.2, 0.2))
    m.material("hair", (0.95, 0.55, 0.2))
    for cx in (-0.75, 0.75):
        for side in (-1, 1):
            x = cx + side * 0.22
            m.box("shoe", (x, 0.12, 0.08), (0.32, 0.24, 0.55))
            m.box("legs", (x, 0.7, 0), (0.3, 1.0, 0.34))
            m.box("shirt", (cx + side * 0.6, 1.8, 0), (0.24, 0.8, 0.28))
            m.box("skin", (cx + side * 0.6, 1.3, 0), (0.22, 0.24, 0.24))
        m.box("shirt", (cx, 1.8, 0), (1.0, 1.0, 0.55))
        for y in (1.55, 1.85, 2.15):
            m.box("stripe", (cx, y, 0), (1.02, 0.1, 0.57))
        m.box("skin", (cx, 2.65, 0), (0.75, 0.72, 0.7))
        eyes(m, 2.72, 0.36, 0.16, 0.13)
        m.box("hair", (cx, 3.05, -0.02), (0.8, 0.22, 0.76))
        m.box("hair", (cx, 2.75, -0.35), (0.8, 0.5, 0.1))
    m.write()


def make_kenji():
    """A ninja: all in black, a red sash and headband with its tails, a sword on his back"""
    m = Model("kenji")
    top = person(m, (0.1, 0.1, 0.12), (0.1, 0.1, 0.12), shoe=(0.08, 0.08, 0.09))
    m.material("mask", (0.12, 0.12, 0.14))
    m.material("red", (0.8, 0.12, 0.12))
    m.material("blade", (0.75, 0.76, 0.8))
    m.material("hilt", (0.4, 0.3, 0.2))
    m.box("mask", (0, top - 0.6, 0.1), (0.94, 0.5, 0.8))                      # Covers all but the eyes
    m.box("mask", (0, top - 0.02, 0), (0.94, 0.12, 0.9))
    m.box("red", (0, top - 0.2, 0), (0.95, 0.14, 0.9))
    m.box("red", (0.2, top - 0.35, -0.6), (0.1, 0.4, 0.3))
    m.box("red", (-0.1, top - 0.45, -0.65), (0.1, 0.5, 0.25))
    m.box("red", (0, 1.65, 0), (1.6, 0.25, 0.82))
    m.box("blade", (0.3, 2.4, -0.48), (0.12, 2.2, 0.06))                     # The sword, across his back
    m.box("hilt", (0.3, 3.6, -0.48), (0.14, 0.5, 0.1))
    m.write()


def make_ivar():
    """A viking: a big red beard, a horned helmet, fur over his shoulders, an axe"""
    m = Model("ivar")
    top = person(m, (0.45, 0.3, 0.2), (0.35, 0.25, 0.18), width=1.15)
    m.material("fur", (0.55, 0.45, 0.35))
    m.material("beard", (0.8, 0.35, 0.12))
    m.material("helmet", (0.62, 0.62, 0.66))
    m.material("horn", (0.93, 0.9, 0.8))
    m.material("wood", (0.45, 0.3, 0.15))
    m.material("steel", (0.75, 0.75, 0.8))
    m.box("fur", (0, 2.95, 0), (1.9, 0.4, 1.0))
    m.box("beard", (0, top - 0.95, 0.42), (0.86, 0.9, 0.3))
    m.box("helmet", (0, top + 0.02, 0), (0.98, 0.32, 0.94))
    m.box("helmet", (0, top - 0.3, 0.46), (0.12, 0.4, 0.06))                  # Nose guard
    for side in (-1, 1):
        m.cylinder("horn", (side * 0.55, top, 0), 0.15, 0.6, axis="x", segments=6, radius_end=0.05)
        m.box("horn", (side * 0.95, top + 0.3, 0), (0.1, 0.4, 0.1))
    m.cylinder("wood", (1.1, 0.9, 0.3), 0.07, 2.4, axis="y", segments=6)
    m.box("steel", (1.1, 2.9, 0.55), (0.12, 0.7, 0.6))
    m.write()


HEROES = {
    "karl": make_karl, "birgit": make_birgit, "bent": make_bent, "sigrid": make_sigrid, "tobias": make_tobias,
    "mads": make_mads, "ditte": make_ditte, "gudrun": make_gudrun, "magnus": make_magnus, "stormy": make_stormy,
    "hugo": make_hugo, "twins": make_twins, "kenji": make_kenji, "ivar": make_ivar,
}

if __name__ == "__main__":
    for name in sys.argv[1:] or HEROES:
        HEROES[name]()
