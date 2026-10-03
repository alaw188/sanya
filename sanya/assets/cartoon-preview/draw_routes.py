# -*- coding: utf-8 -*-
"""Draw itinerary routes + DAY badges onto the clean scene map.
Route semantics (source of truth = itinerary):
  Day 1 (deep teal): 機場 -> 酒店 -> 美食街
  Day 2 (warm gold): 酒店 -> 亞龍灣 -> 水族館 -> 後海村
  Day 3 (coral):     酒店 -> 天涯海角 -> 免稅城 -> 機場
"""
from PIL import Image, ImageDraw, ImageFont
import math, sys

SRC = 'Cute_isometric_3D_miniature_di_2026-10-03T05-28-04.png'
OUT_PNG = 'H_iso_no_wm.png'
OUT_JPG = 'H_iso_web.jpg'

# ---- palette ----
TEAL  = (15, 79, 92)      # Day 1  #0F4F5C
GOLD  = (201, 162, 39)    # Day 2  #C9A227
CORAL = (224, 110, 92)    # Day 3  coral pink

im = Image.open(SRC).convert('RGB')
W, H = im.size
draw = ImageDraw.Draw(im)

# ---- scene centers (measured on the 1536x1024 source) ----
SCENES = {
    'airport':  (242, 171),
    'hotel':    (768, 341),
    'food':     (1251, 256),
    'yalong':   (242, 469),
    'aquarium': (1067, 569),
    'houhai':   (1351, 683),
    'tianya':   (811, 768),
    'dutyfree': (199, 811),
}

ROUTES = [
    ('DAY 1', TEAL,  [('airport', None), ('hotel', None), ('food', None)]),
    ('DAY 2', GOLD,  [('hotel', None), ('yalong', None), ('aquarium', None), ('houhai', None)]),
    # Day 3 last leg (dutyfree -> airport) curves west to avoid crossing 亞龍灣
    ('DAY 3', CORAL, [('hotel', None), ('tianya', None), ('dutyfree', None),
                      ('airport', (-40, 320))]),
]

def dashed_line(dr, p1, p2, color, dash=16, gap=12, width=5):
    x1, y1 = p1; x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1: return
    ux, uy = dx / dist, dy / dist
    t = 0.0
    while t < dist:
        t2 = min(t + dash, dist)
        a = (x1 + ux * t, y1 + uy * t)
        b = (x1 + ux * t2, y1 + uy * t2)
        dr.line([a, b], fill=color, width=width)
        # round caps
        r = width / 2
        dr.ellipse([a[0]-r, a[1]-r, a[0]+r, a[1]+r], fill=color)
        dr.ellipse([b[0]-r, b[1]-r, b[0]+r, b[1]+r], fill=color)
        t = t2 + gap

def qbez(p0, p1, p2, t):
    """Quadratic bezier point."""
    mt = 1 - t
    return (mt*mt*p0[0] + 2*mt*t*p1[0] + t*t*p2[0],
            mt*mt*p0[1] + 2*mt*t*p1[1] + t*t*p2[1])

def dashed_curve(dr, p0, pc, p2, color, dash=16, gap=12, width=5, steps=120):
    """Dashed line along a quadratic bezier from p0 via control pc to p2."""
    pts = [qbez(p0, pc, p2, i/steps) for i in range(steps+1)]
    # walk along polyline placing dashes
    seg = 0; t_in_seg = 0.0
    dashing = True; remain = float(dash)
    cur = pts[0]
    for nxt in pts[1:]:
        seg_len = math.hypot(nxt[0]-cur[0], nxt[1]-cur[1])
        t = 0.0
        while t < seg_len:
            step = min(remain, seg_len - t)
            ta = t / seg_len; tb = (t + (step if dashing else 0)) / seg_len
            a = (cur[0] + (nxt[0]-cur[0])*ta, cur[1] + (nxt[1]-cur[1])*ta)
            if dashing:
                b = (cur[0] + (nxt[0]-cur[0])*tb, cur[1] + (nxt[1]-cur[1])*tb)
                dr.line([a, b], fill=color, width=width)
                r = width / 2
                dr.ellipse([a[0]-r, a[1]-r, a[0]+r, a[1]+r], fill=color)
                dr.ellipse([b[0]-r, b[1]-r, b[0]+r, b[1]+r], fill=color)
            t += step
            remain -= step
            if remain <= 0.0001:
                dashing = not dashing
                remain = dash if dashing else gap
        cur = nxt

def badge(dr, center, label, color, radius=44, font=None):
    x, y = center
    dr.ellipse([x-radius, y-radius, x+radius, y+radius],
               fill=color, outline=(255,255,255), width=4)
    if font is None:
        font = ImageFont.truetype('arialbd.ttf', 30)
    bbox = dr.textbbox((0, 0), label, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    dr.text((x - tw/2 - bbox[0], y - th/2 - bbox[1]), label,
            fill=(255,255,255), font=font)

# ---- badge anchors: pick a point on each route, away from scenes ----
def point_on(p1, p2, t):
    return (p1[0] + (p2[0]-p1[0])*t, p1[1] + (p2[1]-p1[1])*t)

BADGE_POS = {
    'DAY 1': point_on(SCENES['airport'], SCENES['hotel'], 0.55),   # between airport & hotel
    'DAY 2': point_on(SCENES['hotel'], SCENES['aquarium'], 0.45),  # hotel -> aquarium leg
    'DAY 3': (755, 775),  # on tianya->dutyfree leg, nudged right to clear the aquarium label
}
BADGE_R = {'DAY 1': 44, 'DAY 2': 44, 'DAY 3': 42}

# ---- draw routes ----
for label, color, stops in ROUTES:
    for i in range(len(stops)-1):
        (sa, ca), (sb, cb) = stops[i], stops[i+1]
        p1, p2 = SCENES[sa], SCENES[sb]
        if cb is not None:  # curved leg via control point (absolute coords)
            dashed_curve(draw, p1, cb, p2, color)
        else:
            dashed_line(draw, p1, p2, color)

# ---- draw badges on top ----
try:
    font = ImageFont.truetype('arialbd.ttf', 30)
except OSError:
    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 30)

for label, color, _ in ROUTES:
    badge(draw, BADGE_POS[label], label, color, radius=BADGE_R[label], font=font)

im.save(OUT_PNG)
im.save(OUT_JPG, 'JPEG', quality=85, optimize=True, progressive=True)
im.resize((1024, 683)).save('_preview.png')
print('saved', OUT_PNG, OUT_JPG)
