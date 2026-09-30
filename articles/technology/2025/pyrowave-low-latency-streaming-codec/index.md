---
type: article
title: "I designed my own ridiculously fast game streaming video codec – PyroWave"
published: "2025-06-16"
added: "2026-09-30"
authors: ["Hans-Kristian Arntzen"]
venue: "Maister's Graphics Adventures"
source_url: "https://themaister.net/blog/2025/06/16/i-designed-my-own-ridiculously-fast-game-streaming-video-codec-pyrowave/"
tags: ["video-codec", "game-streaming", "latency", "vulkan", "gpu-compute", "wavelet"]
one_liner: "區域網路遊戲串流不缺頻寬、只缺延遲，所以乾脆丟掉動態預測和熵編碼，用小波轉換加原始位元平面，換來 1080p 約 0.13 ms 的 GPU 編碼時間。"
summary: "作者針對「有線區網／良好 WiFi 串流」重新排序取捨：用頻寬換延遲，設計出只做小波轉換、量化與固定時間位元率控制的 intra-only 編碼器 PyroWave。2026 年 9 月 Steam Beta 加入此編碼器，使這篇原始設計文章重新值得閱讀。"
---

# I designed my own ridiculously fast game streaming video codec – PyroWave

## 這篇在談甚麼

把遊戲畫面從 A 機串流到 B 機，整條延遲鏈包括：輸入送出、GPU 渲染、編碼、網路傳送、解碼、顯示。主流做法是用 H.264／HEVC／AV1 的 GPU 硬體編碼器，但這些編碼器為壓縮率而生（B-frame、彈性位元率控制都靠「多等幾格」換取），做即時串流時只能把它們「勒緊」：固定位元率、無 B-frame、無限長 P-frame 或 intra-refresh，效果打折。

作者（Hans-Kristian Arntzen，vkd3d-proton 開發者之一）問了一個反向問題：如果目標只有區網，頻寬近乎免費（Gigabit 乙太網已很普及，WiFi 也能跑數百 Mbit/s），能不能設計一個「以最低延遲為唯一目標」的編碼器？答案就是 PyroWave。

