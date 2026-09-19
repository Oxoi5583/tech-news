---
type: paper
title: "Adaptive-MHE: A Sampling-Based Adaptive MPC for Legged Loco-Manipulation via Moving Horizon Estimation"
published: "2026-09-15"
added: "2026-09-19"
authors:
  - "Hossein Keshavarz"
  - "Alejandro Ramirez-Serrano"
  - "Majid Khadiv"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2609.17832"
code_url: ""
tags:
  - robotics
  - locomotion
  - system-identification
  - model-predictive-control
  - contact-dynamics
  - mech-simulation
one_liner: "讓機器在互動途中自己試出物體有多重、地面有多滑，再立刻用新的物理估計調整下一步動作。"
summary: "這篇把移動視界估計與取樣式模型預測控制結合：持續保留最近一小段真實互動紀錄，並用大量候選物理參數重播這段運動，找出最能解釋觀察結果的質量、慣量與摩擦係數。方法不要求接觸模擬器可微分，適合碰撞與摩擦頻繁、物理參數又會改變的系統。"
---

# Adaptive-MHE: A Sampling-Based Adaptive MPC for Legged Loco-Manipulation via Moving Horizon Estimation

[TOC]

## 先用一個例子理解

想像一台四足機器推箱子。控制器原本以為箱子重 10 kg、地面摩擦係數是 0.8，但實際箱子更重，而且走到另一區後地面突然變滑。

固定參數的控制器仍會按照舊模型出力，因此可能推不動、腳打滑，甚至失去平衡。

Adaptive-MHE 的做法不是事先要求遊戲或感測器直接告訴控制器「這裡的摩擦係數是多少」，而是觀察最近幾秒：我剛才用了這些關節命令，機器與箱子實際上卻這樣移動。接著在背景中試很多組候選的質量、慣量與摩擦係數，看哪一組重新模擬後最接近剛才真正發生的軌跡。

找到較合理的物理參數後，下一輪控制便直接使用新模型。

因此它形成一個循環：

```text
實際互動
  ↓
保存最近一段 state + action
  ↓
用不同候選物理參數重播
  ↓
找出最能重現觀察軌跡的參數
  ↓
更新控制器的 dynamics model
  ↓
下一次動作
```

## 原本的做法有甚麼困難

機器人控制常假設物體質量、慣量、馬達特性與地面摩擦等參數已知。但 contact-rich 系統的麻煩正是：這些參數往往不知道，而且接觸會不斷出現、消失。

傳統 system identification（系統識別，即從輸入與實際運動反推物理模型）常依賴 dynamics 的導數。碰撞、摩擦與 contact switching 卻具有不連續性，因此很難直接套用這類梯度式方法。

另一條路是 sampling-based identification：不求導數，直接猜很多組參數，把每一組都丟進 simulator 跑一次，再比較誰最像真實軌跡。這很適合平行運算，但過去相關方法主要是離線辨識：收集資料、辨識一次、之後才使用。當地面或物體在任務途中改變，舊估計又會失效。

## 它是怎樣做到的

### 1. 把未知物理量當成要搜尋的參數

系統使用同一個參數化 dynamics model：

```text
x(t+1) = f(x(t), u(t), θ)
```

`x` 是機器與物體狀態，`u` 是控制輸入，`θ` 則是未知物理參數，例如物體質量、慣量與地面摩擦。

### 2. 只看最近的一段歷史

Moving Horizon Estimation（移動視界估計）不是把整場任務從頭重算，而是維持一個 sliding window：

```text
舊資料 ────────────── 現在
          [ 最近 H 步 ]
                 ↑
              estimator
```

每隔一段時間，window 向前移，只用最近的 interaction data 重新估計。這使模型能追蹤「剛才是粗糙地面，現在變成低摩擦表面」之類的變化。

### 3. 用模擬重播代替微分

對每組候選 `θ`，從記錄中的狀態開始，以同一批實際控制輸入進行 rollout，再計算模擬軌跡與觀察軌跡的差距。

論文建立在 Sampling-based Parameter Identification（SPI）之上；候選參數分布以 CMA-ES 類型的零階搜尋逐輪改善。這裡「零階」的重點是只需要問 simulator「這組參數跑出來有多錯」，不需要 simulator 提供梯度。

因此碰撞與摩擦即使難以微分，仍然可以參與辨識。

### 4. 辨識與控制非同步運作

Adaptive-MHE 的 estimator 與 whole-body controller 分開運行。控制器持續產生即時動作；較低頻的背景 estimator 定期更新物理參數，再把新估計交給控制器。

