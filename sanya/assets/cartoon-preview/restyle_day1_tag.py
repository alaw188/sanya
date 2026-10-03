# -*- coding: utf-8 -*-
"""DAY 1 標籤重製 v5（final）：
1) 洋蔥剝皮 inpainting 抹掉扁平標籤與溢出文字（顏色由周圍自然延續，無接縫）
2) 取 DAY 2 圓碟（逐列水平內插去字 → 逐像素珊瑚 LUT）縮放對位貼入
3) 文字置中（修正 textbbox 原點 bug）
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

im = Image.open('backup/H_iso_no_wm.png').convert('RGB')
arr = np.array(im).astype(np.float64)


def dilate(m, it):
    for _ in range(it):
        n = m.copy()
        n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        m = n
    return m


# ---- 1) 建立待清除遮罩：扁平標籤 pill ＋ 溢出的白字 ----
pill = np.zeros(arr.shape[:2], dtype=bool)
pill[322:369, 1035:1144] = True            # rounded rect 外接框（含角）
# 白字溢出部分（x > 1143）
pill[343:364, 1143:1162] = True
# 洋蔥剝皮 inpaint
known = ~pill
for _ in range(60):
    hole = pill & ~known
    if not hole.any():
        break
    kn = known.astype(np.float64)
    cnt = kn.copy()
    acc = arr * kn[..., None]
    nsum = np.zeros_like(cnt)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        acc += np.roll(np.roll(arr * kn[..., None], dy, 0), dx, 1)
        nsum += np.roll(np.roll(kn, dy, 0), dx, 1)
    fillable = hole & (nsum > 0)
    avg = acc / np.maximum(nsum, 1)[..., None]
    arr[fillable] = avg[fillable]
    known = known | fillable
print('inpainted px done')

# ---- 2) 珊瑚黏土 LUT ----
dots = np.concatenate([
    arr[410:442, 900:940].reshape(-1, 3),
    arr[418:442, 1035:1068].reshape(-1, 3),
])
r, g, b = dots[..., 0], dots[..., 1], dots[..., 2]
cm = (r > 185) & (r - g > 32) & (g < 215) & (b < 200)
dots = dots[cm]
lum = dots.mean(axis=1)
order = np.argsort(lum)
dots, lum = dots[order], lum[order]
bins = np.linspace(lum.min(), lum.max(), 25)
lut_lum, lut_rgb = [], []
for i in range(24):
    m = (lum >= bins[i]) & (lum <= bins[i + 1])
    if m.sum() >= 3:
        lut_lum.append(lum[m].mean())
        lut_rgb.append(dots[m].mean(axis=0))
lut_lum = np.array(lut_lum)
lut_rgb = np.array(lut_rgb)


def lut_apply(px):
    l = np.clip(px.mean(axis=-1), lut_lum.min(), lut_lum.max())
    idx = np.clip(np.searchsorted(lut_lum, l) - 1, 0, len(lut_lum) - 1)
    frac = np.clip((l - lut_lum[idx]) / (lut_lum[idx + 1] - lut_lum[idx] + 1e-6), 0, 1)[..., None]
    return lut_rgb[idx] * (1 - frac) + lut_rgb[np.minimum(idx + 1, len(lut_lum) - 1)] * frac


# ---- 3) 取 DAY 2 圓碟、去字、轉色 ----
SX0, SY0, SX1, SY1 = 964, 506, 1092, 596
src = arr[SY0:SY1, SX0:SX1].copy()
smask = src[..., 1] > src[..., 0] + 8
eys, exs = np.nonzero(smask)
ecy_f, ecx_f = (eys.min() + eys.max()) / 2, (exs.min() + exs.max()) / 2
plum = src.mean(axis=-1)
mx = src.max(axis=-1); mn = src.min(axis=-1)
txt = (plum > 220) & ((mx - mn) < 58)
txt = dilate(txt, 4) & dilate(smask, 1)     # 4px 涵蓋原字投影
for row in range(src.shape[0]):
    rm = txt[row]
    if not rm.any():
        continue
    xs = np.nonzero(rm)[0]
    splits = np.nonzero(np.diff(xs) > 1)[0]
    for run in np.split(xs, splits + 1):
        x_a, x_b = run[0] - 1, run[-1] + 1
        ca = src[row, max(x_a, 0)]
        cb = src[row, min(x_b, src.shape[1] - 1)]
        n = len(run)
        for i, x in enumerate(run):
            t = (i + 1) / (n + 1)
            src[row, x] = ca * (1 - t) + cb * t
gr = src[..., 1] > src[..., 0] + 6
src[gr] = np.clip(lut_apply(src[gr]), 0, 255)

# ---- 4) 縮放對位：圓碟中心 (1089,345)，略大於原 pill 以完全覆蓋 ----
disc = src[eys.min():eys.max() + 1, exs.min():exs.max() + 1]
dmask = smask[eys.min():eys.max() + 1, exs.min():exs.max() + 1]
TW, TH = 114, 68                       # 目標尺寸（蓋過 pill 1035-1143,322-368）
disc_r = np.array(Image.fromarray(disc.astype(np.uint8)).resize((TW, TH), Image.LANCZOS), dtype=np.float64)
mask_r = np.array(Image.fromarray((dmask * 255).astype(np.uint8)).resize((TW, TH), Image.LANCZOS)
                  .filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float64)[..., None] / 255.0
DX, DY = 1089 - TW // 2, 345 - TH // 2
print('paste at', DX, DY)
dest = arr[DY:DY + TH, DX:DX + TW]
arr[DY:DY + TH, DX:DX + TW] = dest * (1 - mask_r) + disc_r * mask_r

# ---- 5) DAY 1 文字（置中）----
out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
tcx, tcy = 1089, 344
font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 23)
tb = ImageDraw.Draw(out).textbbox((0, 0), 'DAY 1', font=font)
tw, th = tb[2] - tb[0], tb[3] - tb[1]
cx = int(tcx) - tw // 2 - tb[0]
cy = int(tcy) - th // 2 - tb[1]
sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).text((cx + 2, cy + 3), 'DAY 1', font=font, fill=(150, 70, 55, 150))
sh = sh.filter(ImageFilter.GaussianBlur(1.6))
out = Image.alpha_composite(out, sh)
txt = Image.new('RGBA', out.size, (0, 0, 0, 0))
ImageDraw.Draw(txt).text((cx, cy), 'DAY 1', font=font, fill=(255, 255, 255, 255))
txt = txt.filter(ImageFilter.GaussianBlur(0.4))
out = Image.alpha_composite(out, txt)

rgb = out.convert('RGB')
rgb.save('backup/H_iso_no_wm.png')
rgb.save('H_iso_web.jpg', 'JPEG', quality=85, optimize=True, progressive=True)
rgb.crop((990, 270, 1200, 420)).resize((630, 450), Image.NEAREST).save('_t4.png')
print('done')
