---
type: article
title: "『Clair Obscur: Expedition 33』開発ポストモーテム：少人数チームがUE5標準機能を使い倒す方法"
published: "2026-09-24"
added: "2026-09-25"
authors:
  - "稲庭 淳"
venue: "CGWORLD"
source_url: ""
tags:
  - unreal-engine
  - technical-art
  - procedural-generation
  - houdini
  - metahuman
  - nanite
  - virtual-shadow-maps
  - small-team
  - production-pipeline
  - blueprint
  - sequencer
  - continuous-integration
  - perforce
one_liner: "《Expedition 33》的小團隊把「不要自研已有答案的東西」貫穿角色、場景、戰鬥、演出與建置流程，讓少量程式與美術人力集中在真正決定作品特色的地方。"
summary: "CGWORLD 前後篇整理 Sandfall Interactive 的開發 Postmortem：4 人角色團隊與單一 Technical Artist 如何利用既有工具支撐大量內容，後篇再揭示 95% Gameplay Logic 使用 Blueprint、戰鬥與 Cutscene 大量由 Sequencer 驅動，並以 Unreal 標準功能、CI 與資料驅動流程降低少人團隊的維護成本。"
---

# 『Clair Obscur: Expedition 33』開發 Postmortem：少人團隊如何把 UE5 當成共同製作語言

## 這篇在談甚麼

《Clair Obscur: Expedition 33》的規模很容易讓人直覺認為背後需要一支大型內容製作團隊，但 Sandfall Interactive 在 Postmortem 公開的實際配置相當極端：角色團隊只有 4 人，卻需要製作約 120 個角色資產；Technical Artist 更只有 Alexandre Breton 一人，要同時處理 Shader、Houdini 程序化建模與配置、Editor Tool、最佳化和 Profiling。

因此這篇真正值得看的並不是「他們用了哪些 Unreal Engine 5 功能」，而是小團隊如何決定哪些問題不值得自己解，以及如何把引擎、商用工具和程序化資料流組合成可以反覆修改的 Production Pipeline。

## 4 人角色團隊：不要把所有能力都自己造一次

角色團隊需要製作約 10 名主要角色、25 套 Skin、60 名敵人與 20 名 NPC，而且作品採取偏寫實的人體比例與材質。寫實的好處是現成工具很多，但少量拓撲、皮膚或接縫問題也更容易落入「不自然」的區域。

團隊並沒有一開始就得到理想 Pipeline。他們先試 Character Creator 3，雖然可調整性高，但學習成本與 Unreal Engine 之外的往返工作令 Workflow 破碎；之後轉向 MetaHuman，又遇到當時只能在 Browser Customization 的限制，因此再加入 MeshMorpher、Mesh to MetaHuman、ZBrush 等工具。

最後形成的大致資料流是：

```text
MetaHuman Creator
    ↓
建立可用的人體基底
    ↓
ZBrush
    ↓
修改 Silhouette / Sculpt
    ↓
Mesh to MetaHuman
    ↓
回到共同拓撲與 Rig 生態
    ↓
Bake Detail / Texture / Material
    ↓
Unreal Engine
```

Texture 與 Material 亦盡量在角色之間模組化，而不是每個角色從零建立一套材質。

這個流程仍然有代價：Mesh Export 尤其是 Triangulation 麻煩、頭頸與身體接縫需要處理，而且 MetaHuman 的固定拓撲限制了自由度。團隊甚至曾把主要角色重做超過 6 次，並在 Trailer 公開前一個月重做全部 Main Character。

這裡值得注意的是，他們沒有因為工具有缺點就立即自研替代品。角色 Lead Alan Reynaud 在 Q&A 直接說明：4 人團隊沒有餘力建立自己的 Character Tool，因此使用熟悉的工具與市售工具反而合理。

也就是說，問題不是：

```text
這個工具是不是完美？
```

而比較接近：

```text
工具的限制成本
        vs
自己開發 + 維護另一套系統的成本
```

對小團隊而言，一個不完美但能接進既有 Pipeline 的工具，可能比一套理論上更理想的自研方案便宜很多。

## 唯一一名 Technical Artist：工作的核心是消掉重複成本

Alexandre Breton 是 Sandfall 當時唯一專任 Technical Artist。他負責的工作跨度很大：Shader、Houdini、程序化配置、Editor Tool、Optimization 與 Profiling 都包含在內。

文章裡幾項 UE5 技術看似彼此無關，但其實都在消除內容製作中的某種重複成本。