背景補充：2026-09-29 Aftermath 報導 Steam Beta 加入了 PyroWave 串流選項（[Aftermath](https://aftermath.site/pyrowave-steam-remote-play/)，二手報導，僅作時間點參考）。本條目以作者原文為準。

## 作者的核心觀點

- 頻寬與延遲的取捨在區網下反轉：可以接受 100+ Mbit/s（常見串流約 10–20 Mbit/s），換取極低且穩定的延遲。
- 為了讓編碼能完整在 GPU compute shader 上平行執行，作者刻意丟掉兩個傳統壓縮支柱：動態預測（改成 intra-only）與熵編碼（改成輸出原始位元平面）。
- 丟掉熵編碼後，編碼後大小可在事前精確計算，因此位元率控制可以在固定時間內做到「不超過上限」，這是一般編碼器很難做到的。

## 作者如何得出這個看法（機制拆解）

**資料流**：每幀畫面 → 5 層離散小波轉換（DWT，濾波器使用 5/3 類型）→ 依頻帶量化 → 以 32×32 係數為獨立單位封包 → 傳送。

1. **Intra-only**：不做動態預測，代價是位元率暴增；好處是任一幀掉包不會拖累後續幀（錯誤恢復佳），畫質不再依賴動態估計的好壞。
2. **DWT 而非 DCT**：作者形容為「加了調味的 mip-map」——降採樣後計算與高解析度的誤差，屬於臨界取樣濾波器組。量化時考慮各頻帶的重建增益，高頻可量化得更狠（利用視覺心理特性），多數高頻最後量化為 0，位元集中在畫面關鍵區域。經典失敗模式是模糊或 ringing，而非 JPEG 式的方塊；作者半開玩笑說在 TAA 讓畫面本來就偏糊的年代未必明顯。
3. **針對 GPU 階層設計位元封裝**：32×32 為獨立可解碼單位（掉包時將係數視為 0，只造成局部微糊）；再拆成 8×8 與 4×2。一個 thread 負責 4×2 = 8 個係數，一個 subgroup 負責 8×8，一個 workgroup（128 threads）負責 32×32。刻意保持「以位元組為單位」以使用 Vulkan 8-bit SSBO storage，避免在 GPU 記憶體做位元層級操作。每個 4×2 區塊標註所需位元數，使用 subgroup 操作與輕量 prefix sum 編解碼；正負號位元集中放在區塊尾。
4. **快速且精確的率控**：對每個 32×32 區塊，試算「丟掉 1、2、3…個位元平面」時的心理視覺加權 MSE 與位元成本並存入緩衝區；再依「每節省一位元增加的失真」由小到大排序，用 prefix sum 選出足夠的位元丟棄量；最後一趟依決定打包輸出。輸出保證在上限內，通常只差 10–20 bytes。

**已知限制與與常見做法的差異**

- 頻寬需求為一般編碼器的約 5–10 倍；作者自己說不適合經網際網路串流（除非 P2P 光纖）。
- DWT 過程用 FP16 加速（packed FP16 在 RDNA4 上也有明顯收益），但限制了可達到的 PSNR 上限。
- 對比測試中，作者把 NVENC 等編碼器也限制成硬性 CBR、最快模式、GOP=1 才有可比性，並承認「沒有人會這樣串流」，比較只是為了拉平條件；AV1／HEVC 在此設定下常用不滿位元預算。作者也對 VMAF 給 PyroWave 偏高分感到存疑（稱其為此類用途下的「笑話指標」），使用了 XPSNR／PSNR 等其他指標。這意味著畫質數字需保守解讀。
- 測試是作者自己錄的 5 秒遊戲片段、單一硬體組合，沒有大規模主觀評測。

## 重要例子與依據

- 效能：1080p 4:2:0 編碼約 0.13 ms（RX 9070 XT、RADV），解碼低於 100 µs；較單純的遊戲畫面編碼約 80 µs；4K 4:2:0 約 0.25 ms。作者觀察到：把 4K RGBA8 影像經 PCIe 搬到 CPU，比在 GPU 上壓縮再搬壓縮資料還慢。
- 測試素材包含《Expedition 33》（大量綠色植被與 TAA 雜訊，屬於「殘酷」的測試畫面）與經典測試序列 ParkJoy。
- 續作文章 [My side quest measuring input latency with VK_EXT_present_timing](../../2026/present-timing-input-latency-measurement/index.md) 用實測量化了 PyroWave 加入整條串流鏈後增加的延遲。

## 閱讀時需要知道的前提

- 屬 Vulkan 與 GPU compute 的實作導向文章，預設讀者熟悉 subgroup、SSBO、率失真最佳化等概念；訊號處理部分作者多處直接引用自己的碩士論文圖表而不重述。
- 原文發表於 2025-06；文中效能數字對應當時硬體與驅動。

## 我的筆記與延伸

- 可轉移的設計思維：先問「這個場景中哪項資源真的便宜」，再回頭拆除為別的場景設計的複雜度。這裡是拋棄熵編碼以換取「大小可預知 → 率控可平行」。
- 「輸出大小可事前計算」對任何要在 GPU 上做固定預算壓縮的系統（例如紋理串流、遠端渲染、回放記錄）都是有啟發的性質。
- 疑問：TAA／雜訊多的畫面在 intra-only 下位元成本大，實際遊戲類型差異多大，原文只用少數片段展示。

## 來源

- [I designed my own ridiculously fast game streaming video codec – PyroWave](https://themaister.net/blog/2025/06/16/i-designed-my-own-ridiculously-fast-game-streaming-video-codec-pyrowave/)（原文）
- [Steam's Pyrowave Update To Remote Play Chases Latency At All Costs](https://aftermath.site/pyrowave-steam-remote-play/)（Aftermath，2026-09-29，時間點參考）
