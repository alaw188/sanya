# -*- coding: utf-8 -*-
"""Overlay itinerary routes + DAY badges onto the three base maps.

Route semantics (single source of truth = the itinerary):
  Day 1 (teal) : airport -> hotel  -> food street
  Day 2 (gold) : hotel   -> yalong -> aquarium -> houhai
  Day 3 (coral): hotel   -> tianya -> dutyfree -> airport

The base images are AI-generated scene-only maps (no routes, no badges), so
every route here is drawn deterministically from coordinates and cannot get
the day/scene assignment wrong.

Details that matter:
  * scenes use an elliptical keep-out (rx, ry) so strokes stop at the edge of
    the artwork instead of painting over it
  * the yalong -> aquarium leg detours under the central hotel
  * the dutyfree -> airport leg sweeps west around yalong
  * badges are positioned by arc length along the real polyline
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

TEAL = (15, 79, 92)      # #0F4F5C  Day 1
GOLD = (198, 160, 44)    # Day 2
CORAL = (216, 104, 86)   # Day 3
WHITE = (255, 255, 255)

STOPS = {
    1: ['airport', 'hotel', 'food'],
    2: ['hotel', 'yalong', 'aquarium', 'houhai'],
    3: ['hotel', 'tianya', 'dutyfree', 'airport'],
}

GAP = 16  # clearance between stroke tip and artwork


def ell(rx, ry):
    return (rx, ry)


STYLES = {
    'A': {
        'file': 'Cute_isometric_3D_miniature_di_2026-10-03T05-37-26.png',
        'scenes': {
            'airport': (238, 176), 'hotel': (772, 350), 'food': (1276, 178),
            'yalong': (232, 486), 'aquarium': (1272, 502), 'houhai': (1284, 830),
            'tianya': (776, 830), 'dutyfree': (318, 788),
        },
        'rad': {
            'airport': ell(126, 104), 'hotel': ell(300, 196), 'food': ell(126, 100),
            'yalong': ell(132, 108), 'aquarium': ell(136, 112), 'houhai': ell(126, 104),
            'tianya': ell(122, 100), 'dutyfree': ell(136, 108),
        },
        'detour': {('yalong', 'aquarium'): (770, 660)},
        'curve': {('dutyfree', 'airport'): (-70, 300)},
        'wm': (300, 995, 1200, 1016),
        'badges': [
            (1, 'airport', 'hotel', 0.66, -10, -54),
            (2, 'yalong', 'aquarium', 0.50, 0, 4),
            (3, 'tianya', 'dutyfree', 0.50, 0, 50),
        ],
    },
    'B': {
        'file': 'A_hand_drawn_watercolor_illust_2026-10-03T05-37-26.png',
        'scenes': {
            'airport': (240, 232), 'hotel': (786, 414), 'food': (1290, 196),
            'yalong': (228, 512), 'aquarium': (1288, 508), 'houhai': (1130, 822),
            'tianya': (600, 822), 'dutyfree': (218, 812),
        },
        'rad': {
            'airport': ell(122, 100), 'hotel': ell(290, 190), 'food': ell(118, 96),
            'yalong': ell(128, 104), 'aquarium': ell(130, 108), 'houhai': ell(124, 100),
            'tianya': ell(118, 96), 'dutyfree': ell(128, 104),
        },
        'detour': {('yalong', 'aquarium'): (756, 700)},
        'curve': {('dutyfree', 'airport'): (-70, 330)},
        'wm': (300, 995, 1200, 1016),
        'badges': [
            (1, 'airport', 'hotel', 0.70, -14, -56),
            (2, 'yalong', 'aquarium', 0.50, 0, 4),
            (3, 'tianya', 'dutyfree', 0.50, 0, 50),
        ],
    },
    'C': {
        'file': 'A_clean_flat_vector_illustrati_2026-10-03T05-37-29.png',
        'scenes': {
            'airport': (252, 196), 'hotel': (768, 406), 'food': (1284, 168),
            'yalong': (250, 508), 'aquarium': (1284, 512), 'houhai': (1262, 824),
            'tianya': (768, 832), 'dutyfree': (228, 826),
        },
        'rad': {
            'airport': ell(118, 96), 'hotel': ell(272, 182), 'food': ell(116, 92),
            'yalong': ell(122, 100), 'aquarium': ell(124, 104), 'houhai': ell(120, 98),
            'tianya': ell(116, 94), 'dutyfree': ell(124, 100),
        },
        'detour': {('yalong', 'aquarium'): (760, 700)},
        'curve': {('dutyfree', 'airport'): (-70, 300)},
        'wm': (300, 995, 1200, 1016),
        'badges': [
            (1, 'airport', 'hotel', 0.66, -10, -54),
            (2, 'yalong', 'aquarium', 0.50, 0, 4),
            (3, 'tianya', 'dutyfree', 0.50, 0, 50),
        ],
    },
}

BADGE_R = 52
FONT_PX = 30


def qbez(p0, pc, p2, t):
    m = 1 - t
    return (m * m * p0[0] + 2 * m * t * pc[0] + t * t * p2[0],
            m * m * p0[1] + 2 * m * t * pc[1] + t * t * p2[1])


def _ell_t(p_from, p_to, r_from, r_to):
    """Deprecated shim kept for clarity; routing now works in pixel space."""
    return 0.0, 1.0


def _outside(p, c, r, gap=0.0):
    rx, ry = r[0] + gap, r[1] + gap
    return ((p[0] - c[0]) / rx) ** 2 + ((p[1] - c[1]) / ry) ** 2 >= 1.0


def _edge(p_from, p_to, r, extra=GAP):
    """Walk from p_from toward p_to until past ellipse r, then `extra` further."""
    dx, dy = p_to[0] - p_from[0], p_to[1] - p_from[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    ray = 1.0 / math.sqrt((ux / r[0]) ** 2 + (uy / r[1]) ** 2)
    k = min(ray + extra, L)
    return (p_from[0] + ux * k, p_from[1] + uy * k)


def leg_points(cfg, a, b):
    """Polyline for one leg, trimmed so it stops at each scene's artwork edge."""
    sc, rad = cfg['scenes'], cfg['rad']
    p1, p2 = sc[a], sc[b]

    # bezier sweep (dutyfree -> airport)
    if (a, b) in cfg['curve']:
        pc = cfg['curve'][(a, b)]
        raw = [qbez(p1, pc, p2, i / 240.0) for i in range(241)]
        s = 0
        for i, p in enumerate(raw):
            if _outside(p, p1, rad[a], GAP):
                s = i
                break
        e = len(raw) - 1
        for i in range(len(raw) - 1, -1, -1):
            if _outside(raw[i], p2, rad[b], GAP):
                e = i
                break
        if e <= s + 1:
            m = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            return [m, m]
        return raw[s:e + 1]

    # two-leg detour under the hotel (yalong -> aquarium)
    if (a, b) in cfg['detour']:
        w = cfg['detour'][(a, b)]
        A = _edge(p1, w, rad[a])
        B = _edge(p2, w, rad[b])
        if math.hypot(A[0] - w[0], A[1] - w[1]) < 20 or \
           math.hypot(B[0] - w[0], B[1] - w[1]) < 20:
            return [A, B]
        return [A, w, B]

    # plain straight leg
    A = _edge(p1, p2, rad[a])
    B = _edge(p2, p1, rad[b])
    if math.hypot(B[0] - A[0], B[1] - A[1]) < 24:
        m = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        return [m, m]
    return [A, B]


