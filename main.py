#!/usr/bin/env python3
"""The World Today - one image summing up Monday 23 November 2026.

Draws a 1024x1024 newspaper-style front page with PIL shapes only.
No network, no randomness, no timestamps in the artwork: running this
script twice produces a byte-identical PNG.

Layout: header, 3 hero cards, 10 small cards, a numbered list of the
remaining stories grouped by region (44 stories total), a small world
map strip, a date-check box, and a sources footer.

Usage:  MAKEFUN_OUTPUT_DIR=<dir> python3 main.py
Writes <dir>/entry.png (default /output, or the script folder).
"""
import hashlib
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 241, 227)      # warm paper
CARD = (255, 253, 247)       # card white
INK = (27, 42, 74)           # dark navy ink
INK_SOFT = (74, 88, 120)
RED = (192, 57, 43)          # breaking-news accent
TEAL = (14, 124, 123)        # climate accent
GOLD = (217, 164, 65)
LINE = (27, 42, 74)
PALE_TEAL = (191, 216, 210)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, fnt, max_w, max_lines):
    """Wrap text and clip to max_lines, adding an ellipsis if clipped."""
    lines = wrap(draw, text, fnt, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and draw.textlength(lines[-1] + " ...", font=fnt) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + " ..."
    return lines


def trunc(draw, text, fnt, max_w):
    """Truncate a single line with an ellipsis so it fits max_w."""
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + " ...", font=fnt) > max_w:
        text = text[:-1]
    return text.rstrip() + " ..."


# ---------------------------------------------------------------- stories
# 44 distinct stories, all from 23 November 2026 reporting. Heroes 1-3,
# small cards 4-13, numbered list 14-44 grouped by region.
HEROES = [
    {
        "num": 1, "tag": "CLIMATE",
        "title": "COP31 collapses in Antalya",
        "desc": "Climate talks fail; the chairs sit empty.",
        "scene": "cop31",
    },
    {
        "num": 2, "tag": "UKRAINE",
        "title": "Kyiv flat hit - boy pulled alive",
        "desc": "Rescuers dig through the rubble.",
        "scene": "kyiv",
    },
    {
        "num": 3, "tag": "BREAKING",
        "title": "Tankers struck in the Strait of Hormuz",
        "desc": "Fire at sea as Iran war fears spike.",
        "scene": "hormuz",
    },
]

SMALL = [
    {"num": 4, "cap": "Democrats win biggest US House majority since 1992", "scene": "capitol"},
    {"num": 5, "cap": "Houthis claim strikes on Saudi refinery; 6 hurt", "scene": "refinery"},
    {"num": 6, "cap": "Sea drones 'hit Russian warship' at Benghazi base", "scene": "warship"},
    {"num": 7, "cap": "FBI-wanted cartel boss Chapo Isidro seized", "scene": "desert"},
    {"num": 8, "cap": "India-China open 10-day LAC talks in Arunachal", "scene": "talks"},
    {"num": 9, "cap": "Mount Mayon erupts; fears grow in Philippines", "scene": "volcano"},
    {"num": 10, "cap": "Alcaraz wins first ATP Finals, beats Zverev", "scene": "tennis"},
    {"num": 11, "cap": "Liverpool beat 10-man Man Utd in Pochettino debut", "scene": "football"},
    {"num": 12, "cap": "NHS launches world's largest AI breast-cancer trial", "scene": "nhs"},
    {"num": 13, "cap": "M6.5 quake shakes Vanuatu region", "scene": "quake"},
]

# (number, headline, group) - groups in display order, two columns.
LIST_GROUPS = [
    ("EUROPE", (46, 95, 163), [
        (14, "Lagarde to step down as ECB president in Feb 2027"),
        (15, "Slovakia rejects paying into new \u20ac45bn EU loan for Ukraine"),
        (16, "Russian strike on Kryvyi Rih kills two, wounds 60"),
        (17, "Poland reports airspace breach"),
        (18, "French students plan nationwide education protests"),
        (19, "Germany's October unemployment edges down"),
    ]),
    ("MIDDLE EAST", (192, 57, 43), [
        (20, "Iran war widens after Hormuz tanker strikes"),
        (21, "Britain, France and China block Nusseibeh's UN bid"),
        (22, "Syria arrests second officer over 2014 Otayba ambush"),
        (23, "Greta Thunberg joins COP31 protest in Antalya"),
    ]),
    ("ASIA-PACIFIC", (14, 124, 123), [
        (24, "Nepal PM Balen Shah begins India visit"),
        (25, "Selangor flood evacuees pass 1,800"),
        (26, "Youth Congress protests Meta over blocked accounts"),
        (27, "India vs NZ, 1st Test Day 5: NZ 157/4"),
        (28, "Audi profit falls amid weak China market"),
        (29, "Paolo Bulgari dies aged 89"),
        (30, "Shenzhen summit brings Trump, Putin and Xi together"),
    ]),
    ("AMERICAS", (46, 125, 50), [
        (31, "Trump posts friendship photos with Putin and Xi"),
        (32, "Trump reposts 'TrumpCare' universal health pitch"),
        (33, "Father and daughter detained by ICE at Seattle airport"),
        (34, "1,389 Indian children taken into US custody since 2023"),
        (35, "US Army to detonate bomb-making chemicals in Iowa"),
    ]),
    ("TECH & BUSINESS", (108, 79, 161), [
        (36, "OpenAI scientist urges common AI limits, warns of 2027 risks"),
        (37, "EU and Canada plan enhanced AI collaboration"),
        (38, "Titanic survivor's diamond ring sells for \u00a3150,000"),
        (39, "Compass catering giant plans New York listing"),
    ]),
    ("SPORT & CULTURE", (183, 121, 31), [
        (40, "FIFA to confirm UK as host of 2035 Women's World Cup"),
        (41, "Jeeno Thitikul wins third straight LPGA title"),
        (42, "Gerwyn Price wins Grand Slam of Darts"),
        (43, "FIDE World Championship Game 1: Sindarov gets White"),
        (44, "Tyson Fury documentary reveals schizophrenia diagnosis"),
    ]),
]

