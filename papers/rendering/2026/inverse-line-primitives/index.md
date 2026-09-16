---
title: "Inverse Rendering for Modeling with Line Primitives"
published: "2026-09-01"
added: "2026-09-16"
authors:
  - "Kenji Tojo"
  - "Ariel Shamir"
  - "Nobuyuki Umetani"
  - "Bernd Bickel"
venue: "arXiv / ACM Transactions on Graphics (SIGGRAPH Asia 2026)"
paper_url: "https://arxiv.org/abs/2609.00625"
code_url: "https://github.com/kenji-tojo/inverse-line-primitives"
tags:
  - explicit-geometry
  - line-primitives
  - differentiable-rendering
  - fibers
  - procedural-geometry
  - physical-simulation
  - real-time
summary: "從多視角影像把毛髮、纖維與絨毛等模糊幾何重建成大量明確的 line segments，而不是 3D Gaussian 或其他半透明體積 primitive；因此重建結果可直接進入標準 rasterization、shading 與物理模擬流程。"
---

# Inverse Rendering for Modeling with Line Primitives

## 解決甚麼問題

毛髮、絨毛、纖維、細草等結構很難用普通 surface mesh 重建。近年的 radiance field / 3D Gaussian 類方法能從照片得到很好的視覺效果，但結果通常是半透明的 volumetric primitives：它們很適合重新渲染，卻不是遊戲引擎熟悉的明確幾何，因此較難直接拿去做 depth-tested rasterization、一般材質模型、碰撞或物理模擬。

這篇工作的目標不是再做一種更好的 volumetric appearance representation，而是直接把這些 fuzzy objects 重建成大量真正的 line segments。換言之，輸出不是「看起來像毛」，而是可以被視為一束束明確纖維的幾何資料。

## 核心做法

最直接的想法是：用大量一像素寬的線段去擬合多視角照片。但 inverse rendering 需要從影像誤差反向得到「哪條線應該移去哪裡、顏色怎樣改、甚至連接關係怎樣改」的 gradient；普通 rasterizer 的 visibility 與離散 pixel coverage 並不適合直接微分。

作者因此建立 stochastic differentiable rasterizer。Forward pass 仍然很接近傳統圖形管線：

1. 把 line segments 以 Bresenham 類 rasterization 畫到 2x subpixel grid。
2. 使用 screen-space filtering / MSAA，讓大量極細的 opaque lines 在像素尺度形成近似半透明 fuzzy appearance。
3. visibility 使用 stochastic opacity masking；不是把每條線真正改成 volumetric translucent blob。
4. backward pass 使用 score-function gradient estimator，估計 line vertex position、attribute 與離散 connectivity 對最終影像 loss 的影響。
5. 對 MSAA 下多個 fragment 的聯合機率，作者用 independence approximation 將問題 factorize，並在 filter weight 最大的 pixel 評估 opacity gradient，使整個最佳化仍可計算。

因此資料流大致是：

```text
Multi-view photos
      ↓
coarse initialization
      ↓
explicit line segments
      ↓
stochastic differentiable rasterization
      ↓
image-space reconstruction loss
      ↓
gradients for position / attributes / connectivity
      ↓
optimized explicit fiber geometry
```

最終 runtime 不需要 neural renderer。公開 viewer 可以直接把最佳化後的 lines rasterize；大幅放大時也可改用 camera-facing quad sprites，為每條 line 給 world-space radius。

## 與現有方法的差別

### Surface mesh

普通 triangle surface 很難有效表示大量比 pixel 更細、彼此分離的纖維；增加 tessellation 又會產生大量不必要的 surface connectivity。

### 3D Gaussian / radiance field

Gaussian 類方法用半透明 volumetric primitive 很容易重現 fuzzy silhouette，但輸出主要是 appearance representation。要把「這裡有毛」轉回可碰撞、可彎曲、可受風力或可被剪斷的 fiber geometry，仍需要另一層 reconstruction。

這篇直接選擇 line segment 作為 representation：

```text
照片
 ↓
不是：照片 → volumetric appearance → 再猜 geometry
而是：照片 → explicit line geometry
```

因此它最大的 engine 意義不是 image quality，而是 reconstruction output 與 runtime representation 可以是同一種東西。

## 實驗結果與限制

作者在 synthetic 與 real-world fuzzy datasets 上測試，包含毛髮、毛皮、植物纖維與 textile-like structures。論文報告 line representation 在 fuzzy boundaries 上優於 surface-based reconstruction，並能達到與 volumetric representation 相近的視覺品質，同時保留 explicit geometry。

