# Claude Code Insights

Claude Code Skills 與 Subagent 的中文最佳實踐指南。

本倉庫的內容主要引用、整理自 Anthropic 官方文檔、社群文章及高星 GitHub 倉庫，觀點與設計模式歸功於原作者們。這裡是我在學習過程中所見所聞的東西的整理與分享，而非**原創研究**。

## 適合誰

從剛接觸 Claude Code 的新手到想深入掌握 Skills 和 Subagent 設計模式的開發者。

- **新手**：從 CLAUDE.md 指南開始，建立正確的基礎觀念
- **進階**：Skills 和 Subagent 指南涵蓋設計模式與架構策略

## 內容

| 文件 | 說明 | 適合 |
|------|------|------|
| [claude-md-best-practices.md](claude-md-best-practices.md) | CLAUDE.md 最佳實踐 — 為什麼不用 `/init`、三層架構模型、Hooks 取代指令、反模式 | 新手入門 |
| [skills-best-practices.md](skills-best-practices.md) | Skills 最佳實踐 — 檔案格式、載入機制、內容寫作原則、進階模式、設計模板 | 進階 |
| [subagent-best-practices.md](subagent-best-practices.md) | Subagent 最佳實踐 — 黑箱問題與解法、結果持久化、工具範圍策略、架構模式 | 進階 |

三份指南互相引用，建議依序閱讀：CLAUDE.md → Skills → Subagent。

## 實戰範例

### Subagent 範例

| 範例 | 說明 | 難度 |
|------|------|------|
| [examples/security-reviewer](examples/security-reviewer) | 雙重驗證安全審查 Subagent — Semgrep + Codex 交叉驗證，附 Fix-Verify 迴圈、信心分數與衝突處理 | 進階 |

### Hook 範例

| 範例 | 說明 | 難度 |
|------|------|------|
| [examples/npm-supply-chain-defense](examples/npm-supply-chain-defense) | npm 供應鏈三層防禦 — `.npmrc` 腳本封鎖 + PreToolUse Hook 檢查（registry、OSV.dev、版本解析、CLI 語法驗證）+ Semgrep supply chain 掃描。附 42 個回歸測試 | 進階 |

### Skills 範例

以下 Skills 參考自 [mattpocock/skills](https://github.com/mattpocock/skills)（設計樹、TDD vertical slice 等概念的實踐），並依據本倉庫的最佳實踐指南進行改造：模板抽離至 `templates/`、參考文件歸入 `reference/`、補齊 Gotchas 區段。

| 範例 | 說明 | 用途 |
|------|------|------|
| [examples/grill-me](examples/grill-me) | 設計質詢 — 遍歷 decision tree 的每個分支，逐一解決設計決策的依賴關係 | 編碼前的設計壓力測試 |
| [examples/tdd](examples/tdd) | TDD 工作流 — red-green-refactor 垂直切片，附測試範例、mock 指南、深模組設計參考 | 功能開發與 Bug 修復 |
| [examples/prd-to-plan](examples/prd-to-plan) | PRD 轉實作計畫 — 將需求拆成 tracer bullet 垂直切片，輸出至 `./plans/` | 需求分解與階段規劃 |
| [examples/write-a-skill](examples/write-a-skill) | Skill 建構元技能 — 內容類型決策、調用控制、安全配置、Gotchas 迭代閉環 | 建立新的 Skill |

**Solo 開發工作流**：`/grill-me`（質詢設計）→ `/prd-to-plan`（拆成 phase）→ `/tdd`（逐個實作）

> **Gotchas 是 Skill 的靈魂**：每個 Skill 裡信號最強的不是教程，而是團隊踩過的坑。每次 Skill 執行遇到非預期失敗，把失敗模式寫回 Gotchas — 這個迭代閉環讓 Skill 越用越準。詳見 [skills-best-practices.md § 4.3](skills-best-practices.md#43-構建-gotchas-部分)。

> **注意**：範例可直接複製到 `.claude/skills/` 使用。建議先讀完兩份指南，以便理解設計原理並依需求調整。

## 快速導覽

### CLAUDE.md 指南重點

- 為什麼不建議用 `/init` 自動生成（附論文數據）
- 從零開始的正確姿勢：先不寫，出問題再加
- 三層架構模型：強制執行層 / 高頻召回層 / 按需查閱層
- 用 Hooks 取代 CLAUDE.md 指令（確定性 > 建議）
- 五大反模式與維護實務

### Skills 指南重點

- Skill 是什麼、與 CLAUDE.md 的差異
- Frontmatter 欄位完整參考
- 自動觸發 vs 手動調用的控制方式
- Skill vs Subagent vs CLAUDE.md 決策矩陣
- 安全守則與迭代方法論

### Subagent 指南重點

- 何時該用 Subagent（Anthropic 官方觀點：大多數場景不需要）
- 黑箱與一次性問題的四種解法
- 研究型、審查型 Agent 設計模板
- Hub-and-Spoke 架構模式
- Early Victory Problem 與緩解策略

## License

[MIT](LICENSE)
