"""去除 AI 生成圖右下角浮水印。

用法
----
    python remove_wm.py <輸入圖> <輸出圖> [x1 y1 x2 y2] [sample_h]

原理
----
浮水印固定在右下角，且總是疊在較平坦的區域（沙灘／海面／夜色樹叢）。
做法是取浮水印「上方一條同寬的紋理帶」垂直翻轉後填回，
因為翻轉後的顏色與原區域連續，接縫在視覺上不可見。

參數
----
x1 y1 x2 y2  浮水印矩形（含緩衝），預設 (1290, 955, W, H-4)
sample_h      取樣帶高度，預設 80

例
----
    python remove_wm.py in.png out.png
    python remove_wm.py in.png out.png 1290 950 1536 1024 90
"""
import sys
from PIL import Image
import numpy as np


def fill_with_vertical_mirror(input_path, output_path, region=None, sample_h=80):
    img = Image.open(input_path).convert('RGB')
    arr = np.array(img)
    h, w = arr.shape[:2]

    if region is None:
        region = (int(w * 0.84), int(h * 0.93), w, h - 4)
    x1, y1, x2, y2 = region
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    fill_h, fill_w = y2 - y1, x2 - x1
    if fill_h <= 0 or fill_w <= 0:
        raise ValueError('浮水印矩形無效: %r (image %dx%d)' % (region, w, h))

    # 取 region 上方 sample_h 像素作參考帶
    s_top = max(0, y1 - sample_h)
    sample = arr[s_top:y1, x1:x2].copy()
    if sample.shape[0] == 0:
        raise ValueError('上方無可取樣像素，請調高 y1 或降低 sample_h')

    # 垂直翻轉並裁切／補滿到 fill_h
    mirrored = sample[::-1][:fill_h]
    while mirrored.shape[0] < fill_h:
        mirrored = np.concatenate(
            [mirrored, sample[::-1][:fill_h - mirrored.shape[0]]], axis=0)

    arr[y1:y2, x1:x2] = mirrored
    Image.fromarray(arr).save(output_path)
    print('  -> %s  filled %dx%d  sample y=%d..%d  (image %dx%d)'
          % (output_path, fill_w, fill_h, s_top, y1, w, h))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    region = None
    if len(sys.argv) >= 7:
        region = tuple(int(v) for v in sys.argv[3:7])
    sample_h = int(sys.argv[7]) if len(sys.argv) >= 8 else 80
    fill_with_vertical_mirror(inp, outp, region, sample_h)


if __name__ == '__main__':
    main()
