---
type: paper
title: "Windfoil: Closed-Form Coverage for Real-Time and Differentiable Vector Graphics"
published: "2026-10-01"
added: "2026-10-05"
authors:
  - "Matt DesLauriers"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2610.02468"
code_url: "https://github.com/texel-org/windfoil"
tags:
  - vector-graphics
  - rasterization
  - anti-aliasing
  - webgpu
  - differentiable-rendering
  - real-time
one_liner: "直接計算貝茲曲線在每個像素中真正覆蓋了多少面積，讓向量圖形不用先切成大量小線段也能得到高品質抗鋸齒。"
summary: "Windfoil 把二次貝茲輪廓的 box-filtered winding number 寫成適合 GPU 執行的封閉形式，同一套 coverage 計算既可用於即時向量光柵化，也可微分後用於向量圖形最佳化；作者提供 WebGPU 實作與公開 benchmark。"
---

# Windfoil: Closed-Form Coverage for Real-Time and Differentiable Vector Graphics

## 先用一個例子理解

遊戲 UI 的貝茲曲線圖示在縮放時，每個邊界像素只有一部分真正落在圖形內。Windfoil 直接估計這個 coverage，而不是只判斷像素中心在內或在外，也不需要先把曲線切成大量小線段。

## 原本的做法有甚麼困難

向量圖形需要同時處理放大後的平滑、縮小時的 aliasing、大量重疊 shape 的效能，以及避免隨解析度反覆增加曲線細分。作者以 Skia 與 GPU 向量光柵化方法 Slug 作為重要比較。

## 它是怎樣做到的

Windfoil 對二次貝茲輪廓計算 box-filtered winding number 的封閉形式。winding number 可理解成封閉輪廓繞某位置多少圈；Windfoil 處理的是整個 pixel footprint 經 box filter 後的貢獻，而非只取單一 sample point。

資料流可簡化為：

```text
Quadratic Bézier contours
          ↓
row-band acceleration
          ↓
找出影響目前 pixel / cell 的 curve segments
          ↓
closed-form filtered winding
          ↓
coverage
          ↓
color / alpha
```

公開實作用 WebGPU，並使用 row-band acceleration 避免每個 pixel 檢查全部曲線。

## 與現有方法的差別

最有意思的是同一個 coverage function 同時服務 real-time rasterization 與 differentiable rendering。coverage 是解析函數，因此亦可對 shape parameters 求梯度，反過來調整貝茲控制點，使輸出接近目標圖像。

## 實驗結果與限制

作者報告 Windfoil 對 reference box-filtered coverage 的吻合程度優於 Skia 與 Slug，而效能與 Slug 大致相當。公開 repository 的 benchmark 顯示 workload 仍會改變勝負：shape 很小時 Slug 往往較快，shape 佔畫面較大時 Windfoil 傾向略快。

在 differentiable rendering 部分，論文報告相對 DiffVG 與 Bézier Splatting，可用較低的單步成本取得相同或更好的 reconstruction quality，並擴展至數萬個 shape 的 interactive rate。

這不能解讀成所有遊戲 UI workload 都會更快。目前主要公開實作是 WebGPU research/reference implementation，核心對象是 quadratic Bézier contours；production UI 還要處理文字 shaping、stroke、clip、blend、cache 與 batching。論文目前是 arXiv 預印本，尚不能視為同行評審成果。

## 可以怎樣用在遊戲裡

論文已直接驗證 real-time 2D vector rendering。最直接用途包括 resolution-independent HUD、圖示、地圖、node editor、dialogue graph 與需要大量 zoom 的 world editor。

更進一步的推導是讓 authoring 與 runtime 共用同一個向量 representation：

```text
Editable Vector Asset
        ↓
same analytic renderer
   ↙             ↘
runtime draw     optimisation / fitting
```

例如由目標圖片反求仍可編輯的 Bézier path，而不是只能輸出 raster texture。這個遊戲工具用途屬合理延伸，並非論文已驗證的 production workflow。

## 想實作時再看

最小 prototype 可載入一組 quadratic Bézier contours，以 compute shader 求 coverage，並與 supersampled reference、curve flattening、MSAA 比較誤差與時間。應分別測大量小 icon、一般 UI、放大的 editor path，因為公開 benchmark 已顯示螢幕尺度會影響與 Slug 的效能關係。

若再研究 differentiable 部分，可把控制點設成參數，以 image loss 更新 Bézier control points，測試同一 coverage kernel 同時服務 runtime 與 authoring 是否值得成為 engine subsystem。

## 個人筆記

這篇值得留下的不是「另一種文字抗鋸齒」，而是把高品質向量 coverage 與 differentiable authoring 放到同一個數學 primitive 上。對自製 editor 而言，vector renderer 可能不只是 UI renderer，而是 graph、map annotation、曲線工具與 procedural 2D asset 共用的基礎幾何服務。

證據層級：已有可驗證即時圖形實作；遊戲 production adoption 未驗證。
