---
type: article
title: "My side quest measuring input latency with VK_EXT_present_timing"
published: "2026-07-02"
added: "2026-09-30"
authors: ["Hans-Kristian Arntzen"]
venue: "Maister's Graphics Adventures"
source_url: "https://themaister.net/blog/2026/07/02/my-side-quest-measuring-input-latency-with-vk_ext_present_timing/"
tags: ["input-latency", "vulkan", "anti-lag", "game-streaming", "vrr", "profiling"]
one_liner: "不用外接光電硬體，只靠 Vulkan 的 present timing 擴充加上「合成輸入＋畫面差異偵測」，就能把輸入延遲拆成 CPU、GPU、FIFO 排隊等階段來診斷。"
summary: "作者為驗證 Mesa 的 anti-lag 與自家串流方案，寫了一個 Vulkan layer：用 /dev/uinput 注入輸入、讀回小塊畫面算 MSE 判定反應，再配合 VK_EXT_present_timing 的時間戳把延遲分段。文中以實測展示 CPU-bound、GPU-bound、FIFO 緩衝與串流四種情境，並附上 anti-lag 實際省下約 25 ms 的數據。"
---

# My side quest measuring input latency with VK_EXT_present_timing

## 這篇在談甚麼

「遊戲手感有點黏」通常憑感覺判斷，要客觀量測輸入延遲一般需要高速相機或光電感測器等外部硬體。作者（Hans-Kristian Arntzen）想在 Linux 驅動堆疊裡驗證兩件事：AMD_anti_lag 在 Mesa 是否真的有效，以及自製串流方案 PyroFling 的毫秒到底花在哪。隨著 `VK_EXT_present_timing` 逐步進入 Linux 驅動堆疊，他做出一個純軟體的量測 layer。

## 作者的核心觀點

- 有了 present timing API，就不需要奇怪的硬體方案也能做可比較的延遲分析。
- 把「輸入 → 上屏」拆成互相獨立的區段，才能判斷該怪 CPU、GPU 過度排隊、還是 FIFO 緩衝，並據此判斷 anti-lag 是否有用。

## 作者如何得出這個看法（機制拆解）

**量測方法**：layer 讀回 swapchain 中一小塊區域，與前一幀比較算 Mean Square Error；當 MSE 相對過去 N 幀突然飆高，就推定是輸入造成的畫面變化。輸入則由 `/dev/uinput` 在略隨機的時間點合成產生。再用 present timing 取得每次 present 實際流經系統的時間，推得「輸入注入時刻 → 該差異幀上屏」的延遲。

**延遲被分成幾段**（各段的診斷意義是文章最可轉移的部分）：

- 輸入 → QueuePresent：偏大代表 CPU-bound 或應用程式自己緩衝輸入。
- QueuePresent → GPU idle：偏大代表 GPU-bound、提交過量，anti-lag 有望改善。
- GPU idle → PresentComplete：在 VRR 螢幕上應接近 0；偏大代表 FIFO 排隊。
- PresentComplete 的定義依平台不同（Dequeued／FirstPixelOut／FirstPixelVisible），Xwayland 上是合成器承諾顯示的時刻，並非實際翻頁；FirstPixelVisible（光子實際發出）目前沒有已知實作支援——這是方法的精度上限。

## 重要例子與依據

- **CPU-bound 遊戲**（9070 XT 配舊 Zen2 CPU）：平均幀時間 9.21 ms，輸入到 PresentComplete 平均 22.1 ms；輸入到 QueuePresent 14.8 ms（約 1.5 幀＝0.5 幀輸入輪詢抖動加 1 幀 CPU 命令），GPU 段僅 6.85 ms，VRR 額外延遲 0.45 ms。數字與預期吻合，作為方法的健全性檢查。
- **GPU 過載的 Cyberpunk 2077（原生解析度＋重 RT）**：無 anti-lag 時感知延遲平均 75.9 ms，QueuePresent → GPU idle 33.2 ms（約 2 幀 GPU 佇列）；開啟 anti-lag 後降到 50.0 ms（省約 25 ms），該段降為約 16.9 ms（約 1 幀），其餘延遲來自遊戲自身約 2 幀的輸入緩衝。
- **固定更新率 FIFO**：作者自己的 Granite 測試場景（已知 ground truth），預設最多 1 個未完成 present 時 GPU idle → PresentComplete 約 32.3 ms；改用等待前一幀完成（無 CPU/GPU 重疊）約 15.5 ms（約 1 幀）。MAILBOX 在 KDE Wayland 視窗模式下約 6.45 ms，約落在更新週期中間，符合預期。
- **串流**：基準為 60 Hz 限幀的 Sponza，感知延遲 11.8 ms，大部分是 0.5 個更新週期的輸入輪詢。加入 IPC、GPU 上 PyroWave 編碼、localhost UDP、解碼上屏後為 12.8 ms，約多 1 ms，且多半是網路程式碼（單純 sendmsg/recvmsg）。改用 FFmpeg NVENC 10-bit 4:4:4 @50 Mbit 約 20.2 ms（編碼超過 6 ms 加解碼數 ms），RADV 的 H.265（4:2:0）約 14.9 ms。
- **附帶實驗**：為固定更新率（FRR）做「低延遲 pacer」，用 present timing 推估合成器的 flip 寬限期，寬限不足就放大、有把握再縮小；作者說在負載穩定的情境（模擬器、串流）較可行，變動負載不可靠，且在 KHR_display 上比 Wayland/X11 穩定。

## 閱讀時需要知道的前提

- 量測依賴「畫面差異＝輸入反應」的假設；TAA 抖動會在穩定場景也造成差異（作者提到這在此 layer 中可接受），畫面沒有明顯反應的輸入（例如延遲觸發的動作）不適用。
- 結果來自單一機器與少數遊戲；且 `VK_EXT_present_timing` 在 Linux 生態仍在鋪設中，各合成器語意不同。
- 網路部分僅是 localhost，真實網路延遲未涵蓋（作者自己指出實際網路會受頻寬影響）。

## 我的筆記與延伸

- 「分段」的思路很通用：先用簡單指標把延遲歸屬到 CPU／GPU／顯示佇列，再決定要不要優化，避免盲目套用 Reflex／Anti-Lag 之類的方案。
- 和 [PyroWave 原始設計文](../../2025/pyrowave-low-latency-streaming-codec/index.md) 合讀：後者論證為何 intra-only 小波編碼能省時間，本文提供整條鏈路上的實測成本（約 1 ms 對比硬體編碼的 6 ms 以上）。
- 疑問：此方法能否推廣到 Windows／DX12 的 present 時間戳，以及在 Proton 下能否得到可比數據，原文未討論。

## 來源

- [My side quest measuring input latency with VK_EXT_present_timing](https://themaister.net/blog/2026/07/02/my-side-quest-measuring-input-latency-with-vk_ext_present_timing/)（原文）
