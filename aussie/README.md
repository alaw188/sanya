# 2026 澳洲家庭之旅 — Sydney & Melbourne  trip 網站

給父母了解及準備 2026 年 12 月澳洲行程嘅單頁式網站（Single-file static site），繁體中文為主，地點名稱保留英文。

- **開啟方式**：直接雙擊 `index.html`（唔使裝任何嘢、唔使 build）
- **行程日期**：2026/12/11（五）– 12/24（四）
- **資料來源**：Wanderlog 行程 PDF（`2026 Family Trip to Sydney & Mel – Wanderlog.pdf`）

## 行程重點速覽

| 項目 | 內容 |
|------|------|
| 去程 | CX111 香港 → 雪梨 12/11 19:05 – 12/12 07:15（商務，早啲入貴賓室） |
| 內陸機 | SYD → MEL 12/17（票價約 HK$700–1,500／位；手提 8–10kg + 寄艙 23/25kg） |
| 會合 | Andy 搭 CX105 12/17 中午 12:30 抵達墨爾本（MEL） |
| 回程 | SQ218 MEL → SIN 12/24 00:35–05:15；SQ874 SIN → HKG 07:30–11:20（新航寄艙 35kg 只計總重） |
| 雪梨住宿 | Meriton Suites Chatswood（12/12–17，A$1,796，Trip.com 確認號 1359047031130997） |
| 墨爾本住宿 | Swanston Central Airbnb（12/17–23，HK$19,636，確認號 HM35QXK4BK）⚠️ 12/10 3pm 前取消只獲部分退款 |

## 檔案結構

```
aussie/
└── index.html    # 成個網站（HTML + CSS + JS 全部單一檔案）
```

## index.html 內部結構（日後更新睇呢度）

| 區塊 | 位置 | 用途 |
|------|------|------|
| `<style>` | 頂部 | 版面樣式；`.place .cost` 控制費用標籤 |
| HTML sections | 中段 | 行程總覽 / 航班 / 住宿 / 逐日行程（#sydney #melbourne）/ 貼士 |
| `CATS` | `<script>` 內 | 地點分類 → 圖標同標籤 |
| `DAYS` | `<script>` 內 | **逐日行程資料**（每個地點一個 object：`n` 名、`zh` 中文名、`type` 分類、`d` 簡介、`hours`、`wiki`、`book`） |
| `COSTS` | `<script>` 內 | **費用對照表**（key = 地點名，value = 費用文字；`FREE` 常數顯示綠色） |
| `IMGS` | `<script>` 內 | 冇 Wikipedia 條目嘅餐廳／咖啡店 → Wikimedia Commons 實景相 URL |
| Renderer | `<script>` 內 | `renderDay()` 產生卡片；Wikipedia API 自動抓圖；`p.img` 優先於 wiki 抓圖 |

### 點樣加／改一個地點

1. 喺 `DAYS` 對應日子嘅陣列入加一個 object：
   `{n:"地點英文名", zh:"中文名", type:"food", wiki:"Wikipedia條目(如適用)", book:true(需訂位才加), hours:"...", d:"簡介"}`
2. 有需要再喺 `COSTS` / `IMGS` 加同名 key。

## 圖片運作

- **有 Wikipedia 條目**嘅景點（歌劇院、大橋、QVM、State Library、十二門徒石等）：由瀏覽器 runtime call `en.wikipedia.org/api/rest_v1/page/summary/...` 抓縮圖（所有條目名已驗證有圖）。
- **冇條目**嘅餐廳／咖啡店：用 `IMGS` 表內預先搵好嘅 Wikimedia Commons 靜態 URL（食物／店內實景，API 搜尋得嚟）。
- 離線或 API 失敗會自動 fallback 顯示分類圖標，版面唔會爛。
- 現況：全部 61 張卡都有圖（23 張靠 wiki 抓圖、38 張靠 `IMGS`）。
- ⚠️ `IMGS`／`COSTS` 嘅 key **必須同 `DAYS` 入面嘅 `n` 完全一致**，改名時要三個表同步改，否則會變返圖標／冇費用（可用逐行對比 `\{n:"([^"]+)"` 嘅方式核查）。

## 待辦 / 後續跟進（Follow-ups）

- [ ] 訂位：Cafe Margaret、6HEAD、Bar Totti's、The Gidley（必訂）；The Grounds、Higher Ground、Grain Store、mimi's（建議訂）
- [ ] 訂團：Klook 獵人谷一日遊（12/15，$1,275／位含午餐）；Yarra Valley 酒莊團（12/20，兩個選項 8:45 / 9:30 出發）
- [ ] 訂票：Sydney Opera House 導賞團；Phillip Island Penguin Parade（12/19 黃昏場）
- [ ] 內陸機 SYD→MEL（12/17 上午，11:00–12:30 到達）買飛
- [ ] ⚠️ Airbnb Swanston Central：11/17 3pm 前免費取消期限已過／將到，留意 12/10 3pm 部分退款期限
- [ ] 費用標籤全部係估計值，出發前想更新的話改 `COSTS` 表就得

## 已知限制

- 費用為預算參考（非實時匯率／價格），匯率以約 1 AUD ≈ 5 HKD 計
- Commons 圖片伺服器對大量快速請求會回 429（瀏覽器正常逐張載入不受影響）
- 需要互聯網先顯示圖片；離線時顯示圖標