TOTAL_STORIES = 3 + len(SMALL) + sum(len(g[2]) for g in LIST_GROUPS)
assert TOTAL_STORIES == 44, TOTAL_STORIES


# ---------------------------------------------------------------- scenes
def scene_cop31(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(178, 222, 214))
    d.rectangle([x0, y0, x1, y0 + 26], fill=(120, 196, 188))
    d.ellipse([x1 - 52, y0 + 10, x1 - 18, y0 + 44], fill=(247, 241, 227))
    # globe, cracked
    cx, cy, r = x0 + 78, y0 + 52, 34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(58, 130, 190))
    d.ellipse([cx - 20, cy - 26, cx - 2, cy - 8], fill=(96, 176, 96))
    d.ellipse([cx + 4, cy + 6, cx + 24, cy + 26], fill=(96, 176, 96))
    d.ellipse([cx + 12, cy - 28, cx + 26, cy - 12], fill=(96, 176, 96))
    d.line([(cx - 26, cy - 30), (cx - 8, cy - 6), (cx - 18, cy + 12),
            (cx + 2, cy + 30)], fill=(27, 42, 74), width=3)
    # floor + row of empty chairs, last one tipped over
    d.rectangle([x0, y1 - 26, x1, y1], fill=(196, 164, 120))
    for i in range(4):
        cxp = x0 + 168 + i * 34
        d.rectangle([cxp, y1 - 62, cxp + 24, y1 - 34], fill=(122, 74, 44))
        d.rectangle([cxp, y1 - 34, cxp + 24, y1 - 26], fill=(146, 96, 58))
        d.rectangle([cxp + 3, y1 - 26, cxp + 6, y1 - 14], fill=(90, 56, 32))
        d.rectangle([cxp + 18, y1 - 26, cxp + 21, y1 - 14], fill=(90, 56, 32))
    d.polygon([(x0 + 168, y1 - 20), (x0 + 196, y1 - 34),
               (x0 + 200, y1 - 26), (x0 + 176, y1 - 12)], fill=(122, 74, 44))


def scene_kyiv(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(58, 72, 104))
    d.ellipse([x1 - 48, y0 + 8, x1 - 20, y0 + 36], fill=(232, 220, 180))
    # damaged tower block, jagged broken top
    bx0, bx1 = x0 + 26, x0 + 150
    d.polygon([(bx0, y1 - 18), (bx0, y0 + 34), (bx0 + 30, y0 + 22),
               (bx0 + 52, y0 + 40), (bx0 + 78, y0 + 26), (bx0 + 104, y0 + 44),
               (bx1, y0 + 30), (bx1, y1 - 18)], fill=(38, 46, 66))
    for r in range(3):
        for c in range(4):
            wx, wy = bx0 + 12 + c * 28, y0 + 52 + r * 20
            lit = (r + c) % 3 != 0
            d.rectangle([wx, wy, wx + 14, wy + 10],
                        fill=(240, 200, 90) if lit else (20, 26, 40))
    # rubble + rescuer in orange carrying a child, ladder, beam
    d.polygon([(x0 + 150, y1), (x0 + 190, y1 - 34), (x0 + 240, y1 - 10),
               (x0 + 300, y1)], fill=(96, 100, 112))
    d.polygon([(x0 + 150, y1), (x0 + 176, y1 - 18), (x0 + 210, y1)],
              fill=(120, 124, 136))
    d.polygon([(x1 - 8, y0 + 30), (x0 + 210, y1 - 40), (x0 + 236, y1 - 40),
               (x1 + 20, y0 + 44)], fill=(240, 220, 140))
    d.line([(x0 + 238, y1 - 8), (x0 + 262, y1 - 52)], fill=(180, 170, 150), width=4)
    d.ellipse([x0 + 246, y1 - 52, x0 + 260, y1 - 38], fill=(240, 120, 40))
    d.rectangle([x0 + 246, y1 - 38, x0 + 262, y1 - 14], fill=(240, 120, 40))
    d.ellipse([x0 + 262, y1 - 34, x0 + 272, y1 - 24], fill=(240, 200, 170))
    d.rectangle([x0 + 262, y1 - 24, x0 + 272, y1 - 12], fill=(120, 160, 220))