### Nanite：把手工 LOD 從日常工作中拿掉

Nanite 是 UE5 的虛擬化幾何系統，讓引擎根據畫面需求選擇實際需要處理的幾何細節。對 Sandfall 而言，它的重要性不只是「可以畫更多 Polygon」，而是大量資產不再需要由團隊逐級製作傳統 LOD。

對大型團隊，LOD 可能只是 Production Pipeline 的其中一道工序；對人數很少的團隊，每一個必須人工維護的資產變體都會乘上整個世界的資產數量。因此 Nanite 實際換回的是人力與迭代速度。

### Virtual Shadow Maps：把 Light Bake 從迭代迴圈拿掉

Virtual Shadow Maps（VSM）提供高解析度動態陰影。Sandfall 強調的同樣不是單純畫質，而是不用反覆 Light Bake。

傳統 Bake Workflow 可以近似理解為：

```text
修改場景
  ↓
重新 Bake Lighting
  ↓
等待
  ↓
查看結果
  ↓
再修改
```

改用動態陰影後，場景與光照的修改能更直接看到結果。對經常調整內容的小團隊而言，節省的是每一次修改都會支付的等待成本。

團隊仍然會做實際最佳化，例如按 Actor 設定 World Position Offset（WPO，頂點在 Shader 中的位移）停用距離，並按平台使用不同設定；也就是不代表採用 VSM 後就不需要管理 GPU 成本。

## Houdini：真正重要的是「同一輸入能重新產生同一結果」

Breton 使用 Houdini 與 Houdini Engine 建立城市與其他程序化內容。文章展示 UE Spline 可以直接作為 Houdini Spline 的輸入，讓同一份路徑資料重新生成相同結果。

這比「Procedural Generation 可以快速做很多東西」更重要，因為它把場景的一部分從最終 Mesh 重新提升成規則與輸入資料：

```text
Spline / Parameters
       ↓
Houdini Procedure
       ↓
Buildings / Placement / Geometry
```

如果路徑改變，團隊不必把沿線內容全部重新手工調整，而可以重新執行生成流程，再修改真正需要人工判斷的部分。

這和單純 Random Generation 不同。它更接近一個可重建的 Authoring Pipeline：原始資料是 Spline 與參數，場景幾何是生成結果。

不過 Breton 也直接指出 Houdini Engine 的缺點：重、不穩定，而且有 License 問題。因此他後來開始思考相同工作是否能直接在 Engine 裡完成。這點很重要——程序化工具本身也有 Integration Cost；如果每次生成都需要跨越一個脆弱的外部系統，原本省下的內容成本可能被工具成本吃掉。

## Instance Data：不要為了視覺差異複製整套資產

城市建築亦採取很實際的成本控制。只有玩家能進入的建築才建立 Collision；不需要互動的建築不支付同樣的碰撞資料與 Runtime 成本。

外觀變化則使用 Per Instance Custom Data：同一個 Instanced Asset 可以為每個 Instance 提供少量自訂參數，再讓共同 Material 根據參數改變污漬等外觀。

概念上是：

```text
同一 Building Mesh
同一 Material
        +
Instance A: dirt = 0.2
Instance B: dirt = 0.8
Instance C: variation = 3
        ↓
看起來像不同建築
```

而不是為每棟建築複製 Mesh / Material Instance / Texture 組合。

這同時降低 Asset 數量、Material State 管理和內容製作成本。

## VAT：把動畫結果烘成頂點資料

文章亦提到 Vertex Animation Texture（VAT）。它把動畫期間每個頂點的位置等資料預先存入 Texture，Runtime 再由 Shader 讀取，因此某些動畫物件不需要傳統 Skeletal Skinning。

資料流可以簡化為：

```text
Houdini Simulation / Animation
        ↓
Bake Vertex Motion
        ↓
Texture
        ↓
GPU Shader 讀取
        ↓
Mesh Deformation
```

這適合大量不需要完整 Skeleton Interaction 的效果或物件，但代價是動畫已被 Bake，Runtime 可自由修改的程度比完整骨架動畫低。

## 技術選擇的共同點：把人力留給不可自動化的判斷

把整篇的案例放在一起，可以看到 Sandfall 的技術策略並不是單純「大量使用 UE5 最新功能」：

