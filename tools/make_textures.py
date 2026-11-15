#!/usr/bin/env python3
"""
Writes the textures and the ability icons of the game to data/:

    data/textures/grass/grass.png       calm, even grass that the heroes stand out on. It tiles
    data/textures/road/asphalt.png      grey asphalt with a bit of grit. It tiles
    data/icons/<ability>.png            a 64x64 icon for each ability, by the name of the icon in heroes.sd

    python3 tools/make_textures.py

Like the models, these are plain files: they can be painted over or replaced, as long as they keep their names.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
rng = np.random.default_rng(7)


# Noise that tiles: random values on a grid that wraps around, smoothly interpolated
def tiling_noise(size, cells):
    grid = rng.random((cells, cells))
    coords = np.arange(size) * cells / size
    i0 = np.floor(coords).astype(int)
    t = coords - i0
    t = t * t * (3 - 2 * t)
    i1 = (i0 + 1) % cells
    rows0, rows1 = grid[i0], grid[i1]
    a = rows0[:, i0] * (1 - t)[None, :] + rows0[:, i1] * t[None, :]
    b = rows1[:, i0] * (1 - t)[None, :] + rows1[:, i1] * t[None, :]
    return a * (1 - t)[:, None] + b * t[:, None]


def fractal(size, octaves):
    total = np.zeros((size, size))
    amplitude, weight = 1.0, 0.0
    for o in range(octaves):
        total += tiling_noise(size, 4 * 2 ** o) * amplitude
        weight += amplitude
        amplitude *= 0.5
    return total / weight


def save(image, *path):
    full = os.path.join(DATA, *path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    image.save(full)
    print(os.path.relpath(full, DATA))


def make_grass():
    """Grass with some detail: patches of lighter and darker green, short blades and a speck here and there, but in a
    narrow range of tones, so a hero on it is still easy to see"""
    size = 512
    patches = fractal(size, 5)
    tint = fractal(size, 3)
    base = np.array([104, 146, 80], dtype=float)
    light = (patches - 0.5) * 34
    rgb = base[None, None, :] + light[:, :, None] * np.array([0.8, 1.0, 0.6])
    rgb += ((tint - 0.5) * 30)[:, :, None] * np.array([0.9, 0.35, -0.4])      # Yellower and bluer patches

    image = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(image)
    for _ in range(9000):                                                      # Blades, leaning a bit
        x, y = rng.uniform(0, size, 2)
        length = rng.uniform(3, 8)
        angle = rng.uniform(-0.5, 0.5) - math.pi / 2
        shade = rng.uniform(-24, 22)
        color = tuple(int(np.clip(c + shade * w, 0, 255)) for c, w in zip(base, (0.7, 1.0, 0.5)))
        for dx in (-size, 0, size):                                            # Drawn again across the edges, so it tiles
            for dy in (-size, 0, size):
                x2, y2 = x + dx + math.cos(angle) * length, y + dy + math.sin(angle) * length
                draw.line([(x + dx, y + dy), (x2, y2)], fill=color, width=1)
    for _ in range(140):                                                       # Specks: tiny flowers and clover
        x, y = rng.uniform(0, size, 2)
        color = [(232, 226, 150), (220, 220, 210), (150, 186, 96)][rng.integers(0, 3)]
        r = rng.uniform(0.8, 1.6)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
    image = image.filter(ImageFilter.GaussianBlur(0.4))
    save(image, "textures", "grass", "grass.png")


def make_asphalt():
    size = 256
    n = fractal(size, 4)
    grit = rng.random((size, size))
    value = 80 + (n - 0.5) * 14 + (grit - 0.5) * 22
    rgb = np.clip(np.stack([value, value + 1, value + 5], axis=2), 0, 255).astype(np.uint8)
    save(Image.fromarray(rgb, "RGB"), "textures", "road", "asphalt.png")


#
# Icons: a symbol on a colored, shaded background with a frame, drawn at 4x and scaled down
#

S = 256       # The size it is drawn at
OUT = 64


def icon_base(top, bottom):
    image = Image.new("RGB", (S, S))
    draw = ImageDraw.Draw(image)
    for y in range(S):
        t = y / (S - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (S, y)], fill=color)
    return image, draw


def finish(image, name):
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, S - 1, S - 1], outline=(20, 18, 16), width=10)
    draw.rectangle([10, 10, S - 11, S - 11], outline=(160, 140, 100), width=4)
    image = image.resize((OUT, OUT), Image.LANCZOS)
    save(image, "icons", name + ".png")


def poly(draw, points, fill, outline=(20, 20, 20), width=6):
    draw.polygon(points, fill=fill, outline=outline, width=width)


def chevrons(draw, color, x0, count=3):
    for i in range(count):
        x = x0 + i * 52
        poly(draw, [(x, 60), (x + 50, 128), (x, 196), (x + 30, 196), (x + 80, 128), (x + 30, 60)], color)


def icon_sprint():
    image, draw = icon_base((200, 150, 40), (110, 60, 10))
    chevrons(draw, (255, 235, 120), 34)
    finish(image, "sprint")


def icon_charge():
    image, draw = icon_base((170, 40, 30), (70, 10, 10))
    chevrons(draw, (255, 140, 90), 34)
    poly(draw, [(40, 40), (90, 70), (60, 100)], (240, 230, 210))        # Horns
    poly(draw, [(216, 40), (166, 70), (196, 100)], (240, 230, 210))
    finish(image, "charge")


def icon_hook():
    image, draw = icon_base((90, 80, 80), (30, 25, 25))
    draw.line([(128, 20), (128, 140)], fill=(30, 30, 30), width=26)
    draw.line([(128, 20), (128, 140)], fill=(190, 190, 200), width=14)
    draw.arc([60, 100, 196, 236], start=-10, end=200, fill=(30, 30, 30), width=30)
    draw.arc([60, 100, 196, 236], start=-10, end=200, fill=(200, 200, 210), width=18)
    poly(draw, [(56, 160), (40, 120), (88, 150)], (200, 200, 210))     # The barb
    draw.ellipse([110, 10, 146, 46], fill=(140, 90, 40), outline=(30, 30, 30), width=5)
    for y in (180, 205):
        draw.ellipse([150, y, 170, y + 14], fill=(170, 20, 20))         # Blood
    finish(image, "hook")


def icon_freeze():
    image, draw = icon_base((120, 200, 240), (20, 70, 140))
    c = S / 2
    for k in range(6):
        a = math.pi / 3 * k
        x, y = c + math.cos(a) * 95, c + math.sin(a) * 95
        draw.line([(c, c), (x, y)], fill=(255, 255, 255), width=16)
        for f in (0.5, 0.75):
            bx, by = c + math.cos(a) * 95 * f, c + math.sin(a) * 95 * f
            for side in (-1, 1):
                b = a + side * 0.7
                draw.line([(bx, by), (bx + math.cos(b) * 30, by + math.sin(b) * 30)], fill=(255, 255, 255), width=10)
    draw.ellipse([c - 18, c - 18, c + 18, c + 18], fill=(255, 255, 255))
    finish(image, "freeze")


def icon_chill():
    image, draw = icon_base((70, 130, 190), (15, 40, 80))
    c = S / 2
    for r, w in ((100, 10), (70, 10), (40, 10)):
        draw.ellipse([c - r, c - r, c + r, c + r], outline=(190, 235, 255), width=w)
    draw.ellipse([c - 16, c - 16, c + 16, c + 16], fill=(255, 255, 255))
    finish(image, "chill")


def icon_blink():
    image, draw = icon_base((150, 80, 220), (40, 10, 90))
    for i, r in enumerate((95, 70, 45)):
        draw.arc([128 - r, 128 - r, 128 + r, 128 + r], start=200 + i * 40, end=470 + i * 40, fill=(230, 200, 255), width=14)
    poly(draw, [(150, 60), (220, 128), (150, 196), (150, 156), (80, 156), (80, 100), (150, 100)], (250, 240, 255))
    finish(image, "blink")


def icon_slide():
    image, draw = icon_base((180, 230, 250), (60, 130, 190))
    for i, y in enumerate((80, 128, 176)):
        draw.line([(30 + i * 10, y), (170 + i * 10, y)], fill=(255, 255, 255), width=12)
    poly(draw, [(170, 70), (236, 128), (170, 186)], (255, 255, 255))
    finish(image, "slide")


def ghost(draw, fill, outline=(40, 40, 60)):
    draw.pieslice([58, 30, 198, 170], start=180, end=360, fill=fill, outline=outline, width=6)
    points = [(58, 100), (198, 100), (198, 220)]
    for k in range(5):
        x = 198 - k * 28
        points += [(x - 14, 196), (x - 28, 220)]
    points += [(58, 100)]
    draw.polygon(points, fill=fill)
    draw.line([(58, 100), (58, 220)], fill=outline, width=6)
    draw.line([(198, 100), (198, 220)], fill=outline, width=6)
    draw.ellipse([92, 80, 116, 112], fill=(20, 20, 30))
    draw.ellipse([140, 80, 164, 112], fill=(20, 20, 30))


def icon_phase_walk():
    image, draw = icon_base((110, 100, 90), (50, 45, 40))
    for row in range(5):                                                # A brick wall
        y = 30 + row * 40
        offset = 0 if row % 2 == 0 else 30
        for col in range(-1, 5):
            x = offset + col * 60
            draw.rectangle([x, y, x + 56, y + 36], fill=(150, 90, 60), outline=(70, 40, 30), width=4)
    overlay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ghost(ImageDraw.Draw(overlay), (235, 240, 255, 200))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    finish(image, "phase_walk")


def icon_fade():
    image, draw = icon_base((60, 60, 90), (15, 15, 30))
    overlay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ghost(ImageDraw.Draw(overlay), (200, 210, 255, 110), outline=(200, 210, 255))
    overlay = overlay.filter(ImageFilter.GaussianBlur(3))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    finish(image, "fade")


def icon_quick_feet():
    image, draw = icon_base((90, 170, 90), (20, 70, 30))
    poly(draw, [(70, 50), (130, 50), (130, 150), (200, 170), (200, 210), (70, 210)], (150, 90, 50))   # A boot
    draw.rectangle([70, 190, 200, 210], fill=(60, 40, 25))
    for i, y in enumerate((90, 130, 170)):
        draw.line([(20, y), (55 - i * 5, y)], fill=(255, 255, 255), width=10)
    poly(draw, [(130, 60), (190, 30), (170, 80)], (240, 240, 255))     # A wing
    finish(image, "quick_feet")


def icon_leap():
    image, draw = icon_base((200, 140, 80), (90, 50, 20))
    draw.arc([30, 70, 226, 330], start=195, end=345, fill=(30, 20, 10), width=26)      # The arc of the leap
    draw.arc([30, 70, 226, 330], start=195, end=345, fill=(255, 235, 190), width=14)
    for x in (40, 216):
        draw.ellipse([x - 22, 196, x + 22, 222], fill=(90, 60, 30), outline=(30, 20, 10), width=4)   # Dust
    poly(draw, [(118, 40), (150, 62), (138, 92), (100, 96), (88, 66)], (180, 180, 190))    # A helmet at the top
    poly(draw, [(88, 66), (60, 40), (70, 74)], (240, 230, 200), width=4)                    # with horns
    poly(draw, [(150, 62), (180, 34), (168, 72)], (240, 230, 200), width=4)
    finish(image, "leap")


def icon_iron_hide():
    image, draw = icon_base((140, 140, 150), (50, 50, 60))
    draw.ellipse([38, 38, 218, 218], fill=(120, 70, 35), outline=(25, 20, 15), width=8)     # A round shield
    draw.ellipse([62, 62, 194, 194], fill=(170, 30, 25), outline=(25, 20, 15), width=5)
    for a in range(0, 360, 45):
        x, y = 128 + math.cos(math.radians(a)) * 78, 128 + math.sin(math.radians(a)) * 78
        draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(210, 210, 215))                     # Rivets
    draw.ellipse([100, 100, 156, 156], fill=(200, 200, 210), outline=(30, 30, 35), width=5) # The boss
    finish(image, "iron_hide")


def icon_stop_sign():
    image, draw = icon_base((60, 120, 70), (20, 50, 30))
    draw.rectangle([120, 150, 136, 250], fill=(200, 200, 205), outline=(30, 30, 30), width=3)
    c, r = 128, 92

    def octagon(radius):
        return [(c + math.cos(math.pi / 8 + k * math.pi / 4) * radius, 98 + math.sin(math.pi / 8 + k * math.pi / 4) * radius) for k in range(8)]
    poly(draw, octagon(r), (245, 245, 245), width=6)
    poly(draw, octagon(r - 12), (210, 25, 30), outline=(210, 25, 30), width=1)
    draw.rectangle([74, 86, 182, 110], fill=(255, 255, 255))                                # The bar of a stop sign
    finish(image, "stop_sign")


def icon_time_warp():
    image, draw = icon_base((110, 70, 190), (25, 10, 60))
    c = S / 2
    for k in range(4):                                                                      # A spiral
        r = 100 - k * 22
        draw.arc([c - r, c - r, c + r, c + r], start=k * 70, end=k * 70 + 250, fill=(220, 190, 255), width=10)
    draw.ellipse([c - 46, c - 46, c + 46, c + 46], fill=(250, 240, 220), outline=(30, 20, 40), width=6)   # A clock face
    draw.line([(c, c), (c, c - 34)], fill=(30, 20, 40), width=8)
    draw.line([(c, c), (c + 24, c + 10)], fill=(30, 20, 40), width=8)
    finish(image, "time_warp")


def icon_rewind():
    image, draw = icon_base((60, 150, 200), (10, 40, 80))
    for x in (40, 120):                                                                     # Two arrows back
        poly(draw, [(x + 90, 60), (x + 90, 196), (x, 128)], (230, 250, 255))
    draw.arc([30, 30, 226, 226], start=200, end=520, fill=(160, 220, 255), width=8)
    finish(image, "rewind")


if __name__ == "__main__":
    make_grass()
    make_asphalt()
    icon_sprint()
    icon_charge()
    icon_hook()
    icon_freeze()
    icon_chill()
    icon_blink()
    icon_slide()
    icon_phase_walk()
    icon_fade()
    icon_quick_feet()
    icon_leap()
    icon_iron_hide()
    icon_stop_sign()
    icon_time_warp()
    icon_rewind()
