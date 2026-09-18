---
type: article
title: "『Pokémon LEGENDS Z-A』は「1つの街」をどう描いた？ ミアレシティを支える描画技術～CEDEC 2026（2）"
published: "2026-09-17"
added: "2026-09-18"
authors:
  - "葛西 祝"
venue: "CGWORLD / CEDEC 2026"
source_url: "https://cgworld.jp/article/202609-cedec-pkmnza.html"
tags:
  - rendering
  - game-engine
  - occlusion-culling
  - instancing
  - hierarchical-z
  - screen-space-reflection
  - shadow
  - rigging
  - animation-pipeline
  - ci
  - nintendo-switch-2
  - game-freak
one_liner: "《Pokémon LEGENDS Z-A》不是追求一套甚麼場景都能用的通用技術，而是先利用「整款遊戲都在一座城市」這個限制，再為重複物件、遮蔽、水面高度、遠景陰影、角色資產和雙平台開發各自選最便宜而可控的解法。"
summary: "Game Freak 在 CEDEC 2026 說明密阿雷市的 Instanced Draw、CPU/GPU 分層剔除、Hierarchical Z、SSPR、遠距離預烘焙陰影，以及統一角色 Rig 與 Switch 2 自動建置流程。最值得理解的不是某一項新演算法，而是如何從內容與組織限制反推專用 Engine／Pipeline 設計。"
---

# 『Pokémon LEGENDS Z-A』は「1つの街」をどう描いた？ ミアレシティを支える描画技術～CEDEC 2026（2）

[TOC]

## 這篇在談甚麼

《Pokémon LEGENDS Z-A》的世界和《Pokémon Scarlet / Violet》很不一樣：它不是把玩家放進一大片自然環境，而是把整款遊戲集中在密阿雷市這一座城市。

這會直接改變場景資料的分布。城市裡有大量重複出現的街燈、長椅、煙囪，也有大量被建築物遮住、其實不需要畫到螢幕上的東西。Game Freak 因此沒有單純沿用前作的場景處理方式，而是把 **Instanced Draw（一次提交多個相同模型）** 和 **Occlusion Culling（跳過被其他物件遮住的東西）** 放到更重要的位置。

後半篇又從渲染轉到角色 Rig 與 Switch 2 開發流程。乍看是幾個不同主題，但其實有同一條工程邏輯：

> 先找出作品真正固定的限制，再把系統針對這些限制做窄，而不是先追求最通用的方案。

## 城市和自然世界的資料分布不同

### 大量重複物件：Instanced Draw

城市很容易出現數十、數百個相同模型，例如街燈、長椅和煙囪。

如果每一個物件都各自向 GPU 發出繪圖命令，CPU 會花很多時間準備重複工作。Instanced Draw 的做法，是讓同一模型共享一次繪圖命令，再為每個實例提供不同的位置等參數。

可以簡化成：

```text
一般：
Lamp A -> Draw
Lamp B -> Draw
Lamp C -> Draw

Instancing：
Lamp Mesh + [A, B, C 的 transform]
        -> 一次 Draw
```

《Z-A》比過去作品更積極使用這種方式，而且同一組物件的控制參數可以交由美術人員調整。

### 大量遮蔽：CPU 和 GPU 分工做 Culling

城市的另一個特性，是建築會遮住大量物件。

《Z-A》對不同類型物件採取不同剔除方式。Unique Model 會先在 CPU 端用包圍球等方式判斷；大量 Instance 則先由 CPU 粗略排除整個 Group，再由 GPU 對剩餘 Instance 做較細的判斷，最後用 Indirect Draw 決定真正要畫哪些實例。

概念上可以理解成：

```text
很多 Instance
    ↓
CPU：整組是否明顯不可能看見？
    ↓
GPU：組內哪些 Instance 真正可見？
    ↓
Indirect Draw
```

重點不是「GPU Culling 比 CPU Culling 新」，而是不要讓 CPU 為數千個小物件逐一支付判斷成本；CPU 做較便宜的大範圍篩選，再把大量細粒度工作交給 GPU。

## Hierarchical Z：用較粗的深度資料快速判斷遮蔽

《Z-A》的 Occlusion Culling 使用 **Hierarchical Z Culling**。

第一步先做 Depth Prepass，只把容易遮住其他東西的大型物件，例如建築，寫進深度緩衝。之後 GPU 會把這張深度圖逐級縮小，形成類似影像 Mipmap 的深度金字塔。

```text
Occluder
   ↓
Depth Buffer
   ↓
1/2
   ↓
1/4
   ↓
1/8 ...
```

遠處的小物件在畫面上只佔很少像素，因此沒有必要拿完整解析度深度圖逐點檢查；可以直接在較粗的一級深度資料上做近似判斷。