| 製作成本 | 採用的方法 |
| --- | --- |
| 每個角色從零建立人體與材質 | MetaHuman + 共用 Material / Texture |
| 每個角色工具全部自研 | 商用工具與既有 UE 生態 |
| 每個高密度 Asset 製作多級 LOD | Nanite |
| 場景修改後反覆等待 Light Bake | Virtual Shadow Maps |
| 城市內容逐個手工重建 | Houdini + Spline Input |
| 同 Mesh 為視覺差異複製多份材質 | Per Instance Custom Data |
| 某些動畫需要完整 Skinning Pipeline | VAT |

共同模式是：

```text
內容規模增加
      ↓
找出會乘上 Asset 數量的重複工作
      ↓
由 Engine / Tool / Procedure 吃掉
      ↓
Artist 把時間留給造型、構圖、修改與判斷
```

這可能比「小團隊如何做到 AAA 畫面」這種較表面的敘述更接近實際工程問題。

## 後篇補充：Sequencer 不只是 Cutscene Tool，而是戰鬥演出的共同時間軸

CGWORLD 在 9 月 25 日公開同一場 Postmortem 的後篇。Creative Director Guillaume Broche 說自己一半以上開發時間都在 Sequencer；更重要的是，《Expedition 33》的戰鬥在結構上可以理解成「一連串 Sequence 的鏈式播放」。

Menu Transition、Camera、Character Switch 與玩家技能演出都可以由 Sequence 組合。大部分角色又共享 UE5 標準 Skeleton，並以 Tag 綁定，因此同一份 Sequence 可以套到不同角色。

這種做法的價值不是「Cutscene 做得很方便」，而是把多個 Discipline 的資料放進同一個可視時間軸：

```text
Gameplay Event
    ↓
Sequencer
 ├─ Camera
 ├─ Character Animation
 ├─ Light
 ├─ VFX
 └─ Timing
```

對 Turn-based RPG 特別合適，因為玩家技能發動時的時間與鏡頭相對可控。文章也指出敵方攻擊因 Target 與位置更動，Camera Angle 不像玩家技能那麼容易預製，只能利用 FoV 與 Time Dilation 等手段改善可讀性；因此這不是能無條件套到所有 Action Game 的方案。

## Cutscene Pipeline：只清理鏡頭真正看得到的資料

6 人需要製作約 4 小時 30 分鐘 Cutscene，因此團隊把品質拆成 L0 / L1 / L2：

```text
Mocap
 ↓
L0：快速得到 Rough Cut
 ↓
只清理畫面實際會看到的部分
 ↓
L1：完成 Camera / Staging
 ↓
L2：加入 VFX / Sound
```

甚至角色牽手等昂貴接觸動作，也會在適合時直接用 Camera 遮掉，而不是為不可見部分支付完整 Animation Cleanup 成本。

但這不等於全面降低品質。團隊幾乎每個 Shot 都有專用 Lighting，也建立共用 Facial Blueprint 為眼睛、皮膚加入細微動態。真正的原則是：**品質成本集中在最後會進入玩家視野的資訊上。**

## 4 名 Programmer：95% Gameplay Logic 用 Blueprint

Technical Director Tom Guillermin 公開的數字很有代表性：團隊只有 4 名 Programmer，而約 95% Gameplay Logic 使用 Blueprint。

Sandfall 的工程原則是：

- 不對 Engine 做大型修改或 Refactor；
- 能用 Unreal 原生工具就不自研；
- Skill / Item 用 Data Asset 定義；
- Buff、Status、Passive 與敵人特殊行為大量以 Blueprint 組合；
- 約使用 30 個 Unreal 標準 Plugin，加上約 25 個第三方 Plugin。

他們曾自行實作 UI Navigation，後來因維護複雜而改回 CommonUI。這個失敗例子比「用了很多 UE 功能」更重要：**自研系統的成本不是第一次寫完，而是之後所有人都必須持續理解與維護它。**

因此 Sandfall 不是把 Programmer 當成每個 Feature 的必經入口，而是讓 Programmer 建立 Designer 可以自己組合內容的底座：

```text
Programmer
    ↓
穩定的 Gameplay Primitives / Data Contract
    ↓
Designer
    ↓
Data Asset + Blueprint + Sequencer
    ↓
大量實際 Gameplay Content
```

這和前篇 Technical Art 的做法其實是同一件事：把會隨內容數量線性增加的重複工作，移到可重用的系統或現成工具。

## CI：每天都產生一個真的可以玩的版本

開發環境使用 Perforce、Unreal Game Sync 與 TeamCity。TeamCity 每晚自動 Packaging，並把 Build 上傳 Steam；失敗時透過 Discord 通知。

