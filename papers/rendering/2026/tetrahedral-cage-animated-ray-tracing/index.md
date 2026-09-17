---
type: paper
title: "Ray Tracing Massive Amounts of Animated Geometry"
published: "2026-07-17"
added: "2026-09-17"
authors:
  - "Holger Gruen"
  - "Carsten Benthin"
  - "Michael Kern"
  - "David McAllister"
venue: "High-Performance Graphics 2026 / Proceedings of the ACM on Computer Graphics and Interactive Techniques"
source_url: "https://gpuopen.com/learn/ray-tracing-massive-amounts-animated-geometry/"
paper_url: "https://dl.acm.org/doi/10.1145/3820014"
code_url: ""
tags:
  - ray-tracing
  - animation
  - bvh
  - geometry
  - gpu-driven
  - real-time
  - lod
one_liner: "用低解析度的四面體外殼代替數億個三角形參與每幀動畫更新，讓大量各自變形的高密度模型仍能即時做光線追蹤。"
summary: "方法把高密度模型切成由四面體外殼管理的小區塊，區塊內的三角形與加速結構保持靜態；執行時只讓較粗的外殼變形，再把射線轉回模型原本的空間查詢靜態幾何，因此動畫更新成本主要取決於外殼解析度，而不再直接跟三角形數量一起增長。"
---

# Ray Tracing Massive Amounts of Animated Geometry

## 先用一個例子理解

想像森林裡有數萬棵植物，每棵都有非常高密度的葉片與枝條，而且每棵都因風而產生不同變形。

一般即時光線追蹤除了要算頂點動畫，還要讓用來加速射線查詢的 BVH（Bounding Volume Hierarchy，將幾何分層包進包圍盒的搜尋結構）跟著更新。模型愈密，更新的頂點和 BVH 工作就愈大。

這篇論文改成在高密度模型外建立一個粗很多的四面體 cage。真正的數億個三角形不再每幀跟著變形；每幀只變形 cage。射線碰到變形後的四面體時，系統把射線轉換回該四面體的 rest pose，再查詢預先建立、保持靜態的高密度三角形。

因此可以把概念理解成：**不是把數億個三角形搬來搬去，而是只改變一個較小的空間座標框架，讓射線自己回到原本的幾何空間找答案。**

## 原本的做法有甚麼困難

硬體光線追蹤通常需要 BLAS（Bottom-Level Acceleration Structure，針對單一模型幾何建立的 BVH）。如果模型本身每幀變形，BLAS 也要 refit 或 rebuild。

這對一般角色尚可接受，但若場景同時存在大量高密度、而且每個 instance 都有不同動畫的物件，例如：

- 草與樹木；
- 大量生物；
- crowd；
- 幾何極密的遠景角色；
- 每個 instance 都受不同風場影響的植被；

成本會同時出現在頂點動畫、加速結構更新與每個 unique deformation 所需的記憶體。

AMD 公開 demo 的植物最高 LOD 合計約 28 億個三角形；即使 LOD 後每幀仍約有 5 億個三角形需要被 ray trace。若對這些獨立動畫植物使用傳統 BLAS update，AMD 估計在 Radeon RX 9070 XT 上最高可消耗約 80 GB GPU memory，更新時間超過 300 ms。

## 它是怎樣做到的

### 1. 預處理：用四面體 cage 切割高密度模型

先在模型周圍建立低解析度 tetrahedral cage，也就是由許多四面體組成的粗略體積網格。

原本的三角形會依所在四面體被分成互不重疊的小集合。每個四面體所管理的三角形集合各自建立一個小型、靜態的 BLAS。

因此資料大致變成：

```text
Animated Object
  └─ Tetrahedral Cage
       ├─ Tet 0 → Static triangles + static mini-BLAS
       ├─ Tet 1 → Static triangles + static mini-BLAS
       ├─ Tet 2 → Static triangles + static mini-BLAS
       └─ ...
```

真正昂貴的高密度幾何從這一步之後基本保持在 rest pose。

### 2. 執行時：只動畫 cage

每幀只更新四面體頂點。系統因此只需要更新包住這些四面體的上層加速結構，而不用重新處理全部高密度三角形。

動畫成本於是主要由 cage 有多少四面體決定，而不是模型有多少三角形。

### 3. 射線進入變形四面體後，把射線變回去

假設某個四面體在 rest pose 是 A，動畫後變成 A'。

射線實際上先和 A' 相交；若進入 A'，系統利用四面體的 piecewise-linear deformation，把射線轉換回 A 的座標空間，再對 A 裡預先建立好的靜態 mini-BLAS 做正常三角形 intersection。

也就是：

```text
world-space ray
      ↓
animated tetrahedron
      ↓
transform ray to rest space
      ↓
static mini-BLAS
      ↓
original dense triangles
```

高密度 geometry 沒有真的被重新寫成動畫後的頂點位置；變形被編碼在 cage 的空間轉換中。

## 與現有方法的差別

傳統 skinning / vertex animation 的基本思路是「幾何跟著動畫走」：

```text
Animation
  ↓
Dense vertices move
  ↓
BLAS follows dense geometry
```

這篇則變成：

```text
Animation
  ↓
Coarse cage moves
  ↓
Ray is warped into static geometry
```

