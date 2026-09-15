---
title: "Grid-Free Monte Carlo for Time-Dependent Diffusion"
published: "2026-09-11"
added: "2026-09-15"
authors:
  - "Zihong Zhou"
  - "Rohan Sawhney"
  - "Eugene d'Eon"
  - "Wojciech Jarosz"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2609.12306"
code_url: ""
tags:
  - simulation
  - pde
  - diffusion
  - heat-transfer
  - monte-carlo
  - grid-free
  - procedural-world
summary: "把 Walk on Spheres / Walk on Stars 擴展到隨時間變化的熱擴散問題，不需要建立 volumetric mesh，也不需要從 t=0 一步一步 time-step 到目標時間；可直接查詢任意位置與時間的擴散狀態。"
---

# Grid-Free Monte Carlo for Time-Dependent Diffusion

## 解決甚麼問題

熱傳導、污染物擴散、某些聲學／濃度／魔法場等系統通常可寫成 diffusion PDE。傳統 transient solver 通常要先把整個空間離散成 voxel、tetrahedral mesh 或其他 volumetric grid，再從初始時間開始逐步積分：

```text
建立整個 volume
    ↓
t = 0
    ↓
t + Δt
    ↓
t + 2Δt
    ↓
...
    ↓
目標時間 T
```

這有兩個對大型或複雜遊戲世界很麻煩的成本：必須替整個 volume 建資料結構，而且即使只想知道少數幾個位置在某個時間的溫度，也通常需要計算大量根本不會被查詢的空間與中間時間狀態。

這篇把既有的 grid-free Monte Carlo PDE 方法 Walk on Spheres（WoS）與 Walk on Stars（WoSt）擴展到 **time-dependent diffusion / heat equation**。最重要的能力是：**直接估計某個位置在指定時間的解，不需要 volumetric meshing，也不需要 sequential time marching。**

## 核心做法

傳統 Walk on Spheres 解 steady-state PDE 時，從 query point 開始，在幾何內反覆建立能容納的最大球，直接隨機跳到球面；因此一次可以跨過很大的空白區域，不必像 grid solver 一格一格走。

這篇替每條 random walk 再加入一個 **time budget**。

假設要查詢位置 `x` 在時間 `T` 的溫度：

```text
Query(x, T)
    ↓
walker.time = T
    ↓
建立 sphere / star
    ↓
抽樣這一步穿越區域所需的 exit time τ
    ↓
τ < 剩餘時間？
   ├─ 是 → 跳到下一個空間位置
   │        time -= τ
   │        累積 source / boundary contribution
   │        繼續 walk
   │
   └─ 否 → walker 在目標時間之前仍留在這個區域
            抽樣 interior point
            查詢 initial condition
            結束
```

因此 random walk 同時在「空間」與「剩餘時間」中向後追蹤 diffusion 的來源。

對純 Dirichlet boundary，作者擴展 Walk on Spheres；對混合 Dirichlet–Neumann boundary，則擴展 Walk on Stars。技術重點還包括 exit-time kernel 的抽樣、低偏差且不需要大型 lookup table 的 exit-time sampler、rejection sampling，以及 variance reduction。

作者亦提出共享 random walks 的方式，讓多個 target times 不必完全獨立重算。

## 與現有方法的差別

傳統 transient grid / FEM solver 的思維是：

```text
整個世界狀態(t)
        ↓
更新整個世界狀態(t + Δt)
```

這篇則比較像：

```text
「我現在只想知道這個位置在 8.3 秒時是多少？」
        ↓
直接 Monte Carlo Query(x, 8.3)
```

所以它把 diffusion 從一個必須持續維護的 **global simulation state**，部分轉成一個可以按需要求值的 **queryable field**。

這個差異對遊戲引擎很重要：如果 gameplay / AI / renderer 每一幀只需要少量 sample，output-sensitive solver 有機會避免為整個巨大世界維護高解析度 voxel field。

與原有 grid-free WoS / WoSt 相比，新內容則是把 steady-state 解法真正帶到 transient heat equation，包括 initial condition、time-dependent source，以及 time-dependent boundary data，同時避免 time-step selection 與 temporal discretization bias。

## 實驗結果與限制

作者展示方法可以在複雜幾何上直接估計不同時間的 diffusion solution，並與傳統數值解比較。方法保留 Monte Carlo solver 的幾個特性：

- 不需要 volumetric mesh；
- query 彼此高度平行；
- progressive：增加 samples 可逐步降低 noise；
- output-sensitive：成本主要花在真正要求值的位置；
- 不需要選擇 Δt，因此沒有一般 time marching 的 temporal discretization bias。

但這不是「免費的 realtime heat simulation」。Monte Carlo estimator 會有 variance；要求非常低噪聲或同時查詢整個 dense 3D field 時，sample 數量仍可能很大。若遊戲每幀真的需要更新數百萬 voxel，傳統 GPU grid solver 反而可能更合適。

另外，這篇目前是 arXiv 研究工作；不能把它直接當成已有 production evidence 的遊戲引擎方案。

## 對遊戲開發的用途

最值得注意的不是單純「熱傳導更準」，而是它提供另一種 **world-field representation / execution model**：世界中的 diffusion 不一定要永久存在一張 dense voxel texture 裡，也可以在需要時直接 query。

例如大型機甲遊戲可以把裝甲或場景中的熱源表示為 boundary / source data：

```text
雷射命中
  ↓
建立 time-dependent heat source
  ↓
玩家熱感應器 Query(x, t)
AI Query(x, t)
材質系統 Query(x, t)
  ↓
只有真正需要的地方才求值
```

同一個思想也可能延伸到符合 diffusion PDE 的其他場，例如污染、煙霧濃度的低頻近似、腐蝕／濕度傳播、某些 gameplay energy field 等。不過這些是否符合 diffusion model 必須逐項判斷，不能把所有 propagation 都硬套成 heat equation。

它尤其適合「巨大世界，但只有玩家附近／感測器附近需要高精度結果」的系統。這與固定建立整張 3D texture 的思路很不一樣。

## 最小 Prototype

第一版不需要碰複雜 3D mesh，可以先做 2D domain：

1. 建一個有障礙物的 2D 區域。
2. 左側 boundary 設為隨時間升溫的 Dirichlet condition。
3. 實作最基本的 transient Walk on Spheres。
4. 提供 `float QueryTemperature(Vec2 p, float t, int samples)`。
5. 與 512×512 finite-difference grid + small timestep 的 reference 比較。
6. 特別量測「只查 100 個 gameplay points」時，兩種方法真正計算了多少資料。

如果這一步成立，再測大型稀疏 3D 場景；那時才比較容易判斷它是否值得變成 engine subsystem。

建議先讀論文中 transient WoS / WoSt 的 estimator 推導，再讀 exit-time sampling 與 variance reduction 部分。真正決定實作是否實用的不是 WoS 這個名稱，而是 exit-time kernel 怎樣可靠而便宜地抽樣。

## 個人筆記

這篇最有意思的地方是把「隨時間演化的場」從傳統的 **state update problem** 改寫成某種 **space-time query problem**。

對遊戲而言，這可能形成一個很有特色的 engine primitive：

```cpp
float QueryField(Vec3 position, double time);
```

世界不一定每幀把所有地方的熱都算好；只有角色、AI、sensor、renderer 或 gameplay rule 真正需要知道某處狀態時才估計。

技術成熟度：**研究原型 / 方法可實作，暫無 production evidence**。

技術密度：**很高**。

預估閱讀時間：**60–90 分鐘**。
