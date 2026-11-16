#!/usr/bin/env python3
"""
Writes the icons of the abilities of the heroes after the first seven, of the items with abilities, and of the perks,
to data/icons/, in the style of make_textures.py: a gradient, a bold shape with a dark outline, a gold frame.

    python3 tools/make_icons.py                  all of them
    python3 tools/make_icons.py jack hex         only these
"""

import math
import sys

from make_textures import icon_base, finish, poly, S

INK = (20, 20, 20)
C = S / 2


def circle(draw, x, y, r, fill, outline=INK, width=6):
    draw.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=width)


def line(draw, points, color, width=14, outline=True):
    if outline:
        draw.line(points, fill=INK, width=width + 10, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")


def star(draw, x, y, r, fill, points=5, inner=0.45):
    pts = []
    for k in range(points * 2):
        a = -math.pi / 2 + k * math.pi / points
        rr = r if k % 2 == 0 else r * inner
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(draw, pts, fill)


def car_shape(draw, x, y, w, color, lifted=0):
    """A car from the side: body, cabin and two wheels"""
    h = w * 0.3
    poly(draw, [(x - w / 2, y - lifted), (x + w / 2, y - lifted), (x + w / 2, y - h - lifted), (x - w / 2, y - h - lifted)], color)
    poly(draw, [(x - w * 0.25, y - h - lifted), (x + w * 0.2, y - h - lifted), (x + w * 0.1, y - h * 1.9 - lifted),
                (x - w * 0.15, y - h * 1.9 - lifted)], color)
    for wx in (x - w * 0.3, x + w * 0.3):
        circle(draw, wx, y - lifted, w * 0.1, (40, 40, 44))


# Karl


def icon_jack():
    image, draw = icon_base((90, 120, 160), (30, 40, 60))
    car_shape(draw, 128, 150, 180, (210, 70, 50), lifted=40)
    poly(draw, [(110, 210), (146, 210), (136, 120), (120, 120)], (220, 40, 30))
    draw.rectangle([90, 205, 166, 225], fill=(200, 40, 30), outline=INK, width=5)
    finish(image, "jack")


def icon_oil_change():
    image, draw = icon_base((150, 140, 110), (60, 50, 40))
    poly(draw, [(70, 50), (170, 50), (180, 70), (180, 130), (60, 130), (60, 70)], (200, 60, 40))
    line(draw, [(170, 80), (215, 100)], (180, 180, 190), 12)
    draw.ellipse([60, 170, 210, 225], fill=(15, 12, 10), outline=INK, width=5)
    for x, y in ((205, 120), (210, 145), (215, 165)):
        circle(draw, x, y, 9, (25, 20, 15))
    finish(image, "oil_change")


def icon_grease_monkey():
    image, draw = icon_base((60, 100, 150), (20, 30, 50))
    line(draw, [(60, 200), (170, 90)], (190, 190, 200), 26)
    poly(draw, [(150, 50), (210, 50), (220, 110), (190, 90), (170, 110)], (190, 190, 200))
    draw.ellipse([40, 180, 120, 220], fill=(20, 15, 10))
    finish(image, "grease_monkey")


# Birgit


def icon_footbridge():
    image, draw = icon_base((240, 170, 70), (120, 60, 20))
    draw.rectangle([0, 190, S, 230], fill=(60, 60, 64))
    for x in (40, 128, 216):
        draw.rectangle([x - 4, 205, x + 4, 215], fill=(240, 240, 230))
    poly(draw, [(20, 190), (70, 110), (186, 110), (236, 190), (210, 190), (176, 130), (80, 130), (46, 190)], (160, 110, 60))
    for x in range(80, 190, 24):
        draw.line([(x, 110), (x, 80)], fill=(240, 210, 60), width=8)
    draw.line([(76, 80), (180, 80)], fill=(240, 210, 60), width=8)
    finish(image, "footbridge")


def icon_barricade():
    image, draw = icon_base((230, 150, 60), (110, 50, 20))
    for y in (90, 150):
        for k in range(6):
            color = (220, 40, 35) if k % 2 == 0 else (245, 245, 245)
            poly(draw, [(30 + k * 33, y), (63 + k * 33, y), (63 + k * 33, y + 40), (30 + k * 33, y + 40)], color, width=4)
    for x in (50, 206):
        draw.rectangle([x - 8, 90, x + 8, 230], fill=(60, 60, 64), outline=INK, width=4)
    circle(draw, 50, 70, 16, (255, 170, 40))
    finish(image, "barricade")


def icon_overtime():
    image, draw = icon_base((200, 140, 60), (80, 50, 20))
    circle(draw, 128, 128, 90, (245, 240, 225))
    line(draw, [(128, 128), (128, 60)], (40, 40, 40), 12, outline=False)
    line(draw, [(128, 128), (180, 150)], (40, 40, 40), 12, outline=False)
    poly(draw, [(200, 30), (240, 60), (200, 90)], (255, 210, 60))
    finish(image, "overtime")


# Bent


def icon_hop_on():
    image, draw = icon_base((80, 170, 120), (20, 70, 40))
    car_shape(draw, 128, 200, 200, (60, 120, 200))
    circle(draw, 128, 70, 22, (235, 190, 150))
    poly(draw, [(108, 92), (148, 92), (156, 130), (100, 130)], (40, 140, 90))
    finish(image, "hop_on")


def icon_honk():
    image, draw = icon_base((240, 200, 80), (130, 90, 20))
    poly(draw, [(40, 100), (100, 100), (170, 50), (170, 206), (100, 156), (40, 156)], (60, 60, 64))
    for r in (40, 70):
        draw.arc([170 - r, 128 - r, 170 + r, 128 + r], start=-50, end=50, fill=(255, 250, 220), width=12)
    finish(image, "honk")


def icon_timetable():
    image, draw = icon_base((70, 150, 110), (20, 60, 40))
    draw.rectangle([45, 40, 211, 216], fill=(245, 240, 220), outline=INK, width=6)
    for k, y in enumerate(range(70, 200, 28)):
        draw.line([(60, y), (120, y)], fill=(40, 40, 40), width=8)
        draw.line([(140, y), (196, y)], fill=(200, 60, 40) if k == 1 else (40, 40, 40), width=8)
    finish(image, "timetable")


# Sigrid


def icon_broom():
    image, draw = icon_base((90, 60, 130), (25, 15, 45))
    line(draw, [(40, 210), (200, 60)], (130, 85, 40), 14)
    poly(draw, [(50, 190), (20, 240), (90, 230), (70, 180)], (220, 190, 90))
    circle(draw, 200, 50, 30, (250, 245, 200), width=0)
    circle(draw, 214, 44, 26, (90, 60, 130), outline=(90, 60, 130), width=0)
    finish(image, "broom")


def icon_hex():
    image, draw = icon_base((90, 160, 70), (20, 60, 20))
    draw.ellipse([50, 100, 206, 210], fill=(110, 180, 70), outline=INK, width=6)
    for x in (90, 166):
        circle(draw, x, 100, 26, (110, 180, 70))
        circle(draw, x + 4, 98, 11, (20, 20, 20), width=0)
    draw.arc([90, 140, 166, 180], start=10, end=170, fill=INK, width=6)
    star(draw, 200, 50, 26, (230, 200, 255))
    finish(image, "hex")


def icon_nine_lives():
    image, draw = icon_base((70, 50, 90), (15, 10, 25))
    poly(draw, [(70, 210), (70, 110), (90, 70), (110, 100), (146, 100), (166, 70), (186, 110), (186, 210)], (20, 20, 24),
         outline=(160, 140, 200))
    for x in (106, 150):
        draw.ellipse([x - 12, 125, x + 12, 145], fill=(250, 220, 60))
    draw.text((112, 165), "9", fill=(250, 220, 60))
    finish(image, "nine_lives")


# Tobias


def icon_flash_photo():
    image, draw = icon_base((240, 150, 170), (120, 40, 70))
    draw.rounded_rectangle([40, 90, 216, 200], radius=16, fill=(40, 40, 44), outline=INK, width=6)
    draw.rectangle([70, 70, 120, 92], fill=(40, 40, 44), outline=INK, width=5)
    circle(draw, 128, 145, 38, (120, 160, 220))
    circle(draw, 128, 145, 18, (30, 30, 50))
    star(draw, 200, 60, 40, (255, 255, 220), points=8, inner=0.3)
    finish(image, "flash_photo")


def icon_selfie():
    image, draw = icon_base((250, 170, 190), (140, 60, 90))
    for x in (85, 171):
        circle(draw, x, 110, 36, (235, 190, 150))
        poly(draw, [(x - 40, 160), (x + 40, 160), (x + 50, 230), (x - 50, 230)], (240, 120, 150) if x < 128 else (120, 140, 220))
    line(draw, [(108, 60), (148, 40)], (255, 255, 255), 8)
    poly(draw, [(148, 30), (168, 44), (148, 54)], (255, 255, 255))
    line(draw, [(148, 196), (108, 216)], (255, 255, 255), 8)
    finish(image, "selfie")


def icon_lost():
    image, draw = icon_base((230, 200, 150), (130, 100, 60))
    draw.rectangle([40, 50, 216, 206], fill=(240, 230, 200), outline=INK, width=6)
    draw.line([(40, 128), (216, 110)], fill=(180, 160, 120), width=6)
    draw.line([(120, 50), (100, 206)], fill=(180, 160, 120), width=6)
    draw.text((112, 100), "?", fill=(200, 40, 40))
    circle(draw, 128, 128, 34, None, outline=(200, 40, 40), width=10)
    finish(image, "lost")


# Mads


def icon_ollie():
    image, draw = icon_base((250, 140, 70), (130, 50, 10))
    car_shape(draw, 128, 220, 150, (80, 80, 90))
    poly(draw, [(50, 120), (200, 80), (204, 96), (54, 136)], (40, 40, 44))
    for x, y in ((80, 132), (176, 104)):
        circle(draw, x, y, 10, (250, 230, 120))
    draw.arc([40, 40, 220, 180], start=200, end=330, fill=(255, 255, 255), width=8)
    finish(image, "ollie")


def icon_grind():
    image, draw = icon_base((200, 110, 60), (80, 30, 10))
    draw.line([(20, 200), (236, 120)], fill=(240, 240, 230), width=12)
    poly(draw, [(60, 160), (190, 112), (196, 128), (66, 176)], (40, 40, 44))
    for k in range(7):
        a = math.pi * (1.05 + k * 0.08)
        draw.line([(70, 180), (70 + math.cos(a) * 60, 180 + math.sin(a) * 40)], fill=(255, 220, 90), width=5)
    finish(image, "grind")


def icon_rolling():
    image, draw = icon_base((240, 120, 60), (110, 40, 10))
    for k, x in enumerate((60, 110, 160)):
        poly(draw, [(x, 70), (x + 50, 128), (x, 186), (x + 22, 186), (x + 72, 128), (x + 22, 70)], (255, 220 - k * 40, 120))
    circle(draw, 60, 200, 18, (250, 230, 120))
    circle(draw, 196, 200, 18, (250, 230, 120))
    finish(image, "rolling")


# Ditte


def icon_call_ambulance():
    image, draw = icon_base((240, 90, 90), (110, 20, 20))
    draw.rectangle([40, 110, 216, 190], fill=(245, 245, 245), outline=INK, width=6)
    draw.rectangle([150, 80, 216, 110], fill=(245, 245, 245), outline=INK, width=6)
    draw.rectangle([82, 130, 122, 170], fill=(220, 40, 40))
    draw.rectangle([92, 120, 112, 180], fill=(220, 40, 40))
    circle(draw, 90, 196, 18, (40, 40, 44))
    circle(draw, 180, 196, 18, (40, 40, 44))
    circle(draw, 170, 64, 14, (80, 160, 255))
    finish(image, "call_ambulance")


def icon_bandage():
    image, draw = icon_base((120, 200, 130), (30, 90, 40))
    poly(draw, [(60, 160), (160, 60), (196, 96), (96, 196)], (245, 225, 190))
    draw.rectangle([108, 108, 148, 148], fill=(235, 205, 165))
    for x, y in ((118, 118), (138, 118), (118, 138), (138, 138)):
        circle(draw, x, y, 4, (180, 150, 110), width=0)
    finish(image, "bandage")


def icon_colleague():
    image, draw = icon_base((220, 230, 240), (110, 120, 140))
    draw.rectangle([98, 50, 158, 206], fill=(220, 40, 40), outline=INK, width=6)
    draw.rectangle([50, 98, 206, 158], fill=(220, 40, 40), outline=INK, width=6)
    draw.rectangle([104, 56, 152, 200], fill=(220, 40, 40))
    finish(image, "colleague")


# Gudrun


def icon_cane_trip():
    image, draw = icon_base((200, 160, 200), (90, 60, 90))
    line(draw, [(60, 40), (60, 60), (100, 60), (180, 210)], (140, 90, 50), 16)
    star(draw, 190, 80, 24, (255, 230, 90))
    star(draw, 220, 130, 16, (255, 230, 90))
    finish(image, "cane_trip")


def icon_knitting():
    image, draw = icon_base((230, 140, 190), (120, 40, 90))
    circle(draw, 128, 140, 70, (230, 90, 160))
    for k in range(5):
        draw.arc([58 + k * 6, 70 + k * 10, 198 - k * 6, 210 - k * 10], start=200, end=340, fill=(180, 40, 110), width=6)
    line(draw, [(60, 40), (170, 200)], (220, 220, 230), 8)
    line(draw, [(196, 40), (90, 200)], (220, 220, 230), 8)
    finish(image, "knitting")


def icon_respect():
    image, draw = icon_base((200, 200, 220), (90, 90, 110))
    car_shape(draw, 90, 200, 120, (200, 60, 50))
    circle(draw, 190, 110, 30, (240, 230, 225))
    poly(draw, [(160, 140), (220, 140), (230, 220), (150, 220)], (170, 110, 170))
    star(draw, 70, 80, 30, (255, 80, 60), points=8, inner=0.6)
    finish(image, "respect")


# Magnus


def magnet(draw, x, y, s, flip=False):
    draw.arc([x - s, y - s, x + s, y + s], start=0 if not flip else 180, end=180 if not flip else 360, fill=INK, width=int(s * 0.62))
    draw.arc([x - s, y - s, x + s, y + s], start=0 if not flip else 180, end=180 if not flip else 360, fill=(220, 40, 40), width=int(s * 0.5))
    dy = -1 if not flip else 1
    for side in (-1, 1):
        draw.rectangle([x + side * s * 0.75 - s * 0.25, y + dy * s * 0.45 - s * 0.3, x + side * s * 0.75 + s * 0.25, y],
                       fill=(230, 230, 235), outline=INK, width=5)


def icon_repel():
    image, draw = icon_base((150, 160, 190), (50, 55, 80))
    magnet(draw, 128, 90, 60)
    for x in (60, 128, 196):
        line(draw, [(x, 180), (x, 236)], (255, 250, 200), 10)
        poly(draw, [(x - 16, 220), (x + 16, 220), (x, 246)], (255, 250, 200))
    finish(image, "repel")


def icon_attract():
    image, draw = icon_base((170, 140, 190), (60, 40, 80))
    magnet(draw, 70, 128, 50)
    circle(draw, 200, 128, 26, (235, 190, 150))
    for y in (100, 156):
        line(draw, [(170, y), (120, y)], (255, 250, 200), 8)
        poly(draw, [(126, y - 14), (126, y + 14), (106, y)], (255, 250, 200))
    finish(image, "attract")


def icon_steel_frame():
    image, draw = icon_base((170, 175, 190), (70, 75, 90))
    poly(draw, [(128, 30), (210, 70), (200, 170), (128, 226), (56, 170), (46, 70)], (180, 185, 195))
    for x in (90, 166):
        for y in (90, 170):
            circle(draw, x, y, 10, (120, 125, 135))
    finish(image, "steel_frame")


# Stormy


def icon_lightning():
    image, draw = icon_base((90, 100, 140), (20, 25, 50))
    for x, y, r in ((90, 70, 40), (140, 60, 50), (180, 80, 36)):
        circle(draw, x, y, r, (110, 115, 135), width=0)
    poly(draw, [(140, 100), (100, 170), (130, 170), (110, 236), (170, 150), (138, 150), (160, 100)], (255, 220, 60))
    finish(image, "lightning")


def icon_downpour():
    image, draw = icon_base((100, 130, 180), (30, 50, 90))
    for x, y, r in ((80, 70, 40), (130, 60, 50), (180, 75, 38)):
        circle(draw, x, y, r, (150, 155, 175), width=0)
    for k in range(9):
        x = 50 + k * 20
        y = 130 + (k % 3) * 25
        line(draw, [(x, y), (x - 10, y + 35)], (150, 200, 255), 6, outline=False)
    finish(image, "downpour")


def icon_tailwind():
    image, draw = icon_base((140, 200, 230), (40, 90, 140))
    for y, w in ((80, 160), (128, 190), (176, 140)):
        draw.line([(40, y), (40 + w, y)], fill=(255, 255, 255), width=12)
        draw.arc([20 + w, y - 30, 80 + w, y + 10], start=90, end=330, fill=(255, 255, 255), width=10)
    finish(image, "tailwind")


# Hugo


def icon_puppet():
    image, draw = icon_base((150, 90, 190), (50, 20, 70))
    draw.rectangle([60, 30, 196, 46], fill=(120, 80, 40), outline=INK, width=4)
    for x in (80, 128, 176):
        draw.line([(x, 46), (x, 140)], fill=(240, 240, 240), width=3)
    circle(draw, 128, 150, 24, (235, 190, 150))
    poly(draw, [(108, 175), (148, 175), (156, 230), (100, 230)], (200, 60, 60))
    draw.line([(108, 185), (80, 140)], fill=(200, 60, 60), width=10)
    draw.line([(148, 185), (176, 140)], fill=(200, 60, 60), width=10)
    finish(image, "puppet")


def icon_sleep():
    image, draw = icon_base((70, 70, 150), (15, 15, 50))
    circle(draw, 110, 140, 70, (250, 240, 180), width=0)
    circle(draw, 145, 120, 62, (70, 70, 150), outline=(70, 70, 150), width=0)
    for x, y, s in ((170, 70, 40), (205, 40, 26)):
        poly(draw, [(x, y), (x + s, y), (x, y + s), (x + s, y + s), (x + s, y + s + 6), (x - 2, y + s + 6), (x + s - 4, y + 6),
                    (x, y + 6)], (255, 255, 255), width=3)
    finish(image, "sleep")


def icon_calm_mind():
    image, draw = icon_base((160, 120, 200), (60, 40, 90))
    for r in (95, 70, 45, 20):
        draw.ellipse([C - r, C - r, C + r, C + r], outline=(230, 210, 255), width=10)
    finish(image, "calm_mind")


# Tim & Tom


def kid(draw, x, y, color, alpha=255):
    circle(draw, x, y - 50, 26, (235, 190, 150))
    poly(draw, [(x - 30, y - 22), (x + 30, y - 22), (x + 34, y + 50), (x - 34, y + 50)], color)


def icon_split():
    image, draw = icon_base((240, 210, 80), (130, 100, 20))
    kid(draw, 80, 150, (240, 200, 40))
    kid(draw, 176, 150, (170, 170, 180))
    line(draw, [(110, 70), (150, 70)], (255, 255, 255), 8)
    poly(draw, [(150, 58), (172, 70), (150, 82)], (255, 255, 255))
    finish(image, "split")


def icon_swap():
    image, draw = icon_base((90, 140, 230), (20, 50, 120))
    draw.arc([50, 50, 206, 206], start=200, end=340, fill=(255, 255, 255), width=16)
    poly(draw, [(196, 90), (226, 96), (206, 126)], (255, 255, 255))
    draw.arc([50, 50, 206, 206], start=20, end=160, fill=(255, 255, 255), width=16)
    poly(draw, [(60, 166), (30, 160), (50, 130)], (255, 255, 255))
    finish(image, "swap")


def icon_double_take():
    image, draw = icon_base((240, 200, 90), (120, 80, 20))
    kid(draw, 100, 150, (240, 200, 40))
    kid(draw, 156, 150, (90, 140, 230))
    draw.text((118, 30), "?!", fill=(255, 255, 255))
    finish(image, "double_take")


# Kenji


def icon_smoke_bomb():
    image, draw = icon_base((110, 110, 120), (30, 30, 35))
    for x, y, r in ((90, 110, 50), (150, 90, 56), (170, 150, 46), (100, 160, 44)):
        circle(draw, x, y, r, (190, 190, 200), width=0)
    circle(draw, 128, 200, 26, (30, 30, 34))
    line(draw, [(128, 174), (140, 150)], (200, 150, 60), 6, outline=False)
    finish(image, "smoke_bomb")


def icon_shadow_step():
    image, draw = icon_base((60, 40, 70), (10, 5, 15))
    car_shape(draw, 150, 200, 150, (110, 110, 120))
    for k, x in enumerate((50, 80, 110)):
        circle(draw, x, 110, 18, (40 + k * 30, 20 + k * 20, 50 + k * 30), width=0)
    poly(draw, [(30, 60), (60, 40), (60, 80)], (200, 30, 30))
    finish(image, "shadow_step")


def icon_roll():
    image, draw = icon_base((80, 80, 90), (20, 20, 25))
    draw.arc([50, 50, 206, 206], start=0, end=300, fill=(200, 30, 30), width=20)
    poly(draw, [(196, 70), (230, 110), (186, 116)], (200, 30, 30))
    circle(draw, 128, 128, 30, (20, 20, 24), outline=(200, 30, 30))
    finish(image, "roll")


# Ivar


def icon_battle_cry():
    image, draw = icon_base((200, 80, 50), (90, 20, 10))
    poly(draw, [(60, 90), (110, 90), (140, 60), (150, 200), (110, 170), (60, 170)], (230, 230, 230))
    for r in (40, 70, 100):
        draw.arc([150 - r, 128 - r, 150 + r, 128 + r], start=-45, end=45, fill=(255, 220, 120), width=10)
    finish(image, "battle_cry")


def icon_axe_throw():
    image, draw = icon_base((140, 100, 60), (50, 30, 15))
    line(draw, [(60, 200), (170, 90)], (130, 85, 40), 14)
    poly(draw, [(150, 50), (230, 70), (210, 150), (170, 110)], (210, 210, 220))
    for k in range(3):
        draw.line([(40 + k * 20, 220 - k * 30), (10 + k * 20, 236 - k * 30)], fill=(255, 255, 255), width=5)
    finish(image, "axe_throw")


def icon_berserk():
    image, draw = icon_base((220, 50, 40), (70, 0, 0))
    circle(draw, 128, 128, 80, (240, 200, 180))
    for x in (95, 161):
        poly(draw, [(x - 22, 100), (x + 22, 110), (x - 22, 120)] if x < 128 else [(x + 22, 100), (x - 22, 110), (x + 22, 120)], (200, 0, 0))
    draw.rectangle([90, 150, 166, 180], fill=(255, 255, 255), outline=INK, width=5)
    for x in range(100, 166, 14):
        draw.line([(x, 150), (x, 180)], fill=INK, width=3)
    finish(image, "berserk")


ICONS = {name[5:]: f for name, f in dict(globals()).items() if name.startswith("icon_") and callable(f) and f.__module__ == __name__ and name != "icon_base"}

if __name__ == "__main__":
    for name in sys.argv[1:] or ICONS:
        ICONS[name]()