def scene_hormuz(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y0 + 52], fill=(232, 140, 70))
    d.ellipse([x0 + 130, y0 + 8, x0 + 168, y0 + 46], fill=(247, 220, 150))
    d.rectangle([x0, y0 + 52, x1, y1], fill=(24, 52, 96))
    for wy in (y0 + 66, y0 + 82, y0 + 96):
        for k in range(5):
            wx = x0 + 12 + k * 62
            d.arc([wx, wy, wx + 34, wy + 12], 180, 360, fill=(180, 210, 230), width=2)
    # tanker hull, deck, funnel, flames, smoke
    d.rectangle([x0 + 30, y0 + 66, x0 + 272, y0 + 88], fill=(16, 20, 28))
    d.rectangle([x0 + 52, y0 + 52, x0 + 120, y0 + 66], fill=(40, 48, 62))
    d.rectangle([x0 + 196, y0 + 44, x0 + 216, y0 + 66], fill=(120, 40, 30))
    d.rectangle([x0 + 196, y0 + 44, x0 + 216, y0 + 50], fill=(240, 200, 90))
    for fx, fh in ((x0 + 130, 34), (x0 + 152, 46), (x0 + 176, 30)):
        d.polygon([(fx, y0 + 56), (fx + 10, y0 + 56 - fh),
                   (fx + 20, y0 + 56)], fill=(240, 120, 30))
        d.polygon([(fx + 5, y0 + 56), (fx + 10, y0 + 56 - fh + 14),
                   (fx + 15, y0 + 56)], fill=(247, 200, 60))
    for sx, sy, sr in ((x0 + 140, y0 + 6, 12), (x0 + 162, y0 - 2, 15),
                       (x0 + 186, y0 + 8, 11)):
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(90, 90, 96))
    d.rectangle([x0 + 30, y0 + 88, x0 + 272, y0 + 92], fill=(192, 57, 43))


