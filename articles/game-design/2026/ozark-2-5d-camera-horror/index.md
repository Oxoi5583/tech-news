---
type: article
title: "OZARK: Creating a Dark Story-Driven 2.5D Action-Horror Game"
published: "2026-09-22"
added: "2026-09-23"
authors:
  - "Alter-Boy"
  - "David Jagneaux (interviewer)"
venue: "80 Level"
source_url: "https://80.lv/articles/ozark-creating-a-dark-story-driven-2-5d-action-horror-game"
tags:
  - game-design
  - 2.5d
  - camera
  - horror
  - readability
  - level-design
  - lighting
  - indie-development
  - co-op
  - unity
one_liner: "《OZARK》把固定 2.5D 鏡頭同時當成構圖工具與遊戲規則：鏡頭限制玩家能看見甚麼，也因此必須連同瞄準、敵人行為、恐怖感與資訊可讀性一起設計。"
summary: "Alter-Boy 回顧《OZARK》如何從一個 2.5D 技術實驗長成 3–6 小時的動作恐怖遊戲。最值得讀的是固定鏡頭如何向下影響瞄準、AI、公平感、合作模式與場景構圖，以及小團隊為何選擇熟悉的 Unity Built-in Pipeline 而不是追逐較新的渲染技術。"
---

# OZARK: Creating a Dark Story-Driven 2.5D Action-Horror Game

## 這篇在談甚麼

《OZARK》最初不是先有完整故事，再決定用甚麼形式呈現。它起源於一個很小的技術實驗：鎖定鏡頭、讓角色主要橫向移動，但又保留一定的景深方向移動，看看這種 2.5D 射擊遊戲是否成立。之後故事、世界、美術與系統才逐步圍繞這個形式生長。

這令文章最有價值的地方不是某項單獨技術，而是展示一個看似簡單的形式限制——固定的 2.5D 鏡頭——如何一路滲透到 Level Design、瞄準、Enemy AI、恐怖感、合作玩法與畫面可讀性。

## 固定鏡頭既是優勢，也是整套遊戲的約束

固定視角最大的優勢是構圖。團隊可以像電影鏡頭一樣安排場景：移動 Camera、燈光與 Props，反覆實際遊玩，直到畫面中的事件在特定 Frame 裡形成想要的效果。環境也不是單向服務劇本；實作中的空間可以反過來改變寫作，劇情亦會要求團隊重新修改場景。

但只要玩家不再被限制在一條完全平面的線上，2.5D 就立刻出現額外問題。

在純粹側向平面中，射擊大致只需要處理左右方向與少量垂直角度；一旦角色可以向畫面深處移動，瞄準其實已經重新變成三維 Target Selection 問題。團隊最初以 Controller 為主，建立適合手掣的 Target Lock；Steam Next Fest 後因玩家要求加入 Mouse / Keyboard，又必須支援更接近 Point-and-click 的瞄準方式。於是同一套戰鬥實際上需要容納兩種不同的輸入語意。

Enemy AI 亦不能獨立於 Camera 設計。敵人多久可以進入畫面？畫面外的敵人可以施加多少壓力？能否在玩家看不見的位置投擲手榴彈？這些都不是單純 AI 強弱，而是玩家是否能取得足夠資訊作出反應的問題。

可以把它理解成：

```text
Camera / Visible Region
        ↓
玩家可以取得的資訊
        ↓
Aiming + Reaction Window + Enemy Behaviour
        ↓
玩家判斷「緊張」還是「遊戲在作弊」
```

因此固定鏡頭不是 Presentation Layer；它實際上成為 Gameplay Rule 的一部分。

## 恐怖不一定來自剝奪玩家能力

《OZARK》讓玩家持槍，而且角色並不無力。團隊沒有把「玩家能戰鬥」視為恐怖感的反面，而是把恐怖來源轉移到局面的不穩定性。

玩家會流血、武器需要 Reload；不同敵人會疊加不同壓力，一個小失誤可能迅速把場面推向失控。團隊對這種狀態的概括很精確：玩家應該感覺「我能打贏它」，而不是「我在這裡很安全」。

也就是：

```text
Capability != Safety
```

這與常見的 Survival Horror 做法有一點不同。恐怖不一定要靠拿走武器、降低彈藥或把角色做得遲鈍；也可以讓玩家擁有充分的 Action Capability，但讓系統狀態快速變化，使玩家無法把「有能力」轉換成「有控制感」。

## Readability 不是越高越好

團隊花了大量時間處理 Lighting、Post-processing、Fog、Color Correction 與 Camera，但他們並不追求完美可讀性。

原因很簡單：恐怖需要一定程度的不確定。如果每個敵人都有極亮 Rim Light，玩家會更容易辨認威脅，但場景原本建立的黑暗與不安亦會消失。

所以《OZARK》不是用單一強 Cue 把敵人從背景切出來，而是疊加多個較弱訊號：橙色衣服、Silhouette、局部 Contrast、Lighting、Environment Composition 和 Camera Framing。

這形成一個值得保留的設計問題：

