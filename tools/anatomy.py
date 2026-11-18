"""
Anatomy: the bodies, skeletons and clips that heroes are built from, with tools/sculpt.py and tools/rig.py.

A body is made from where its joints are (joints(), with any of them moved): the same points make the rig, so the
skin bends where the bones do. brute_body() is a hulking body (a wedge of a torso with a gut, a hump of muscle over the
shoulders, massive forearms, big hands, short thick legs and big feet), every part bound to its bones. clips() are the
clips every rig of make_rig() can play: idle, walk, and what a hero does when it casts.
"""

import math

import numpy as np

from rig import Rig, clip
from sculpt import (Paint, blob, bulge, ellipsoid, fbm, leather, loft, lumps, metal, mirror_bone_name, push, tube,
                    smoothstep, torus, _over, _varied, rgb)


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
    # Throwing the hook: a quick windup with the right arm back and the body turned away, then the arm flung forward
    # with the whole body behind it, and back. The hook leaves the moment it is cast, so the clip starts wound up and
    # the arm is flung forward at once, the hook going with it
    hook_back = {"upper_r": (40, 0, 75), "fore_r": (-70, 0, 0), "chest": (-4, 32, 0), "spine": (0, 14, 0), "head": (-6, -20, 0),
                 "upper_l": (-25, 0, -20), "fore_l": (-40, 0, 0), "thigh_r": (12, 0, 0), "thigh_l": (-14, 0, 0), "shin_l": (14, 0, 0),
                 "hips": {"rot": (0, 10, 0), "pos": (0, -0.05, 0)}}
    hook_throw = {"upper_r": (-100, 0, 18), "fore_r": (-4, 0, 0), "chest": (10, -32, 0), "spine": (6, -14, 0), "head": (-4, 14, 0),
                  "upper_l": (20, 0, -25), "fore_l": (-30, 0, 0), "thigh_r": (-20, 0, 0), "shin_r": (14, 0, 0), "thigh_l": (12, 0, 0),
                  "hips": {"rot": (0, -10, 0), "pos": (0, -0.1, 0.12)}}
    hook_follow = {"upper_r": (-70, 0, 6), "fore_r": (-12, 0, 0), "chest": (12, -22, 0), "spine": (6, -8, 0), "upper_l": (5, 0, -15),
                   "fore_l": (-30, 0, 0), "thigh_r": (-14, 0, 0), "shin_r": (10, 0, 0), "hips": {"rot": (0, -6, 0), "pos": (0, -0.06, 0.08)}}
    # Heaving a car: down into a crouch with both arms forward under it, then up and over with a shove
    crouch = {"upper_r": (-55, 0, 12), "upper_l": (-55, 0, -12), "fore_r": (-60, 0, 0), "fore_l": (-60, 0, 0), "spine": (22, 0, 0),
              "chest": (10, 0, 0), "head": (-20, 0, 0), "thigh_r": (-38, 0, 0), "thigh_l": (-38, 0, 0), "shin_r": (48, 0, 0),
              "shin_l": (48, 0, 0), "hips": {"rot": (8, 0, 0), "pos": (0, -0.3, 0)}}
    lift = {"upper_r": (-160, 0, 18), "upper_l": (-160, 0, -18), "fore_r": (-15, 0, 0), "fore_l": (-15, 0, 0), "spine": (-12, 0, 0),
            "chest": (-14, 0, 0), "head": (10, 0, 0), "thigh_r": (-8, 0, 0), "thigh_l": (-8, 0, 0), "shin_r": (6, 0, 0),
            "shin_l": (6, 0, 0), "hips": {"rot": (-4, 0, 0), "pos": (0, 0.08, 0)}}
    shove = {"upper_r": (-95, 0, 10), "upper_l": (-95, 0, -10), "fore_r": (-5, 0, 0), "fore_l": (-5, 0, 0), "spine": (14, 0, 0),
             "chest": (8, 0, 0), "thigh_r": (-24, 0, 0), "shin_r": (16, 0, 0), "thigh_l": (14, 0, 0), "hips": {"rot": (4, 0, 0), "pos": (0, -0.1, 0.15)}}
    return {"idle": clip(2.0, (0.0, idle0), (1.0, idle1)), "walk": clip(1.0, (0.0, walk(0)), (0.25, passing(1)), (0.5, walk(1)), (0.75, passing(-1))),
            "cast": clip(0.9, (0.0, idle0), (0.35, windup), (0.55, slam), (0.8, idle0)),
            "hook": once(0.75, (0.0, hook_back), (0.1, hook_throw), (0.32, hook_follow), (0.75, idle0)),
            "heave": once(0.9, (0.0, idle0), (0.2, crouch), (0.42, lift), (0.58, shove), (0.9, idle0))}


