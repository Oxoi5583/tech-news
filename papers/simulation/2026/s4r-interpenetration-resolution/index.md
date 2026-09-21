---
type: paper
title: "S4R: Scaling for Rigid-Body Interpenetration Resolution"
published: "2026-09-17"
added: "2026-09-22"
authors:
  - "Zhiyang Dou"
  - "Ang Zhao"
  - "Chen Peng"
  - "Minghao Guo"
  - "Haixu Wu"
  - "Cheng Lin"
  - "Yuan Liu"
  - "Junfeng Yao"
  - "Xiaohu Guo"
  - "Wenping Wang"
  - "Wojciech Matusik"
venue: "ACM Transactions on Graphics 45(6), SIGGRAPH Asia 2026"
paper_url: "https://arxiv.org/abs/2609.20524"
code_url: "https://github.com/Frank-ZY-Dou/S4R"
tags:
  - collision-detection
  - rigid-body
  - geometry-processing
  - physics
  - procedural-generation
  - gpu
  - toolchain
one_liner: "把一堆互相穿進去的剛體先縮小分開，再逐步恢復原尺寸，以很少的位置改動整理成可以安全交給物理引擎的場景。"
summary: "S4R 將嚴重的靜態穿透問題改寫成一連串較容易處理的淺接觸問題：先把物件縮至互不重疊，再逐步放大，每一步只求解維持分離所需的最小位移。它適合程序生成、批量匯入或使用者編輯後的場景清理，而不是取代遊戲執行中的動態碰撞求解器。"
---

# S4R: Scaling for Rigid-Body Interpenetration Resolution

## 先用一個例子理解

假設程序生成器一次把數百件家具、箱子與雜物塞進房間。位置大致合理，但很多 mesh 已經彼此穿透。若直接把這個場景交給剛體引擎，solver 會在第一幀嘗試排除很深的穿透，物件可能像爆炸一樣被彈飛。

S4R 不直接問「怎樣一次把所有深度穿透推開」。它先把每件物件以自己的固定中心等比例縮小，直到場景成為無穿透狀態；之後逐步把所有物件恢復到 100% 大小。每次放大只會新產生很淺的接觸，因此可以用一個較簡單的最佳化問題，把碰到的物件移動最低限度的距離來保持分離。

論文在 50 個 YCB 物件的測試中，把原本因初始穿透而在一秒內出現的峰值速度，從 MuJoCo 的 7.8 m/s、PyBullet 的 12.5 m/s、Isaac Gym / PhysX 的 230.6 m/s，降到修復後約 0～0.001 m/s。這項實驗關閉了重力，因此主要量到的就是錯誤初始接觸造成的爆炸式反應。

## 原本的做法有甚麼困難

深度穿透與一般 runtime 接觸不是同一種問題。物理引擎最擅長的是兩個表面剛開始碰到時，從一個合理的上一幀狀態求下一幀；但程序生成、批量 asset placement 或匯入錯誤可能直接產生「物件已經深入另一件物件內部」的靜態場景。

此時若一次求完整修正，不只接觸關係複雜，而且「把哪件物件往哪裡移」有大量互相牽連的選擇。直接使用非線性最佳化可以很慢；依賴粗略 collision proxy 又可能在 proxy 上分開、真正 mesh 仍然穿透。

## 它是怎樣做到的

S4R 的核心是 **scale continuation（尺度延續）**：不要直接解最難的 100% 尺寸問題，而是從一個已知容易、沒有穿透的小尺寸狀態開始，逐步把問題變回原本大小。

流程可以理解成：

```text
原始場景：100% 尺寸，嚴重穿透
        ↓
統一縮小各物件，找到已分離的尺度
        ↓
稍微放大
        ↓
偵測剛出現的接觸
        ↓
解 minimum-norm contact QP
只移動維持分離所需的最小距離
        ↓
再放大 → 再修正 → 再放大
        ↓
100% 尺寸
        ↓
完整 mesh evaluator 驗證
        ↓
必要時做 bounded tail refinement
```

每個尺度步驟使用凸二次規劃（convex quadratic program，QP）：接觸條件被線性化成分離限制，而目標函數偏好最小總位移。因為每一步只處理剛形成的淺接觸，比從嚴重穿透直接猜一個全局修正容易得多。

作者另外用 **Scale-of-Impact / conservative scale-event bound** 預測「下一個新接觸最早會在哪個尺度發生」，避免固定用很小的 scale step 慢慢試；對已知接觸則用 frozen-witness gap prediction 減少昂貴的精確 mesh query。最後仍以獨立的 mesh-level evaluator 檢查 100% 尺寸結果，而不是把近似預測當作最終正確性證明。

官方程式同時提供 CPU canonical solver，以及以 NVIDIA Warp、GPU broad phase 和 Dual-APGD QP solver 實作的 GPU 路徑。

## 與現有方法的差別

最重要的改變不是換一個更快的碰撞函式，而是**改變問題的求解路徑**。

