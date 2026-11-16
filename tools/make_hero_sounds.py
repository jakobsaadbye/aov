#!/usr/bin/env python3
"""
Writes the sounds of the abilities of the heroes after the first seven, and of the items that are used, to
data/sounds/ability/ and data/sounds/item/, with the synthesizer of make_sounds.py.

    python3 tools/make_hero_sounds.py
"""

import numpy as np

from make_sounds import (save_sound, noise, env, adsr, osc, tone, glide, whoosh, thud, crack, metal, mix, place,
                         bandpass, highpass, lowpass, sweep_filter, chord_bells, fm, voice, saturate, pluck, n_of, rng)


def ratchet(clicks, spacing, f=2600):
    out = np.zeros(n_of(clicks * spacing + 0.1))
    for k in range(clicks):
        place(out, highpass(noise(0.012), f) * env(0.012, 0.0002, 6) * 0.8, k * spacing)
        place(out, metal(f / 6, 0.03, ring=0.1) * env(0.03, 0.0002, 8) * 0.3, k * spacing)
    return out


def horn(freq, seconds):
    x = sum(osc(freq * h, "saw") * (0.5 / h) for h in (1, 1.26, 1.5))
    return saturate(lowpass(x[:n_of(seconds)], 2200) * adsr(seconds, 0.02, 0.06, 0.9), 1.6)