這個改變把**動畫複雜度與幾何密度拆開**。

如果把一棵植物從 100 萬三角形換成 1000 萬三角形，只要 cage 解析度不變，每幀需要動畫的 proxy 規模可以基本不變。代價是動畫變形只能由 cage 的 piecewise-linear deformation 近似；cage 太粗時，細小或尖銳的局部變形會失真。

## 實驗結果與限制

AMD 公開的實時 demo 使用 Radeon RX 9070 XT、1080p，場景有約 25,000 棵各自動畫的植物。植物最高 LOD 原始幾何合計約 28 億個三角形；LOD 選擇與不同解析度 cage 後，每幀約 ray trace 5 億個動畫三角形，包含 primary ray 與 shadow ray，仍可超過 60 FPS。

另一個論文場景約有 5.85 億個動畫三角形，同樣展示約 60 FPS。

這些數字不能理解成「任何 5 億三角形場景都能 60 FPS」：demo 聚焦大量動畫幾何，不是複雜材質、全套 GI 或完整遊戲 frame；實際成本仍取決於射線數量、材質、cage 密度、場景結構與其他 rendering passes。

方法的主要限制包括：

- 適合保持 triangle connectivity 的動畫；
- 不適合 topology change、切割、破壞等直接改變網格連接關係的效果；
- cage 愈粗愈便宜，但局部動畫近似愈差；
- 細小且需要精準 silhouette 的角色變形未必適合；
- 目前 AMD 公開文章表示 DXR sample 與 header-only C++ cage library 仍在開發中，尚未形成完整可直接整合的 production SDK。

論文在 HPG 2026 獲 Wolfgang Straßer Award 第三名（並列）。`published` 採 HPG 2026 官方 schedule 中本論文發表場次的 2026-07-17；AMD GPUOpen 技術文章則於 2026-07-22 發布，並於 2026-09-02 新增 cage-driven animation demo。

## 可以怎樣用在遊戲裡

### 1. 真正高密度的動態植被

這是論文已直接驗證的用途。若 virtual geometry 讓靜態植物可以非常密，傳統 ray tracing 的下一個問題就是「它一動怎麼辦」。四面體 cage 可以把高密度 visual geometry 與 animation update rate 拆開。

對 engine 而言，它可以成為一種 **Animation LOD**：近處仍用完整 deformation，遠處改用愈來愈粗的 cage，而高密度 rest-pose geometry 本身仍可共享。

### 2. 把「動畫解析度」與「幾何解析度」分成兩個獨立維度

這是我認為比單純 ray tracing 加速更值得注意的 engine 思想。

一般模型往往默認：geometry LOD 降低，animation representation 也跟著那份 mesh 改變。但這篇暗示可以分開控制：

```text
Geometry Detail = very high
Animation Detail = medium cage
```

或：

```text
Geometry Detail = very high
Animation Detail = very low cage
```

所以一個遠處巨大生物、森林或柔性建築可以保留高頻幾何細節，同時只以很粗的 deformation field 運動。

### 3. 可作為特殊「變形空間」的 engine primitive

以下是延伸構想，不是論文已驗證的 gameplay：如果 cage 不只由骨骼動畫驅動，而由風場、物理、程序化控制或 gameplay field 驅動，同一份高密度幾何可以透過不同 coarse deformation field 產生大量 unique instances。

例如巨型草原可以讓每一區 cage 受到不同風力，而不是逐根草更新；大型生物表皮也可以讓呼吸、肌肉或衝擊先作用於 coarse volume，再由射線看到高密度表面隨空間變形。

## 想實作時再看

最小 prototype 不需要先做完整 cage generator。

可以手工建立一個立方體中的少量 tetrahedra，再放入一份高密度靜態 triangle mesh：

1. 預先計算每個 triangle 屬於哪個 tetrahedron；
2. 每個 tetrahedron 建一個 CPU mini-BVH；
3. runtime 只移動 tetrahedral vertices；
4. ray 先測 animated tetrahedron；
5. 命中後用四面體的 affine transform 把 ray 轉回 rest pose；
6. 在靜態 mini-BVH 做 triangle intersection；
7. 與直接 deform 全部 vertices + rebuild BVH 比較 update cost。

第一版甚至可以完全在 CPU 上做，先驗證「ray warping 取代 dense geometry update」這個核心資料流，再考慮 DXR / Vulkan RT。

值得優先看論文中的 tetrahedral partition、ray transformation 與 acceleration-structure layout；AMD GPUOpen 的文章則較適合先建立整體 execution flow。

## 個人筆記

這篇真正有趣的不是「5 億 triangles @ 60 FPS」這個 headline，而是它把 **geometry representation** 與 **deformation representation** 拆成兩個不同解析度的系統。

這和 virtual geometry 的思路有某種互補：virtual geometry 解決「幾何很多時怎樣只處理需要的細節」，這篇則在問「幾何很多而且會動時，是否真的需要讓每個 triangle 都參與動畫」。答案是把動畫提升成一個較粗的空間 deformation field，讓高頻 geometry 留在靜態座標系。

如果未來 cage generation、cluster acceleration structure 與 animation LOD 能整合得足夠好，它有機會成為大量動態高密度幾何的一種專用 engine representation，而不只是單篇 ray tracing optimization。
