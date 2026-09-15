---
title: "Learning Terrain-Adaptive Humanoid Locomotion on Granular Terrain"
published: "2026-09-09"
added: "2026-09-15"
authors:
  - "Junnosuke Kamohara"
  - "Feiyang Wu"
  - "Andy Ningan Zong"
  - "Daniel I. Goldman"
  - "Yashwanth Nakka"
  - "Seth Hutchinson"
  - "Ye Zhao"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2609.10286"
code_url: ""
tags:
  - granular-material
  - contact-physics
  - locomotion
  - robotics
  - real-time
  - mech-simulation
summary: "以 3D Resistive Force Theory 建立比完整顆粒模擬便宜得多、但仍能表現下陷與方向性阻力的地面接觸模型，讓角色或機甲真正受到沙地、鬆散地面的物理影響。"
---

# Learning Terrain-Adaptive Humanoid Locomotion on Granular Terrain

## 解決甚麼問題

遊戲和一般機器人模擬常把沙地、泥地簡化成「硬地面 + 較低摩擦力」。這種做法不會真正表現腳掌下陷、不同移動方向造成不同阻力，以及腳掌角度改變受力等現象。

另一個極端是使用 MPM、DEM 等方法直接模擬大量顆粒或連續介質，但成本通常太高，不適合大量角色、強化學習訓練，或一般遊戲 runtime。

這篇工作的核心目標，就是找一個介乎兩者之間的模型：**不要真的模擬每粒沙，但仍然讓接觸力像沙一樣。**

## 核心做法

方法使用 3D Resistive Force Theory（3D RFT）估計腳掌在顆粒材料中的局部阻力。

可以簡化理解成：把腳掌表面切成很多小 sample，每個 sample 根據以下資料計算局部受力：

- 插入地面的深度
- 接觸面的方向
- 腳掌移動方向與速度
- 顆粒材料的密度與內部摩擦特性
- 重力方向

每個 sample 算出局部阻力後，再把所有力與力矩累加，得到整隻腳的 6D contact wrench：

```text
Foot surface samples
        ↓
penetration / direction / material
        ↓
3D RFT local forces
        ↓
sum forces + moments
        ↓
whole-body dynamics
```

這個設計很重要，因為 articulated-body solver 不必直接處理大量細碎接觸點；它只需要接收每隻腳最後的總合力和總力矩。

論文另外使用 teacher-student reinforcement learning，讓角色只靠自身關節、IMU、上一動作等 proprioception history，估計腳下地形的性質並調整步態。

## 與現有方法的差別

最簡單的 rigid-contact 方法通常只是：

```text
不能穿地
+ normal impulse
+ Coulomb friction
```

這不能正確表現顆粒材料的 penetration 與 directional drag。

完整 MPM 雖然能模擬更真實的顆粒／連續介質行為，但成本高很多。

3D RFT 的定位則是：

```text
Rigid contact      3D RFT                 MPM / DEM
很便宜       ←      中間層      →       高精度、高成本
很粗糙             保留主要接觸物理          更完整
```

因此它很適合作為 gameplay physics 的專用地面模型，而不是視覺粒子模擬。

## 實驗結果與限制

作者使用 NVIDIA Newton 的 MPM 作為較高 fidelity 的比較基準。3D RFT 在撞入顆粒地面時，對下陷距離、水平移動以及地面反作用力都比簡化 heuristic 模型更接近 MPM。

在 deep-sand 測試中，使用 3D RFT 訓練的 humanoid policy 成功率約 85%，而兩個簡化 granular baseline 約為 3% 與 8%。作者亦在 Unitree G1 上測試 basalt、dry sand 與 beach sand，證明這不是只在模擬器中有效。

論文使用 NVIDIA Warp 實作 granular contact，可在 RTX 4090 上支援大量平行模擬；訓練時使用 4096 個 agents。

限制包括：

- 3D RFT 仍然是 reduced contact model，不是完整顆粒流動模擬。
- 它主要描述物體和顆粒地面的受力，不等於會自然產生高品質的沙堆、坑洞與長期地形變形。
- 若要讓地面外觀也永久改變，仍需要另外的 terrain state / deformation representation。
- 論文重點是 humanoid locomotion；重型機甲、輪胎、履帶需要重新驗證參數與尺度。

## 對遊戲開發的用途

最直接的用途是把「地面材質」由一個 friction 數值升級成真正的 contact model。

例如重型機甲踩進泥地時，不再只是：

```cpp
moveSpeed *= 0.8f;
```

而可以變成：

```text
右腳陷得較深
    ↓
右腳阻力增加
    ↓
機體向右偏
    ↓
姿態控制器補償
    ↓
能源消耗增加、轉向變慢、開炮穩定性下降
```

因此沙、泥、雪、火山灰、碎石等地面可以真正改變機體控制感，而不是只換貼圖和移動速度倍率。

它亦可以與 whole-body control、actuator simulation、damage system 結合。腳掌面積、機體重量、腿部輸出、姿態控制能力都會自然影響通過軟地的能力，令「機體設計」和「地形」真正互相作用。

## 個人筆記

這篇最值得拿走的不是 RL，而是 **RFT 作為中階 gameplay physics representation** 的概念。

一個最小 prototype 可以完全不做 AI：

1. 建一塊平面和一隻 rectangular foot。
2. 在腳掌放 16–64 個 surface samples。
3. 每個 sample 根據 penetration depth、velocity direction、surface orientation 計算 RFT force。
4. 累加成總力與力矩。
5. 與普通 spring + Coulomb friction 比較 vertical drop、horizontal drag、斜向拖動與不同腳掌角度。
6. 第二階段再接一條 2-link leg + PD controller。

如果 prototype 中「同一條腿在硬地、沙地、泥地上自然產生不同姿態與能耗」，就已經證明這套 representation 對遊戲有價值。

Project page: <https://humanoid-gm-locomotion.github.io/HUMANOID-GM/>
