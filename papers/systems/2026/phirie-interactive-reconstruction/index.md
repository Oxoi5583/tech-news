---
type: paper
title: "φ-RIE: From Photorealistic Reconstruction to Interactive Environments"
published: "2026-09-22"
added: "2026-09-24"
authors:
  - "Runyi Yang"
  - "Deheng Zhang"
  - "Xiaoye Wang"
  - "Kanzhi Wu"
  - "Lei Sun"
  - "Ajad Chhatkuli"
  - "Kunyu Peng"
  - "Luc Van Gool"
  - "Danda Pani Paudel"
venue: "arXiv"
paper_url: "https://arxiv.org/abs/2609.26795"
code_url: ""
tags:
  - real-to-sim
  - gaussian-splatting
  - world-representation
  - physics-simulation
  - scene-reconstruction
  - interactive-environment
one_liner: "把實景掃描得到的漂亮但不能互動的 3D 場景，拆成真正能搬動、碰撞的物件與移走物件後仍完整的背景。"
summary: "φ-RIE 將 3D Gaussian Splatting 場景中的指定物件轉成有碰撞幾何、可由物理模擬器驅動的獨立資產，同時移除原本黏在場景裡的外觀並補回被遮住的背景；重點是讓視覺物件、碰撞物件與背景修補共享同一個物件身份與座標。"
---

# φ-RIE: From Photorealistic Reconstruction to Interactive Environments

## 先用一個例子理解

用多視角照片重建一間廚房後，3D Gaussian Splatting（3DGS）可以把杯子、桌面與光照重現得很像照片，但「杯子」未必是一個真正獨立的物件。它的高斯點可能和桌面外觀混在一起，杯底沒有被拍到，杯子下面的桌面也從未被看見。

所以若只是替場景加入一個剛體杯子再把它拿起來，常會同時出現三個問題：原來的杯子殘影還留在桌上、新杯子的碰撞形狀缺失，以及杯子移走後桌面出現空洞。

φ-RIE 的目標就是把這種「只能看」的重建結果轉成可互動場景：同一個物件身份同時決定要建立哪個可動資產、要從原始 Gaussian 場景刪掉哪些外觀，以及要補回哪一塊被遮住的背景。

## 原本的做法有甚麼困難

3DGS 的 primitive 是為了解釋輸入影像而最佳化，不是為了形成乾淨的遊戲物件邊界。因此畫面上看似清楚分離的杯子和桌子，在資料上仍可能由互相重疊的 Gaussians 共同解釋。

互動場景另外需要照片本身沒有直接提供的資料：物件被遮住的完整幾何、碰撞形狀、物件移走後才會露出的背景，以及視覺資產與 physics body 之間一致的 metric transform。若「生成物件」「刪除原場景物件」「補背景」各自獨立做，很容易得到彼此不對齊的三套結果。

## 它是怎樣做到的

整個 pipeline 可以分成三段。

第一段是 Scene Observation。輸入是 Gaussian reconstruction、已校正相機的 RGB 影像與 pose，以及由掃描或深度融合得到的對齊 surface。系統用 SAM3 找出各視角中的物件 mask，再以 ray intersection 把 mask 投回 3D surface，最後用 voxel overlap 將不同視角的觀測合併成同一 object instance。

第二段是 Coupled Scene Construction。每個物件會由 TRELLIS 與 ReconViaGen 等生成器提出完整 3D candidate。系統不直接相信生成結果，而是把 candidate 對齊實際觀測 surface：先估 scale、搜尋 yaw，再以 ICP 與 scale / translation refinement 對齊；評分同時懲罰「生成物件多出觀測不支持的表面」與「觀測到的表面沒有被生成物件解釋」。若方向假設失敗，會以其他 source-up axis 重試 registration。

同一個 object identity 亦會驅動背景分離。系統把三種證據取聯集：靠近觀測 surface 的 Gaussians、靠近已註冊完整 asset 的 Gaussians，以及在多個視角投影進 instance mask 的 Gaussians。這比只沿著可見表面刪除更能清走低 opacity 或藏在遮擋區域的物件外觀。

物件移走後露出的背景則先在影像空間 inpaint，再在局部區域估計 support plane，建立 normal-aligned Gaussian disks 並只最佳化這批新 Gaussians。原本沒有被修改的 Gaussian scene 保持不動。因此它不是重新生成整個房間，而是局部把原 reconstruction 因互動而缺少的部分補起來。

第三段是 Interactive Environment。完整 mesh 經 CoACD 等方法產生 convex collision components；physics simulator 計算 rigid-body pose，而 Gaussian asset 的位置則跟隨同一 body 的相對 transform。也就是碰撞幾何負責「摸起來在哪裡」，Gaussians 負責「看起來是甚麼」，但兩者由同一個 simulator state 驅動。

## 與現有方法的差別

最值得注意的不是單一 reconstruction backend，而是「資產建立與 source removal 必須耦合」這個設計。