def once(duration, *keys):
    """A clip that is played once, from its first key to its last, not looped"""
    c = clip(duration, *keys)
    c["once"] = True
    return c


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
# A person's skeleton and body: the same bones as a brute, in human proportions, chunky like a hero of a strategy game
# (big hands and feet, a head a bit big), so every hero can be rigged and play the same kinds of clips
#


def human_joints(**over):
    j = dict(hips=(0, 1.85, 0), spine=(0, 2.3, 0.03), chest=(0, 2.85, 0.06), neck=(0, 3.3, 0.06), head=(0, 3.5, 0.1),
             shoulder_r=(0.66, 3.15, 0.0), elbow_r=(0.86, 2.47, -0.06), wrist_r=(0.94, 1.84, 0.1), hand_end_r=(0.97, 1.56, 0.18),
             hip_r=(0.3, 1.82, 0.0), knee_r=(0.35, 1.04, 0.08), ankle_r=(0.4, 0.3, -0.02), toe_r=(0.42, 0.08, 0.52))
    j.update(over)
    return {k: np.asarray(v, dtype=float) for k, v in j.items()}


def human_body(m, J, shirt_p, sleeve_p, skin_p, legs_p, glove_p, boot_p, sole_p=None, chest=1.0, hips=1.0, bust=0.0,
               arm=1.0, leg=1.0, rolled=True, cuff_p=None, knee_p=None, left_open=False):
    """A person's body on the joints J, every part bound to its bones: a torso (shirt_p) that narrows at the waist,
    shoulders, arms whose sleeves (sleeve_p) are rolled up to the elbow over bare forearms (skin_p) when rolled, big
    gloved hands (glove_p) closed round a grip, legs (legs_p) with knee pads (knee_p) and heavy boots (boot_p). With
    left_open, the left hand is open (open_hand), e.g for casting. Returns the surfaces of the torso, for clothes over it"""
    lump = lumps(0.008, 3, 5)
    h, s, c, n = J["hips"], J["spine"], J["chest"], J["neck"]
    # The torso: pelvis, waist, chest and shoulders, a little square, up into the neck
    path = [h + [0, -0.24, -0.02], h + [0, 0.06, 0], s, c, (c + n) / 2 + [0, 0.02, -0.02], n + [0, 0.1, -0.02]]
    secs = [dict(w=0.5 * hips, d=0.33, e=2.6), dict(w=0.52 * hips, d=0.34, e=2.6), dict(w=0.43, d=0.3, e=2.5),
            dict(w=0.56 * chest, d=0.36, e=2.7, oy=0.02), dict(w=0.6 * chest, d=0.32, e=3.0), dict(w=0.16, d=0.16, e=2.2)]
    torso = m.add(loft(path, secs, nu=26, nv=24).deform(
        lump, bulge(c + [0.19, -0.02, 0.32], 0.2, 0.07 * bust), bulge(c + [-0.19, -0.02, 0.32], 0.2, 0.07 * bust),
        push(h + [0, -0.05, -0.3], 0.3, (0, -0.02, -0.04))), shirt_p, bones=["hips", "spine", "chest"])
    m.add(tube([(c + n) / 2 + [0, 0, -0.02], J["head"] + [0, 0.12, 0.02]], 0.15, nu=12, caps=False), skin_p, bones=["chest", "neck"])
    # Arms: a round shoulder, the upper arm in its sleeve with a rolled cuff, a bare forearm that is thick below the
    # elbow and narrows to the wrist
    sh, e, w = J["shoulder_r"], J["elbow_r"], J["wrist_r"]
    m.mirror(m.add(blob(sh + [-0.05, 0.0, 0], (0.18 * arm, 0.17, 0.18), (0.8, 0.8)), sleeve_p, bones=["upper_r"]))
    upper = [sh, sh + (e - sh) * 0.45, e + (sh - e) * 0.08]
    m.mirror(m.add(loft(upper, [(0.17 * arm, 0.17 * arm, 2.2), (0.165 * arm, 0.17 * arm, 2.2), (0.15 * arm, 0.15 * arm, 2.2)], nu=14, nv=14, caps=None),
                   sleeve_p, bones=["upper_r", "fore_r"]))
    fore_p = skin_p if rolled else sleeve_p
    fore = [e + (sh - e) * 0.12, e, e + (w - e) * 0.35, w]
    m.mirror(m.add(loft(fore, [(0.12 * arm, 0.12 * arm, 2.2), (0.13 * arm, 0.13 * arm, 2.2), (0.145 * arm, 0.13 * arm, 2.3), (0.1 * arm, 0.09 * arm, 2.3)],
                        facing=(0, 0, 1), nu=14, nv=14).deform(lump), fore_p, bones=["upper_r", "fore_r"]))
    if rolled:
        m.mirror(m.add(torus(e + (sh - e) * 0.1, 0.165 * arm, 0.055, rot=_tilt(sh - e), nu=16, nv=6), cuff_p or sleeve_p, bones=["upper_r", "fore_r"]))
    glove(m, J, glove_p, both=not left_open)
    if left_open:
        open_hand(m, J, glove_p)
    # Legs: the thigh, a knee pad over the knee, the shin, into the boot
    hp, kn, an = J["hip_r"], J["knee_r"], J["ankle_r"]
    path = [hp + [0, 0.12, 0], (hp + kn) / 2, kn, (kn + an) / 2 + [0, 0, -0.02], an + [0, 0.22, 0]]
    secs = [(0.25 * leg, 0.26 * leg, 2.3), (0.22 * leg, 0.23 * leg, 2.3), (0.17 * leg, 0.18, 2.3), (0.175 * leg, 0.18, 2.3), (0.15, 0.15, 2.3)]
    m.mirror(m.add(loft(path, secs, nu=14, nv=18).deform(lump), legs_p, bones=["thigh_r", "shin_r"]))
    if knee_p is not None:
        m.mirror(m.add(blob(kn + [0, -0.02, 0.15], (0.15, 0.17, 0.07), (0.6, 0.6)), knee_p, bones=["shin_r"]))
    boot(m, J, boot_p, sole_p)
    return torso