```text
Readability ↑
通常會令操作公平感 ↑

但在 Horror 中：
Uncertainty ↓
可能令恐怖感 ↓
```

因此目標不是最大化 Readability，而是找到「玩家沒有完全看清，但仍然相信自己有合理機會反應」的位置。

文章給出的 Off-screen Enemy 是很好的例子：畫面外突然出現威脅可以非常緊張；但如果玩家認為自己根本沒有可能預測或反應，完全相同的事件就會由恐怖變成挫折。

## Co-op 的 Camera Mode 本身會改變玩家關係

團隊最後建立三種合作遊戲 Camera：永久 Split Screen、兩人靠近時共享而分開後動態 Split，以及強制所有玩家留在同一畫面的 Single Camera。

這三種模式不是純粹 UI 選項。強制共享畫面會壓縮兩人的活動空間，玩家必須協商移動；Dynamic Split 增加獨立探索能力；Permanent Split 則給予最高的個人自主性。

換句話說：

```text
Camera Policy
    ↓
Spatial Freedom
    ↓
玩家需要協調的程度
    ↓
Co-op 的社會體驗
```

這是一個很容易被忽略的關係：Camera System 可以直接成為 Multiplayer Design。

團隊亦刻意避免為合作模式加入大量「兩人站不同開關」式的專用關卡，因為 Solo Play 仍然必須完整成立。網路合作則沒有自己實作傳統 Networking，而是以 Local Co-op 為核心，再利用 Steam Remote Play Together 把本地畫面串流給另一位玩家。這是一個很典型的小團隊 Scope Decision：不是每個想提供的使用情境都需要自己擁有整套底層系統。

## 小團隊不一定應追逐最新 Renderer

《OZARK》使用 Unity 2022 LTS 的 Built-in Render Pipeline。專案跨越約六年，團隊多次升級 Unity，但沒有因此轉向較新的 Rendering Pipeline。

原因不是 Built-in 技術上較新，而恰恰是相反：團隊非常熟悉它，而且日常的 Simulation 工作亦使用同一套技術。對只有少數人、並且主要利用下班時間製作的團隊而言，已累積多年的操作速度與 Debug Knowledge 本身就是生產力資產。

遊戲大部分系統由團隊自行建立，但陰影、IK 等部分會使用現成方案。環境資產也混合自製與 Marketplace Asset，再透過重新貼圖、修改 Mesh、Decal、組合不同模型等方式大量改造。

這種 Pipeline 並不追求「全部自己做」或「全部買現成 Asset」，而是把有限人力放在真正決定作品特性的部分。

## Scope 是 Production Constraint 的結果

遊戲最後被控制在約 3–6 小時，並不是市場研究後得到的最佳商業時長，而是團隊根據少數成員、全職工作之外的開發時間，以及自己真正能完成到滿意品質的內容量逐步形成。

這和文章其他部分其實有同一個方向：形式不是先由抽象理想決定，再要求 Production 配合；Camera、工具熟悉度、人數、時間與內容量都會反過來塑造作品。

## 閱讀時需要知道的前提

這是開發團隊接受 80 Level 訪問的第一手製作回顧，但《OZARK》仍不是一篇技術論文或完整 Postmortem。文章沒有公開 Target Selection 演算法、Enemy AI State Machine、Lighting Shader、Performance Profile 或具體的 Production Metrics。

因此它最適合用來理解「固定視角這個設計決定如何向其他系統傳播」，而不是直接重做其實作。

另外，團隊對作品成效的判斷屬於開發者自身回顧，文章沒有獨立的玩家行為資料來驗證所有設計是否達到預期效果。

## 我的筆記與延伸

這篇最值得留下的一點，是 Camera 其實可以被視為一種 **Information Architecture**。

Camera 決定玩家能從世界取得甚麼資訊，而 AI、公平感、恐怖、瞄準甚至合作關係都建立在這個資訊邊界上。這比把 Camera 理解成「Renderer 最後把世界投影到畫面的方法」更接近遊戲設計中的真實作用。

也可以反過來說：

```text
Game State
   ↓
Camera 選擇讓哪些 State 可被玩家觀察
   ↓
Player Knowledge
   ↓
Decision
```

如果 Camera 改變，Player Knowledge 就改變；如果 Player Knowledge 改變，合理的 AI 行為、Reaction Window 和 Difficulty 也應該一起重新檢查。

另一個有意思的地方是「不追求完美 Readability」。一般 UI / Combat Design 很容易把資訊可讀性當成單調遞增的好處，但《OZARK》提供一個很清楚的反例：有些體驗的核心正是資訊不完整。真正需要控制的不是「玩家看不看得清楚」，而是 **資訊不足是否仍然允許玩家建立因果與責任感**。

這個區分不只適用 Horror。Stealth、偵探、戰爭迷霧、探索甚至一些 Boss Design，都可能需要刻意保留 Unknown；問題只是 Unknown 是否仍有足夠規則讓玩家學習。

## 來源

- [OZARK: Creating a Dark Story-Driven 2.5D Action-Horror Game](https://80.lv/articles/ozark-creating-a-dark-story-driven-2-5d-action-horror-game)