傳統思路面對的是：

```text
深度穿透的最終場景
        ↓
直接找一個 collision-free configuration
```

S4R 則建立一條容易追蹤的路徑：

```text
無穿透的小尺寸場景
0.2 → 0.3 → 0.5 → 0.8 → 1.0
        ↓
每一步只處理局部新接觸
```

這種 continuation 思路值得獨立記住：若最終幾何限制太難直接滿足，可以先改變一個全局參數，把問題帶到容易的狀態，再沿參數空間逐步返回真正問題。

## 實驗結果與限制

作者在 Kubric、HY3D-Bench 與 Thingi10K 三類 mesh 上測試。主要比較最多到 5,000 個 rigid bodies；GPU 實作另延伸到 30,000 個物件的規模。

Kubric scaling study 中，S4R CPU 在 5,000 個物件時平均約 68.1 秒，QP/LCP 約 220 秒、PD-PGS 約 404 秒；同一 GPU tier 的 S4R-Warp 在 RTX 2080 Ti 上約 9.7 秒，而 ISIR 約 1,775 秒且仍平均留下 39 個 penetration pairs。這些數字只應在論文各自相同 hardware tier 與 timing protocol 內比較，不能拿來直接推算遊戲 runtime FPS。

在 HY3D-Bench 與 Thingi10K 的 2,000-object 測試中，S4R 分別約 22.2 秒與 21.4 秒，且 shared mesh evaluator 報告零殘留穿透。作者也公開 benchmark harness、固定 seeds、scene fingerprints 與結果重建腳本，重現性相當完整。

限制同樣很重要：S4R 是**靜態場景修復器，不是動態 rigid-body contact solver**。如果一件物件被困在另一件封閉物件內、物件中心幾乎重合，或環境太狹窄而不存在可沿縮放路徑恢復的配置，它仍可能失敗。主要實驗也以平移 3-DOF 為主；加入旋轉雖能減少位移，但 Kubric N=40 測試約增加至 15 倍時間。tabletop extension 還假設單一平面支撐，不處理堆疊、抬起與翻倒。

## 可以怎樣用在遊戲裡

論文已直接驗證它可以作為 physics-engine initialization 的前處理，因此最實際的遊戲用途是 **toolchain / runtime editing 的場景合法化階段**：

- procedural dungeon / room generator 放完大量 props 後，自動清除 mesh 穿透；
- 玩家建造系統或 runtime editor 完成一次大規模 layout 操作後，將近似位置投影回 collision-free configuration；
- 大量外部 asset 匯入或 scatter pipeline 在 bake 前做物理可用性檢查；
- destruction 後若使用較高層級的重新組裝／重置流程，可以在重新啟動 rigid-body simulation 前整理初始狀態。

更值得借用的是它的 **editable scale-space** 概念。作者展示過先把物件縮到互相分離的空間、讓使用者在這個較容易編輯的狀態重新排列，再恢復原尺寸。這可以延伸成一種特殊 editor：使用者看到的不是「紅色 collision error」，而是一個暫時把擁擠場景展開的操作空間，完成修改後由 solver 把結果重新投影回真實尺度。

這部分比較像 production tool / world editor 的專用 engine solution，而不是每幀 gameplay physics。

## 想實作時再看

最小 prototype 不必先做任意 triangle mesh。可以從 2D convex polygons 或 3D spheres / boxes 開始：

1. 為每個 rigid body 保存固定 reference center 與目前 translation。
2. 找到一個全局 scale `s0 < 1`，使所有物件互不重疊。
3. 增加 scale，直到偵測到下一組 contact。
4. 對 contact normals 建立線性 separation constraints。
5. 解一個最小化所有 body displacement 的 QP。
6. 重複到 `s = 1`，最後用獨立 collision checker 驗證。

先驗證「深度穿透 → 縮小 → 逐步恢復」是否比直接 iterative push-out 更穩，再研究論文的 Scale-of-Impact bound、frozen-witness prediction 與 GPU QP。官方 repo 的 `baselines/s4r_qp.py` 是最適合先讀的 canonical CPU implementation；`S4R/` 則是 GPU-native Warp 版本。

## 個人筆記

這篇最有價值的地方不是做出另一個 collision solver，而是把「壞掉的場景」視為一條 continuation path 可以修復的幾何問題。它很適合程序生成與 agentic toolchain：生成器不必一次就產生完美 collision-free layout，可以先產生語意與大致位置，再由一個專門的 geometry-repair pass 收斂成物理可用場景。

技術成熟度：**可實作研究方案**。已有完整 CPU/GPU source、可重現 benchmark 與 MuJoCo / PyBullet / Isaac Gym 初始化驗證，但尚未見遊戲 production adoption。

技術密度：**中高**。預估先讀懂方法與實驗約 **45–60 分鐘**；若要追 QP、Scale-of-Impact 與 GPU solver 實作，約需 **2 小時以上**。