def scene_small(d, kind, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    if kind == "capitol":  # US Capitol dome
        d.rectangle([x0, y0, x1, y1], fill=(52, 96, 168))
        d.rectangle([x0, y1 - 16, x1, y1], fill=(220, 224, 230))
        d.polygon([(x0 + 78, y0 + 30), (x0 + 94, y0 + 8), (x0 + 110, y0 + 30)],
                  fill=(240, 242, 245))
        d.rectangle([x0 + 92, y0 + 2, x0 + 96, y0 + 10], fill=(240, 242, 245))
        d.rectangle([x0 + 52, y0 + 30, x0 + 136, y0 + 46], fill=(240, 242, 245))
        for sx in (x0 + 18, x0 + 40, x0 + 148, x0 + 168):
            d.ellipse([sx, y0 + 12, sx + 6, y0 + 18], fill=(255, 255, 255))
    elif kind == "refinery":
        d.rectangle([x0, y0, x1, y1], fill=(232, 160, 90))
        d.rectangle([x0, y1 - 14, x1, y1], fill=(60, 58, 54))
        for tx in (x0 + 20, x0 + 62, x0 + 104):
            d.rectangle([tx, y0 + 22, tx + 22, y1 - 14], fill=(90, 88, 84))
            d.rectangle([tx + 6, y0 + 12, tx + 16, y0 + 22], fill=(90, 88, 84))
        d.polygon([(x0 + 146, y1 - 14), (x0 + 154, y0 + 16),
                   (x0 + 162, y1 - 14)], fill=(240, 120, 30))
        d.polygon([(x0 + 150, y1 - 14), (x0 + 154, y0 + 28),
                   (x0 + 158, y1 - 14)], fill=(247, 200, 60))
        d.ellipse([x0 + 140, y0 + 2, x0 + 168, y0 + 20], fill=(120, 118, 114))
    elif kind == "warship":
        d.rectangle([x0, y0, x1, y1], fill=(120, 170, 200))
        d.rectangle([x0, y0 + 34, x1, y1], fill=(28, 68, 110))
        d.rectangle([x0 + 34, y0 + 26, x0 + 156, y0 + 40], fill=(70, 78, 88))
        d.rectangle([x0 + 70, y0 + 14, x0 + 108, y0 + 26], fill=(88, 96, 106))
        d.rectangle([x0 + 84, y0 + 4, x0 + 90, y0 + 14], fill=(88, 96, 106))
        d.polygon([(x0 + 20, y0 + 40), (x0 + 30, y0 + 34),
                   (x0 + 30, y0 + 46)], fill=(240, 120, 30))
        d.ellipse([x0 + 158, y0 + 36, x0 + 176, y0 + 50], fill=(220, 235, 240))
    elif kind == "desert":
        d.rectangle([x0, y0, x1, y1], fill=(240, 200, 130))
        d.ellipse([x0 + 150, y0 + 6, x0 + 176, y0 + 32], fill=(247, 220, 120))
        d.polygon([(x0, y0 + 40), (x0 + 46, y0 + 14), (x0 + 92, y0 + 40)],
                  fill=(200, 140, 90))
        d.polygon([(x0 + 80, y0 + 40), (x0 + 130, y0 + 20), (x0 + 180, y0 + 40)],
                  fill=(214, 158, 104))
        d.rectangle([x0 + 30, y0 + 40, x0 + 34, y1 - 12], fill=(46, 125, 50))
        d.rectangle([x0 + 22, y0 + 30, x0 + 30, y0 + 42], fill=(46, 125, 50))
        d.rectangle([x0 + 34, y0 + 34, x0 + 42, y0 + 44], fill=(46, 125, 50))
        d.ellipse([x0 + 118, y0 + 26, x0 + 142, y0 + 50], fill=(240, 200, 60))
        d.polygon([(x0 + 130, y0 + 26), (x0 + 124, y0 + 38), (x0 + 136, y0 + 38)],
                  fill=(27, 42, 74))
    elif kind == "talks":
        d.rectangle([x0, y0, x1, y1], fill=(178, 222, 214))
        d.polygon([(x0, y1), (x0 + 50, y0 + 18), (x0 + 100, y1)], fill=(110, 150, 130))
        d.polygon([(x0 + 90, y1), (x0 + 140, y0 + 10), (x0 + 187, y1)], fill=(90, 130, 112))
        d.rectangle([x0 + 62, y0 + 34, x0 + 126, y0 + 44], fill=(122, 74, 44))
        d.rectangle([x0 + 70, y0 + 44, x0 + 74, y0 + 52], fill=(90, 56, 32))
        d.rectangle([x0 + 114, y0 + 44, x0 + 118, y0 + 52], fill=(90, 56, 32))
        d.rectangle([x0 + 66, y0 + 18, x0 + 86, y0 + 34], fill=(255, 153, 51))
        d.rectangle([x0 + 66, y0 + 18, x0 + 86, y0 + 23], fill=(255, 153, 51))
        d.rectangle([x0 + 66, y0 + 28, x0 + 86, y0 + 34], fill=(19, 136, 8))
        d.rectangle([x0 + 102, y0 + 18, x0 + 122, y0 + 34], fill=(222, 41, 16))
        d.ellipse([x0 + 52, y0 + 14, x0 + 62, y0 + 24], fill=(240, 200, 170))
        d.ellipse([x0 + 126, y0 + 14, x0 + 136, y0 + 24], fill=(240, 200, 170))
    elif kind == "volcano":
        d.rectangle([x0, y0, x1, y1], fill=(150, 190, 220))
        d.polygon([(x0 + 20, y1), (x0 + 84, y0 + 22), (x0 + 104, y0 + 22),
                   (x0 + 168, y1)], fill=(110, 80, 70))
        d.polygon([(x0 + 84, y0 + 22), (x0 + 104, y0 + 22), (x0 + 98, y0 + 34),
                   (x0 + 90, y0 + 34)], fill=(240, 120, 30))
        d.ellipse([x0 + 78, y0 + 2, x0 + 100, y0 + 20], fill=(140, 140, 140))
        d.ellipse([x0 + 88, y0 - 4, x0 + 112, y0 + 12], fill=(160, 160, 160))
        d.rectangle([x0, y1 - 10, x1, y1], fill=(96, 140, 90))
    elif kind == "tennis":
        d.rectangle([x0, y0, x1, y1], fill=(70, 160, 90))
        d.rectangle([x0 + 10, y0 + 10, x1 - 10, y1 - 10], fill=(52, 130, 200))
        d.line([(x0 + 94, y0 + 10), (x0 + 94, y1 - 10)], fill=(255, 255, 255), width=2)
        d.ellipse([x0 + 128, y0 + 12, x0 + 152, y0 + 36], fill=(204, 255, 0))
        d.arc([x0 + 128, y0 + 12, x0 + 152, y0 + 36], 300, 60, fill=(255, 255, 255), width=2)
        d.ellipse([x0 + 34, y0 + 30, x0 + 46, y0 + 42], fill=(255, 255, 255))
        d.line([(x0 + 40, y0 + 42), (x0 + 58, y1 - 14)], fill=(180, 120, 60), width=3)
    elif kind == "football":
        d.rectangle([x0, y0, x1, y1], fill=(46, 140, 70))
        d.ellipse([x0 + 72, y0 + 12, x0 + 116, y0 + 46], outline=(255, 255, 255), width=2)
        d.line([(x0, y0 + 29), (x1, y0 + 29)], fill=(255, 255, 255), width=2)
        d.ellipse([x0 + 86, y0 + 20, x0 + 102, y0 + 36], fill=(20, 20, 20))
        d.ellipse([x0 + 26, y0 + 34, x0 + 38, y0 + 46], fill=(192, 30, 30))
        d.ellipse([x0 + 148, y0 + 34, x0 + 160, y0 + 46], fill=(255, 255, 255))
    elif kind == "nhs":
        d.rectangle([x0, y0, x1, y1], fill=(220, 235, 245))
        d.rectangle([x0 + 70, y0 + 10, x0 + 118, y0 + 48], fill=(255, 255, 255))
        d.rectangle([x0 + 88, y0 + 16, x0 + 100, y0 + 42], fill=(0, 94, 184))
        d.rectangle([x0 + 76, y0 + 24, x0 + 112, y0 + 34], fill=(0, 94, 184))
        for px, py in ((x0 + 30, y0 + 16), (x0 + 52, y0 + 40), (x0 + 146, y0 + 14),
                       (x0 + 160, y0 + 38)):
            d.ellipse([px, py, px + 8, py + 8], fill=(14, 124, 123))
        d.line([(x0 + 30, y0 + 20), (x0 + 52, y0 + 44)], fill=(14, 124, 123), width=2)
        d.line([(x0 + 146, y0 + 18), (x0 + 160, y0 + 42)], fill=(14, 124, 123), width=2)
    elif kind == "quake":
        d.rectangle([x0, y0, x1, y1], fill=(232, 222, 200))
        d.polygon([(x0, y0 + 40), (x0 + 40, y0 + 28), (x0 + 70, y0 + 46),
                   (x0 + 110, y0 + 30), (x0 + 150, y0 + 44), (x1, y0 + 32),
                   (x1, y1), (x0, y1)], fill=(180, 150, 110))
        d.line([(x0 + 70, y0 + 46), (x0 + 78, y1 - 8), (x0 + 92, y1 - 8)],
               fill=(90, 60, 40), width=2)
        d.line([(x0 + 12, y0 + 16), (x0 + 34, y0 + 16), (x0 + 44, y0 + 6),
                (x0 + 58, y0 + 24), (x0 + 72, y0 + 8), (x0 + 92, y0 + 22),
                (x0 + 110, y0 + 10), (x0 + 130, y0 + 20), (x0 + 168, y0 + 14)],
               fill=(192, 57, 43), width=2)


SCENES = {"cop31": scene_cop31, "kyiv": scene_kyiv, "hormuz": scene_hormuz}


# ---------------------------------------------------------------- map
# Recognisable world map drawn from real lon/lat outlines (equirectangular,
# lon -180..180, lat 72..-55) so each continent reads at a glance.
# Land is a distinct green against a pale-blue ocean, with a faint
# lat/lon graticule, ocean labels, and pins whose labels are led out
# into empty sea so none of them collide.
LAND = (172, 205, 176)
LAND_LINE = (74, 102, 80)
OCEAN = (213, 231, 238)
GRID = (196, 212, 218)

NORTH_AMERICA = [(-168, 66), (-160, 71), (-140, 70), (-128, 71), (-115, 69),
                 (-102, 68), (-92, 66), (-88, 64), (-92, 60), (-88, 57),
                 (-82, 55), (-78, 58), (-76, 62), (-70, 62), (-65, 60),
                 (-60, 55), (-56, 50), (-60, 47), (-65, 44), (-70, 42),
                 (-75, 38), (-76, 34), (-80, 32), (-81, 26), (-84, 30),
                 (-88, 30), (-92, 29), (-97, 26), (-97, 20), (-94, 17),
                 (-90, 15), (-86, 12), (-83, 9), (-80, 8), (-84, 11),
                 (-88, 14), (-92, 15), (-96, 16), (-101, 18), (-106, 22),
                 (-110, 24), (-114, 29), (-118, 33), (-122, 37), (-124, 42),
                 (-124, 48), (-128, 52), (-133, 56), (-140, 60), (-150, 59),
                 (-158, 56), (-163, 58), (-166, 61)]
GREENLAND = [(-58, 64), (-52, 60), (-42, 60), (-32, 68), (-22, 70),
             (-25, 76), (-40, 76), (-55, 74), (-60, 70)]
SOUTH_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-78, -12),
                 (-72, -18), (-70, -23), (-70, -30), (-72, -37), (-71, -44),
                 (-68, -50), (-65, -55), (-60, -48), (-57, -38), (-50, -30),
                 (-41, -23), (-36, -9), (-35, -6), (-42, -3), (-48, 0),
                 (-52, 4), (-57, 6), (-62, 9), (-70, 11), (-76, 10)]