def abilities():
    # Karl's jack: a ratchet that pumps, a groan of metal
    out = mix(ratchet(6, 0.07), metal(110, 0.8, ring=0.6) * env(0.8, 0.01, 3) * 0.4)
    save_sound("ability", "jack", out, level=0.7, room=0.6)

    # Oil change: a glug of thick liquid and a splat
    out = np.zeros(n_of(0.8))
    for k in range(4):
        place(out, osc(glide(180 + k * 20, 90, 0.08), "sine") * env(0.08, 0.002, 5) * 0.6, k * 0.1)
    place(out, lowpass(noise(0.25), 900) * env(0.25, 0.002, 6) * 0.9, 0.45)
    save_sound("ability", "oil", out, level=0.7, room=0.5)

    # Birgit's footbridge: planks thrown down, hammer blows
    out = np.zeros(n_of(1.0))
    for k in range(5):
        place(out, mix(thud(160, 90, 0.15, 2) * 0.6, bandpass(noise(0.05), 400, 2000) * env(0.05, 0.001, 6)), k * 0.14)
    place(out, metal(800, 0.3, ring=0.5) * env(0.3, 0.0005, 6) * 0.5, 0.75)
    save_sound("ability", "build", out, level=0.75, room=0.7)

    # Barricade: a heavy thing set down, a clatter
    out = mix(thud(110, 50, 0.4, 2.5), bandpass(noise(0.2), 300, 3000) * env(0.2, 0.001, 5) * 0.6)
    save_sound("ability", "barricade", out, level=0.75, room=0.6)

    # Bent hops on: a grunt and a thump on a roof
    out = mix(voice(glide(160, 130, 0.2), 0.2, "uh", breath=0.4) * adsr(0.2, 0.01, 0.1) * 0.4, np.zeros(n_of(0.5)))
    place(out, mix(thud(90, 60, 0.3, 2) * 0.9, metal(300, 0.25, ring=0.3) * env(0.25, 0.001, 8) * 0.3), 0.15)
    save_sound("ability", "hop_on", out, level=0.75, room=0.6)

    # Honk: a bus horn, two blasts
    out = np.zeros(n_of(1.0))
    place(out, horn(220, 0.25), 0)
    place(out, horn(220, 0.45), 0.35)
    save_sound("ability", "honk", out, level=0.8, room=0.8)

    # Sigrid's broom: a rush of air with a cackle
    out = whoosh(1.0, 300, 2400, 1.6) * 1.2
    for k in range(4):
        place(out, voice(glide(700, 550, 0.08), 0.08, "ah", breath=0.3) * env(0.08, 0.005, 4) * 0.3, 0.1 + k * 0.1)
    save_sound("ability", "broom", out, level=0.7, room=1.0)

    # Hex: a sparkle that turns into a croak
    out = mix(chord_bells([1046, 1318, 1568], 0.6, 2.5, 3.0) * 0.3, np.zeros(n_of(0.9)))
    croak = saturate(osc(glide(140, 100, 0.25), "saw") * env(0.25, 0.01, 2), 3) * 0.5
    place(out, lowpass(croak, 900), 0.45)
    save_sound("ability", "hex", out, level=0.7, room=1.1, wet=0.3)

    # Tobias's flash: a shutter click and the whine of the flash
    out = mix(crack(0.01, 4000) * 1.5, osc(glide(2000, 6000, 0.4), "sine") * env(0.4, 0.01, 3) * 0.15)
    place(out, crack(0.008, 3000), 0.06)
    save_sound("ability", "flash", out, level=0.65, room=0.5)

    # Selfie: a click, a whoosh both ways
    out = mix(crack(0.01, 4000) * 1.2, np.zeros(n_of(0.6)))
    place(out, whoosh(0.4, 600, 2400, 1.2), 0.08)
    save_sound("ability", "selfie", out, level=0.65, room=0.6)

    # Mads: the clack of an ollie, and the scrape of a grind
    out = mix(crack(0.02, 1500) * 1.3, np.zeros(n_of(0.6)))
    place(out, mix(thud(200, 120, 0.12, 2) * 0.6, crack(0.02, 1200)), 0.4)
    save_sound("ability", "ollie", out, level=0.7, room=0.5)
    out = mix(bandpass(noise(0.9), 1800, 6000) * adsr(0.9, 0.02, 0.15, 0.8) * 0.8, metal(900, 0.9, ring=0.4) * 0.2)
    save_sound("ability", "grind", out, level=0.65, room=0.5)

    # Ditte: a radio that crackles and beeps, a bandage torn off its roll
    out = mix(bandpass(noise(0.5), 800, 3500) * env(0.5, 0.01, 2) * 0.4, np.zeros(n_of(0.6)))
    place(out, tone(1200, 0.1, "square") * env(0.1, 0.002, 2) * 0.2, 0.25)
    place(out, tone(1600, 0.1, "square") * env(0.1, 0.002, 2) * 0.2, 0.38)
    save_sound("ability", "radio", out, level=0.6, room=0.3)
    out = bandpass(noise(0.4), 1500, 7000) * adsr(0.4, 0.01, 0.1, 0.7)
    save_sound("ability", "bandage", out, level=0.55, room=0.4)

    # Gudrun: a cane that whacks, knitting needles that click
    out = mix(crack(0.02, 1800) * 1.4, thud(250, 140, 0.12, 2) * 0.5)
    save_sound("ability", "cane", out, level=0.7, room=0.5)
    out = np.zeros(n_of(0.6))
    for k in range(6):
        place(out, metal(2200, 0.04, ring=0.2) * env(0.04, 0.0003, 8) * 0.5, k * 0.08)
    save_sound("ability", "knit", out, level=0.6, room=0.5)

    # Magnus: a hum that swells and pushes out, or pulls in
    hum = sum(osc(f, "sine") for f in (55, 110, 165))[:n_of(0.9)] * 0.3
    save_sound("ability", "repel", mix(hum * adsr(0.9, 0.05, 0.4), whoosh(0.9, 200, 1600, 1.4) * 0.7), level=0.75, room=0.8)
    save_sound("ability", "attract", mix(hum * adsr(0.9, 0.3, 0.1), whoosh(0.9, 1600, 200, 1.4) * 0.7), level=0.75, room=0.8)

    # Stormy: thunder, and rain
    length = 2.2
    rumble = lowpass(noise(length), 220) * env(length, 0.005, 1.5) * 1.6
    out = mix(crack(0.04, 2500) * 2, rumble)
    save_sound("ability", "lightning", out, level=0.85, room=1.5, wet=0.3)
    out = highpass(noise(2.0), 1500) * adsr(2.0, 0.3, 0.6, 0.6) * 0.6
    for k in range(40):
        place(out, highpass(noise(0.01), 3000) * env(0.01, 0.0002, 6) * 0.3, rng.uniform(0, 1.9))
    save_sound("ability", "downpour", out, level=0.55, room=0.6)

    # Hugo: a swirl of chimes, and a lullaby of falling bells
    out = sum(fm(f, 2.0, 2.0, 1.0, 1.5) * env(1.0, 0.05, 2) for f in (440, 554, 659)) * 0.15
    save_sound("ability", "puppet", out, level=0.6, room=1.2, wet=0.35)
    out = np.zeros(n_of(1.4))
    for k, f in enumerate((1318, 1046, 880, 659)):
        place(out, chord_bells([f], 0.6, 2.0, 2.5) * 0.3, k * 0.2)
    save_sound("ability", "sleep", out, level=0.55, room=1.4, wet=0.35)

    # Tim & Tom: a pop, and a giggle; a swap whoosh
    out = mix(crack(0.015, 2500), osc(glide(400, 900, 0.12), "sine") * env(0.12, 0.002, 3) * 0.4)
    save_sound("ability", "split", out, level=0.6, room=0.6)
    save_sound("ability", "swap", mix(whoosh(0.4, 2400, 600, 1.2), crack(0.01, 3000)), level=0.6, room=0.6)

    # Kenji: a smoke bomb that bursts and hisses, a step out of the shadows
    out = mix(thud(130, 60, 0.2, 3) * 0.8, crack(0.03, 1000) * 1.2, highpass(noise(1.0), 2000) * env(1.0, 0.01, 2.5) * 0.5)
    save_sound("ability", "smoke", out, level=0.7, room=0.8)
    save_sound("ability", "shadow_step", mix(whoosh(0.3, 1800, 300, 1.0), crack(0.01, 3500) * 0.6), level=0.6, room=0.9)

    # Ivar: a roar, an axe that spins through the air, and hits
    roar = saturate(voice(glide(120, 90, 0.9), 0.9, "ah", breath=0.6, vibrato=0.04) * adsr(0.9, 0.05, 0.3) * 2, 2.5)
    save_sound("ability", "battle_cry", roar, level=0.8, room=1.0)
    out = np.zeros(n_of(0.6))
    for k in range(5):
        place(out, whoosh(0.1, 400, 1800, 1.0) * 0.7, k * 0.1)
    save_sound("ability", "axe_throw", out, level=0.6, room=0.6)
    save_sound("ability", "axe_hit", mix(thud(120, 60, 0.3, 2.5), metal(400, 0.3, ring=0.5) * env(0.3, 0.001, 6) * 0.4),
               level=0.75, room=0.7)


