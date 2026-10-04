---
type: article
title: "Behind the Scenes: How the Marvel Rivals Art Team Builds a Character"
published: "2026-10-02"
added: "2026-10-03"
authors:
  - "Marvel Rivals Art Team"
venue: "80 Level"
source_url: "https://80.lv/articles/inside-marvel-rivals-character-art-vfx-destruction-pipeline"
tags:
  - character-art
  - technical-art
  - npr
  - pbr
  - vfx
  - cross-platform
  - visual-readability
one_liner: "《Marvel Rivals》把角色辨識度拆成跨概念設計、動畫、VFX、皮膚與平台效能都必須保存的視覺錨點，而不是只在 Concept Art 階段處理。"
summary: "80 Level 訪問《Marvel Rivals》美術團隊，從 Cyclops 的角色製作流程談到 NPR/PBR 混合著色、英雄專屬 VFX、動態場景與跨平台資產分級。最值得理解的是：角色身份被整理成能穿過整條 Production Pipeline 的視覺不變量，再由統一渲染框架與效能預算維持多人畫面的可讀性。"
---

# Behind the Scenes: How the Marvel Rivals Art Team Builds a Character

## 這篇在談甚麼

《Marvel Rivals》的角色已在漫畫、電影、動畫、玩具與其他遊戲中累積數十年的視覺歷史。團隊既不能只複製某個舊版本，也不能改到失去辨識度；放進高速多人遊戲後，角色、技能、皮膚與環境效果還必須在複雜畫面中保持清楚。

80 Level 這篇第一手訪談讓美術團隊從參考、概念設計、建模、動畫、VFX，一路談到 NPR/PBR 混合著色、動態環境與跨平台效能策略。它真正有價值的地方，是讓人看到「角色身份」如何穿過完整 Production Pipeline。

## 角色身份先被拆成視覺錨點

團隊不是先問「這一版角色要改甚麼」，而是先辨認玩家認出角色時最依賴的訊號，例如身體輪廓、代表性色彩、標誌、招牌裝備與能力的視覺表現。

這些元素構成角色在不同媒介、不同皮膚甚至不同主題下仍然能被辨認的最低條件。

因此角色設計不是忠於原作與創新的二選一，而比較像：

```text
先固定 Identity Constraints
        ↓
再決定哪些區域可以重新設計
```

團隊亦指出，專案早期已先系統化整理漫畫輪廓、角色特徵與能力系統，建立共同美術標準，避免每個角色、每個部門都重新發明判斷方式。

## 從 Cyclops 看角色 Pipeline

訪談以 Cyclops 為較具體的案例。

概念階段先研究 Marvel Comics 中的 Scott Summers，也參考電影、動畫、遊戲、玩具等其他媒介。團隊希望保留 Cyclops 的指揮官氣質與標誌性 visor，同時加入較現代的未來感與時裝語言。

重點不是直接拼貼參考資料，而是先找出「哪些特徵令玩家認為這就是 Cyclops」，再決定哪些部分可以重新編碼。

動畫先從 idle、跑步、跳躍等基本動作建立 movement style，再以此為基礎設計技能動畫。技能首先滿足 Gameplay Function，之後才加入來自漫畫招牌動作的表演細節。

```text
IP 歷史資料
   ↓
核心視覺錨點
   ↓
Concept Design
   ↓
Model / Rig
   ↓
Movement Style
   ↓
Gameplay Requirement
   ↓
Character-specific Animation / VFX
```

角色身份因此不是某一張設定圖，而是一組沿 Pipeline 持續被保存的條件。

## NPR/PBR 混合著色

角色使用客製化 Shading Model，把非寫實渲染（NPR）與物理式渲染（PBR）的部分特性混合。

團隊需要控制陰影區域的色彩傾向、Stylized Highlight 的形狀、材質質感與 2D 平面筆觸感。這表示目標不是簡單把 N·L 做成幾階明暗，而是在保留材質可理解性的同時，重新控制光照資訊如何被整理成漫畫式形狀。

```text
PBR
提供材質與光照的一致基礎
        +
NPR
控制色塊 / Highlight / 平面化資訊
        ↓
統一的角色視覺語言
```

這和完全放棄 PBR 不同：物理式材質仍提供穩定基礎，但最後哪些光照訊號可以主導角色外觀，交回 Art Direction 控制。

訪談沒有公開 BRDF、G-buffer、Lighting Pass 或 Shader Code，因此不能把這部分當成完整 Renderer Documentation。

## VFX 同時負責角色身份與戰鬥可讀性

每個英雄都需要很強的個人特徵，但所有英雄又同時存在於同一場多人遊戲。

團隊使用統一的 Comic Rendering Framework，再透過材質、IP 元素、顏色與 Dynamic Rhythm 區分角色：

```text
共同 Framework
        +
Hero-specific Vocabulary
        ↓
在一致性中製造差異
```

這避免兩個極端：如果每個角色完全使用獨立視覺語言，整體畫面容易失控；如果所有效果完全統一，角色身份又會變弱。

