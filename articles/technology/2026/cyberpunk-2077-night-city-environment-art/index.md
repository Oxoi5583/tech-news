---
type: article
title: "Interview: How Cyberpunk 2077’s Night City Was Built Almost Entirely by Hand"
published: "2026-09-18"
added: "2026-09-20"
authors:
  - "CD PROJEKT RED"
  - "David Jagneaux"
venue: "80 Level"
source_url: "https://80.lv/articles/interview-how-cyberpunk-2077-s-night-city-was-built-almost-entirely-by-hand"
tags:
  - environment-art
  - world-building
  - level-design
  - lighting
  - path-tracing
  - rendering
  - production
  - first-person
  - cyberpunk-2077
one_liner: "《Cyberpunk 2077》的城市不是靠程序生成填滿，而是先建立可供所有美術人員共用的歷史、風格與對比規則，再大量手工配置細節；真正可擴展的不是自動生成內容，而是讓人能一致做決策的視覺語言。"
summary: "CD PROJEKT RED 的美術總監回顧 Night City 的環境製作：城市以四種有年代關係的視覺風格建立歷史層次，第一人稱視角迫使團隊重做尺度與細節標準，而《Phantom Liberty》則以更明確的負空間、色彩與跨職能團隊規則修正本篇過度雜訊的問題。訪談亦解釋了為何從一開始追求物理可預測的光照，使後來加入 Path Tracing 比想像中自然。"
---

# Interview: How Cyberpunk 2077’s Night City Was Built Almost Entirely by Hand

## 這篇在談甚麼

Night City 最容易令人誤會的一點，是它的規模和密度看起來很像必須大量依賴程序生成：高樓、廣告、垃圾、塗鴉、街道與小型道具遍布整座城市，如果逐件由人配置，直覺上似乎很難擴展。

但 CD PROJEKT RED 的回答幾乎相反。Environment Art Director Kacper Niepokólczycki 表示，從建築、廣告、垃圾桶到人行道上的紙張，最終內容基本都是由美術人員手工製作和配置。程序工具曾被測試，真正留下來最接近程序化的例子是道路工具：先用 spline（沿一條曲線配置物件的路徑）生成道路、橋樑、天橋與沿路裝飾，再由美術人員手工修整。

所以這篇真正值得讀的問題不是「怎樣自動生成一座大城市」，而是另一個方向：**如果內容仍然主要由人製作，怎樣讓大量人員在多年開發中仍然做出同一座城市？**

## 可擴展的是視覺語言，而不一定是內容生成

團隊在前期把 Night City 的美術風格整理成具有年代先後的四層：Entropy、Kitsch、Neomilitarism、Neo-Kitsch。它們不是單純四套 Style Preset，而被設定成城市歷史不同時期留下的痕跡。

這個差異很重要。現實城市通常不會在某一年突然全部換成同一種建築；舊建築、後來的企業擴張、富人區的新設計會疊在一起。Night City 因此不是：

```text
District A = Style A
District B = Style B
```

而更接近：

```text
城市歷史
  ↓
不同年代留下不同 Style
  ↓
每個 District 依自己的歷史、企業與居民
以不同比例混合這些 Style
```

團隊再加上一條反覆使用的「Rule of Contrast（對比規則）」：普通住宅可以突然插入一架墜毀的 AV；熟悉的日常物件與荒謬的未來科技並置。對比不只是構圖技巧，也讓 Cyberpunk 的陌生科技仍然掛在玩家能理解的現實尺度上。

這使數百名製作者不需要每次都向 Art Director 詢問「這裡應該長甚麼樣」。真正被標準化的是**判斷方式**：這是哪個年代留下的東西？這個區域由甚麼社群與企業塑造？這裡需要哪一種對比？

## 密度不是一直加東西：本篇到 Phantom Liberty 的修正

團隊坦白承認《Cyberpunk 2077》本篇有些區域過度嘈雜。廣告、霓虹、垃圾、建築色彩與小型道具同時競爭注意力，雖然成功製造出壓迫性的商業都市，但部分畫面失去清楚的閱讀群組。