官方 implementation 已完整公開，包含訓練 scripts、Fuzzy Dataset、Shelly Dataset 實驗、released checkpoints、interactive viewer、Web viewer 與 rendering benchmark script。作者指出 differentiable renderer 因 atomic reductions 與 PyTorch seeding 並非 bit-deterministic，但重跑時各 scene 的數值波動只出現在最後顯示位，平均分數四捨五入後可重現 paper 數字。

限制包括：

- reconstruction 本身仍是離線 optimization，不是遊戲 runtime 每幀執行的演算法；
- line-only representation 適合纖維狀物體，不代表所有 fuzzy volume 都應改成 lines；
- 一像素 Bresenham lines 在近距離大幅放大時會暴露 primitive structure，因此 runtime viewer 另提供 quad-sprite 模式；
- optimization pipeline 目前依賴 PyTorch、Vulkan，訓練通常還需要 NVIDIA CUDA；
- explicit geometry 雖然方便物理模擬，但 paper 本身沒有展示完整的動態 hair / cloth simulation pipeline，因此「重建後直接拿去做 gameplay physics」仍是可轉移的工程方向，而非已驗證 production feature。

不同 representation 的 quality、memory 與 runtime benchmark 受 scene、primitive count、anti-aliasing mode 與硬體影響，不應只抽一個 FPS 數字與 3D Gaussian 系統直接比較。

## 對遊戲開發的用途

這篇最值得注意的是一種 representation 思路：**對具有明確細長拓撲的 fuzzy object，不一定要把它視作半透明 volume；可以直接把最小 runtime primitive 定義成 fiber / segment。**

這可以形成一套 Fiber Geometry System：

```text
Fiber / grass / fur capture
        ↓
explicit segments
        ├─ rasterization
        ├─ wind / bending
        ├─ collision
        ├─ cutting / burning
        └─ gameplay queries
```

例如遊戲中的長草，如果視覺、碰撞、風力、燃燒傳播與斬草全部共享同一批 line / polyline primitives，就不必維護「render grass」與「gameplay grass」兩個完全不同的世界表示。毛皮也可以把 visual fiber 與 grooming / deformation 的控制結構連起來。

更有意思的是 destruction：line primitive 天然有離散 connectivity，切斷一條 fiber、改變兩段的連接關係，比在 volumetric Gaussian field 中定義「這根毛被剪斷」直接得多。這正是 explicit representation 可能塑造 interaction 的地方。

它也適合作為 procedural / scanned asset pipeline：先用多視角照片取得複雜纖維幾何，再把結果轉成 engine 自己的 compact polyline、strand cluster、meshlet-like fiber cluster 或 physics guide representation，而不是手工重建。

## 最小 Prototype

不需要先重做 inverse renderer。可以直接下載作者 released checkpoints，把 line models 轉成自己的 C++ runtime format：

```cpp
struct FiberVertex {
    Vec3 position;
    Vec3 color;
};

struct FiberSegment {
    uint32_t a;
    uint32_t b;
};
```

第一版只做三件事：

1. GPU instanced / indirect line 或 camera-facing ribbon rendering。
2. 把相鄰 segments cluster 成 polyline，測試 spatial partition / culling。
3. 選少量 guide fibers 加簡單 Verlet / PBD bending，再讓附近 visual fibers 跟隨。

接著再測試「切斷 connectivity」：ray / blade 命中 segment 後斷開 graph，看看 rendering、physics 與 gameplay state 是否能共用同一 representation。這比一開始重現完整 differentiable optimization 更能快速驗證它對遊戲引擎的價值。

若要理解論文本身，優先讀 Technical Overview 中 stochastic opacity masking 如何擴展到 MSAA，以及 discrete connectivity optimization；若要實作，先看官方 `inverse-line-primitives` 的 training scripts，再看獨立公開的 `fuzzydr` Vulkan differentiable rasterizer。

## 個人筆記

技術成熟度：**可實作研究原型**。官方 MIT source、datasets、checkpoints、viewer 與 benchmark scripts 已公開，但目前沒有 production game adoption 證據。

技術密度：**高**。

預估閱讀時間：**50–75 分鐘**；若連 FuzzyDR implementation 一起追，約 2 小時以上。

真正值得留下的不是「用線重建毛髮」這個表面結果，而是：**如果某種世界內容天然具有一維拓撲，就應該考慮讓 reconstruction、rendering、physics 與 gameplay 都共享一維 explicit primitive，而不是先把它膨脹成容易渲染、卻難以互動的 volume。**