傳統 real-to-sim pipeline 很容易變成：先生成一個杯子，再另外把照片裡的杯子擦掉，再另外補桌面。φ-RIE 則要求這三件事共享同一 object identity、觀測證據與 metric registration。這令 scene representation 從一整塊 photorealistic field，轉成「保留的背景 Gaussians + 可獨立移動的 Gaussian assets + 對應 collision meshes」。

它也沒有為了可互動而把整個 captured scene 換成 mesh。未修改的部分仍保留原始 Gaussian reconstruction，因此可以把高視覺保真與少量真正需要 interaction 的物件分開處理。

## 實驗結果與限制

作者在 50 個 ScanNet++ 場景、1,871 個 object requests 上測試 construction。使用相同 1,800 個 retained candidates 時，固定優先選 generator 的 F1@20mm 為 0.336；加入 evidence-based selection 後為 0.348，再加入 registration retry 後升至 0.383，Chamfer distance 從 7.638 cm 降至 5.720 cm。不過 retry 亦把平均 construction time 從每場景 35.68 分鐘提高至 70.82 分鐘，這顯然仍是離線 world-building pipeline，不是 runtime reconstruction。

轉換亦有可量化的視覺代價：ScanNet++ held-out view 的 PSNR 從原始 Gaussians 的 21.582 dB 降到 20.438 dB。也就是「可拆、可動」不是免費得到的，物件替換與背景 completion 會犧牲一部分初始畫面 fidelity。

在 RoboCasa 的 480 次 manipulation trials 中，原始 prepared environment 成功 385 次；TRELLIS-only replacement 成功 73 次；完整 φ-RIE 成功 128 次。這證明生成資產可以實際進 simulator 做 manipulation，但距離手工準備好的 production asset 仍有很大差距。作者也明確指出，selection / retry 帶來的幾何改善並沒有在這組 policy test 中證明額外成功率提升。

目前方法主要面向 rigid objects。背景 completion 使用局部平面假設，適合桌面等區域，不代表真正恢復所有被遮擋幾何；物理 mass、friction 等參數也主要來自 priors，而不是由實景可靠辨識。Gaussian appearance 本身亦沒有動態 relighting，物件移動後的陰影與光照 mismatch 只能選擇性用後處理 harmonizer 改善，而且那不是物理正確的 lighting solution。

## 可以怎樣用在遊戲裡

論文已驗證的是 real-to-sim 與 robotics interaction，不是遊戲 production pipeline。對遊戲引擎更值得借用的是「只把需要互動的部分從高保真世界 representation 中解耦出來」的想法。

例如大型掃描城市不必先把每一個 Gaussian、NeRF 或其他 captured primitive 都轉成乾淨 game mesh。世界可以保留一個主要用於 rendering 的 captured field；只有玩家能搬動、破壞或操作的物件才經過 construction pass，取得 object identity、collision geometry、可動 visual representation，以及移走後的 background completion。

這會形成一種很實際的混合世界：大部分環境追求 capture fidelity，少量 gameplay-relevant objects 才支付完整 simulation-ready asset 的成本。對 photogrammetry-heavy 遊戲、VR 掃描場景、UGC world capture，甚至把真實空間快速變成可玩的關卡，都比「所有東西先人工 retopology 成標準資產」更值得研究。

更進一步可以把這種 coupling 做成 engine invariant：任何從 static world 升格成 interactive object 的資料，都必須同時提供 source removal、revealed-background representation、collision proxy 與 visual-to-physics transform，而不是讓四個 subsystem 各自猜測。

## 想實作時再看

最小 prototype 不必重現生成模型。可以先建立一個小型 Gaussian 或 point-based room，手工標記一件桌上物件，並準備它的完整 mesh。實作四件事即可驗證 abstraction：

1. 以 object mask / bounds 找出並移除原 scene primitives。
2. 用簡單平面或鄰域 interpolation 補回物件下面的背景。
3. 為 mesh 建立 convex collision proxy。
4. 讓 renderer 的 visual asset 與 physics body 共用同一相對 transform。

先測試「拿起物件後是否沒有殘影、洞、視覺／碰撞錯位」，再考慮自動 asset generation。論文實作細節值得優先看 Section III-C 的 candidate registration、三來源 Gaussian removal，以及 Section III-D 的 visual / physical state coupling。

## 個人筆記

這篇真正有價值的不是 3DGS 本身，而是指出 photorealistic world representation 與 interactive world representation 其實不是同一件事。與其要求一種 representation 同時完美服務 rendering、collision、editing 與 hidden geometry，不如明確設計一個「把某部分世界升格成可互動物件」的 conversion boundary。

如果未來遊戲大量使用掃描、生成式場景或 neural representation，這種 boundary 很可能會比單一 reconstruction algorithm 更重要：Engine 要知道的不只是「世界長甚麼樣」，還要知道當某件東西第一次被玩家碰動時，哪些資料必須一起從背景中被分離出來。