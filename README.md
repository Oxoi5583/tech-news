# Tech News

以 Markdown 收錄新技術論文，記錄核心做法、實驗限制，以及對遊戲開發的實際用途。
執行根目錄的 `build.py`，即可產生靜態 HTML 網站。

## 快速開始

需要 Python 3.10 或以上版本。

```bash
python -m pip install -r requirements.txt
python build.py
```

開啟 `site/index.html` 即可閱讀。沒有文章時也能正常生成首頁和分類頁。
網站不需要後端、資料庫、Node.js 或外部 CDN。

也可以透過本機 HTTP 伺服器預覽：

```bash
python -m http.server 8000 --directory site
```

瀏覽 <http://localhost:8000>。按 `Ctrl+C` 停止預覽。

## 目錄結構

| 路徑 | 用途 |
| --- | --- |
| `build.py` | 網站生成腳本 |
| `requirements.txt` | Markdown 及 YAML 解析依賴 |
| `templates/paper.md` | 新論文範本，不參與預設的網站生成 |
| `web/page.html` | 所有頁面共用的 HTML 版型 |
| `web/style.css` | 網站樣式，支援窄螢幕及系統深淺色偏好 |
| `papers/rendering/` | 渲染、光照、材質、幾何表示 |
| `papers/simulation/` | 物理、碰撞、流體、破壞模擬 |
| `papers/animation/` | 動畫、IK、動作生成 |
| `papers/ai/` | 遊戲 AI、機器學習、LLM |
| `papers/systems/` | 記憶體、平行運算、資料結構、引擎架構 |
| `site/` | 生成結果，已被 Git 忽略 |

每篇論文建議使用 `papers/<主題>/<發表年份>/<英文短名>/index.md`。
例如以下路徑僅示範命名，不代表已收錄真實論文：

```text
papers/rendering/2026/example-paper/index.md
papers/rendering/2026/example-paper/assets/overview.png
```

同一篇論文只存一份，放在最相關的主題中；跨領域關係用 `tags` 表示。
可自行新增主題資料夾，腳本會自動產生分類頁。`tags`、`_static` 為保留分類名稱。
`.gitkeep` 只用來讓 Git 保存尚未收錄文章的分類。

## 新增論文

1. 建立主題、年份和論文資料夾。
2. 複製 `templates/paper.md` 至該資料夾，改名為 `index.md`。
3. 填寫 metadata 及正文，刪除尚未填寫的提示文字。
4. 圖片放在同層的 `assets/`，使用相對路徑引用。
5. 執行 `python build.py`。

PowerShell 範例：

```powershell
New-Item -ItemType Directory -Force papers/rendering/2026/example-paper
Copy-Item templates/paper.md papers/rendering/2026/example-paper/index.md
```

### Metadata

| 欄位 | 格式與用途 |
| --- | --- |
| `title` | 必填：完整論文標題 |
| `published` | 必填：發表日期，`YYYY-MM-DD` |
| `added` | 必填：本站收錄日期，`YYYY-MM-DD`；首頁主要排序依據 |
| `one_liner` | 新文章應填：一句最簡單的用途說明；顯示於列表卡片及文章開頭的「一句話用途」。舊文省略時暫用 `summary`，但不會自動將術語改成白話 |
| `summary` | 必填：一兩句白話補充做法及適用範圍，顯示於用途下方並用作網頁描述 |
| `authors` | 作者字串清單；可省略或填 `[]` |
| `venue` | 會議、期刊或預印本平台；可省略或留空 |
| `paper_url` | 原始論文的完整 HTTP(S) URL；可省略或留空 |
| `code_url` | 程式碼的完整 HTTP(S) URL；可省略或留空 |
| `tags` | 標籤字串清單；可省略或填 `[]` |

### 寫作方式：先看得懂用途，再理解方法

以下規則也適用於自動收錄、整理論文的工作：

- `one_liner` 只回答「這項技術用來做甚麼」，一句話、一個主要用途，避免縮寫及未解釋的術語。
- 例如：`不用逐粒模擬沙子，也能估算機器人踩進沙地時會受到多大阻力。`
- `summary` 補充簡單做法和範圍，不要壓縮整篇論文的所有技術重點。
- 正文先給具體例子，再依序說明原本的困難、資料如何處理、得到甚麼結果。
- 專有名詞首次出現時就解釋，例如「力矩（讓物體轉動的作用）」；只展開英文縮寫並不算解釋。
- 優先使用容易理解的中文，英文名稱供查找即可。技術細節放在後面的「想實作時再看」，不要用術語解釋另一個術語。
- 實驗數字保留條件和比較對象；區分論文已展示的成果與遊戲應用構想，不為了簡化而誇大能力。
- 首頁、分類頁、標籤頁和文章開頭都會顯示「一句話用途」，由同一個欄位提供內容。

標籤建議使用 `spatial-partitioning`、`real-time` 等小寫英文。
中文標籤也可以使用；腳本會為它產生穩定的雜湊網址，頁面仍顯示原標籤。
不要填入猜測的發表日期；需填寫完整日期的來源應先查證。

正文支援標題、表格、程式碼區塊、註腳及一般 Markdown。
在正文加入 `[TOC]` 可產生目錄。
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
python build.py --source "./papers" --output "./site"
```

Windows 範例：

```powershell
python build.py --source "./papers" --output "E:/Websites/tech-news"
```

省略參數時，路徑以 `build.py` 所在目錄為準。
明確傳入的相對路徑以目前工作目錄為準，支援包含空白的路徑。
自訂來源也要保留 `<主題>/.../*.md` 結構。

腳本遞迴讀取來源內所有 `.md`（副檔名大小寫皆可），每份都需要 metadata。
慣例使用每篇一個 `index.md`，其他名稱也可以，例如 `notes.md` 會變成 `notes.html`。
不要在來源根目錄放 Markdown，也不要在分類根目錄放 `index.md`，後者會與自動分類頁衝突。

| 來源 | 生成結果 |
| --- | --- |
| `papers/rendering/2026/example-paper/index.md` | `site/rendering/2026/example-paper/index.html` |
| `papers/rendering/2026/example-paper/assets/overview.png` | `site/rendering/2026/example-paper/assets/overview.png` |
| 全部文章 metadata | `site/index.html` |
| `rendering` 分類 | `site/rendering/index.html` |
| `real-time` 標籤 | `site/tags/real-time/index.html` |

輸出使用相對網址及明確的 `index.html`，可直接在瀏覽器開啟，也能部署到 `/tech-news/` 等子路徑。
部署時複製整個輸出目錄；此 repo 尚未設定自動部署。

## 重建與檔案保護

- 來源和輸出不能相同，也不能互相包含。
- 解析、渲染、Markdown 連結及路徑衝突檢查完成後才開始寫入。
- 輸出根目錄的 `.tech-news-manifest.json` 記錄本腳本管理的檔案。
- 再次生成會覆寫受管理的檔案，並刪除已不再使用的受管理檔案，例如被移除文章的 HTML。
- 不會清空整個輸出目錄；遇到同名的非受管理檔案會停止，其他檔案保留。
- 不要手動修改生成的 HTML，請修改 Markdown 或 `web/` 中的版型後重建。
- 保留 manifest 才能持續辨認生成檔案；遺失時請改用新的空輸出目錄。
- 每次僅執行一個建置程序。這是本機檔案生成工具，多個檔案的寫入不具整批原子性。

無效的日期、metadata 或找不到的文章連結會顯示具體檔案並以非零狀態結束。
