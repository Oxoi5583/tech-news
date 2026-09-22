---
type: paper
title: "STRIDER: Stepping-Enabled Multi-Gait Hierarchical 3D Loco-Manipulation Framework for Humanoid Robots"
published: "2026-09-20"
added: "2026-09-23"
authors:
  - "Yuanzhuo Li"
  - "Wen Zhao"
  - "Zhe Yong"
  - "Xiang Meng"
  - "Gang Han"
  - "Hengle Ren"
  - "Xiaoyang Zheng"
  - "Zhen Wang"
  - "Yijie Guo"
venue: "arXiv; submitted to ICRA 2027"
paper_url: "https://arxiv.org/abs/2609.23483"
code_url: ""
tags:
  - humanoid
  - locomotion
  - whole-body-control
  - reinforcement-learning
  - foothold-planning
  - robotics
one_liner: "讓同一個人形角色既能自然連續走路，也能在需要時精確指定每一腳踩在哪裡，並同時控制上半身做操作動作。"
summary: "STRIDER 把自然行走、精確踏步與上半身笛卡爾控制拆成專長不同的控制器，再用帶潛在表示對齊的策略蒸餾，把多種步態能力合併進單一可執行策略。它在 TianGong Omni 人形機器人的模擬與實機上驗證，適合思考機甲或角色如何從一般移動平滑切換到需要精確落腳的互動。"
---

# STRIDER: Stepping-Enabled Multi-Gait Hierarchical 3D Loco-Manipulation Framework for Humanoid Robots

## 先用一個例子理解

想像一台人形機甲平常只需要朝搖桿方向自然走路，但來到碎石、窄樑或高低差時，遊戲不再只需要「往前走」，而是需要明確要求左腳踩在某一塊安全位置；同時雙手仍可能要舉槍、搬物或抓住扶手。

這三件事通常不是同一種控制問題：自然走路適合用連續速度命令，精確踏步需要指定 foothold（下一隻腳真正要落下的位置），上半身操作又常以手部的笛卡爾空間位置與姿態為目標。STRIDER 的核心不是發明另一個單一步行策略，而是建立一個能把這些異質技能合併起來的分層控制架構。

## 原本的做法有甚麼困難

只輸入前後左右速度的 locomotion policy 很適合一般行走，卻很難要求「右腳必須踩在這個 3D 點」。反過來，專門追蹤 foothold 的 stepping controller 可以精確踏步，但通常不容易同時保持自然連續行走與 whole-body manipulation。

另一個問題出現在策略蒸餾。若先訓練數個專家，再讓單一 student 模仿它們的 action，student 可以學到表面輸出，卻不一定形成能跨技能共用的內部表示；兩種控制模式的切換與泛化因此仍可能很差。

## 它是怎樣做到的

STRIDER 先保留不同控制問題最適合的表示，而不是強迫所有行為都變成同一種 command。

自然行走使用基於 Adversarial Motion Priors（以參考動作分布約束策略，使運動保持類似自然動作）的 walking expert。需要精確踩點時，stepping expert 則在 stance-foot frame，也就是以目前支撐腳為局部座標系，選擇可行的 3D 落腳點，再產生考慮地面高度與腳部離地間隙的 swing trajectory。上半身另外接受 Cartesian control，使手部／身體操作目標不必被硬塞進腳步命令。

真正的新方法集中在 LD-PPO（Latent Distillation Proximal Policy Optimization）。作者不只讓 student 重建 teacher action，而是同時加入三條學習訊號：

1. on-policy reinforcement learning：student 自己在環境中執行並依任務結果更新；
2. DAgger-based action reconstruction：在 student 實際走到的狀態上取得 teacher 行為，減少只模仿 teacher 軌跡造成的 distribution shift；
3. teacher-conditioned latent alignment：要求 student 的內部 latent representation 與對應 expert 的表示對齊。

