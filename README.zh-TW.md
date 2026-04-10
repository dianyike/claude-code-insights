# Claude Code Insights

[English](README.md) | 繁體中文

**中文社群最完整的 Claude Code 進階指南** — 涵蓋 CLAUDE.md 架構設計、Skills 撰寫、Subagent 編排，附可直接使用的實戰範例。

> 由 **dianyike / 典億創研工作室** 維護。獨立接案工程師，專注於網頁設計、爬蟲自動化、API 串接。這個 repo 是我實際接案時使用 Claude Code 的心得整理。
>
> <!-- TODO: 替換為你的實際連結 -->
> [個人網站](https://dianyistudio.com/) · [Threads](https://threads.net/@dianyike1013) · [接案詢問](mailto:service@dianyistudio.com)

## 適合誰

| 你是... | 從這裡開始 | 你會得到什麼 |
|---------|-----------|-------------|
| **剛接觸 Claude Code** | [CLAUDE.md 指南](claude-md-best-practices.zh-TW.md) | 理解三層架構、Hooks 機制，避開最常見的反模式 |
| **已有使用經驗，想進階** | [Skills 指南](skills-best-practices.zh-TW.md) → [Subagent 指南](subagent-best-practices.zh-TW.md) | 掌握 Hub-and-Spoke 架構、決策矩陣、黑箱問題解法 |
| **接案工程師 / 獨立開發者** | [實戰範例](#實戰範例)：grill-me → write-prd → prd-to-plan → tdd | 一套從需求質詢到 TDD 實作的完整工作流程 |

## 內容

| 文件 | 說明 | 適合 |
|------|------|------|
| [claude-md-best-practices.zh-TW.md](claude-md-best-practices.zh-TW.md) | CLAUDE.md 最佳實踐 — 為什麼不該使用 `/init`、三層架構模型、以 Hooks 取代指令、常見反模式 | 新手入門 |
| [skills-best-practices.zh-TW.md](skills-best-practices.zh-TW.md) | Skills 最佳實踐 — 檔案格式、載入機制、內容撰寫原則、進階模式、設計範本 | 進階 |
| [subagent-best-practices.zh-TW.md](subagent-best-practices.zh-TW.md) | Subagent 最佳實踐 — 黑箱問題與解法、結果持久化、工具範圍策略、架構模式 | 進階 |

三份指南互相引用，建議依序閱讀：CLAUDE.md → Skills → Subagent。

## 實戰範例

### Subagent 範例

| 範例 | 說明 | 難度 |
|------|------|------|
| [examples/security-reviewer](examples/security-reviewer) | 雙重驗證安全稽核 — 唯讀的 `/security:review`（Semgrep + Codex 交叉驗證、信心分數）+ 明確 opt-in 的 `/security:fix`（收斂強化 Fix-Verify Loop，含可反駁預測、分級回退、假設帳本）。嚴格的 review/fix 邊界：review 永遠唯讀；fix 需使用者明確觸發且在主對話中執行。實踐 [Harness Engineering](https://openai.com/index/harness-engineering/) 方法論 | 進階 |

### Hook 範例

| 範例 | 說明 | 難度 |
|------|------|------|
| [examples/npm-supply-chain-defense](examples/npm-supply-chain-defense) | npm 供應鏈三層防禦 — `.npmrc` 腳本封鎖 + PreToolUse Hook 檢查（registry、OSV.dev、版本解析、CLI 語法驗證）+ Semgrep 供應鏈掃描，附 42 個回歸測試 | 進階 |

### Skills 範例

以下 Skills 改編自 [mattpocock/skills](https://github.com/mattpocock/skills)，重新整理為：範本抽出至 `templates/`、參考資料移至 `reference/`，並補上 Gotchas 區段。

| 範例 | 說明 | 用途 |
|------|------|------|
| [examples/grill-me](examples/grill-me) | 設計質詢 — 走訪決策樹的每個分支，逐一釐清設計決策間的依賴關係 | 編碼前的設計壓力測試 |
| [examples/write-prd](examples/write-prd) | 撰寫 PRD — 從設計決策或模糊想法產出結構化需求文件，銜接 grill-me 與 prd-to-plan | 需求撰寫與結構化 |
| [examples/tdd](examples/tdd) | TDD 工作流程 — red-green-refactor 垂直切片，附測試範例、mock 指南與深模組設計參考 | 功能開發與 Bug 修復 |
| [examples/prd-to-plan](examples/prd-to-plan) | PRD 轉實作計畫 — 將需求拆成 tracer bullet 垂直切片，輸出至 `./plans/`，並可選擇加入 Codex 審核高風險計畫 | 需求拆解與階段規劃 |
| [examples/write-a-skill](examples/write-a-skill) | Skill Builder 後設 Skill — 內容類型決策、呼叫控制、安全配置、Gotchas 迭代回饋循環，含 eval 工作流參考 | 建立新 Skill |
| [examples/skill-eval-toolkit](examples/skill-eval-toolkit) | Skill 評測工具包 — eval 驅動測試、量化基準測試、盲測 A/B 比較、description 觸發優化，以及 SKILL.md body 的 autopilot keep/revert 迴圈 | 驗證與優化現有 Skill |
| [examples/frontend-design](examples/frontend-design) | Frontend Design — 拒絕 AI 罐頭美學的高品質前端介面。大膽創作自由搭配不可妥協的基線（字級地板、元素遮擋防護、無障礙）。含 SKILL.md + [UMBRA 影展](examples/frontend-design/umbra-film-festival/) hero section 產出展示 | 打造有辨識度的前端介面 |

**個人開發工作流程**：`/grill-me`（質詢設計）→ `/write-prd`（撰寫 PRD）→ `/prd-to-plan`（拆成階段，可選擇用 Codex 審核）→ `/tdd`（逐步實作）

**Skill 開發工作流程**：`/write-a-skill`（撰寫 Skill）→ `/skill-eval-toolkit`（評測與優化）

#### write-prd — PRD 撰寫 Skill

填補 `/grill-me` 和 `/prd-to-plan` 之間的 gap — 將設計決策或模糊想法轉化為結構化 PRD：

- 一次一題的結構化訪談流程（target user → success state → non-goals）
- 強制 P0/P1/P2 優先級、References 引用決策紀錄、`docs/prds/` 輸出慣例
- 停留在產品 / 系統契約層級 — 不洩漏 implementation details（httpOnly cookies、SDK pinning 等）
- Delegated/Eval Mode — 區分 draft artifacts 與 canonical PRD file
- 附 4 個功能 eval case + 12 個觸發測試（經 skill-eval-toolkit 兩輪迭代驗證，pass rate 90%）

```
你：「幫我根據 docs/decisions/login-redesign.md 寫成 PRD」
Claude：（載入 write-prd，讀取決策紀錄，識別 gaps，
         產出含 user stories + traceability 的 PRD 草稿，詢問確認）
```

#### write-a-skill — Skill 撰寫指南

用於**從零建立新的 Skill**，涵蓋完整的撰寫生命週期：

- 內容類型決策（Reference vs Task）與呼叫控制（`disable-model-invocation`、`context: fork` 等）
- Frontmatter schema、漸進式揭露（metadata → body → bundled resources）
- Description 撰寫原則 — 以觸發情境為導向，而非功能摘要
- 安全檢查清單與審查流程
- Gotchas 迭代回饋循環 — 讓 Skill 隨使用愈來愈準的機制

```
你：「我想建一個能從 OpenAPI spec 自動產生 API 文件的 skill」
Claude：（載入 write-a-skill，訪談需求，產出 SKILL.md 草稿，跑 smoke test）
```

#### skill-eval-toolkit — Eval 驅動的測試與優化工具包

用於**評測與改善已存在的 Skill**，提供結構化的 eval 迴圈與 4 個專職 subagent：

| Subagent | 職責 |
|----------|------|
| **grader** | 評估 assertions 是否通過，同時回頭檢視 eval 本身的品質 |
| **comparator** | 盲測 A/B 比較 — 隱藏來源，純粹根據輸出品質評分 |
| **comparison-analyzer** | 事後分析 — 解盲後找出贏家勝出的原因 |
| **benchmark-analyzer** | 從 benchmark 數據中挖掘聚合統計隱藏的模式 |

工作流程：建立測試 prompt → with-skill 與 baseline 並行執行 → 評分 → 聚合 benchmark → 互動式 viewer 供人工審查 → 改善 → 重複。另含自動化 description 觸發優化（train/test split、迭代改進），以及用 benchmark 結果驅動的 SKILL.md body autopilot 迭代。

```
你：「評測我的 json-diff skill，看看它到底有沒有用」
Claude：（載入 skill-eval-toolkit，建測試案例，並行 spawn runs，
         評分輸出，開啟 viewer，呈現結果）
```

> **什麼時候用哪個**：如果問題是「這個 skill 該怎麼寫？」→ `write-a-skill`。如果問題是「這個 skill 到底好不好用？」→ `skill-eval-toolkit`。大部分 skill 從前者起步，需要量化驗證時再引入後者。

> **Gotchas 是 Skill 的靈魂**：一個 Skill 最有價值的往往不是教學內容，而是團隊實際踩過的坑。每次 Skill 執行遇到非預期失敗時，都把失敗模式寫回 Gotchas；這個回饋循環會讓 Skill 隨著使用愈來愈準。詳見 [skills-best-practices.zh-TW.md § 4.3](skills-best-practices.zh-TW.md#43-構建-gotchas-部分)。

> **注意**：這些範例可直接複製到 `.claude/skills/` 中使用。建議先讀完相關指南，以理解設計原理，並依自己的需求調整。

## 快速導覽

### CLAUDE.md 指南重點

- 為什麼不建議用 `/init` 自動產生（附研究數據佐證）
- 從零開始的正確姿勢：先不寫，出問題再加
- 三層架構模型：強制執行層 / 高頻召回層 / 按需查閱層
- 用 Hooks 取代 CLAUDE.md 指令（確定性 > 建議）
- 五大反模式與維護實務

### Skills 指南重點

- Skill 是什麼、與 CLAUDE.md 的差異
- Frontmatter 欄位完整參考
- 自動觸發 vs 手動呼叫的控制方式
- Skill vs Subagent vs CLAUDE.md 決策矩陣
- 安全守則與迭代方法論

### Subagent 指南重點

- 何時該用 Subagent（Anthropic 官方觀點：大多數場景不需要）
- 黑箱與一次性問題的四種解法
- 研究型、審查型 Agent 設計模板
- Hub-and-Spoke 架構模式
- Early Victory Problem 與緩解策略

## 關於作者 / 接案服務

<!-- TODO: 替換為你的實際連結和內容 -->

我是 **dianyike**，經營**典億創研工作室**，獨立接案工程師。

| 服務項目 | 說明 |
|---------|------|
| 網頁設計與開發 | 響應式網站、Landing Page、後台管理系統 |
| 爬蟲自動化 | 資料擷取、定時排程、反爬對策 |
| API 串接與整合 | 第三方 API 對接、資料同步、Webhook 設計 |

有合作需求歡迎聯繫：

- [個人網站](https://dianyistudio.com)
- [Threads](https://threads.net/@dianyike1013)
- [Email](mailto:service@dianyistudio.com)

## 致謝與參考來源

本儲存庫的內容彙整自 Anthropic 官方文件、社群文章與熱門 GitHub 儲存庫，相關觀點與設計模式歸功於原作者。我做的是中文化、結構化整理，並加入自己的實戰經驗與決策框架。

Skills 範例改編自 [mattpocock/skills](https://github.com/mattpocock/skills)，依據本儲存庫的最佳實踐指南重新整理。

## License

[MIT](LICENSE)