def _tilt(d):
    """The rotation (degrees, x then z) that stands a ring at the origin, flat in xz, across the direction d"""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    rx = math.degrees(math.atan2(d[2], d[1]))
    rz = -math.degrees(math.asin(np.clip(d[0], -1, 1)))
    return (rx, 0, rz)


def glove(m, J, paint, size=1.0, both=True):
    """A big work glove closed round a grip: a cuff that flares at the wrist, a broad back of the hand, four fingers
    curled round, and a thumb over them. The grip (for a handle) is at grip_point(J)"""
    w, he = J["wrist_r"], J["hand_end_r"]
    d = (he - w) / np.linalg.norm(he - w)
    out = np.array([1.0, 0, 0])                 # Away from the body: the back of the hand
    fwd = np.cross(d, out)
    fwd = fwd / np.linalg.norm(fwd) * np.sign(fwd[2] or 1)
    k = size
    parts = []
    parts.append(m.add(loft([w - d * 0.12, w + d * 0.02], [(0.13 * k, 0.13 * k, 2.4), (0.155 * k, 0.15 * k, 2.4)], nu=14, caps="flat"), paint, bones=["fore_r", "hand_r"]))
    palm = w + d * 0.17 * k
    parts.append(m.add(blob(palm, (0.13 * k, 0.17 * k, 0.15 * k), (0.6, 0.6)), paint, bones=["hand_r"]))
    for f in range(4):
        base = palm + d * 0.1 * k + fwd * (f - 1.5) * 0.075 * k + out * 0.06 * k
        tip = base + d * 0.06 * k - out * 0.16 * k
        curl = base + d * 0.13 * k - out * 0.06 * k
        parts.append(m.add(loft([base, curl, tip], [(0.05 * k, 0.05 * k, 2.2), (0.048 * k, 0.048 * k, 2.2), (0.044 * k, 0.044 * k, 2.2)], nu=8, nv=8),
                           paint, bones=["hand_r"]))
    parts.append(m.add(loft([palm - out * 0.06 * k + fwd * 0.08 * k, palm - out * 0.14 * k + fwd * 0.08 * k + d * 0.08 * k, palm - out * 0.14 * k + d * 0.16 * k],
                            [(0.05 * k, 0.05 * k, 2.2), (0.05 * k, 0.05 * k, 2.2), (0.045 * k, 0.045 * k, 2.2)], nu=8, nv=8), paint, bones=["hand_r"]))
    if both:
        for p in parts:
            m.mirror(p)
    return parts