因此蒸餾目標從「同一個 state 輸出同一個 action」提升為「讓 student 也學會多種 expert 在內部如何表示控制問題」。

## 與現有方法的差別

最值得注意的不是某一個 RL loss，而是 command space 的分層：一般移動仍可用高層速度意圖；只有在地形或玩法需要時，才切到明確 foothold；上半身操作則保持自己的 Cartesian target。這比要求單一低階介面同時承擔導航、腳步規劃和操作更容易保留每種技能的可控性。

LD-PPO 相對普通 action-only distillation 再多保留一層「技能表示」。這使 walking expert 與 stepping expert 不只是被壓成一張輸入輸出表，而是嘗試讓 student 建立共享的技能空間。

## 實驗結果與限制

作者在 TianGong Omni humanoid 上做模擬與實機驗證。論文報告 LD-PPO 相較 vanilla distillation-PPO 有較好的 foothold tracking 與 posture tracking，並展示真實硬體上的多步態 loco-manipulation、精確落腳與 end-effector tracking。

目前公開摘要沒有提供足夠條件讓不同遊戲或機器人 controller 做公平的毫秒級 benchmark，因此不應把這篇理解成「某種 locomotion 快多少」。它驗證的是控制架構與蒸餾方法能否把異質技能放進同一策略。

限制也很重要：這仍是針對特定 humanoid morphology 與訓練分布得到的 learned controller；論文展示的地形感知踏步並不等於一般用途的全域 footstep planner，也沒有證明任意角色骨架可以直接套用。arXiv 版本目前標示為 submitted to ICRA 2027，尚不是已完成同行評審的正式會議版本。

## 可以怎樣用在遊戲裡

最值得移植的未必是整套神經網路，而是把 locomotion command 分成不同精度層級：

```text
玩家／AI 移動意圖
        |
        +-- 一般地面 --> velocity locomotion
        |
        +-- 精確互動 --> explicit foothold
        |                  |
        |                  +-- 跨石頭
        |                  +-- 踩窄樑
        |                  +-- 避開陷阱
        |                  +-- 抵抗外力
        |
        +-- 上半身 ----> Cartesian manipulation target
```

對機甲尤其有意思。角色不必永遠以動畫系統假裝「腳踩到地面」；世界可以在需要時把特定接觸點提升成真正的 gameplay constraint。例如踩在移動載具、殘骸或不穩定地形時，AI 或玩家高層只決定目標，低階 whole-body controller 負責把身體重新協調到能實際完成那一步。

這部分屬於遊戲引擎延伸，而不是論文已驗證的遊戲用途。

## 想實作時再看

最小 prototype 不需要先訓練完整 humanoid。可以用一個簡化雙足角色做兩個 expert：

- Walking expert：輸入 `(vx, vy, yaw_rate)`；
- Stepping expert：輸入下一個左右腳的 `(x, y, z)` target。

先確認兩者各自能完成任務，再做 student distillation。第一版只比較 action reconstruction；第二版才加入 teacher latent alignment，觀察在 walking / stepping 切換附近的 foot error、body orientation error 與 failure rate 是否改善。

閱讀時最值得抓住三個部分：terrain-aware stepping 如何在 stance-foot frame 建立落腳命令、不同 expert 的 observation/action interface 如何統一，以及 LD-PPO 的 latent alignment 如何與 PPO、DAgger loss 一起訓練。

## 個人筆記

這篇最有價值的觀念是「自然移動」與「精確接觸」不必二選一。遊戲角色平常可以保持容易操作的 velocity-level control，但當世界幾何真的重要時，engine 可以暫時把腳掌接觸升格為明確控制目標。

如果要做機甲專用 locomotion system，我會優先研究這種 hierarchical interface，而不是一開始就追求端到端 policy。它讓 gameplay system 仍能明確說出「我要踩這裡」，而低階 controller 才負責解決如何用整個身體做到。這種責任分層比完全黑箱的 locomotion 更容易和遊戲規則、動畫與 AI 整合。
