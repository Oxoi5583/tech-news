---
type: paper
title: "DELUGE: Decomposed Entropy-coded Live Unstructured Geometry Exchange for Real-time Particle Streaming"
published: "2026-09-17"
added: "2026-09-20"
authors:
  - "Hikari Yanagawa"
  - "Yuichi Hiroi"
  - "Takefumi Hiraki"
venue: "IEEE Transactions on Visualization and Computer Graphics (TVCG) / IEEE ISMAR 2026"
paper_url: "https://arxiv.org/abs/2609.19750"
code_url: ""
tags:
  - real-time
  - networking
  - compression
  - particle-simulation
  - vr
  - streaming
  - octree
one_liner: "利用粒子的速度與前後幀連續性，把伺服器上的流體、煙霧或顆粒模擬低延遲串流到多個客戶端，而不必讓每台裝置各自重跑物理模擬。"
summary: "DELUGE 不把每一幀粒子當成新的靜態點雲重新壓縮，而是利用模擬器已知的粒子對應、速度與時間連續性，只定期傳完整空間結構，其餘幀傳座標差分；再以平行熵解碼與扁平查表重建位置，將 65K 粒子的編解碼壓到單幀時間預算內。"
---

# DELUGE: Decomposed Entropy-coded Live Unstructured Geometry Exchange for Real-time Particle Streaming

## 先用一個例子理解

假設多人 VR 遊戲裡有一池由伺服器模擬的液體，共有約 65,000 個粒子。兩名玩家可以同時把手伸進去攪動它。

最直接的做法有兩種：每個客戶端自己跑同一套流體模擬，或者伺服器把結果畫成影片再串流。前者要求頭戴裝置有足夠算力，而且多人狀態同步麻煩；後者則會把頭部轉動也綁在遠端畫面的往返延遲上。

DELUGE 選第三條路：**伺服器只跑一份權威物理模擬，但把粒子的幾何狀態直接串流給所有客戶端，由客戶端本地渲染。** 玩家轉頭時不必等待新的影片畫面，而玩家的手部輸入仍可以送回伺服器影響同一份共享模擬。

作者的 Vision Pro prototype 使用 MLS-MPM 流體模擬；65K 粒子的 keyframe 在伺服器端約 4.4 ms 編碼，在 Vision Pro 約 8.4 ms 解碼，壓縮後的同一 packet 可以廣播給任意數量的客戶端，不必為每個玩家重新編碼。

## 原本的做法有甚麼困難

G-PCC、Draco 等點雲壓縮方法主要把輸入視為一組空間中的靜態幾何點。當粒子每一幀都在移動時，這種方法容易反覆重建空間索引；G-PCC 的 octree 也不是為了利用物理模擬本身已知的粒子 ID、速度與前後幀對應而設計。

但物理模擬其實比一般點雲多了很多免費資訊：同一粒子在下一幀通常仍然存在，而且位置不會任意跳躍。DELUGE 的核心就是不把這些資訊丟掉。

作者也比較了 neural dynamic point-cloud codec；這類方法可以追求較高壓縮效率，但部分既有方案需要數百毫秒甚至秒級 GPU inference，與 60 FPS 的 16.67 ms frame budget 不在同一個 execution regime。DELUGE 因此刻意優先追求**低延遲解碼**，而不是最佳 rate-distortion。

## 它是怎樣做到的

整體結構類似影片編碼的 I-frame / P-frame：

```text
Keyframe
  ├─ 完整 octree 空間結構
  └─ 絕對量化座標

Delta frame
  └─ 相對上一幀的量化座標差分
```

DELUGE 再加入三個針對粒子模擬的設計。

### 1. 速度自適應 Octree

粒子速度不同時，固定深度的空間格會產生差異很大的座標殘差。作者因此依最近數幀的粒子位移決定它應落在哪一層 octree：

- 慢粒子放進較深、較小的 cell；
- 快粒子放進較淺、較大的 cell。

這不是單純降低快粒子的精度。每個 leaf 使用的量化 bit 數會跟深度一起改變，使不同深度仍維持近似固定的 world-space quantization step。真正的目的，是讓「位移相對 cell 大小」較一致，令 delta frame 的量化殘差集中在較窄範圍，降低熵。

Octree node 又可以由 Global ID 直接推出 bounds，因此不必逐 leaf 傳送額外幾何範圍。作者也測試 KD-tree 版本；在其設定下，KD-tree 因各 leaf bounds 需要額外描述，而且 binary split 要更深，BD-Rate 比 octree 方案高約 17.4% 至 19.4%。

### 2. XYZ 分開做 rANS 熵編碼

量化後的 x、y、z 不混成一條 symbol stream，而是拆成三條獨立資料流，各自建立頻率表，再使用 rANS（range Asymmetric Numeral Systems，一種可以高效率解碼符號的熵編碼）壓縮。

這有兩個效果：重力等因素會令垂直軸與水平軸的統計分布不同，分開建模可以避免把三種分布平均掉；而三條 payload 在 packet 中物理上也是獨立區域，所以客戶端可以同時解 x、y、z，而不是走一條 sequential entropy-decoding chain。

Delta frame 的座標差分先經 circular differencing 與 ZigZag encoding，把小的正負差值集中到接近零的非負整數，再交給 rANS。

### 3. 把 Octree 解碼結果攤平成每粒子的查表

若每個粒子 inverse quantization 時都回頭 traversal octree 找 leaf bounds，解碼器會被大量 branch 與 tree access 拖慢。

