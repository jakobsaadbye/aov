#!/usr/bin/env python3
"""
Writes the icons of the abilities of the heroes after the first seven, of the items, the perks and the statuses, to
data/icons/, like make_textures.py: shapes drawn on a background, which tools/iconkit.py paints as raised, lit objects.

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


# Magnus


def magnet(draw, x, y, s, flip=False):
    draw.arc([x - s, y - s, x + s, y + s], start=0 if not flip else 180, end=180 if not flip else 360, fill=INK, width=int(s * 0.62))
    draw.arc([x - s, y - s, x + s, y + s], start=0 if not flip else 180, end=180 if not flip else 360, fill=(220, 40, 40), width=int(s * 0.5))
    dy = -1 if not flip else 1
    for side in (-1, 1):
        draw.rectangle([x + side * s * 0.75 - s * 0.25, y + dy * s * 0.45 - s * 0.3, x + side * s * 0.75 + s * 0.25, y],
                       fill=(230, 230, 235), outline=INK, width=5)


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


# Items


def icon_item_banana_peel():
    image, draw = icon_base((250, 220, 90), (150, 110, 20))
    for k, (dx, dy) in enumerate(((-60, 40), (60, 40), (0, 70))):
        poly(draw, [(128, 110), (128 + dx * 0.4, 120), (128 + dx, 128 + dy), (128 + dx * 0.7, 140 + dy), (128, 140)], (250, 225, 60))
    circle(draw, 128, 100, 22, (130, 95, 30))
    finish(image, "item_banana_peel")


def icon_item_mirror():
    image, draw = icon_base((180, 200, 230), (60, 70, 110))
    draw.ellipse([60, 30, 196, 190], fill=(150, 110, 60), outline=INK, width=6)
    draw.ellipse([74, 44, 182, 176], fill=(200, 225, 250))
    draw.line([(95, 80), (130, 60)], fill=(255, 255, 255), width=8)
    draw.rectangle([115, 186, 141, 240], fill=(150, 110, 60), outline=INK, width=5)
    finish(image, "item_mirror")


def icon_item_energy_drink():
    image, draw = icon_base((80, 150, 255), (20, 40, 120))
    draw.rounded_rectangle([80, 50, 176, 226], radius=14, fill=(40, 90, 220), outline=INK, width=6)
    draw.rectangle([86, 50, 170, 66], fill=(200, 200, 210))
    poly(draw, [(140, 90), (105, 145), (130, 145), (115, 200), (155, 130), (130, 130), (145, 90)], (255, 230, 60))
    finish(image, "item_energy_drink")


def icon_item_traffic_cone():
    image, draw = icon_base((255, 160, 80), (130, 60, 10))
    draw.rectangle([50, 205, 206, 228], fill=(240, 110, 20), outline=INK, width=5)
    poly(draw, [(128, 30), (180, 205), (76, 205)], (255, 120, 20))
    poly(draw, [(108, 100), (148, 100), (158, 135), (98, 135)], (250, 250, 250), width=3)
    finish(image, "item_traffic_cone")


def icon_item_megaphone():
    image, draw = icon_base((220, 220, 230), (90, 90, 110))
    poly(draw, [(50, 105), (90, 105), (190, 50), (190, 206), (90, 151), (50, 151)], (240, 240, 245))
    draw.rectangle([70, 150, 92, 200], fill=(60, 60, 64), outline=INK, width=4)
    for r in (30, 55):
        draw.arc([190 - r, 128 - r, 190 + r, 128 + r], start=-45, end=45, fill=(220, 40, 40), width=9)
    finish(image, "item_megaphone")


def icon_item_rubber_chicken():
    image, draw = icon_base((250, 230, 100), (160, 120, 20))
    draw.ellipse([60, 110, 190, 190], fill=(250, 220, 60), outline=INK, width=6)
    poly(draw, [(170, 120), (200, 50), (225, 60), (195, 130)], (250, 220, 60))
    circle(draw, 210, 55, 22, (250, 220, 60))
    poly(draw, [(228, 52), (250, 60), (228, 68)], (240, 120, 40))
    poly(draw, [(200, 30), (210, 18), (220, 32)], (220, 40, 40))
    circle(draw, 210, 50, 4, (0, 0, 0), width=0)
    finish(image, "item_rubber_chicken")


def icon_item_balloon():
    image, draw = icon_base((255, 140, 170), (140, 30, 70))
    draw.ellipse([70, 30, 186, 160], fill=(240, 60, 100), outline=INK, width=6)
    draw.ellipse([95, 55, 120, 85], fill=(255, 170, 190))
    poly(draw, [(118, 158), (138, 158), (128, 172)], (240, 60, 100))
    draw.line([(128, 172), (115, 200), (140, 230)], fill=(240, 240, 240), width=4)
    finish(image, "item_balloon")


def icon_item_lucky_dice():
    image, draw = icon_base((200, 200, 210), (70, 70, 90))
    draw.rounded_rectangle([50, 50, 206, 206], radius=24, fill=(250, 250, 250), outline=INK, width=6)
    for x, y in ((90, 90), (128, 128), (166, 166), (166, 90), (90, 166)):
        circle(draw, x, y, 13, (200, 30, 30), width=0)
    finish(image, "item_lucky_dice")


def icon_item_umbrella():
    image, draw = icon_base((240, 100, 120), (110, 20, 40))
    draw.pieslice([30, 40, 226, 220], start=180, end=360, fill=(230, 50, 70), outline=INK, width=6)
    line(draw, [(128, 130), (128, 210), (110, 225), (95, 210)], (60, 40, 30), 9)
    finish(image, "item_umbrella")


# Perks: a bronze medallion with a sign on it


def medallion(top, bottom):
    image, draw = icon_base(top, bottom)
    circle(draw, 128, 128, 100, (160, 120, 60), width=8)
    circle(draw, 128, 128, 82, (110, 80, 40), outline=(220, 180, 100), width=5)
    return image, draw


def icon_perk_thick_skin():
    image, draw = medallion((200, 150, 120), (100, 60, 40))
    poly(draw, [(128, 70), (175, 90), (170, 150), (128, 185), (86, 150), (81, 90)], (230, 180, 140))
    finish(image, "perk_thick_skin")


def icon_perk_scavenger():
    image, draw = medallion((200, 180, 120), (90, 70, 30))
    circle(draw, 115, 115, 36, None, outline=(240, 230, 210), width=10)
    line(draw, [(140, 140), (175, 175)], (240, 230, 210), 12)
    finish(image, "perk_scavenger")


def icon_perk_revenge():
    image, draw = medallion((200, 60, 60), (80, 10, 10))
    poly(draw, [(85, 90), (150, 90), (150, 70), (180, 110), (150, 150), (150, 130), (85, 130)], (250, 200, 180))
    finish(image, "perk_revenge")


def icon_perk_pocket():
    image, draw = medallion((150, 110, 70), (70, 40, 20))
    poly(draw, [(85, 80), (171, 80), (165, 160), (128, 180), (91, 160)], (90, 110, 170))
    draw.line([(85, 100), (171, 100)], fill=(250, 220, 120), width=6)
    finish(image, "perk_pocket")


def icon_perk_nimble():
    image, draw = medallion((150, 220, 160), (30, 90, 40))
    draw.arc([80, 80, 176, 176], start=200, end=340, fill=(250, 250, 250), width=12)
    poly(draw, [(165, 95), (185, 120), (155, 120)], (250, 250, 250))
    finish(image, "perk_nimble")


def icon_perk_cold_blooded():
    image, draw = medallion((150, 210, 240), (30, 80, 130))
    poly(draw, [(115, 70), (141, 70), (141, 150), (115, 150)], (240, 250, 255))
    circle(draw, 128, 165, 22, (200, 40, 40))
    finish(image, "perk_cold_blooded")


def icon_perk_hot_potato():
    image, draw = medallion((240, 150, 60), (120, 50, 10))
    draw.ellipse([85, 95, 171, 165], fill=(190, 140, 80), outline=INK, width=5)
    for x in (100, 128, 156):
        line(draw, [(x, 85), (x + 6, 65)], (255, 120, 40), 6, outline=False)
    finish(image, "perk_hot_potato")


def icon_perk_focus():
    image, draw = medallion((170, 140, 220), (60, 30, 100))
    for r in (55, 35, 15):
        circle(draw, 128, 128, r, None, outline=(240, 230, 255), width=8)
    finish(image, "perk_focus")


def icon_perk_long_arms():
    image, draw = medallion((130, 180, 240), (30, 60, 120))
    line(draw, [(80, 160), (176, 96)], (235, 190, 150), 14)
    poly(draw, [(170, 80), (195, 92), (180, 115)], (235, 190, 150))
    finish(image, "perk_long_arms")


# The redesigned kits


def bus_shape(draw, x, y, w, color):
    """A bus from the side: a long box with windows and three wheels"""
    h = w * 0.36
    poly(draw, [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], color)
    for k in range(4):
        wx = x - w / 2 + 14 + k * (w - 28) / 4
        draw.rectangle([wx, y - h + 10, wx + (w - 28) / 4 - 8, y - h * 0.5], fill=(170, 210, 240), outline=INK, width=3)
    for wx in (x - w * 0.32, x + w * 0.05, x + w * 0.32):
        circle(draw, wx, y, w * 0.07, (40, 40, 44))


def icon_possess():
    image, draw = icon_base((120, 140, 200), (30, 30, 70))
    car_shape(draw, 128, 200, 190, (200, 60, 50))
    poly(draw, [(90, 150), (90, 70), (110, 45), (146, 45), (166, 70), (166, 150), (150, 135), (128, 150), (106, 135)], (225, 235, 255))
    circle(draw, 115, 80, 8, INK, width=2)
    circle(draw, 141, 80, 8, INK, width=2)
    finish(image, "possess")


def icon_adrenaline():
    image, draw = icon_base((230, 90, 70), (90, 10, 10))
    poly(draw, [(128, 210), (50, 130), (50, 85), (85, 60), (128, 90), (171, 60), (206, 85), (206, 130)], (230, 40, 50))
    line(draw, [(40, 135), (85, 135), (105, 95), (130, 175), (150, 115), (170, 135), (216, 135)], (255, 245, 200), 10, outline=False)
    finish(image, "adrenaline")


def icon_heave():
    image, draw = icon_base((170, 90, 70), (60, 20, 20))
    for x in (60, 128, 196):
        draw.line([(x, 20), (x, 236)], fill=(240, 240, 230), width=6)
    car_shape(draw, 150, 120, 120, (60, 120, 200), lifted=0)
    line(draw, [(40, 210), (90, 170), (150, 150)], (235, 190, 150), 16)
    poly(draw, [(200, 70), (240, 100), (200, 130)], (255, 210, 60))
    finish(image, "heave")


def icon_igloo():
    image, draw = icon_base((150, 200, 240), (40, 80, 140))
    draw.pieslice([40, 70, 216, 246], start=180, end=360, fill=(240, 248, 255), outline=INK, width=6)
    for y in (125, 158):
        draw.line([(52, y), (204, y)], fill=(160, 190, 220), width=4)
    draw.pieslice([102, 120, 154, 210], start=180, end=360, fill=(50, 60, 80), outline=INK, width=5)
    draw.rectangle([40, 158, 216, 168], fill=(240, 248, 255))
    finish(image, "igloo")


def icon_wave_through():
    image, draw = icon_base((250, 210, 90), (150, 90, 20))
    poly(draw, [(70, 200), (70, 110), (90, 70), (110, 110), (110, 60), (130, 100), (135, 55), (155, 100), (165, 70), (180, 120), (175, 200)], (235, 190, 150))
    for y, w in ((80, 40), (120, 55), (160, 40)):
        draw.line([(190, y), (190 + w * 0.8, y)], fill=(255, 255, 255), width=8)
    finish(image, "wave_through")


def icon_lollipop():
    image, draw = icon_base((250, 220, 80), (150, 110, 20))
    draw.rectangle([120, 120, 136, 240], fill=(230, 230, 235), outline=INK, width=4)
    circle(draw, 128, 90, 64, (230, 40, 40))
    circle(draw, 128, 90, 46, (250, 250, 250), outline=None, width=0)
    draw.text((101, 78), "STOP", fill=(200, 30, 30))
    finish(image, "lollipop")


def icon_reverse():
    image, draw = icon_base((180, 140, 240), (50, 30, 100))
    draw.arc([50, 50, 206, 206], start=210, end=500, fill=INK, width=30)
    draw.arc([54, 54, 202, 202], start=212, end=498, fill=(240, 220, 255), width=20)
    poly(draw, [(40, 110), (90, 120), (60, 160)], (240, 220, 255))
    finish(image, "reverse")


def icon_trampoline():
    image, draw = icon_base((250, 180, 80), (120, 60, 20))
    draw.ellipse([30, 150, 226, 200], fill=(60, 140, 230), outline=INK, width=6)
    for x in (50, 128, 206):
        draw.rectangle([x - 6, 178, x + 6, 236], fill=(80, 80, 90), outline=INK, width=3)
    circle(draw, 128, 70, 20, (235, 190, 150))
    poly(draw, [(110, 92), (146, 92), (150, 128), (106, 128)], (245, 160, 40))
    line(draw, [(60, 130), (90, 110)], (255, 255, 255), 6, outline=False)
    line(draw, [(196, 130), (166, 110)], (255, 255, 255), 6, outline=False)
    finish(image, "trampoline")


def icon_night_bus():
    image, draw = icon_base((40, 50, 100), (10, 10, 30))
    circle(draw, 200, 55, 26, (250, 240, 190))
    circle(draw, 212, 48, 22, (35, 45, 95), outline=None, width=0)
    bus_shape(draw, 120, 210, 210, (250, 190, 30))
    finish(image, "night_bus")


def icon_blend_in():
    image, draw = icon_base((150, 170, 150), (60, 80, 60))
    draw.rectangle([60, 70, 196, 200], fill=(240, 230, 190), outline=INK, width=6)
    draw.line([(105, 70), (105, 200)], fill=(180, 160, 120), width=4)
    draw.line([(151, 70), (151, 200)], fill=(180, 160, 120), width=4)
    line(draw, [(75, 170), (120, 120), (170, 150)], (220, 60, 60), 6, outline=False)
    circle(draw, 128, 55, 18, (235, 190, 150))
    finish(image, "blend_in")


def icon_yarn_leash():
    image, draw = icon_base((230, 120, 180), (100, 30, 70))
    circle(draw, 90, 150, 50, (230, 90, 160))
    for k in range(3):
        draw.arc([50 + k * 8, 110 + k * 6, 130 - k * 8, 190 - k * 6], start=200 + k * 30, end=340 + k * 30, fill=(250, 170, 210), width=5)
    line(draw, [(130, 130), (170, 90), (200, 110), (220, 60)], (230, 90, 160), 8)
    finish(image, "yarn_leash")


def icon_mind_the_cane():
    image, draw = icon_base((190, 140, 200), (70, 40, 80))
    line(draw, [(160, 230), (160, 80)], (140, 90, 50), 16)
    draw.arc([100, 40, 170, 110], start=180, end=360, fill=INK, width=24)
    draw.arc([104, 44, 166, 106], start=180, end=360, fill=(140, 90, 50), width=14)
    star(draw, 70, 170, 26, (255, 230, 90))
    star(draw, 50, 110, 16, (255, 230, 90))
    finish(image, "mind_the_cane")


def icon_magnetize():
    image, draw = icon_base((170, 180, 200), (50, 60, 80))
    car_shape(draw, 128, 220, 150, (60, 120, 200))
    draw.arc([70, 40, 186, 156], start=180, end=360, fill=INK, width=44)
    draw.arc([74, 44, 182, 152], start=180, end=360, fill=(220, 40, 40), width=34)
    draw.rectangle([70, 96, 108, 130], fill=(220, 220, 230), outline=INK, width=5)
    draw.rectangle([148, 96, 186, 130], fill=(220, 220, 230), outline=INK, width=5)
    finish(image, "magnetize")


def icon_lightning_rod():
    image, draw = icon_base((70, 90, 160), (20, 20, 50))
    draw.rectangle([120, 90, 136, 236], fill=(170, 175, 190), outline=INK, width=4)
    poly(draw, [(128, 40), (140, 90), (116, 90)], (170, 175, 190))
    poly(draw, [(200, 20), (160, 80), (185, 80), (140, 130), (205, 70), (178, 70)], (255, 240, 120))
    finish(image, "lightning_rod")


def icon_gust():
    image, draw = icon_base((140, 190, 240), (40, 80, 140))
    for y, x0, x1 in ((80, 40, 190), (128, 60, 220), (176, 30, 170)):
        draw.line([(x0, y), (x1, y)], fill=INK, width=20)
        draw.line([(x0, y), (x1, y)], fill=(240, 250, 255), width=12)
        draw.arc([x1 - 30, y - 30, x1 + 10, y + 2], start=270, end=90 + 180, fill=(240, 250, 255), width=10)
    finish(image, "gust")


def icon_static_charge():
    image, draw = icon_base((120, 140, 230), (30, 30, 90))
    for k, x in enumerate((70, 128, 186)):
        poly(draw, [(x + 10, 50), (x - 18, 130), (x, 130), (x - 12, 206), (x + 22, 110), (x + 4, 110)],
             (255, 240, 120) if k == 2 else (150, 160, 200))
    finish(image, "static_charge")


def icon_substitution():
    image, draw = icon_base((120, 120, 140), (40, 40, 50))
    for cx, cy, r in ((90, 120, 45), (140, 100, 40), (170, 140, 40), (110, 160, 35)):
        circle(draw, cx, cy, r, (200, 200, 210), outline=(120, 120, 130), width=4)
    draw.ellipse([60, 170, 200, 220], fill=(140, 95, 50), outline=INK, width=6)
    draw.ellipse([170, 170, 210, 220], fill=(210, 170, 110), outline=INK, width=5)
    finish(image, "substitution")


def icon_shadowed():
    image, draw = icon_base((90, 80, 110), (20, 15, 30))
    car_shape(draw, 110, 170, 170, (120, 120, 140))
    draw.polygon([(195, 170), (240, 170), (240, 236), (170, 236)], fill=(10, 10, 15))
    circle(draw, 210, 140, 18, (30, 30, 36))
    poly(draw, [(196, 160), (224, 160), (228, 220), (192, 220)], (30, 30, 36))
    draw.line([(200, 140), (220, 140)], fill=(230, 230, 240), width=4)
    finish(image, "shadowed")


def icon_bloodlust():
    image, draw = icon_base((200, 50, 40), (60, 5, 5))
    poly(draw, [(128, 40), (180, 140), (170, 185), (128, 215), (86, 185), (76, 140)], (190, 20, 25))
    draw.ellipse([100, 140, 125, 170], fill=(240, 120, 110))
    finish(image, "bloodlust")


def icon_status_stun():
    image, draw = icon_base((240, 210, 90), (140, 90, 20))
    draw.ellipse([50, 140, 206, 200], fill=None, outline=INK, width=8)
    for x, y in ((70, 150), (128, 195), (186, 150)):
        star(draw, x, y, 30, (255, 240, 120))
    circle(draw, 128, 100, 45, (235, 190, 150))
    finish(image, "status_stun")


def icon_status_slow():
    image, draw = icon_base((120, 170, 120), (30, 60, 30))
    draw.ellipse([60, 120, 190, 200], fill=(200, 160, 90), outline=INK, width=6)
    draw.arc([90, 90, 170, 180], start=180, end=360, fill=INK, width=24)
    poly(draw, [(60, 200), (40, 180), (60, 175)], (180, 210, 130))
    circle(draw, 205, 170, 20, (180, 210, 130))
    finish(image, "status_slow")


def icon_status_winded():
    image, draw = icon_base((130, 160, 220), (40, 50, 90))
    circle(draw, 128, 110, 60, (235, 190, 150))
    draw.line([(98, 100), (118, 100)], fill=INK, width=6)
    draw.line([(138, 100), (158, 100)], fill=INK, width=6)
    draw.ellipse([113, 125, 143, 155], fill=(60, 20, 20), outline=INK, width=3)
    for x in (70, 186):
        poly(draw, [(x, 170), (x + 10, 195), (x, 215), (x - 10, 195)], (150, 200, 255))
    finish(image, "status_winded")


def icon_item_remote_control():
    image, draw = icon_base((90, 90, 100), (30, 30, 36))
    poly(draw, [(80, 90), (176, 90), (186, 220), (70, 220)], (60, 60, 70))
    line(draw, [(160, 90), (190, 30)], (180, 180, 190), 8)
    circle(draw, 128, 140, 26, (220, 40, 40))
    for x in (98, 158):
        circle(draw, x, 190, 12, (240, 240, 240))
    finish(image, "item_remote_control")


def icon_item_stopwatch():
    image, draw = icon_base((200, 200, 210), (80, 80, 90))
    circle(draw, 128, 140, 80, (245, 245, 240))
    draw.rectangle([115, 40, 141, 62], fill=(180, 180, 190), outline=INK, width=5)
    line(draw, [(128, 140), (128, 80)], (200, 30, 30), 10, outline=False)
    line(draw, [(128, 140), (165, 160)], (40, 40, 40), 8, outline=False)
    circle(draw, 128, 140, 8, INK, width=2)
    finish(image, "item_stopwatch")


def icon_item_snow_globe():
    image, draw = icon_base((150, 200, 240), (40, 70, 120))
    poly(draw, [(70, 190), (186, 190), (200, 230), (56, 230)], (140, 90, 50))
    circle(draw, 128, 120, 80, (210, 235, 255))
    poly(draw, [(100, 180), (128, 110), (156, 180)], (40, 140, 70))
    for x, y in ((80, 90), (110, 70), (150, 85), (175, 120), (90, 140), (160, 160), (128, 60)):
        circle(draw, x, y, 6, (255, 255, 255), outline=None, width=0)
    finish(image, "item_snow_globe")


def icon_item_portal_gun():
    image, draw = icon_base((60, 80, 110), (20, 25, 40))
    draw.ellipse([20, 60, 90, 200], fill=(90, 200, 255), outline=INK, width=6)
    draw.ellipse([166, 60, 236, 200], fill=(255, 160, 60), outline=INK, width=6)
    draw.ellipse([38, 85, 72, 175], fill=(20, 40, 70))
    draw.ellipse([184, 85, 218, 175], fill=(70, 35, 10))
    poly(draw, [(95, 140), (150, 120), (160, 150), (110, 175)], (230, 230, 235))
    finish(image, "item_portal_gun")


def icon_perk_thick_soles():
    image, draw = medallion((200, 160, 110), (90, 60, 30))
    poly(draw, [(80, 120), (95, 80), (130, 80), (140, 110), (180, 120), (180, 140), (80, 140)], (240, 240, 245))
    draw.rectangle([78, 140, 182, 165], fill=(60, 50, 40), outline=INK, width=5)
    finish(image, "perk_thick_soles")


def icon_perk_hit_and_run():
    image, draw = medallion((230, 90, 70), (100, 20, 20))
    car_shape(draw, 128, 160, 110, (60, 120, 200))
    star(draw, 175, 100, 22, (255, 230, 90))
    finish(image, "perk_hit_and_run")


def icon_perk_scrapper():
    image, draw = medallion((220, 150, 90), (100, 50, 20))
    poly(draw, [(85, 140), (85, 100), (150, 100), (150, 85), (185, 120), (150, 155), (150, 140)], (235, 190, 150))
    finish(image, "perk_scrapper")


ICONS = {name[5:]: f for name, f in dict(globals()).items() if name.startswith("icon_") and callable(f) and f.__module__ == __name__ and name != "icon_base"}

if __name__ == "__main__":
    for name in sys.argv[1:] or ICONS:
        ICONS[name]()
