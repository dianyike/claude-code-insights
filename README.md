# Claude Code Insights

Claude Code Skills 與 Subagent 的中文最佳實踐指南。

本倉庫的內容主要引用、整理自 Anthropic 官方文檔、社群文章及高星 GitHub 倉庫，觀點與設計模式歸功於原作者們。這裡是我在學習過程中所見所聞的東西的整理與分享，而非**原創研究**。

## 適合誰

已有 Claude Code 基礎使用經驗，想進一步掌握 Skills 和 Subagent 設計模式的開發者。

**前置知識**：熟悉 Claude Code 基本操作、了解 `.claude/` 目錄結構、有使用 CLAUDE.md 的經驗。

## 內容

| 文件 | 說明 |
|------|------|
| [skills-best-practices.md](skills-best-practices.md) | Skills 最佳實踐 — 檔案格式、載入機制、內容寫作原則、進階模式、設計模板 |
| [subagent-best-practices.md](subagent-best-practices.md) | Subagent 最佳實踐 — 黑箱問題與解法、結果持久化、工具範圍策略、架構模式 |

兩份指南互相引用，建議都讀。

## 實戰範例

### Subagent 範例

| 範例 | 說明 | 難度 |
|------|------|------|
| [examples/security-reviewer](examples/security-reviewer) | 雙重驗證安全審查 Subagent — Semgrep + Codex 交叉驗證，附信心分數與衝突處理 | 進階 |

### Skills 範例

以下 Skills 參考自 [mattpocock/skills](https://github.com/mattpocock/skills)（設計樹、TDD vertical slice 等概念的實踐），並依據本倉庫的最佳實踐指南進行改造：模板抽離至 `templates/`、參考文件歸入 `reference/`、補齊 Gotchas 區段。

| 範例 | 說明 | 用途 |
|------|------|------|
| [examples/grill-me](examples/grill-me) | 設計質詢 — 遍歷 decision tree 的每個分支，逐一解決設計決策的依賴關係 | 編碼前的設計壓力測試 |
| [examples/tdd](examples/tdd) | TDD 工作流 — red-green-refactor 垂直切片，附測試範例、mock 指南、深模組設計參考 | 功能開發與 Bug 修復 |
| [examples/prd-to-plan](examples/prd-to-plan) | PRD 轉實作計畫 — 將需求拆成 tracer bullet 垂直切片，輸出至 `./plans/` | 需求分解與階段規劃 |
| [examples/write-a-skill](examples/write-a-skill) | Skill 建構指南 — 結構、description 撰寫、拆分時機的元技能 | 建立新的 Skill |

**Solo 開發工作流**：`/grill-me`（質詢設計）→ `/prd-to-plan`（拆成 phase）→ `/tdd`（逐個實作）

> **注意**：範例可直接複製到 `.claude/skills/` 使用。建議先讀完兩份指南，以便理解設計原理並依需求調整。

## 快速導覽

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