DELUGE 只在 keyframe 到達時建立兩個 flat arrays：每個粒子的 offset 與 scale。之後 delta frame 的位置重建基本上只剩：

```text
position = offset + quantized_value * scale
```

因此 inverse quantization 是固定長度、無 branch、連續記憶體的 O(N) loop，很適合 CPU SIMD。論文設定每 60 幀才重建一次 LUT；65,536 粒子額外需要約 1.6 MB。

整個 client data flow 因而變成：

```text
Network Packet
      ↓
rANS X/Y/Z parallel decode
      ↓
Delta reconstruction
      ↓
Flat LUT inverse quantization
      ↓
Particle positions
      ↓
Local rendering
```

## 與現有方法的差別

DELUGE 最重要的差異不是「發明一個更強的通用點雲 codec」，而是承認 **simulation particles 與任意 point cloud 並不是同一種資料**。

它利用了普通幾何 codec 不一定擁有的條件：粒子有穩定 ID、前後幀有 correspondence、模擬器知道速度，而且使用者真正需要的是很低的 motion-to-interaction latency。因此它願意犧牲部分通用性與最佳壓縮率，換取 predictable、sub-frame 的編解碼成本。

這是一個很值得遊戲引擎借用的設計思想：network representation 不必等於通用 asset representation；如果資料來自一個有明確動力學規則的 subsystem，可以直接利用那個 subsystem 的結構做壓縮。

## 實驗結果與限制

作者在 dynamic point-cloud datasets 上比較 G-PCC（TMC13）與 Draco，報告 DELUGE 約有：

- **20× 較快的 decoding**，相對 G-PCC；
- **6× 較快的 encoding**，相對 Draco。

所有 codec 以 in-process FFI 測量，以減少外部 process overhead 對比較的影響。系統另外實作 Web browser（WASM + SIMD）與 Apple Vision Pro（Swift + Rust FFI）客戶端，並做了主觀品質評估與兩人 Vision Pro 協作實驗。

這些數字不能解讀成 DELUGE 在所有 compression 指標都勝過 G-PCC 或 Draco。作者明確把 decoding latency 放在 rate-distortion efficiency 之前；它也依賴 simulator 提供穩定粒子 ID 與時間連續性，因此不是任意掃描點雲的 drop-in replacement。

此外，這套方法解決的是**模擬結果的傳輸**，不是分散式 physics solver 本身。權威 simulation 仍在 server；多人輸入的 arbitration、prediction、rollback、packet loss recovery、interest management 等遊戲網路問題仍需另一層系統處理。

## 可以怎樣用在遊戲裡

論文已實際證明的是多人 VR 中共享流體粒子場的低延遲串流；以下則是對遊戲引擎的延伸構想。

最直接的用途是讓「大型物理效果只在 server 算一次」變得更合理。例如：

```text
Authoritative Server
  ├─ Fluid
  ├─ Smoke
  ├─ Sand / granular material
  └─ Debris particles
          ↓
    Simulation-aware codec
          ↓
   多個低算力 Client
```

這對 VR MMO 或 persistent world 特別有意思。傳統 replication 常以 rigid-body transform、角色狀態等少量離散 entity 為中心；一旦玩法真的依賴十萬級粒子場，例如玩家共同挖沙、改變泥流、攪動液體，逐 entity replication 很快就不再合適。DELUGE 類型的 codec 可以形成一個專門的 **Particle Replication Channel**。

更值得抽象化的方向是：不同 simulation subsystem 使用不同的 temporal codec，而不是把所有世界狀態硬塞進同一套 replication schema。流體可以利用粒子 velocity；可變形網格可以利用 deformation basis；布料可以利用 topology + vertex residual；大型 voxel field 則可以利用 changed bricks。換句話說，**networking 可以理解 simulation representation，而不只是序列化它。**

## 想實作時再看

最小 prototype 不必先做完整 DELUGE。可以用 C++ 做一個 2D 或 3D 粒子 simulator，固定粒子 ID，然後比較兩種 packet：

```text
Baseline:
每幀直接量化並壓縮所有 position

Prototype:
每 60 幀傳 keyframe
其他幀只傳 quantized delta
```

先量測：

1. encode / decode latency；
2. bytes per particle per frame；
3. reconstruction error；
4. 粒子突然高速運動時 residual entropy 如何變化。

確認 temporal delta 的價值後，再依序加入：

1. velocity-adaptive octree；
2. depth-dependent quantization；
3. x/y/z separated rANS；
4. flat inverse-quantization LUT。

論文最值得直接讀的部分是 Section 2 Proposed Algorithm，尤其 2.1 的 velocity-adaptive depth、2.2 的 axis-separated rANS，以及 2.3 的 flat LUT。若目標是做遊戲 networking prototype，Section 3 的 WebSocket server/client architecture 也很有參考價值。

## 個人筆記

這篇真正有意思的地方不是「點雲壓縮又快了一點」，而是把 **physics simulation 的內部資訊直接變成 networking codec 的先驗**。

一般 engine 很容易形成這種界線：Physics 算完位置，Networking 完全不知道位置從哪裡來，只負責 serialize。DELUGE 則反過來證明，如果 networking 知道這是一群有穩定 ID、有速度、而且時間連續的 physics particles，representation 可以完全不同。

如果未來要做大量可互動的沙、泥、水或破壞碎片，值得研究的未必只是「如何把 simulation 跑快」，也可能是：**如何令昂貴 simulation 只存在一份，而其他玩家仍然能以幾何狀態參與同一個物理世界。**