# Tech News

以 Markdown 收錄技術論文與深度文章，記錄值得理解的方法、觀點與問題。
深度文章可以是技術解析、遊戲設計、文化評論、社會分析或哲學討論，不限於學術論文。
執行根目錄的 `build.py`，即可產生靜態 HTML 網站。

## 快速開始

需要 Python 3.10 或以上版本。

```bash
python -m pip install -r requirements.txt
python build.py
```

預設同時讀取 `papers/` 和 `articles/`，開啟 `site/index.html` 即可閱讀全部收錄。
也可從導覽選擇「技術論文」「深度文章」、主題分類或標籤。沒有文章時仍可正常生成。
網站不需要後端、資料庫、Node.js 或外部 CDN。

也可以透過本機 HTTP 伺服器預覽：

```bash
python -m http.server 8000 --directory site
```

瀏覽 <http://localhost:8000>。按 `Ctrl+C` 停止預覽。

## 閱讀介面

- 首頁以最新收錄和閱讀卡片呈現，每張卡片先顯示一句白話用途或重點，再列出原文標題、標籤與收錄日期。
- 搜尋可比對標題、一句話重點、摘要、標籤、作者、來源名稱及主題名稱，並搭配內容類型篩選。多個關鍵字以空白分隔，會尋找同時符合的內容；不搜尋整篇正文。
- 首頁及「搜尋內容」頁搜尋全部收錄；分類、類型和標籤頁僅搜尋目前列表。搜尋條件會保留在網址中，方便收藏或分享。
- 文章頁包含白話重點、原文連結、發表與收錄日期、自動目錄，以及依相同主題或標籤挑選的延伸閱讀。
- 閱讀時間依正文的中文字數與英文詞數粗估，僅供參考。
- 窄螢幕使用單欄卡片與可展開的主題導覽、文章目錄。深淺色預設跟隨系統，也可手動切換並記住偏好。
- 搜尋和手動切換主題使用少量原生 JavaScript；停用 JavaScript 時仍可閱讀文章、瀏覽分類及使用目錄。

## 目錄結構

| 路徑 | 用途 |
| --- | --- |
| `build.py` | 網站生成腳本 |
| `requirements.txt` | Markdown 及 YAML 解析依賴 |
| `templates/paper.md` | 新論文範本，不參與預設的網站生成 |
| `templates/article.md` | 深度文章整理範本，不要求實驗數據或遊戲應用 |
| `web/page.html` | 所有頁面共用的 HTML 版型 |
| `web/style.css` | 網站樣式原始檔，生成時完整嵌入每頁 HTML；包含桌面、手機、深淺色及列印版面 |
| `web/site.js` | 搜尋、類型篩選、深淺色切換與導覽展開狀態 |
| `web/favicon.svg` | 網站分頁圖示 |
| `papers/rendering/` | 渲染、光照、材質、幾何表示 |
| `papers/simulation/` | 物理、碰撞、流體、破壞模擬 |
| `papers/animation/` | 動畫、IK、動作生成 |
| `papers/ai/` | 遊戲 AI、機器學習、LLM |
| `papers/systems/` | 記憶體、平行運算、資料結構、引擎架構 |
| `articles/technology/` | 科技觀察、技術解析、產業深度文章 |
| `articles/game-design/` | 遊戲設計與開發經驗 |
| `articles/culture/` | 文化、作品評論與創作討論 |
| `articles/society/` | 社會、政治、歷史等分析 |
| `articles/philosophy/` | 哲學、思想與概念討論 |
| `site/` | 生成結果，已被 Git 忽略 |

論文使用 `papers/<主題>/<發表年份>/<英文短名>/index.md`；
深度文章使用 `articles/<主題>/<發表年份>/<英文短名>/index.md`。
深度文章的原始發表日期不詳時，年份資料夾可用 `undated`，metadata 的 `published` 留空。
例如以下路徑僅示範命名，不代表已收錄真實論文：

```text
papers/rendering/2026/example-paper/index.md
papers/rendering/2026/example-paper/assets/overview.png
articles/culture/2026/example-essay/index.md
articles/culture/2026/example-essay/assets/illustration.png
```

同一篇內容只存一份，放在最相關的主題中；跨領域關係用 `tags` 表示。
**內容類型與主題分開**：一篇渲染技術解析可以是 `article`，一篇遊戲設計研究可以是 `paper`。
兩個來源中的同名主題會合併到同一分類頁，標籤也共用。
例如可同時有 `papers/game-design/` 與 `articles/game-design/`。
可自行新增主題資料夾，腳本會自動產生分類頁。`tags`、`types`、`_static` 為保留分類名稱。
`.gitkeep` 只用來讓 Git 保存尚未收錄文章的分類。

## 新增內容