論文的 whole-body controller 使用 sampling-based Model Predictive Control（模型預測控制，即預先模擬多個未來動作序列並選較好的方案）。控制側還利用步態 contact mode 的週期性，只在接觸模式改變時進行較昂貴的多輪 refinement，其餘週期沿用上次 sampling distribution 作 warm start。

## 與現有方法的差別

真正重要的改變不是單獨發明另一種 MPC，而是把兩個 sampling loop 接起來：

```text
外界真正發生甚麼？
        ↓
Sampling-based MHE
        ↓
目前最合理的 physics parameters
        ↓
Sampling-based MPC
        ↓
接下來應該怎樣動？
```

傳統 domain randomization 通常在訓練階段讓 policy 看過很多物理條件，但部署後不一定知道現在到底是哪一種條件；固定 model-based controller 則直接假設參數已知。

Adaptive-MHE 相反地把「理解現在世界的物理參數」本身放進 runtime control loop，而且因為採取 sampling-based system identification，不要求 contact dynamics 可微分。

## 實驗結果與限制

作者在 simulation 與硬體實驗中測試未知物體與地面條件，包括物體質量變化及 terrain friction 改變。論文報告 Adaptive-MHE 持續優於不進行同等線上適應的 baseline，並可接近直接取得 ground-truth 物理參數之 controller 的表現。

這裡要注意幾個限制：

- 這不是任意材質的完整物理重建；只能辨識事先放進參數化 dynamics model 的物理量。
- 某個參數是否能被辨識，取決於最近的動作有沒有提供足夠資訊。例如完全沒有滑動時，摩擦係數可能很難精確判斷。
- sampling 的成本會隨參數維度、horizon 與候選數增加；論文藉由非同步低頻 estimator 避免阻塞高頻控制 loop。
- 論文目前是 robotics research，而不是遊戲引擎 production system。

## 可以怎樣用在遊戲裡

論文驗證的是機器人對未知真實物理條件的在線適應；以下是遊戲引擎方向的延伸構想。

### 機甲不必直接讀取地面的「正確答案」

一般遊戲 AI 或控制系統可以直接查：

```cpp
float friction = terrain.GetFriction(position);
```

但如果機甲控制器反而只能從自己的 actuator、IMU、腳部滑移與機身運動推測環境，操控模型會變成：

```text
踩下去
 ↓
預期腳應移動 2 cm
 ↓
實際滑了 12 cm
 ↓
背景 physics estimator：這裡可能很滑
 ↓
控制器縮短步幅 / 改變姿態 / 改變力矩
```

這會讓「地面材質」不再只是角色移速 modifier，而成為機體需要透過互動逐步理解的世界性質。

### 動態 payload 與損傷

同一概念亦可以放在機甲自身：拿起未知重物、武器被破壞、腿部結構受損或重心偏移後，不必替每種狀態手寫一套 animation/controller，而讓控制系統根據近期 motion error 重新估計有效質量、重心或 actuator response。

這不是論文已驗證的遊戲玩法，但它提供了一個很有意思的 engine 思路：**controller 使用的 physics model 本身也是 runtime state，而且可以由互動反推。**

## 想實作時再看

最小 prototype 不需要先做完整四足機器人。可以用一個簡單的 2D rigid body + 推力器：

1. simulator 內真正質量設為 15 kg，但 controller 初始模型假設 10 kg；
2. 保存最近 1–2 秒 `(state, action)`；
3. 每隔 0.5 秒產生例如 64 組候選質量；
4. 每組從 window 起點重播相同 action；
5. 用位置、速度誤差選出最佳候選；
6. controller 下一輪 prediction 使用新質量。

確認質量能在線收斂後，再加入 friction，最後才加入 articulated body 與 contact switching。

閱讀時最值得先看論文 Section III 的 sampling-based parameter identification，再看 Section IV 的 moving-horizon estimator、非同步資料流及 Algorithm 1。真正值得抄的不是特定四足機器人的 reward，而是「最近 observation → parallel hypothetical rollouts → parameter estimate → predictive controller」這條 runtime pipeline。

## 個人筆記

這篇對遊戲最有價值的地方，不是讓 NPC 變成機器人研究 demo，而是提供另一種思考 physics API 的方式。

通常 engine 把世界物理狀態視為 authoritative truth：controller 想知道甚麼便直接讀甚麼。但對機甲、載具或需要強烈操控感的角色，可以刻意分成兩層：世界有真正 physics state，而機體只有自己的 estimated physics state。

兩者之間的誤差便會自然產生試探、適應、失誤與重新控制。若配合 granular terrain、可變形地面或 actuator simulation，這可能比單純提高動畫精度更能形成一套專用 mech engine solution。