Game Freak 實測後，Unique Model 的 Occlusion Query 使用 **1/4 解析度**的 Mipmap，在效果與成本之間取得平衡。Switch 2 版本又把相關工作移到 **Asynchronous Compute（非同步運算）**，讓部分 GPU 計算不必完全堵在主要 Graphics Pipeline 上。

這裡值得記住的是：Culling 並不是追求「絕對準確地知道每一個像素會不會被遮住」，而是用足夠便宜的近似方法，快速拒絕大量不值得繼續處理的物件。

## SSPR：不把限制消掉，而是讓內容配合限制

水面反射使用 **SSPR（Screen-Space Planar Reflection）**，即螢幕空間平面反射。

和一般 SSR（Screen-Space Reflection）相比，SSPR 不需要對每個像素做相同形式的螢幕空間 Ray Marching，因此成本可以更低；和真正重新渲染一次鏡像場景的 Planar Reflection 相比，也比較輕量。

但它有一個很明顯的限制：**反射平面高度需要固定。**

密阿雷市偏偏有不同高度的河流和水池。Game Freak 沒有因此放棄 SSPR 或改做完全通用的方案，而是把水面分成三個高度群組：

```text
Water Level A -> SSPR Texture A
Water Level B -> SSPR Texture B
Water Level C -> SSPR Texture C
```

每一個水面只讀自己那一組反射。

這是一個很有代表性的專用引擎思路：

> 如果世界本身只需要少數幾種情況，就不一定值得為「任意高度的任意平面」付出通用演算法的成本。

也就是把問題從「如何消除演算法限制」改成「內容能否被約束在幾個可接受的情況內」。

## 遠距離陰影：用四張基底近似時間變化

近距離陰影使用 **CSM（Cascade Shadow Maps，分層陰影貼圖）**。它把相機附近的空間分成幾個距離區間，用不同解析度的 Shadow Map 保留近距離細節。

問題是，如果 CSM 一直覆蓋到很遠，成本與解析度都會惡化。

因此《Z-A》在數十米外改用預先烘焙的陰影。但遊戲有晝夜循環，單一靜態陰影又不夠。

Game Freak 的做法是從四個方向事先烘焙陰影，再塞進一張 RGBA Texture：

```text
R = Direction 0
G = Direction 1
B = Direction 2
A = Direction 3
```

Runtime 根據時間計算各 Channel 的權重，再把四個結果混合，近似目前太陽方向下的遠景陰影。

這可以理解為一種很簡單的「基底插值」：

```text
真正想求：
Shadow(position, sun_direction)

改成預先儲存：
S0, S1, S2, S3

Runtime：
weighted_sum(S0, S1, S2, S3)
```

它不是完整重新計算遠景光照，而是用儲存空間換每幀運算量。

同一類思路並不限於陰影。只要某個連續狀態可以由少數代表狀態合理插值，就可以考慮把昂貴計算提前做掉。

## PokeRig：生成結果不是 Source of Truth

文章後半介紹 Game Freak 的統一 Rigging System「ポケリグ（PokeRig）」。

系列長期面對幾個問題：

- Pokémon 和 Motion 的數量極大；
- 新作品會持續修改需求；
- 過去人物 Rig 與 Pokémon Rig 使用不同系統，工具、知識與維護成本分散。

PokeRig 把 Rig 拆成可配置 Module，再由 Build System 產生完整 Rig。

更重要的原則是：

> Rig 生成完成後，原則上不再由人手修改。

也就是：

```text
Rig Modules + Parameters
        ↓
Build System
        ↓
Generated Rig
```

如果結果有問題，應修改 Module、Parameter 或 Generator，而不是直接把生成結果手工修好。

這和一般程式碼生成或 Procedural Asset Pipeline 的健康做法相同：**Generated Artifact 不應變成新的 Source of Truth。**

否則很容易變成：

```text
Generator 產生 90%
↓
每個 Artist 手修 10%
↓
大量 Asset 都出現自己的例外
↓
Generator 更新後無法安全重建
```

## 不同骨架仍要重用 Motion

Pokémon 有二足、四足等不同身體結構，骨架也不完全相同。

PokeRig 透過 Rig Remapping 與中間的 Convert Scene，把來源動作映射到不同 Target Rig，使相近類型 Pokémon 可以重用 Motion。

《Z-A》進一步讓人物角色也使用 PokeRig 的共同 Workflow。人物因骨架較統一，Motion Capture 可以使用 HumanIK 轉換，不必完全照 Pokémon 的路徑處理。

這裡真正值得注意的不是 HumanIK 本身，而是 Game Freak 刻意讓：

```text
Human
+
Pokémon
↓
共同 Workflow / Dataflow
```

原因很務實：資料量足夠大時，長期維護一套共同流程，比為每類 Asset 各做一套局部最佳化工具更便宜。

## Switch 2：組織限制反過來決定 CI 架構