到《Phantom Liberty》，團隊不是降低細節量，而是建立更明確的規則：

- 把相近色彩、形狀和細節組成視覺群組；
- 刻意保留 Negative Space（負空間，即沒有高密度細節、讓視線休息的區域）；
- 讓高密度區與安靜區形成節奏，而不是每平方米都同樣複雜。

這裡有一個很實用的區分：

```text
Detail Density ↑
不必等於
Visual Noise ↑
```

問題不只是「場景有多少東西」，而是這些東西能否被眼睛分組。細節可以很多，但如果顏色、形狀、留白與焦點有階層，畫面仍然可讀。

## 第一人稱不是換 Camera，而是重做整套尺度

《The Witcher 3》到《Cyberpunk 2077》最大的環境製作變化之一，是第三人稱轉為第一人稱。

第三人稱遊戲裡，玩家一直看見 Geralt，因此角色本身就是一把視覺尺。建築、門、家具和道路相對角色有多大，很容易被理解。

第一人稱拿走了這把尺。團隊因此發現《The Witcher》的 Level Design Metrics 直接搬過來並不好看，需要重新建立第一人稱的空間尺度。環境中也大量使用玩家熟悉尺寸的物件，例如紙張、瓶子和長椅，讓大建築旁邊存在可供大腦比較的尺度參照。

材質要求也跟著改變。《Cyberpunk 2077》的 texel density（世界空間中每單位表面分配多少材質像素）一開始約是《The Witcher 3》的兩倍，因為玩家可以走得非常靠近牆面和道具；後來團隊利用大量 decal（貼在表面上的局部材質）補細節，對固定 texel density 的要求才變得較有彈性。

更大的改變發生在敘事場景。《The Witcher》可以為 cutscene 構圖一個漂亮鏡頭；《Cyberpunk 2077》的玩家通常仍能轉頭、走動和觀察，因此不能只裝飾攝影機前方：

```text
第三人稱 Cutscene
Camera -> 一個主要 Frame

第一人稱互動場景
Player -> 360° 都可能成為 Frame
```

環境美術因此同時變成敘事攝影的一部分。

## Open World 與 Quest Location 從不同方向開始

CD PROJEKT RED 會區分兩種環境製作起點。

Open World、Badlands 等非任務或輕戰鬥區域主要由 Art 驅動。Level Artist 先用大型形狀建立區域的情緒與視覺方向，再與設計、任務等團隊協作。

Quest Location 和重戰鬥區則反過來，先由 Level Designer 做 blockout，確保戰鬥、任務流程和空間功能成立，再由 Art 在這個結構上建立最終環境。

```text
Open World：
Art / Mood -> Space -> Gameplay coordination

Quest / Combat：
Gameplay blockout -> Space -> Art development
```

這不是兩個部門輪流「交件」。訪談反覆強調 Level Designer 與 Environment Artist 從早期就配對協作；製作中即使某項工作曾被標記完成，只要後來發現更好的方案仍會重新打開。

## 為甚麼 Path Tracing 對他們反而不是一次推翻

Global Art Director Jakub Knapik 原本來自電影 VFX。他在《Cyberpunk 2077》早期參與建立 Lighting Pipeline 時，希望整個世界像一個 **Lighting Sandbox**：美術人員改一盞燈、時間或天氣，結果應該按照物理規則可預測地改變，而不是每一種情況都需要人手重新作弊。

原因很現實。Night City 同時有：

```text
巨大世界
× 晝夜循環
× 天氣
× 大量室內外光源
```

如果每個地點在每個時間都靠人手調整，組合數會失控。

所以即使當時還沒有決定使用即時 Ray Tracing，團隊也已把傳統 GI（間接光）與 Reflection Probe 系統盡量往 Physically Based、可預測的方向推，並用電影業的 Arnold Path Tracer 作離線參照，檢查引擎結果是否合理。

後來加入 Path Tracing 時，最大的變化不是「美術突然要學一套完全不同的打光哲學」。相反，因為原本的目標就是讓光照接近物理沙盒，Path Tracing 只是讓 Runtime Solver 更接近那個原本就追求的模型。真正麻煩的反而是舊有 Probe：它們需要大量人工規劃，而 Path Tracing 減少了這種例外工作。

