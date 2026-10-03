# -*- coding: utf-8 -*-
"""候選 4 修正 v2：DAY 1 / DAY 2 標籤文字對調。
關鍵：標籤底是暖奶油色（sat 30-45），珊瑚字 sat~128、薄荷字 g>r 且 sat~37。
以「sat>75」抓珊瑚字、「g-r>8 & sat>26」抓薄荷字，其餘一律保留。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

rng = np.random.default_rng(5)
im = Image.open('_c4.png').convert('RGB')
arr = np.array(im).astype(np.float64)


def dilate(m, it):
    for _ in range(it):
        n = m.copy()
        n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        m = n
    return m


def replace_text(a, region, center, rot, new_text, new_color, pick, font_size=34, dark_band=None):
    x0, y0, x1, y1 = region
    sub = a[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = mx - mn
    plum = sub.mean(axis=-1)
    textish = pick(r, g, b, sat)
    textish = dilate(textish, 2)
    if dark_band is not None:
        bx0, by0, bx1, by1 = dark_band
        band = np.zeros_like(textish)
        band[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0] = True
        textish |= (plum < 198) & dilate(textish, 3) & band
    face = ~textish
    cream = np.median(sub[face].reshape(-1, 3), axis=0)
    print('cream', cream.round(0), 'text px', int(textish.sum()))
    n = int(textish.sum())
    sub[textish] = np.clip(cream[None, None, :] + rng.normal(0, 2.0, (n, 3)), 0, 255)
    a[y0:y1, x0:x1] = sub

    out_img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    # 柔和陰影
    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', font_size)
    sh = Image.new('RGBA', out_img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    tb = sd.textbbox((0, 0), new_text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    gx = int(center[0] - tw / 2 - tb[0])
    gy = int(center[1] - th / 2 - tb[1])
    sd.text((gx + 2, gy + 3), new_text, font=font, fill=(140, 110, 85, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(1.6))
    out_img = Image.alpha_composite(out_img, sh)
    # 主字
    tl = Image.new('RGBA', out_img.size, (0, 0, 0, 0))
    ImageDraw.Draw(tl).text((gx, gy), new_text, font=font, fill=tuple(int(c) for c in new_color) + (255,))
    tl = tl.filter(ImageFilter.GaussianBlur(0.4))
    out_img = Image.alpha_composite(out_img, tl)
    return out_img


# 取樣文字顏色
t1 = arr[272:312, 592:692].reshape(-1, 3)
r, g, b = t1[..., 0], t1[..., 1], t1[..., 2]
coral = np.median(t1[(r > 180) & (r - b > 60)], axis=0)
t2 = arr[478:535, 928:1045].reshape(-1, 3)
r, g, b = t2[..., 0], t2[..., 1], t2[..., 2]
mint = np.median(t2[(g > 150) & (g - r > 25)], axis=0)
print('coral', coral.round(0), 'mint', mint.round(0))

# Tag1（亞龍灣旁，薄荷線）：珊瑚字 → DAY 2 薄荷字
out = replace_text(arr, (576, 266, 698, 324), (641, 293), -2, 'DAY 2', mint,
                   pick=lambda r, g, b, s: s > 75,
                   dark_band=(585, 275, 694, 320))
# Tag2（美食街旁，珊瑚線）：薄荷字 → DAY 1 珊瑚字
arr = np.array(out.convert('RGB')).astype(np.float64)
out = replace_text(arr, (920, 470, 1052, 545), (987, 508), -12, 'DAY 1', coral,
                   pick=lambda r, g, b, s: (g - r > 8) & (s > 24),
                   dark_band=(928, 480, 1038, 538))

rgb = out.convert('RGB')
rgb.save('backup/H_iso_no_wm.png')
rgb.save('H_iso_web.jpg', 'JPEG', quality=85, optimize=True, progressive=True)
rgb.crop((540, 240, 740, 350)).resize((500, 275), Image.NEAREST).save('_s1.png')
rgb.crop((890, 440, 1110, 570)).resize((550, 325), Image.NEAREST).save('_s2.png')
print('done')
