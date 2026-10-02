---
type: paper
title: "CoDimRecon: Agentic Reconstruction of Sim-Ready 3D Scenes with Deformable Curves, Surfaces, and Volumes"
published: "2026-09-28"
added: "2026-10-02"
authors:
  - "Shuzhao Xie"
  - "Lelin Wang"
  - "Guying Lin"
  - "Zhi Wang"
  - "Minchen Li"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2609.36024"
code_url: ""
tags:
  - simulation
  - reconstruction
  - deformable
  - robotics
  - world-representation
one_liner: "把照片重建出的場景直接整理成適合不同物理模型的曲線、薄殼與實體，而不只是做出看起來像真的表面。"
summary: "CoDimRecon 從多視角 RGB 建立可編輯、可模擬的場景，將細長物、薄片與有體積軟物分別重建為曲線、表面與體積表示，再用模擬中的行為測試修正幾何、數值設定或材料模型。"
---

# CoDimRecon: Agentic Reconstruction of Sim-Ready 3D Scenes with Deformable Curves, Surfaces, and Volumes

## 先用一個例子理解

同一間辦公室裡，電話線、塑膠袋與椅墊雖然都能被相機拍成 3D 外觀，但它們適合的物理表示並不相同：

- 電話線是細長的一維結構，適合用中心線加半徑表示並交給 rod simulation。
- 塑膠袋是薄的二維結構，適合用有厚度的 manifold shell。
- 椅墊是真正具有體積的軟物，適合重建成 watertight solid，再做 volumetric meshing。

CoDimRecon 的目標不是只得到「可以看」的重建，而是直接建立之後能交給 simulator 的資產。

## 原本的做法有甚麼困難

許多 scene reconstruction 方法主要處理靜態或剛體外觀。即使視覺重建很好，simulation 還需要另一批資訊：物件是否有關節、薄片到底應視為 shell 還是 solid、細線是否有中心線與半徑，以及材料模型是否能產生合理行為。

若把所有物件都強行轉成一般 triangle surface，再事後補 physics，細線、薄片與軟體往往需要大量手工修復，或者產生不必要的網格與數值成本。

## 它是怎樣做到的

CoDimRecon 從多視角 RGB 開始，先建立場景尺度、相機與幾何脈絡，再逐個物件建立可編輯幾何。剛體與 articulated object 會建立對應的部件與 joint；deformable object 則按幾何維度分流。

資料流可簡化為：

```text
Multi-view RGB
      ↓
Scene / object geometry context
      ↓
Object reconstruction
      ↓
Curve / Surface / Volume
      ↓
Rod / Shell / Solid simulation
      ↓
Behavioral tests
      ↓
Targeted revision
```

曲線類物件重建成 centerline + radius；表面類物件重建成 manifold midsurface + thickness；體積類物件重建成 watertight solid，再產生 volumetric mesh。

另一個重要部分是 behavioral testing。系統不是看到靜態外形相近就停止，而會在 simulator 裡操作物件。例如論文展示紙張折疊後，如果純彈性模型會完全彈回，就需要改用能保留摺痕的塑性彎曲模型。這些測試可觸發對 motion、geometry、numerics 或 material model 的修正。

作者也特別提醒：由這種行為校準得到的 material parameter 應理解為「在目前模型假設下能重現目標行為的有效參數」，而不是由照片直接量測出的真實材料常數。

## 與現有方法的差別

它真正改變的是 reconstruction target。

傳統流程常近似為：

```text
照片 → 幾何外觀 → 之後再補 Physics
```

CoDimRecon 則把「之後要如何模擬」提前到 representation 選擇階段：

```text
照片
 ↓
判斷物件結構
 ↓
選擇 Curve / Surface / Volume
 ↓
建立對應 Simulation Asset
```

因此不同維度的物體不必全部先被塞進同一種 mesh 表示。

## 實驗結果與限制

作者在 Replica 與 ScanNet++ 的室內場景上評估 compositional reconstruction，並展示 rigid、articulated，以及 curve、surface、volume 三類 deformable asset 的模擬互動。官方 project page 展示電話線的 rod simulation、塑膠袋的 shell simulation、椅墊的 solid simulation，以及抽屜關節與 humanoid traversal。

這些結果證明 pipeline 能產生可供 simulator 使用的異質 representation，但目前仍是研究型 scene-building workflow，而不是即時遊戲匯入器。

限制包括：

- 物理參數並不是直接從 RGB 精確量測。
- deformable 評估仍較偏代表性案例，不等於任意材質都能可靠恢復。
- reconstruction 與 behavioral verification 的成本目前不適合 frame-time runtime。
- 對 occlusion 嚴重、拓撲含糊或缺少觀測的物件，仍需要 generative / heuristic priors。

## 可以怎樣用在遊戲裡

以下是遊戲工程上的延伸，不是論文已經驗證的 production game architecture。

這篇最值得借用的觀念，是把不同幾何維度做成 engine 的 first-class world primitive：

```text
World Object
├─ Curve
├─ Surface
└─ Volume
```

例如機甲或可破壞場景可以把：

- 電纜、液壓管、天線、鋼筋視為 curve / rod。
- 布、薄裝甲、薄板、紙張視為 shell。
- 輪胎、軟墊、厚實軟體視為 volume。

這比「所有東西都是 triangle mesh，其他系統再附加 component」更接近物件真正的力學結構。

另一個很實用的延伸是 behavioral asset validation。遊戲資產 CI 不只檢查 topology、UV、normal 或 collider，也可以自動執行「拉電纜」「壓軟墊」「折薄片」「跑關節全行程」等測試，確認資產在 simulator 中真的能正常工作。

## 想實作時再看

最小 prototype 不需要先做任何 vision 或 agent。

先定義一個 `SimulationAsset`：

```text
GeometryKind = Curve | Surface | Volume

Curve   = polyline + radius
Surface = triangle mesh + thickness
Volume  = closed surface + tetrahedral mesh
```

再做三個 deterministic tests：

```text
Cable:
pull(endpoint)
check stretch / solver stability

Sheet:
fold(angle)
release()
check crease retention

Cushion:
press(depth)
release()
check recovery
```

如果這套 representation 與測試架構值得保留，再考慮加入「照片 → representation selection → reconstruction」的前端。

優先閱讀論文中 deformable reconstruction、simulation-ready representation 與 behavioral testing 的部分；官方 project page 也適合先看各類物件如何進入不同 simulator。

## 個人筆記

這篇最值得留下的不是 agent 本身，而是「representation 應由後續 interaction / simulation 決定」的設計。

如果把這個思路放進專用遊戲引擎，世界可以天然由異質幾何 primitive 組成，而不是一律先轉成 surface mesh。這和 line primitive、voxel、SDF、Gaussian 等不同 representation 的研究可以放在同一條長期方向上理解：世界資料結構本身會限制，也會創造可以做的互動。
