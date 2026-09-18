---
type: paper
title: "Semi-Implicit Pairwise Descent for Nonlocal Continuum Mechanics"
published: "2026-09-09"
added: "2026-09-18"
authors:
  - "Xukun Luo"
  - "Xiao Cheng"
  - "Yuzhong Guo"
  - "Ying Qiao"
  - "Wencheng Wang"
  - "Xiaowei He"
venue: "SIGGRAPH Asia 2026 Conference Paper / arXiv"
paper_url: "https://arxiv.org/abs/2609.09834"
code_url: ""
tags:
  - simulation
  - soft-body
  - fem
  - contact
  - friction
  - gpu
  - real-time
one_liner: "把軟體材料內部的受力改寫成鄰近點之間的成對作用，讓 GPU 不必反覆建立昂貴的大型二階導數矩陣，也能穩定處理大量變形、碰撞與摩擦。"
summary: "SIPD 將有限元素法的彈性力重新表達成成對力，讓每個頂點只需求解很小的局部系統；接觸與摩擦也被放進同一套成對能量模型。作者展示了百萬級四面體與大量接觸的即時模擬，但目前接觸仍不是嚴格的不可穿透保證。"
---

# Semi-Implicit Pairwise Descent for Nonlocal Continuum Mechanics

## 先用一個例子理解

假設遊戲裡有一大堆軟膠、肉塊、輪胎或會互相擠壓的柔軟物件。真正困難的通常不只是「讓它變形」，而是它們一旦大量互相碰撞、摩擦，穩定的隱式求解器每一步都要處理很大的二階導數矩陣，GPU 上的暫存器與記憶體成本很高。

SIPD 的核心想法是：**不要每次都從整個元素的大矩陣角度處理，而把材料受力重新寫成頂點與鄰近頂點之間的成對作用。**

於是執行時更像：

```text
每個頂點
  ↓
讀取鄰居目前的位置與成對受力係數
  ↓
解一個很小的 3×3 局部系統
  ↓
更新位置
  ↓
所有頂點在 GPU 上平行重複
```

作者展示的案例包含超過一百萬個四面體，以及數百萬組接觸的場景。

## 原本的做法有甚麼困難

有限元素法（Finite Element Method，FEM）會把連續材料切成很多小元素，例如四面體，再從材料能量求出力。若使用 Newton 類的隱式方法，通常還要計算 Hessian，也就是「力如何隨位置改變」的二階資訊。

這種方法很穩，但對 GPU 不太友善：每個元素可能需要處理 9×9 或 12×12 等較大的局部矩陣，還要確保矩陣具有適合下降求解的性質。當元素、碰撞和摩擦數量都很大時，暫存器壓力、矩陣建立與投影成本會變得很明顯。

另一類非局部方法會直接把材料理解成很多點之間的「鍵」，很適合平行計算，但通常與標準 FEM 的材料模型和邊界行為並不完全相同。

## 它是怎樣做到的

### 1. 把 FEM 力精確拆成成對力

作者證明，一個 FEM 元素對頂點產生的力，可以重新組合成頂點對 `(i, j)` 之間的作用力，而不只是用彈簧近似 FEM。

概念上由：

```text
四面體元素 → 應力 → 每個頂點的力
```

改寫成：

```text
頂點 i ←→ 頂點 j
頂點 i ←→ 頂點 k
頂點 i ←→ 頂點 l
...
```

每一對之間保存一個會隨目前材料狀態改變的 3×3 張量，描述這一對點之間的方向性受力。

### 2. 每個頂點只解 3×3 系統

每次迭代先固定目前的成對係數，再讓每個頂點根據鄰居解自己的局部位置修正。這很像 Jacobi 式平行更新：大量頂點可以同時執行，而且不需要建立傳統 Newton 法的大型 Hessian。

這個改動的重要性主要在 GPU 執行模型：局部資料較小，暫存器需求下降，能同時駐留更多 threads。

### 3. 用解析方式保證局部矩陣適合求解

高度變形時，某些材料項可能讓更新矩陣失去正定性，求解器便可能往錯誤方向走。傳統做法常用特徵分解或 SVD 修正，但這些操作昂貴。

SIPD 對常見超彈性材料把成對張量解析地拆成正、負兩部分：適合隱式處理的部分留在左邊，不適合的部分移到右邊顯式處理。作者藉此得到穩定的下降方向，而不需要逐元素做昂貴的數值投影。

### 4. 碰撞和摩擦也變成「材料作用」