def open_hand(m, J, paint, size=1.0):
    """The left hand, open, its fingers together and straight on from the palm, the thumb out to the front: a hand
    that gestures and casts. On the bone hand_l"""
    w, he = L(J["wrist_r"]), L(J["hand_end_r"])
    d = (he - w) / np.linalg.norm(he - w)
    out = np.array([-1.0, 0, 0])                # The back of the hand, away from the body
    fwd = np.cross(out, d)
    fwd = fwd / np.linalg.norm(fwd) * np.sign(fwd[2] or 1)
    k = size
    m.add(loft([w - d * 0.1, w + d * 0.02], [(0.1 * k, 0.1 * k, 2.4), (0.11 * k, 0.1 * k, 2.4)], nu=14, caps="flat"), paint, bones=["fore_l", "hand_l"])
    palm = w + d * 0.15 * k
    m.add(blob(palm, (0.06 * k, 0.13 * k, 0.12 * k), (0.6, 0.6)), paint, bones=["hand_l"])
    for f in range(4):
        base = palm + d * 0.1 * k + fwd * (f - 1.5) * 0.055 * k
        length = (0.22 - abs(f - 1.4) * 0.03) * k
        tip = base + d * length - out * 0.02 * k + fwd * (f - 1.5) * 0.015 * k
        m.add(loft([base, (base + tip) / 2 - out * 0.01 * k, tip], [(0.032 * k, 0.03 * k, 2.2), (0.028 * k, 0.026 * k, 2.2), (0.022 * k, 0.02 * k, 2.2)],
                   nu=8, nv=8), paint, bones=["hand_l"])
    thumb = palm + fwd * 0.09 * k - out * 0.02 * k
    m.add(loft([thumb, thumb + fwd * 0.07 * k + d * 0.08 * k, thumb + fwd * 0.1 * k + d * 0.16 * k],
               [(0.034 * k, 0.034 * k, 2.2), (0.03 * k, 0.03 * k, 2.2), (0.024 * k, 0.024 * k, 2.2)], nu=8, nv=8), paint, bones=["hand_l"])


def grip_point(J):
    """Where a handle goes through the right fist of glove()"""
    w, he = J["wrist_r"], J["hand_end_r"]
    d = (he - w) / np.linalg.norm(he - w)
    return w + d * 0.24 + np.array([-0.04, 0, 0])


def boot(m, J, paint, sole_p=None):
    """A heavy work boot: a shaft to above the ankle, a broad foot with a round steel toe, and a thick sole"""
    an, toe = J["ankle_r"], J["toe_r"]
    m.mirror(m.add(loft([an + [0, 0.3, -0.02], an + [0, 0.02, -0.02]], [(0.17, 0.17, 2.4), (0.19, 0.2, 2.4)], nu=14, caps=None), paint, bones=["shin_r", "foot_r"]))
    m.mirror(m.add(loft([an + [0, 0.02, -0.24], an + [0, -0.04, 0.05], toe + [0, 0.04, -0.12], toe + [0, 0.04, 0.06]],
                        [(0.19, 0.2, 2.6), (0.21, 0.22, 2.6), (0.19, 0.15, 2.4), (0.17, 0.12, 2.2)], facing=(0, 1, 0), nu=16, nv=14), paint, bones=["foot_r"]))
    m.mirror(m.add(loft([an + [0, -0.2, -0.27], toe + [0, -0.09, 0.1]], [(0.23, 0.06, 4.0), (0.2, 0.06, 4.0)], facing=(0, 1, 0), nu=14, nv=6, caps="flat"),
                   sole_p or leather((0.16, 0.12, 0.1)), bones=["foot_r"]))