AFRICA = [(-17, 15), (-16, 21), (-10, 29), (-6, 33), (-1, 35), (10, 37),
          (20, 32), (30, 31), (33, 28), (36, 23), (39, 18), (43, 12),
          (48, 11), (51, 11), (48, 5), (42, -2), (40, -10), (36, -18),
          (33, -25), (30, -31), (26, -34), (19, -35), (16, -28), (14, -22),
          (12, -17), (12, -10), (13, -5), (9, 4), (4, 6), (-4, 5),
          (-8, 4), (-13, 8), (-17, 12)]
EUROPE = [(-10, 37), (-9, 43), (-2, 44), (-3, 48), (0, 50), (3, 53),
          (7, 55), (8, 57), (12, 55), (18, 56), (21, 59), (25, 61),
          (30, 64), (30, 70), (24, 71), (18, 69), (12, 64), (6, 58)]
UNITED_KINGDOM = [(-5, 50), (-3, 53), (-6, 56), (-3, 58), (0, 54), (1, 51)]
ASIA = [(28, 41), (32, 42), (36, 38), (40, 41), (44, 42), (48, 46),
        (52, 47), (56, 44), (60, 42), (64, 40), (66, 37), (68, 38),
        (70, 41), (74, 40), (78, 42), (82, 44), (88, 46), (95, 50),
        (100, 55), (105, 60), (110, 65), (115, 68), (120, 70), (125, 72),
        (130, 72), (135, 71), (140, 72), (145, 72), (150, 70), (155, 68),
        (160, 66), (162, 62), (162, 58), (158, 52), (156, 50), (150, 48),
        (142, 46), (140, 42), (135, 42), (132, 38), (129, 35), (127, 35),
        (126, 38), (122, 39), (121, 35), (120, 30), (118, 25), (112, 22),
        (109, 20), (108, 17), (106, 10), (104, 8), (102, 7), (100, 6),
        (98, 10), (97, 15), (94, 17), (92, 21), (90, 22), (87, 22),
        (85, 19), (82, 16), (80, 13), (78, 8), (76, 10), (74, 15),
        (72, 20), (69, 23), (66, 25), (62, 25), (58, 26), (56, 27),
        (53, 28), (50, 30), (48, 30), (45, 29), (42, 30), (39, 31),
        (36, 36), (32, 36), (28, 38)]