def items():
    # A banana peel: a squish, and a slide whistle
    out = mix(lowpass(noise(0.1), 1200) * env(0.1, 0.002, 6) * 0.8, np.zeros(n_of(0.7)))
    place(out, osc(glide(1800, 500, 0.5), "sine") * env(0.5, 0.01, 2) * 0.3, 0.08)
    save_sound("item", "banana", out, level=0.6, room=0.5)
    # A pop of bubble wrap
    out = np.zeros(n_of(0.5))
    for k in range(5):
        place(out, crack(0.008, 2500) * rng.uniform(0.6, 1.0), k * 0.07 + rng.uniform(0, 0.02))
    save_sound("item", "bubble_wrap", out, level=0.65, room=0.4)
    # A mirror that rings
    save_sound("item", "mirror", chord_bells([1568, 2093, 2637], 0.8, 2.5, 3.0) * 0.4, level=0.6, room=1.2, wet=0.35)
    # A can that is opened and gulped
    out = mix(highpass(noise(0.15), 3000) * env(0.15, 0.001, 4), np.zeros(n_of(0.8)))
    for k in range(3):
        place(out, osc(glide(220, 120, 0.1), "sine") * env(0.1, 0.005, 4) * 0.5, 0.25 + k * 0.15)
    save_sound("item", "drink", out, level=0.6, room=0.4)
    # A cone set down, a megaphone, a squeaky chicken, a balloon
    save_sound("item", "cone", mix(thud(240, 140, 0.15, 2) * 0.7, crack(0.02, 1500) * 0.6), level=0.6, room=0.4)
    out = saturate(bandpass(voice(glide(220, 200, 0.5), 0.5, "ah", breath=0.2) * 2, 600, 3000), 3) * adsr(0.5, 0.01, 0.1)
    save_sound("item", "megaphone", out, level=0.7, room=0.6)
    out = osc(glide(900, 1400, 0.25), "saw") * env(0.25, 0.01, 2) * 0.3
    save_sound("item", "chicken", bandpass(out, 600, 4000), level=0.6, room=0.4)
    save_sound("item", "balloon", mix(osc(glide(300, 600, 0.3), "sine") * env(0.3, 0.01, 2) * 0.3, highpass(noise(0.3), 2000) * 0.2),
               level=0.5, room=0.4)
    # Dice that roll
    out = np.zeros(n_of(0.6))
    for k in range(6):
        place(out, crack(0.01, 2200) * (1 - k * 0.12), k * 0.07 + rng.uniform(0, 0.02))
    save_sound("item", "dice", out, level=0.6, room=0.4)


if __name__ == "__main__":
    abilities()
    items()
