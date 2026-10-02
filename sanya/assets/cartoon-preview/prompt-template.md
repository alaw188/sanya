# 卡通手繪行程圖 · 可重用提示詞模板

> 來源：三亞海棠灣行程地圖實測（2026-10）。下次換地點時替換 `【】` 內容即可。
> 搭配本資料夾的 `remove_wm.py` 可去除生成圖右下角浮水印。

---

## 模板 A — 卡通手繪行程地圖（橫式，實測效果最佳）

```text
A hand-drawn watercolor sketch illustration travel map of 【目的地／地區名】,
sketchbook travel journal style. Soft watercolor washes with fine ink line
work, slight paper texture, gentle pastel palette dominated by
【主色 1】、【主色 2】、【強調色】 and off-white.

Title at top center in bold Chinese brush-painted characters:
【行程標題，例：東京五日親子遊】. NO subtitle, NO quotation marks around
the title, NO bracketed punctuation. NO watermark, NO AI signature,
NO platform branding anywhere.

Mark the following 【N】 locations with hand-drawn circular badges.
Each badge should contain a tiny scene showing the actual character of
that place, NOT just an icon:

1. 【地點名】 position: 【該地最具辨識度的場景，如：紅色鐵塔＋櫻花】
2. 【地點名】 position: 【場景描述】
…（依序列出，每個地點一行，一句話描述「畫面裡要出現什麼」）

Connect the locations in itinerary order with 【天數】 clearly distinct
colored dashed lines forming one continuous journey:
- Day 1 segments in 【顏色 A】 dashes (【當日動線順序】)
- Day 2 segments in 【顏色 B】 dashes (【當日動線順序】)
- 【…依天數增加】

Add a small 「DAY 1」「DAY 2」 tag on each colored line near its midpoint
so the days are unmistakable.

Decorative touches: 【當地氛圍小元素 3–5 個，如：電車、壽司、楓葉、神社鳥居】.
Small Chinese caption labels hand-lettered on the map like
【地名，如：東京灣】.

Landscape composition, generous whitespace, no clutter. Avoid realistic
geography but keep recognizable as 【地區特徵】. Style reference:
studio ghibli travel sketch + watercolor postcard.
```

### 推薦生成參數

| 參數 | 值 |
|---|---|
| size | `1536x1024` |
| quality | `high` |
| style | `vivid` |

---

## 模板 C — 三日日程速覽資訊圖（直式）

```text
A hand-drawn watercolor sketch infographic, vertical poster format,
sketchbook travel journal aesthetic. Off-white paper texture background.

Title block at top: 【行程標題】 brush-lettered, subtitle 【副標】,
tiny tag 【起訖點，如：HKG ⇄ NRT】 at the very top.
NO watermarks, NO AI signature.

Three horizontal bands (Day 1 / 2 / 3), each with:
- colored left accent bar (Day 1 【色 A】, Day 2 【色 B】, Day 3 【色 C】)
- large rounded number badge
- Chinese day subtitle (抵達 / 探索 / 離別 或自訂)
- horizontal flow of 【7–8】 hand-drawn watercolor icons connected by
  dotted arrows, each icon with a tiny Chinese caption underneath:
  【每日逐項列出：icon 場景 + 中文短標】

Footer: thin hand-drawn wave separator + tiny hand-lettered line
【全程 N 日 · 地區 · 年月】.
```

### 推薦生成參數

| 參數 | 值 |
|---|---|
| size | `1024x1536` |
| quality | `high` |
| style | `vivid` |

---

## 實測關鍵技巧

| 技巧 | 說明 |
|---|---|
| **場景式 badge** | 每個地點寫「畫面裡要出現什麼」（如：蒸氣火鍋店），而不是只給 icon 名稱——這是細節感的來源 |
| **動線分日著色** | 明確指定每天一個顏色＋要求「DAY n」標籤夾在路線中段，避免顏色混在一起 |
| **標題規則寫清楚** | `NO subtitle, NO quotation marks, NO bracketed punctuation`——少了這句會自動加「」和副標 |
| **指定色票** | 給實際 hex 色碼（如 `deep teal #0f4f5c`），畫面配色才會跟網站一致 |
| **中文標註** | 生成中文標籤成功率不錯，但每個標籤控制在 **4–8 字**最穩 |
| **浮水印必出現** | 生成平台強制加「AI生成」浮水印，prompt 擋不掉；用 `remove_wm.py` 以周邊紋理鏡像填補（改 region 座標即可） |
| **網頁輸出** | PNG 原檔約 3MB，記得轉 `JPEG quality 85 + progressive`（實測 3MB → 435KB）再上站 |

---

## 三亞版實際使用範例（主色票參考）

- 主色：deep teal `#0f4f5c`
- 強調：warm gold `#c9a227`、coral pink
- Day 1 橘金 / Day 2 青藍 / Day 3 珊瑚粉
- 八個景點：三亞鳳凰機場、海棠灣洲際、海棠68美食街、亞龍灣熱帶天堂、亞特蘭蒂斯水族館、後海村、天涯海角（南天一柱）、三亞國際免稅城