1. 選擇 `papers/` 或 `articles/`，建立主題、年份和文章資料夾。
2. 複製相應的 `templates/paper.md` 或 `templates/article.md`，改名為 `index.md`。
3. 填寫 metadata 及正文，刪除尚未填寫的提示文字。
4. 圖片放在同層的 `assets/`，使用相對路徑引用。
5. 執行 `python build.py`。

PowerShell 範例：

```powershell
New-Item -ItemType Directory -Force papers/rendering/2026/example-paper
Copy-Item templates/paper.md papers/rendering/2026/example-paper/index.md

New-Item -ItemType Directory -Force articles/culture/2026/example-essay
Copy-Item templates/article.md articles/culture/2026/example-essay/index.md
```

### Metadata

| 欄位 | 格式與用途 |
| --- | --- |
| `type` | `paper`（技術論文）或 `article`（深度文章）。新內容請明確填寫；舊文省略時，來源根目錄名為 `articles` 則視為深度文章，其他來源視為論文 |
| `title` | 必填：原文標題或這份整理的標題 |
| `published` | 原始發表日期，`YYYY-MM-DD`。論文必填；深度文章不詳時可省略或填 `""`，網站顯示「日期未詳」 |
| `added` | 必填：本站收錄日期，`YYYY-MM-DD`；首頁主要排序依據 |
| `one_liner` | 新文章應填：一句最簡單的用途或重點；論文顯示「一句話用途」，深度文章顯示「一句話重點」。舊文省略時暫用 `summary`，不會自動白話改寫 |
| `summary` | 必填：一兩句白話補充方法或核心觀點，顯示於首頁最新收錄卡片及文章開頭，並用作網頁描述及搜尋依據 |
| `authors` | 作者字串清單；可省略或填 `[]` |
| `venue` | 出處：會議、期刊、媒體、網站或部落格名稱；可省略或留空 |
| `source_url` | 原文的完整 HTTP(S) URL，兩種類型皆可使用；可省略或留空。多來源整理可留空並在正文逐一列出 |
| `paper_url` | 保留舊論文格式；未填 `source_url` 時使用此連結，兩者都有時以 `source_url` 為準 |
| `code_url` | 程式碼的完整 HTTP(S) URL；可省略或留空 |
| `tags` | 標籤字串清單；可省略或填 `[]` |

### 寫作方式：先看懂用途或觀點，再深入理解

以下規則也適用於自動收錄、整理內容的工作。分類與格式擴充不會自動改變排程的搜尋範圍：

- 論文的 `one_liner` 回答「這項技術用來做甚麼」，例如：`不用逐粒模擬沙子，也能估算機器人踩進沙地時會受到多大阻力。`
- 深度文章的 `one_liner` 回答「作者提出甚麼值得理解的看法」，例如：`作者認為，遊戲中的等待也能讓玩家感受到旅途的距離。` 此句只是寫法示例，不代表已收錄文章。
- 一句話避免縮寫及未解釋的術語；可以說明一個主要重點，正文仍要保留原文多個觀點之間的關係。
- `summary` 補充簡單做法、觀點或適用範圍，不要壓縮整篇原文的所有內容。
- 論文先給具體例子，再說明原本的困難、資料如何處理、得到甚麼結果；深度文章先交代問題與背景，再整理作者的推理和依據。
- 專有名詞首次出現時就解釋，例如「力矩（讓物體轉動的作用）」；只展開英文縮寫並不算解釋。
- 優先使用容易理解的中文，英文名稱供查找即可。較深入的細節後置，不要用術語解釋另一個術語。
- 實驗數字保留條件和比較對象；區分論文已展示的成果與遊戲應用構想，不為了簡化而誇大能力。
- 深度文章分清原文事實、作者解讀、價值判斷及整理者的延伸；個人筆記不要冒充原作者的主張。
- 依原文特性增刪章節，評論不需要硬填「實驗結果」「如何實作」或「遊戲用途」，也不必為了平衡而刻意反駁。
- 用自己的話整理並保留原文連結；引用明確標示，多來源整理在相應段落說明來源。
- 首頁、內容類型頁、主題分類頁、標籤頁和文章開頭共用 `one_liner`，依類型顯示對應標籤。

標籤建議使用 `spatial-partitioning`、`real-time` 等小寫英文。
中文標籤也可以使用；腳本會為它產生穩定的雜湊網址，頁面仍顯示原標籤。
不要填入猜測的發表日期；需填寫完整日期的來源應先查證。

正文支援標題、表格、程式碼區塊、註腳及一般 Markdown。
文章頁會自動依二、三級標題產生閱讀目錄；舊文中的 `[TOC]` 會併入同一份目錄，避免重複顯示。
目前沒有加入數學公式排版、Mermaid 渲染或程式碼語法上色。

### 圖片與文章連結

```markdown
![方法概覽](assets/overview.png)

[另一篇論文](../another-paper/index.md)

[該論文的指定章節](../another-paper/index.md#method)
```