作者建立暫時的 Virtual Boundary Elements，把接近中的表面連成虛擬元素，再把法向碰撞與切向摩擦寫成異向性的彈性能量。

所以資料流不是：

```text
彈性 solver
  ↓
另一套 collision solver
  ↓
另一套 friction solver
```

而比較接近：

```text
真實材料 pair ─┐
碰撞虛擬 pair ─┼→ 同一套 pairwise update
摩擦虛擬 pair ─┘
```

這是它作為 engine solver 最有意思的部分之一。

## 與現有方法的差別

它不是發明一種新的「軟體看起來比較 Q 彈」的材料，而是改變 **FEM solver 的計算 representation**：保留 FEM 的材料力，卻把求解工作改寫成 GPU 更容易大量平行的小型成對運算。

相較 Newton 類方法，它避免反覆形成大型 Hessian；相較純 peridynamics 等非局部模型，它仍從 FEM 力精確推導出成對表示；相較把碰撞視為獨立 constraint pipeline 的做法，它把接觸和摩擦納入相同的能量／成對框架。

## 實驗結果與限制

論文報告 SIPD 在彈性模擬的總收斂時間約比 Vertex Block Descent 快 1.6 倍；GPU 實作中每個 thread 的暫存器使用量報告為 56，而比較方法 VBD 超過 100。作者亦展示超過一百萬個四面體、約 260 萬組接觸的即時案例，測試硬體包含 NVIDIA RTX 5090。

這些數字只適用於論文自己的場景、硬體、誤差門檻與比較設定，不能直接理解成「任何遊戲 soft body 都會快 1.6 倍」。

另一個重要限制是目前的接觸屬 penalty / energy 式處理，**沒有像 IPC（Incremental Potential Contact，一種利用 barrier energy 與連續碰撞檢測嚴格避免穿透的方法）那樣提供嚴格不可穿透保證**。極端高速、極薄幾何或非常複雜的接觸仍可能需要更強的碰撞處理。

## 可以怎樣用在遊戲裡

論文已驗證的是大規模超彈性、接觸與摩擦求解；以下是遊戲引擎方向的延伸構想。

如果把它做成專用 engine solution，真正有趣的不是一個「SoftBody Component」，而是讓大量可變形物件可以共同存在：輪胎、橡膠履帶、肉體、軟裝甲、可壓縮地形物件、纜線或大量互相擠壓的材料，都能使用相近的 GPU pairwise execution model。

對破壞系統也有潛在價值。既然內部作用已被表示成局部 pair，未來若加入斷裂準則，可以研究把某些 pair 的連接移除或重新建立；不過這不是本論文已展示的 dynamic fracture 能力，不能直接視為現成功能。

對機甲遊戲而言，另一個值得試的方向是讓輪胎、腳底墊、橡膠關節、軟性外殼等不再只是 rigid collider，而真正成為控制系統會感受到的變形結構。這樣接觸面積、壓縮程度與摩擦便可能自然影響 locomotion，而不是靠固定 grip 參數模擬。

## 想實作時再看

最小 prototype 不需要一開始做百萬元素。

1. 建立一個很小的 tetrahedral mesh，例如幾千個 tetrahedra。
2. 先只實作 Neo-Hookean 超彈性材料，不做碰撞。
3. 依論文推導，把 FEM element force 拆成 vertex-pair force。
4. 實作每頂點 3×3 的 Jacobi-style semi-implicit update。
5. 與自己已有的 explicit FEM 或簡單 Newton solver 比較：大時間步下是否仍穩定、每 iteration 的 GPU 資料量與 register pressure 有何差別。
6. 最後才加入 Virtual Boundary Elements、normal contact 與 friction。

最值得先讀的是論文中「FEM force 的 pairwise decomposition」、「semi-implicit pairwise solver」及「contact / friction formulation」三部分。先弄清楚成對張量如何由元素應力得到，再看 GPU 優化會比較容易。

## 個人筆記

這篇真正值得記住的不是「又一個更快的 soft-body solver」，而是它展示了一個很好的 engine 思路：**同一套物理模型未必要沿用傳統的計算 representation。**

FEM 在數學上仍然是 FEM，但 runtime 可以重新排列成更符合 GPU 的 pair graph。這種「保留物理模型，改寫執行 representation」的思路，很適合尋找專用遊戲引擎方案。

成熟度：可實作研究方案；已有大型 GPU 實驗，暫未見遊戲 production adoption。

技術密度：高。

預估閱讀時間：60–90 分鐘。