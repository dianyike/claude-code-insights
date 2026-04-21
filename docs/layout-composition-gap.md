# frontend-design skill:排版決策方法的缺口

狀態:待研究。本檔為下一次迭代的起點,非實作計畫。

## 問題

skill 在排版面向已經涵蓋六塊內容:

| 範疇 | 位置 |
|------|------|
| Grid catalog(10 種網格 + 選擇規則) | `references/layout-judgment.md` Layer 2 |
| Star Element(必須主導 + 必須連結內容故事) | `SKILL.md` Design Thinking |
| Spatial Composition(不對稱、重疊、對角流、打破網格、留白 vs 密度) | `SKILL.md` Frontend Aesthetics Guidelines |
| Visual Rhyming(2–3 個 motif 在不同元素間呼應) | 同上 |
| Typography hierarchy(層級與空間關係) | `references/layout-judgment.md` Layer 3 |
| Focal hierarchy check(眯眼測試) | `SKILL.md` Editing Pass step 2 |

**缺的不是內容,是決策方法**。skill 規範了「有哪些排版選項」與「必須遵守的底線」,但沒有教「如何從這篇具體內容的情緒/節奏,推導出應該用哪種構圖」。

## 觀察證據

測試題「餘燼季刊 — 陶藝師訪談(慢慢做一件事)」產出:
- 技術層面全部合規(65ch measure、skip link、modal focus、token 命名)
- 視覺層面走「Manuscript + marginalia + 巨型 07 + drop cap」的編輯類套路
- 問題:陶藝師主題是「慢、沉默、等待」,但版面本身沒有呼應這個情緒。大 hero + 大 drop cap 是外放的、有重量的,而不是安靜、留白、有呼吸的構圖

產出並非不好,只是落在「編輯排版的統計平均」,不是為這個內容量身的構圖。

## 兩條修補路徑

### 路徑 1 — 參考圖(低成本,治標)

下題時附 2–3 張使用者認可的參考頁,skill 已支援 `references/styles/` 的抽圖流程,會先做跨圖分析再動手。能把產出從「平均的編輯味」拉到「某個具體刊物的味道」,但只解決**視覺語彙**,不解決**構圖意圖**。

### 路徑 2 — 在 Purpose 層補「節奏/呼吸」決策題(根本解)

目前 Purpose 層只問三題:
- reader intent
- success criteria
- information density

density 是一個量的問題(密/疏),但**不是情緒節奏的問題**。「慢」和「快」可以都是低密度,但版面該長什麼樣截然不同。

建議在 Purpose 層補一題大約這樣:

> **Pace & breath** — What rhythm should the layout itself carry?
> - **Slow / patient** — generous negative space, small hero, low contrast, reader pauses built into the scroll
> - **Taut / urgent** — compressed spacing, high contrast, directional flow, no dead zones
> - **Quiet / reverent** — single-column, extreme left/right asymmetry, heavy silence around a small focal
> - **Loud / kinetic** — overlap, diagonal flow, scale jumps, multiple competing elements
>
> The content's emotional register decides this, not the category of product. An interview about slowness and a meditation app can both be "slow / patient" — a news site and a product launch can both be "taut / urgent."

有這題之後,`Star Element` 的大小/位置、grid 的選擇、留白的比重就會被推導出來,而不是從 catalog 挑套路。

## 為什麼不立刻動手

- 路徑 1 可以直接驗證(下次丟題加上參考圖),不需改 skill
- 路徑 2 是 skill 結構改動,影響所有未來產出,應先觀察路徑 1 的效果再決定
- 兩條路徑不互斥,但先後順序會影響最終寫法

## 下一次迭代要決定的事

1. 路徑 1 先做一輪驗證,還是直接走路徑 2
2. 如果走路徑 2,「節奏/呼吸」的分類要用哪幾種?上面 4 種是直覺舉例,未必是最終切法
3. 要不要同步更新 `references/layout-judgment.md` Layer 1,把節奏題加到現有三題之後(變四題),還是獨立成新 reference