這看似只是普通 CI，但對小團隊的意義很實際：Build 是否仍然成立，不需要等到某個人「有空時再 Build 一次」。

```text
Daily Changes
    ↓
Nightly TeamCity
    ↓
Package
    ↓
Upload to Steam
    ↓
Success / Discord Failure Alert
```

它把「專案現在到底能不能完整 Build」從人類記憶與習慣，轉成每天由機器重新驗證的條件。

## 少人團隊的真正邊界：不要把管理也做成主要工作

Round Table 裡，Sandfall 表示未來仍希望維持 30 人以下。理由不是「30 是神奇數字」，而是人數增加後，管理本身開始吃掉創作時間，也更難維持清楚的 Creative Vision。

需要特定階段才大量投入的 QA 等工作則 Outsource。也就是把團隊拆成：

```text
長期需要共享脈絡的人
        ↓
Core Team

只在特定階段需要的能力
        ↓
External / Outsource
```

這和「小團隊甚麼都自己做」正好相反。Sandfall 的小團隊成立，是因為它把 Engine、Plugin、工具生態與 Outsourcing 都視為外部能力的一部分。

## UE 作為共同語言，也會帶來黑箱問題

Round Table 裡，《Persona 3 Reload》的山口拓也與《Hi-Fi RUSH》的 John Johanas 都提到 UE 讓 Artist / Designer 更容易自行 Prototype；但代價是 Engine 內部變得更像 Black Box。

Guillermin 提出另一個實務角度：內製 Engine 的知識可能隨原開發者離職而消失，而 UE 的龐大使用者社群與公開知識反而降低了這種「只有公司內某個人知道」的風險。

因此 Buy vs Build 不只是 Feature 與效能比較，也包含 **Knowledge Availability**：

```text
Internal Tool
  → 高度符合需求
  → 但知識可能集中在少數人

Widely-used Engine
  → 未必完全符合需求
  → 但文件、社群、人才市場共同保存知識
```

這對長期維護其實是一種很現實的工程成本。

## 閱讀時需要知道的前提

這份筆記合併 CGWORLD 對同一場 Sandfall Postmortem 的前後篇整理，不是完整技術文件。它沒有公開 Nanite / VSM 的底層實作、Houdini Graph、Shader Code、Profiling 數據或實際節省了多少人時，因此能可靠學到的是 Production Strategy、工具組合與問題拆法，而不是直接重現其 Pipeline。

另外，Nanite 並不等於「完全不需要最佳化」；VSM 亦不等於「動態陰影沒有成本」。文章本身就提到 WPO Distance 與平台差異設定等實際最佳化工作。

## 我的筆記與延伸

這篇和一般「自研工具可以提高效率」的論述形成一個很好用的反例：**工具本身也需要人。**

當 Technical Artist 只有一名、角色團隊只有 4 人時，真正稀缺的資源不是 License Fee，而是可以理解、維護和修理 Pipeline 的工程時間。這時「使用成熟生態，再只補真正缺失的部分」可能比建立漂亮的全自研 Pipeline 更合理。

另一個值得延伸的是 Houdini 的資料流。若把它抽象掉產品名稱，真正有價值的是：

```text
Human-readable / Editable Source Data
          ↓
Deterministic Build Procedure
          ↓
Engine Runtime Asset
```

這和獨立於 Engine 的 World Authoring Tool 很接近。道路、建築群或場景規則可以先保存成較容易 Version Control 的高階資料，最後再 Parse / Cook 成 Engine 真正需要的 Mesh、Collision、Navigation 與 Spatial Partition。Runtime Data 不必等同 Authoring Data。

而 Breton 對 Houdini Engine「重、不穩定、License 有成本」的抱怨，又補上一個很重要的限制：如果中間 Compiler / Generator 本身太昂貴，Authoring 與 Runtime 分離的好處會被 Integration Cost 抵消。因此專用工具最值得追求的可能不是功能最多，而是輸入資料穩定、生成可重現、失敗容易 Debug。

## 來源

- [『Clair Obscur: Expedition 33』開発ポストモーテム【前編】キャラクター制作＆テクニカルアートから紐解くUE5活用術](https://cgworld.jp/article/202609-coe33-01.html)
- [『Clair Obscur: Expedition 33』開発ポストモーテム【後編】シーケンサーとUE標準機能を使い倒す、Sandfall流のゲーム開発](https://cgworld.jp/article/202609-coe33-02.html)