圖片路徑原樣保留，`assets/` 內的非 Markdown 檔案會複製至相同相對位置。
文章連結的 `.md` 會轉為 `.html`，並保留 query string 及章節錨點。
參照式連結及正文中 HTML 的 `href` 也適用；程式碼區塊內的文字不會被改寫。
連到不存在或未納入生成範圍的 Markdown 會報錯；章節錨點本身不做存在性檢查。

以相對路徑連接文章，圖片放入 `assets/`，才能直接搬移整個網站或部署到子路徑。
Markdown 允許原始 HTML，請只生成你信任的筆記；這不是 HTML 清理工具。

## 指定來源及輸出路徑

```bash
# 預設合併論文與深度文章
python build.py --output "./site"

# 自訂多個來源：每個目錄各使用一次 --source
python build.py --source "./papers" --source "./articles" --output "./site"

# 只生成論文，可使用另一個輸出目錄
python build.py --source "./papers" --output "./papers-site"
```

Windows 範例：

```powershell
python build.py --output "E:/Websites/tech-news"
```

省略 `--source` 時，會讀取 `build.py` 旁的 `papers/` 和 `articles/`；預設輸出仍是旁邊的 `site/`。
明確傳入的相對路徑以目前工作目錄為準，支援包含空白的路徑。
自訂來源也要保留 `<主題>/.../*.md` 結構。
`--source` 指定的是這一次建置的完整來源清單。若只選一個來源並輸出至舊網站目錄，
其他來源上次生成的頁面會依 manifest 清除；要保留兩種類型，請用預設來源或明確指定兩個來源。

既有 `rebuild.sh` 已調整為同時生成兩類內容，輸出位置仍是 `/var/wiki/html/tech_news`。

腳本遞迴讀取來源內所有 `.md`（副檔名大小寫皆可），每份都需要 metadata。
慣例使用每篇一個 `index.md`，其他名稱也可以，例如 `notes.md` 會變成 `notes.html`。
不要在來源根目錄放 Markdown，也不要在分類根目錄放 `index.md`，後者會與自動分類頁衝突。

| 來源 | 生成結果 |
| --- | --- |
| `papers/rendering/2026/example-paper/index.md` | `site/rendering/2026/example-paper/index.html` |
| `papers/rendering/2026/example-paper/assets/overview.png` | `site/rendering/2026/example-paper/assets/overview.png` |
| `articles/culture/2026/example-essay/index.md` | `site/culture/2026/example-essay/index.html` |
| 全部文章 metadata | `site/index.html` |
| 全部文章搜尋 | `site/search.html` |
| 所有 `paper` 類型 | `site/types/paper/index.html` |
| 所有 `article` 類型 | `site/types/article/index.html` |
| `rendering` 分類 | `site/rendering/index.html` |
| `real-time` 標籤 | `site/tags/real-time/index.html` |

論文的既有檔案與網址維持原樣。兩個來源都映射到相同網站根目錄，
因此 `<主題>/<年份>/<英文短名>` 必須不重複；同名文章或圖片會報錯，不會互相覆寫。
兩個來源之間也可用相對 `.md` 連結，腳本會改寫為正確的 HTML 路徑。

輸出使用相對網址及明確的 `index.html`，可直接在瀏覽器開啟，也能部署到 `/tech-news/` 等子路徑。
部署時複製整個輸出目錄；此 repo 尚未設定自動部署。

## 重建與檔案保護

- 來源和輸出不能相同，也不能互相包含；多個來源之間也不能互相包含。
- 解析、渲染、Markdown 連結及路徑衝突檢查完成後才開始寫入。
- 輸出根目錄的 `.tech-news-manifest.json` 記錄本腳本管理的檔案。
- 再次生成會覆寫受管理的檔案，並刪除已不再使用的受管理檔案，例如被移除文章的 HTML。
- 不會清空整個輸出目錄；遇到同名的非受管理檔案會停止，其他檔案保留。
- 不要手動修改生成的 HTML，請修改 Markdown 或 `web/` 中的版型後重建。
- CSS 會直接放進每頁 HTML 的 `<style>` 中，不再另外載入樣式檔，避免新版頁面配上舊版 CSS。`web/style.css` 仍是樣式的編輯來源，修改後重新生成即可。
- JavaScript 及分頁圖示的網址會附上依檔案內容計算的版本參數。若重建後瀏覽器仍顯示舊 HTML，可先按 `Ctrl+F5` 強制重新載入。
- 保留 manifest 才能持續辨認生成檔案；遺失時請改用新的空輸出目錄。
- 每次僅執行一個建置程序。這是本機檔案生成工具，多個檔案的寫入不具整批原子性。

無效的日期、metadata 或找不到的文章連結會顯示具體檔案並以非零狀態結束。
