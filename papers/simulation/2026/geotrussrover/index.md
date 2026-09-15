---
title: "GeoTrussRover: Morphological Computation with Contact-Semantic Control Primitives"
published: "2026-09-10"
added: "2026-09-15"
authors:
  - "Muyuan Ma"
  - "Yi Zhang"
  - "Yang Yang"
  - "Xuanyan Zheng"
  - "Ruiqi Hu"
  - "Boxuan Ke"
  - "Zhenyu Chen"
  - "Yicong Lin"
  - "Xin Hao Yang"
  - "Daliang Xiao"
  - "Zhinan Hou"
  - "Wanhao Niu"
  - "Yuan Sun"
  - "Yan Yang"
  - "Yue Xie"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2609.11361"
code_url: ""
tags:
  - reconfigurable-robotics
  - morphology
  - locomotion
  - control
  - robotics
  - mech-simulation
summary: "把可變形機體本身當成 locomotion primitive：先用接觸階段描述『整台機器應該變成甚麼形狀』，再由約束求解器計算各 actuator 的實際動作。"
---

# GeoTrussRover: Morphological Computation with Contact-Semantic Control Primitives

## 解決甚麼問題

可變形機器人遇到固定車體無法跨越的障礙時，可以改變整個承重結構的形狀。但當一台機器有大量可伸縮結構件、輪子與接觸點時，直接每次重新規劃所有 actuator trajectory 會變成高維度而昂貴的問題。

GeoTrussRover 使用 Variable-Geometry Truss（VGT）作為可承重、可變形的車體，並嘗試回答：**能否把「整台機器如何變形」壓縮成少量可重用的 locomotion primitive？**

## 核心做法

系統先對一個已知障礙完整求解一次 traversal，再從解中抽出四個 contact-semantic primitives。

這些 primitive 不是直接記錄 21 個結構件在每個時間點應伸長多少，而是描述不同接觸階段中，機體各部分需要完成的協同功能。

可以簡化成：

```text
Obstacle
   ↓
Contact phase
   ↓
Morphology primitive
   ↓
Physics-constrained projection
   ↓
21 truss members + wheels
```

如果新障礙高度不同，但接觸拓撲仍相同，系統就把舊 primitive 投影到新的幾何與物理約束上，不必重新規劃整段動作。

如果只有某一個 phase 在新條件下失去可行性，就只重新求解那一段。最後再使用 full-space QP 去追蹤目標並修正 truss members 與 wheel errors。

## 與現有方法的差別

最直接的做法是每遇到一個新障礙，就在完整 actuator space 中重新 optimization：

```text
21 members + wheels
        ↓
full trajectory optimization
        ↓
完整新動作
```

GeoTrussRover 把問題拆成：

```text
高維機體
   ↓
少量 contact-semantic phases
   ↓
低維 morphology primitive
   ↓
再映射回完整 actuator space
```

也就是說，它不是把「動作」儲存成固定動畫，而是儲存一種可適應新幾何的協同策略。

這個差異對遊戲特別重要：機體不需要為每個障礙高度準備一條 animation clip，也不必每次從零開始求整段 trajectory。

## 實驗結果與限制

論文中的系統有 21 個 VGT structural members，並與 wheeled base 協同控制。

在把 0.10 m 階梯的 source traversal 轉移到 0.075 m 階梯時，相較完整重新求解，objective-function evaluations 減少約 63.7%。

作者分析的可行 step height 約為 0.10–0.46 m，亦即 1.08–4.97 個 wheel radii；實際電動 prototype 成功跨越約 2.11 wheel radii 的高度。

限制包括：

- 目前 primitive 仍針對特定 VGT + wheel morphology 設計，不是通用機甲控制器。
- 「相同 contact topology」時最容易重用；遇到完全不同的障礙類型仍可能需要新 source solution。
- 需要 physics-constrained projection 與 full-space QP，因此不是單純播放一段參數化動畫。
- 真正大型、重型機甲的 inertia、actuator limits、碰撞與結構負載會令問題複雜很多。

## 對遊戲開發的用途

最值得移植的概念是：**形態本身也可以是一種 locomotion vocabulary。**

一般機甲移動系統通常把 locomotion 想成腿或輪子的 trajectory；但如果機體可以改變：

- 腿長
- 車體高度
- 肩部支架
- 履帶／輪子位置
- 軀幹長度與俯仰
- 額外支撐臂

那麼跨越障礙可以先描述成「需要甚麼 contact pattern 和 body shape」，再由底層控制器決定每個 actuator 怎樣配合。

例如：

```text
高牆
 ↓
前方先建立支撐
 ↓
軀幹拉長 + 前輪／前腳抬高
 ↓
重心移到前支撐
 ↓
後半部收縮並越過障礙
```

這會比 `PlayClimbAnimation()` 更像真正的機械系統，而且可以自然支援不同障礙尺寸。

如果和 granular-contact、whole-body control、actuator power / heat system 結合，機體形態甚至可以因地形與負載而改變，令「機甲設計」本身直接進入玩法。

## 個人筆記

這篇最有價值的部分，不是 VGT 這種特定機器，而是 **先用低維的 contact / morphology 語意描述策略，再由約束系統展開成完整 actuator motion** 的架構。

一個最小 2D prototype 就足夠驗證：

1. 建四個節點、4–6 條可伸縮 truss 和兩個 wheel/contact points。
2. 手工定義 `Approach`、`FrontSupport`、`RearLift` 三個 contact phases。
3. 每個 phase 只存 body pitch、前後高度、wheel load ratio 等低維目標，不存每條 actuator trajectory。
4. 根據障礙高度，用 constrained solver 算出實際 member lengths。
5. 比較不同 step height 是否可以重用同一組 morphology primitives。

如果同一套 phase 可以自然跨越不同高度，而不需要每次重寫動畫或完整重規劃，就已經證明這個方向對可變形機甲很有價值。