角色出場與 MVP 演出則可以暫時離開純 Gameplay Function，成為很短的 Character Narrative。團隊會讓動畫、環境與 VFX 一起表達服裝或角色設定，也會利用慢動作、黑白 Freeze Frame 等處理強化特定情緒。

因此 VFX 同時承擔 Gameplay Feedback、Character Branding 與短篇敘事。

## Alternate Costume 的自由度有明確邊界

不同年代、世界觀與主題皮膚可以大幅改變服裝，但團隊仍優先保存 Silhouette、Hero Logo、代表性裝備與 Unique Color Scheme。

這些視覺錨點相當於 Skin System 的 Invariant：

```text
哪些資訊可以自由變化？
        ×
哪些資訊一旦一起消失
玩家就需要重新辨認角色？
```

對 Multiplayer Game 而言，這不只是品牌問題，也會直接影響玩家在短時間內辨識角色的成本。

## 動態環境也要服從 Gameplay

Technical Art 團隊建立了自動化場景切割工具、碎片效果，以及配合角色能力的環境變化系統。

訪談特別提到，不同建材需要不同斷面結構；系統產生的片段要有自然的大小比例，同時仍需滿足 Gameplay 對場景掩體與空間結構的需求。

這裡的重要限制是：

```text
Visual Plausibility
        ×
Art Quality
        ×
Gameplay Space Requirement
```

三者必須一起成立。

文章沒有公開幾何切割演算法、Collision Update、Navigation 或狀態同步，因此這部分適合作為系統需求與 Production Decision 的案例，而不是實作文件。

## 跨平台不是最後才降低畫質

團隊使用 Asset Tiering 與嚴格 Rendering Budget 管理不同平台版本，包括不同品質等級的場景 Lighting、VFX，以及額外的 Engine Feature 來控制效果成本。

這表示跨平台策略不是完成最高畫質版本後才整體縮 Resolution，而是在 Production 階段已經把內容拆成可分級資料：

```text
Content Authoring
      ↓
Quality Tier / Budget
      ↓
Platform-specific Selection
      ↓
Runtime
```

代價是 Pipeline 更複雜：Artist 必須知道哪些效果存在 Tier、哪些特徵不能因降級而消失。好處則是低階版本可以優先保留真正影響角色辨識與 Gameplay Readability 的資訊。

## 為甚麼值得讀

這篇最有轉移價值的地方，是它把「角色辨識度」從 Concept Artist 的問題擴大成整個 Pipeline 的共同 Constraint。

一個角色是否仍然像自己，會同時受到：

```text
Concept
Model
Rig
Animation
Shader
VFX
Skin
Environment
Performance Tier
```

影響。

因此大型 IP Adaptation 的核心工作之一，其實是先把模糊的「像不像這個角色」拆成一組可以跨部門保存的 Visual Invariants。

即使完全不做既有 IP，原創遊戲也可以問：

```text
角色身份中
哪些訊號一定要保留？
哪些可以隨 Costume / State / Platform 改變？
```

一旦回答清楚，Art Direction 就不再只是 Concept Sheet，而開始成為 Shader、VFX、Animation、LOD 與 Optimization 都能共同使用的設計約束。

## 閱讀時需要知道的前提

這是一篇由開發團隊直接回答的 80 Level 訪談，第一手價值高，但形式仍偏 Production Overview。

它涵蓋範圍很廣，代價是每個技術主題都沒有深入到可重現程度：NPR/PBR Shader 沒有公式與 Pass 結構；動態環境沒有完整資料結構；跨平台也沒有 Frame Budget 或具體平台數字。

因此它最適合作為 Character Art Pipeline、Art Direction 如何變成跨部門 Constraint，以及多人遊戲如何同時處理角色個性與 Visual Readability 的案例，而不是 Implementation Guide。

## 我的筆記與延伸

我認為這篇最值得延伸的概念是 **Visual Invariant**。

很多角色設計流程會有 Model Sheet，但 Model Sheet 容易只描述「角色現在長甚麼樣」。如果進一步把角色拆成：

```text
Invariant
├─ Silhouette
├─ Motion Rhythm
├─ Signature Color Relation
├─ Signature Prop
└─ Ability Shape Language

Variant
├─ Costume
├─ Material
├─ Historical Theme
├─ State
└─ Platform Quality
```

那麼角色身份就開始變成可以被 Pipeline 驗證的東西。

這尤其適合有大量 Costume、機體換裝、角色狀態變化或長期更新的遊戲：真正需要先設計的可能不是「第二套 Skin 長甚麼樣」，而是先決定無論怎樣變，哪些訊號絕對不能一起消失。

另一個值得留意的地方，是它和近期不少 NPR Production Case 指向同一方向：Stylized Rendering 並不是單一 Shader Algorithm，而是把 Art Direction 逐步轉成資料、工具、Budget 與跨部門規則。

## 來源

- [Behind the Scenes: How the Marvel Rivals Art Team Builds a Character](https://80.lv/articles/inside-marvel-rivals-character-art-vfx-destruction-pipeline)
