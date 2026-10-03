# -*- coding: utf-8 -*-
"""H 地圖路線修正 v3：
- 放寬珊瑚紅遮罩（含飯店陰影下的圓點）
- 擦除區改用周圍取樣中位色 + 高斯噪點，消除色塊感
- 重畫 DAY 1 標籤於斜線段
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

rng = np.random.default_rng(7)
im = Image.open('backup/H_iso_no_wm.png').convert('RGB')  # v2 狀態（含部分修正）
arr = np.array(im).astype(np.float64)


def coral_mask(a, loose=False):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if loose:
        return (r > 185) & (r - g > 38) & (g < 185) & (b < 178)
    return (r > 200) & (g > 60) & (g < 165) & (b > 60) & (b < 165) & (r - g > 55)


def mint_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (g > 160) & (r < 185) & (g - r > 22) & (g - b > 3)


# ---- 取樣 ----
coral_reg = arr[410:442, 900:940]
coral_avg = coral_reg[coral_mask(coral_reg)].mean(axis=0)
mint_reg = arr[462:492, 700:780]
mint_avg = mint_reg[mint_mask(mint_reg)].mean(axis=0)
print('coral_avg', coral_avg.round(1), 'mint_avg', mint_avg.round(1))

# 舊標籤底色：取區域四周細條中位數（標籤已於 v2 被平塗覆蓋，改從更外圈取）
ring1 = np.concatenate([
    arr[330:336, 520:665].reshape(-1, 3),
    arr[340:428, 508:516].reshape(-1, 3),
    arr[340:428, 667:675].reshape(-1, 3),
    arr[428:434, 520:665].reshape(-1, 3),
])
bg1 = np.median(ring1, axis=0)
# 斜線段底色（避開標籤與圓點，取更上方與右側）
ring2 = np.concatenate([
    arr[300:306, 1035:1135].reshape(-1, 3),
    arr[312:380, 1137:1145].reshape(-1, 3),
])
bg2 = np.median(ring2, axis=0)
print('bg1', bg1.round(1), 'bg2', bg2.round(1))

tag_color = np.array([234.2, 152.6, 129.8])  # v2 已取樣


def textured_fill(a, x0, y0, x1, y1, color, feather=8, noise=2.5):
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(np.float64)
    alpha = np.clip(d / feather, 0, 1)[..., None]
    fill = color[None, None, :] + rng.normal(0, noise, (h, w, 3))
    zone = a[y0:y1, x0:x1]
    a[y0:y1, x0:x1] = np.clip(zone * (1 - alpha) + fill * alpha, 0, 255)


# ---- 1) 補改色（放寬遮罩，涵蓋陰影中的圓點）----
x0, y0, x1, y1 = 425, 400, 830, 480
zone = arr[y0:y1, x0:x1]
m = coral_mask(zone, loose=True) & ~mint_mask(zone)
ratio = zone.mean(axis=-1, keepdims=True) / (coral_avg.mean() + 1e-6)
zone[m] = np.clip(mint_avg[None, None, :] * ratio, 0, 255)[m]
arr[y0:y1, x0:x1] = zone
print('recolored px:', int(m.sum()))

# ---- 2) 兩個擦除區重填（含紋理）----
textured_fill(arr, 518, 338, 667, 430, bg1)
textured_fill(arr, 1035, 312, 1135, 380, bg2)

# ---- 3) 重畫 DAY 1 標籤 ----
out = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
shadow = Image.new('RGBA', out.size, (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle([1035, 326, 1143, 372], radius=23, fill=(60, 45, 35, 70))
shadow = shadow.filter(ImageFilter.GaussianBlur(4))
out = Image.alpha_composite(out, shadow)

draw = ImageDraw.Draw(out, 'RGBA')
tc = tuple(int(round(c)) for c in tag_color)
draw.rounded_rectangle([1035, 322, 1143, 368], radius=23, fill=tc + (255,))
hl = tuple(min(255, int(round(c + (255 - c) * 0.35))) for c in tag_color)
draw.rounded_rectangle([1040, 326, 1138, 344], radius=9, fill=hl + (110,))
font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 21)
tb = draw.textbbox((0, 0), 'DAY 1', font=font)
tw, th = tb[2] - tb[0], tb[3] - tb[1]
draw.text((1089 - tw / 2 - tb[0], 345 - th / 2 - tb[1]), 'DAY 1', font=font, fill=(255, 255, 255, 255))

rgb = out.convert('RGB')
rgb.save('backup/H_iso_no_wm.png')
rgb.save('H_iso_web.jpg', 'JPEG', quality=85, optimize=True, progressive=True)
rgb.crop((400, 300, 1250, 560)).save('_chkE.png')
print('saved')