《Z-A》開發期間 Switch 2 尚未公開，因此不是所有 Switch 開發成員都能知道新硬體資訊。

最初只有 4 名常駐成員，加上少量需要時加入的人，在獨立上鎖的空間內維護 Switch 2 版本。甚至因為部分內部工具的管理者沒有相應權限，初期連正常使用 Confluence 都可能遇到資訊隔離問題。

這種組織限制代表少數人不可能長期用人手同步兩套專案。團隊因此把 Switch 版本當基礎，由 Script 每天自動產生 Switch 2 版本：

```text
Switch Build
   ↓
自動替換 Visual Studio Solution
   ↓
替換 Switch 2 Library
   ↓
切換 Texture Format
   ↓
套用 Platform Config
   ↓
Switch 2 Build
```

Git 也另外設定，避免 Switch 2 專屬資料誤推到一般開發環境。

Texture 則保留高解析度 Master Data：Switch 版本輸出時縮小，Switch 2 版本使用較高解析度版本。

Switch 2 版本另外加入 60 FPS、DLSS 與 SSAO。這些是硬體能力增加後的品質提升，但更值得注意的是：**平台差異盡量被寫成可以由機器處理的規則，而不是依賴少數人每天手工維護。**

## 整篇最值得記住的工程模式

單獨看，Hierarchical Z、Instancing、CSM、SSPR、Rig Retargeting、CI 都不是新發明。

這篇真正有價值的是它們被選中的理由：

| 現實限制 | 對應做法 |
| --- | --- |
| 城市有大量相同物件 | 更積極使用 Instanced Draw |
| 建築會遮住大量場景 | CPU / GPU 分層 Culling + Hierarchical Z |
| 水面只有少數高度 | 不做任意平面反射，分三組 SSPR |
| 遠景陰影不值得完整動態計算 | 四方向預烘焙結果做時間插值 |
| Pokémon 與 Motion 數量巨大 | Rig Module 化、統一 Build System |
| 不同骨架仍需共用動作 | Rig Remapping / Retargeting |
| 少數人才能接觸 Switch 2 | 把平台差異自動化到 CI |

可以把這套思路概括成：

```text
Content / Production Constraint
            ↓
找出真正的資料分布與固定條件
            ↓
針對條件選 Algorithm / Tool
            ↓
接受合理限制
            ↓
把成本留給真正需要的地方
```

這和追求「一套能處理任何情況的 General Solution」是不同方向。

## 閱讀時需要知道的前提

這篇是 CGWORLD 對 CEDEC 2026 Session 的公開整理，不是完整技術論文。文章沒有公開：

- Renderer 的完整架構；
- GPU Frame Breakdown；
- Hierarchical Z 的 Shader 與 Buffer Layout；
- SSPR 的完整演算法細節；
- PokeRig 原始碼；
- Switch / Switch 2 CI Script。

因此可以從中學習**問題如何拆分與技術如何選擇**，但不能只靠這篇重做 Game Freak 的實作。

另外，SSPR、Hierarchical Z、CSM 等技術本身並非《Z-A》發明；真正值得注意的是 Game Freak 如何依密阿雷市這個特殊世界結構組合它們。

## 我的筆記與延伸

我最想留下的是一個看似很樸素的原則：

> **專用 Engine 的優勢，不一定是它擁有比通用引擎更高級的演算法，而是它可以承認「我們的遊戲根本不需要處理所有情況」。**

例如水面反射，如果引擎知道整款遊戲只需要三個主要水位，就可以接受「只有三組 SSPR」這個很窄的答案。

同樣地，遠距離陰影也不必因為有晝夜循環，就直接推導成「所有遠景都需要完整 Dynamic Shadow」。四個預烘焙方向加插值，已經足以滿足畫面目的。

這類設計很適合在自己的 Engine 中反覆問：

1. 這個系統真正會遇到多少種資料？
2. 哪些自由度只是理論上存在，遊戲其實不需要？
3. 如果把那些自由度拿掉，可以換回多少效能、工具簡單度或可預測性？
4. 未來如果真的需要更一般的情況，再擴張是否仍然可行？

另一個值得留下的是 PokeRig 的 Source-of-Truth 原則。任何 Procedural Tool 一旦允許使用者在生成結果上長期手修，就會逐漸失去「可重建」能力。生成器真正成熟的標誌，不只是第一次可以產生結果，而是**你敢隨時刪掉生成結果，再由原始定義完整重建一次。**

## 來源

- [『Pokémon LEGENDS Z-A』は「1つの街」をどう描いた？ ミアレシティを支える描画技術～CEDEC 2026（2）](https://cgworld.jp/article/202609-cedec-pkmnza.html)
- 原文整理自 CEDEC 2026 Session「ミアレシティがメガシンカ!? 『Pokémon LEGENDS Z-A』の描画技術」