這是一個值得留意的 Engine Design 原則：**如果 Authoring Model 本身建立在穩定的物理／語意規則上，底層實作換代時，內容未必需要跟著全部重做。**

## Phantom Liberty 的 Production Lesson：組織結構也是 Pipeline

訪談最後談到《Cyberpunk 2077》本篇後最大的 Production 改變。原本團隊較按 Discipline 組織，例如 Art、Design、Narrative 各自形成垂直部門。這有利於專業文化和技術成長，但專案規模變大後，跨部門溝通開始成為瓶頸。

《Phantom Liberty》期間，他們把結構變得更扁平，圍繞 Quest 與 Open World 建立 multidisciplinary hub，同時保留各 Discipline 的 Lead／Director 作專業骨架。

可以粗略理解成：

```text
以前：
Art | Design | Narrative | ...
  \      |       /
   大量跨部門同步

後來：
Quest / World Hub
  ├ Art
  ├ Design
  ├ Narrative
  └ ...

+ 各 Discipline Lead 維持專業標準
```

兩位受訪者把《Phantom Liberty》形容為他們經歷過最順暢的製作之一。這當然仍是開發者回顧，不能單靠訪談證明組織重構就是唯一原因，但它與前面的美術規則其實指向同一件事：大型製作真正難以擴展的往往不是「做內容」本身，而是**讓大量人員在局部自主決策時仍然朝同一方向前進**。

## 閱讀時需要知道的前提

這是 80 Level 對 CD PROJEKT RED 美術主管的回顧訪談，不是完整技術論文，也不是《Cyberpunk 2077》所有部門的 Postmortem。

「幾乎全部手工製作」是 Environment Art Director 對其環境製作流程的描述，不應理解成遊戲完全沒有程序化、系統生成或自動化技術；訪談本身也提到道路 spline 工具。它主要回答的是最終環境美術如何建立，而不是整個 Open World Runtime 的生成方式。

Path Tracing 部分也沒有公開 GI、Probe、Ray Tracing 的完整演算法、效能數據或 Shader 實作，因此更適合用來理解 **Lighting Authoring Philosophy**，而不是作為 Rendering Implementation Guide。

## 我的筆記與延伸

我認為這篇最值得留下的地方，反而和「手工 vs 程序生成」這個表面問題不同。

一般談大型世界的可擴展性，很容易把問題直接翻譯成：

```text
內容很多
-> 人做不完
-> Procedural Generation
```

Night City 展示的是另一條路：

```text
內容很多
-> 人仍然做
-> 先把「如何判斷」編碼成共享語言
-> 每個人可以局部自主製作
```

也就是說，**Abstraction 不一定用來取代作者，也可以用來提高作者群體的一致決策能力。** 四種歷史風格、Rule of Contrast、District Backstory、色彩與負空間規則，本質上都像一層高階的資料模型；只不過執行這個模型的不是 Generator，而是人。

另一個有意思的對照是《Phantom Liberty》的「更詳細但更不嘈雜」。這和單純降低 Asset Density 不同：真正被控制的是視覺資訊的頻寬。大量小物件如果被組成幾個清楚的 Shape / Color Group，大腦實際需要處理的視覺單位可能反而更少。

最後，Path Tracing 的案例也提醒一件事：Engine 的長期可替換性不只是 API 抽象問題。如果美術內容依賴大量「為目前 Renderer 特製的作弊」，Renderer 一換，內容本身就是技術債；如果 Authoring 規則盡量描述真實世界的光源、材質與空間關係，底層 Solver 升級反而可能更容易。這不是說所有遊戲都應追求物理正確，而是 **Content Contract 越依賴穩定語意，越不依賴某一代實作細節，長期越容易演進。**

## 來源

- [Interview: How Cyberpunk 2077’s Night City Was Built Almost Entirely by Hand](https://80.lv/articles/interview-how-cyberpunk-2077-s-night-city-was-built-almost-entirely-by-hand)