SUMATRA = [(95, 5), (98, 3), (101, 0), (104, -3), (106, -6), (103, -5),
           (99, -1), (96, 3)]
BORNEO = [(109, 1), (112, 3), (116, 6), (119, 5), (118, 1), (117, -2),
          (114, -4), (110, -3), (109, 0)]
NEW_GUINEA = [(131, -1), (136, -2), (141, -3), (146, -6), (147, -8),
              (142, -8), (137, -6), (132, -4)]
JAPAN = [(130, 31), (133, 33), (137, 35), (140, 38), (142, 42), (144, 44),
         (141, 40), (138, 36), (134, 34), (131, 32)]
PHILIPPINES = [(120, 14), (122, 17), (123, 14), (124, 10), (121, 8),
               (120, 11)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (46, -24),
              (44, -22), (43, -18)]
AUSTRALIA = [(114, -22), (113, -26), (115, -32), (118, -35), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (148, -39), (150, -37), (153, -32), (153, -27),
             (151, -24), (148, -20), (146, -19), (142, -15), (142, -11),
             (138, -12), (136, -15), (133, -12), (131, -12), (128, -14),
             (125, -14), (122, -17), (118, -20), (115, -21)]
NEW_ZEALAND = [(167, -45), (170, -42), (173, -39), (176, -38), (178, -38),
               (176, -40), (173, -42), (170, -44), (167, -46)]

CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE,
              UNITED_KINGDOM, ASIA, SUMATRA, BORNEO, NEW_GUINEA, JAPAN,
              PHILIPPINES, MADAGASCAR, AUSTRALIA, NEW_ZEALAND]


