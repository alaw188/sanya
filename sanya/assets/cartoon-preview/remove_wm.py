"""用周邊紙張/沙灘紋理鏡像填補右下角浮水印，輸出無浮水印版本。"""
from PIL import Image
import numpy as np


def fill_with_vertical_mirror(input_path, output_path, region, sample_h=80):
    """
    region = (x1, y1, x2, y2) 浮水印矩形 (含邊界緩衝)
    從 region 上方取一段高度同 region 的樣本，垂直翻轉後填入 region。
    """
    x1, y1, x2, y2 = region
    fill_h = y2 - y1
    fill_w = x2 - x1

    img = Image.open(input_path).convert('RGB')
    arr = np.array(img)

    # 取 region 上方 sample_h 像素作參考帶
    s_top = max(0, y1 - sample_h)
    sample = arr[s_top:y1, x1:x2].copy()  # (sample_h, fill_w, 3)

    # 翻轉並裁切到 fill_h
    mirrored = sample[::-1][:fill_h]

    # 若 mirrored 不足 fill_h，再多翻幾次填滿
    while mirrored.shape[0] < fill_h:
        mirrored = np.concatenate([mirrored, sample[::-1][:fill_h - mirrored.shape[0]]], axis=0)

    arr[y1:y2, x1:x2] = mirrored
    Image.fromarray(arr).save(output_path)
    print(f"  -> {output_path}  filled ({fill_w}x{fill_h})")


print("[A] landscape map (1536x1024)")
fill_with_vertical_mirror(
    'A_hand_drawn_watercolor_sketch_2026-10-02T09-22-49.png',
    'A_no_wm.png',
    region=(1295, 940, 1536, 1020),  # 含緩衝
    sample_h=80,
)

print("[C] portrait poster (1024x1536)")
fill_with_vertical_mirror(
    'A_hand_drawn_watercolor_sketch_2026-10-02T05-58-55.png',
    'C_no_wm.png',
    region=(860, 1430, 1024, 1536),
    sample_h=110,
)