def arc_point(pts, t):
    """Point at fraction t of the polyline's arc length."""
    segs = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            for i in range(len(pts) - 1)]
    total = sum(segs) or 1.0
    target, acc = total * t, 0.0
    for i, s in enumerate(segs):
        if acc + s >= target or i == len(segs) - 1:
            f = (target - acc) / s if s else 0.0
            f = max(0.0, min(1.0, f))
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f,
                    pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f)
        acc += s
    return pts[-1]


def stroke(dr, pts, color, width=7, dash=18, gap=14):
    on, remain = True, float(dash)
    r = width / 2.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        t = 0.0
        while t < seg:
            step = min(remain, seg - t)
            if on:
                p = (a[0] + ux * t, a[1] + uy * t)
                q = (a[0] + ux * (t + step), a[1] + uy * (t + step))
                dr.line([p, q], fill=color, width=width)
                dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)
                dr.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=color)
            t += step
            remain -= step
            if remain <= 1e-6:
                on = not on
                remain = dash if on else gap


def badge(dr, c, text, color, radius, font):
    x, y = c
    halo = radius + 9
    dr.ellipse([x - halo - 4, y - halo - 2, x + halo + 4, y + halo + 6],
               fill=(120, 112, 98, 55))
    dr.ellipse([x - halo, y - halo, x + halo, y + halo], fill=WHITE)
    dr.ellipse([x - radius, y - radius, x + radius, y + radius],
               fill=color, outline=WHITE, width=4)
    bb = dr.textbbox((0, 0), text, font=font)
    dr.text((x - (bb[2] - bb[0]) / 2 - bb[0],
             y - (bb[3] - bb[1]) / 2 - bb[1]), text, fill=WHITE, font=font)


def strip_watermark(im, sample_box, wm_box, seed=11):
    arr = np.array(im).astype(np.float64)
    x0, y0, x1, y1 = sample_box
    patch = arr[y0:y1, x0:x1].reshape(-1, 3)
    q = (patch // 3).astype(np.int64)
    key = q[:, 0] * 65536 + q[:, 1] * 256 + q[:, 2]
    vals, counts = np.unique(key, return_counts=True)
    fill = patch[key == vals[np.argmax(counts)]].mean(axis=0)
    bx0, by0, bx1, by1 = wm_box
    rng = np.random.default_rng(seed)
    arr[by0:by1, bx0:bx1] = fill[None, None, :] + rng.normal(0, 1.0, (by1 - by0, bx1 - bx0, 3))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def build(key, cfg):
    im = Image.open(os.path.join(HERE, cfg['file'])).convert('RGB')
    im = strip_watermark(im, cfg['wm'], (1300, 928, 1536, 1024))

    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    palette = {1: TEAL, 2: GOLD, 3: CORAL}
    legs = {}
    for day, stops in STOPS.items():
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            pts = leg_points(cfg, a, b)
            legs[(day, a, b)] = pts
            stroke(dr, pts, palette[day])

    try:
        font = ImageFont.truetype('arialbd.ttf', FONT_PX)
    except OSError:
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', FONT_PX)

    for day, a, b, t, dx, dy in cfg['badges']:
        p = arc_point(legs[(day, a, b)], t)
        badge(dr, (p[0] + dx, p[1] + dy), 'DAY %d' % day, palette[day], BADGE_R, font)

    out = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    out.save(os.path.join(HERE, 'map_%s_no_wm.png' % key))
    out.save(os.path.join(HERE, 'map_%s_web.jpg' % key), 'JPEG',
             quality=86, optimize=True, progressive=True)
    out.resize((1024, 683)).save(os.path.join(HERE, '_prev_%s.png' % key))
    print('%s ok' % key)


if __name__ == '__main__':
    for k in ('A', 'B', 'C'):
        build(k, STYLES[k])