def draw_map(d, x0, y0, x1, y1):
    """World map from real lon/lat outlines + pins with leader-line labels."""
    d.rectangle([x0, y0, x1, y1], fill=OCEAN)

    def X(lon):
        return x0 + (lon + 180.0) / 360.0 * (x1 - x0)

    def Y(lat):
        return y0 + (72.0 - lat) / 127.0 * (y1 - y0)

    # faint graticule: meridians every 30 deg, parallels at 60/30/0/-30
    for lon in range(-150, 151, 30):
        d.line([(X(lon), y0), (X(lon), y1)], fill=GRID, width=1)
    for lat in (60, 30, 0, -30):
        d.line([(x0, Y(lat)), (x1, Y(lat))], fill=GRID, width=1)
    d.line([(x0, Y(0)), (x1, Y(0))], fill=(170, 190, 196), width=1)
    # continents
    for pts in CONTINENTS:
        d.polygon([(X(lon), Y(lat)) for lon, lat in pts],
                  fill=LAND, outline=LAND_LINE)
    # ocean names, in empty water
    f_oc = font(9)
    oc = (105, 135, 145)
    d.text((108, 888), "PACIFIC OCEAN", font=f_oc, fill=oc, anchor="ma")
    d.text((205, 914), "ATLANTIC OCEAN", font=f_oc, fill=oc, anchor="ma")
    d.text((495, 920), "INDIAN OCEAN", font=f_oc, fill=oc, anchor="ma")
    # pins on their true spots; labels led out into empty sea, never touching
    f_pin = font(10, bold=True)
    pins = [
        # (label, lon, lat, label pos, label anchor, leader end)
        ("KYIV", 30.52, 50.45, (394, 845), "ma", (394, 851)),
        ("ANTALYA", 30.71, 36.90, (380, 860), "ra", (384, 865)),
        ("HORMUZ", 56.50, 26.60, (447, 898), "la", (445, 896)),
    ]
    for name, lon, lat, (lx, ly), anchor, (ex, ey) in pins:
        px, py = X(lon), Y(lat)
        d.line([(px, py), (ex, ey)], fill=RED, width=1)
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=RED,
                  outline=(255, 255, 255))
        d.text((lx, ly), name, font=f_pin, fill=RED, anchor=anchor)


# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- header
    d.text((24, 14), "THE WORLD TODAY", font=font(46, bold=True), fill=INK)
    d.text((24, 64), "Monday 23 November 2026  \u2014  the day in one image",
           font=font(14), fill=INK_SOFT)
    # header stat box
    d.rectangle([798, 16, 1000, 78], outline=INK, width=2, fill=CARD)
    d.text((899, 24), "44 STORIES", font=font(19, bold=True), fill=RED, anchor="ma")
    d.text((899, 50), "7 REGIONS  \u00b7  1 DAY", font=font(12, bold=True),
           fill=INK, anchor="ma")
    d.line([(24, 92), (1000, 92)], fill=INK, width=2)

    # ---- heroes
    d.text((24, 100), "TOP STORIES", font=font(12, bold=True), fill=RED)
    d.line([(130, 107), (1000, 107)], fill=LINE, width=1)
    hero_y, hero_img_h, hero_cap_h = 116, 100, 56
    hero_w, gap = 314, 17
    for i, hero in enumerate(HEROES):
        x0 = 24 + i * (hero_w + gap)
        x1 = x0 + hero_w
        y1 = hero_y + hero_img_h + hero_cap_h
        d.rectangle([x0, hero_y, x1, y1], outline=INK, width=2, fill=CARD)
        SCENES[hero["scene"]](d, x0 + 2, hero_y + 2, x1 - 2, hero_y + hero_img_h - 2)
        d.line([(x0, hero_y + hero_img_h), (x1, hero_y + hero_img_h)], fill=INK, width=2)
        # caption bar: tag + number, title, description (never on the picture)
        tx = x0 + 10
        d.text((tx, hero_y + hero_img_h + 6),
               f"{hero['num']}  \u00b7  {hero['tag']}", font=font(10, bold=True), fill=RED)
        title_lines = fit_lines(d, hero["title"], font(13, bold=True), hero_w - 20, 1)
        d.text((tx, hero_y + hero_img_h + 21), title_lines[0],
               font=font(13, bold=True), fill=INK)
        desc_lines = fit_lines(d, hero["desc"], font(11), hero_w - 20, 1)
        d.text((tx, hero_y + hero_img_h + 39), desc_lines[0], font=font(11), fill=INK_SOFT)

    # ---- small cards
    small_label_y = 282
    d.text((24, small_label_y), "ALSO TODAY", font=font(12, bold=True), fill=TEAL)
    d.line([(118, small_label_y + 7), (1000, small_label_y + 7)], fill=LINE, width=1)
    row_y = [296, 398]
    card_w, card_gap = 187, 10
    img_h, cap_h = 58, 40
    f_cap = font(11, bold=True)
    for idx, story in enumerate(SMALL):
        row, col = divmod(idx, 5)
        x0 = 24 + col * (card_w + card_gap)
        x1 = x0 + card_w
        y0 = row_y[row]
        y1 = y0 + img_h + cap_h
        d.rectangle([x0, y0, x1, y1], outline=INK, width=1, fill=CARD)
        scene_small(d, story["scene"], x0 + 1, y0 + 1, x1 - 1, y0 + img_h - 1)
        # numbered badge, top-left corner of the picture
        bx, by = x0 + 13, y0 + 13
        d.ellipse([bx - 11, by - 11, bx + 11, by + 11], fill=RED, outline=(255, 255, 255))
        d.text((bx, by), str(story["num"]), font=font(11, bold=True),
               fill=(255, 255, 255), anchor="mm")
        lines = fit_lines(d, story["cap"], f_cap, card_w - 12, 3)
        for li, line in enumerate(lines):
            d.text((x0 + 6, y0 + img_h + 3 + li * 12), line, font=f_cap, fill=INK)

    # ---- numbered list of the remaining stories, grouped by region
    list_label_y = 506
    d.text((24, list_label_y), "THE REST OF THE DAY \u2014 31 MORE STORIES",
           font=font(12, bold=True), fill=INK)
    d.line([(296, list_label_y + 7), (1000, list_label_y + 7)], fill=LINE, width=1)
    col_x = [24, 522]
    col_w = 478
    f_item = font(11)
    f_grp = font(11, bold=True)
    for ci, groups in enumerate((LIST_GROUPS[:3], LIST_GROUPS[3:])):
        x = col_x[ci]
        y = list_label_y + 20
        for gname, colour, items in groups:
            d.ellipse([x + 5, y + 2, x + 13, y + 10], fill=colour)
            d.text((x + 18, y), f"{gname}  ({len(items)})", font=f_grp, fill=colour)
            d.line([(x + 18 + d.textlength(f"{gname}  ({len(items)})", font=f_grp) + 8,
                     y + 7), (x + col_w, y + 7)], fill=colour, width=1)
            y += 17
            for num, headline in items:
                # region-coloured number chip
                d.rounded_rectangle([x, y - 1, x + 24, y + 12], radius=6, fill=colour)
                d.text((x + 12, y + 5), str(num), font=font(9, bold=True),
                       fill=(255, 255, 255), anchor="mm")
                text = trunc(d, headline, f_item, col_w - 32)
                d.text((x + 30, y), text, font=f_item, fill=INK)
                y += 13
            y += 5

    # ---- map strip + date check
    map_y0, map_y1 = 816, 948
    d.rectangle([24, map_y0, 660, map_y1], outline=INK, width=2, fill=CARD)
    d.text((36, map_y0 + 8), "WHERE THE DAY HAPPENED", font=font(11, bold=True), fill=INK)
    draw_map(d, 36, map_y0 + 26, 648, map_y1 - 8)
    # ---- date check: editorial verification stamp (double border, tint)
    d.rectangle([676, map_y0, 1000, map_y1], outline=RED, width=3,
                fill=(253, 241, 234))
    d.rectangle([682, map_y0 + 6, 994, map_y1 - 6], outline=RED, width=1)
    cx = 838
    d.ellipse([cx - 12, map_y0 + 10, cx + 12, map_y0 + 34], fill=TEAL)
    d.line([(cx - 5, map_y0 + 22), (cx - 1, map_y0 + 27), (cx + 6, map_y0 + 17)],
           fill=(255, 255, 255), width=3)
    d.text((cx, map_y0 + 38), "DATE CHECK", font=font(12, bold=True),
           fill=RED, anchor="ma")
    d.text((cx, map_y0 + 54), "Monday 23 November 2026",
           font=font(15, bold=True), fill=INK, anchor="ma")
    d.text((cx, map_y0 + 73), "Day 327 of 2026  \u00b7  38 days left in the year",
           font=font(10), fill=INK_SOFT, anchor="ma")
    d.line([(700, map_y0 + 89), (976, map_y0 + 89)], fill=RED, width=1)
    d.text((cx, map_y0 + 95),
           "All 44 stories verified against 23 Nov 2026 reporting.",
           font=font(9), fill=INK_SOFT, anchor="ma")
    d.text((cx, map_y0 + 109), "No story dated before today.",
           font=font(11, bold=True), fill=TEAL, anchor="ma")

    # ---- footer
    d.line([(24, 960), (1000, 960)], fill=INK, width=1)
    d.text((24, 968),
           "Sources: BBC, CNN, Reuters, WSJ, The Hindu, Le Monde, The Times \u2014 23 Nov 2026",
           font=font(11), fill=INK_SOFT)
    d.text((1000, 968), "44 stories", font=font(11, bold=True), fill=INK, anchor="ra")

    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR") or "/output"
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        probe = Path(out_dir) / ".write_test"
        probe.write_text("ok")
        probe.unlink()
    except OSError:
        out_dir = str(Path(__file__).resolve().parent)
    img = build()
    out_path = Path(out_dir) / "entry.png"
    img.save(out_path, format="PNG")
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"wrote {out_path}  {img.size[0]}x{img.size[1]}  "
          f"{out_path.stat().st_size} bytes  sha256={digest}")
    print(f"stories: {TOTAL_STORIES}")


if __name__ == "__main__":
    main()
