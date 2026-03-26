# Claude Code Skills 最佳實踐指南

> 本指南的啟發來源：[从开发、评估到安全使用，构建 skill：精读《Equipping agents for the real world with Agent Skills》 ③](https://www.bilibili.com/video/BV1ZmCLBmExv/)
>
> 基於 Anthropic 官方文檔、高星 GitHub 倉庫、社群經驗及 [Lessons from Building Claude Code: How We Use Skills](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc) 整理

---

## 目錄

1. [Skill 是什麼](#1-skill-是什麼)
2. [核心架構：漸進式載入](#2-核心架構漸進式載入)
3. [SKILL.md 檔案格式](#3-skillmd-檔案格式)
4. [內容寫作原則](#4-內容寫作原則)
5. [Frontmatter 欄位完整參考](#5-frontmatter-欄位完整參考)
6. [Skill 類型與調用控制](#6-skill-類型與調用控制)
7. [目錄結構與存放位置](#7-目錄結構與存放位置)
8. [進階模式](#8-進階模式)
9. [Skill vs Subagent vs CLAUDE.md 決策矩陣](#9-skill-vs-subagent-vs-claudemd-決策矩陣)
10. [最佳實踐設計模板](#10-最佳實踐設計模板)
11. [Skill 與 Subagent 的協作](#11-skill-與-subagent-的協作)
12. [安全守則](#12-安全守則)
13. [迭代方法論](#13-迭代方法論)
14. [常見問題排查](#14-常見問題排查)
15. [參考資源](#15-參考資源)
16. [快速檢查清單](#16-快速檢查清單)

---

## 1. Skill 是什麼

Skill 是由**指令、腳本、和資源**組成的結構化資料夾，Claude 能夠動態發現並載入這些內容，以提升特定任務的表現。

> 來源：[Extend Claude with skills](https://code.claude.com/docs/en/skills)

### 核心定義

- 每個 Skill 以一個 `SKILL.md` 檔案為入口，搭配可選的腳本和參考資料
- Claude 根據 `description` 自動判斷是否載入，或由用戶透過 `/skill-name` 手動觸發
- 遵循 [Agent Skills](https://agentskills.io) 開放標準，跨工具相容

### 關鍵能力

| 能力 | 說明 |
|------|------|
| **可發現** | Claude 掃描所有 skill 的 `name` + `description`，自動判斷是否觸發 |
| **可操作** | 不只提供知識，還能執行腳本、呼叫工具、產出檔案 |
| **可複用** | 同一 skill 可跨專案（`~/.claude/skills/`）或跨組織（enterprise）共用 |
| **支援 Hooks** | 可在 skill 生命週期中註冊動態 hooks |
| **靈活配置** | 工具白名單、model 選擇、effort 等級、subagent 隔離 |
| **目錄結構** | 善用子目錄放置模板、範例、腳本、參考文檔 |

### Skill 的目標

**封裝可移植、可複用的過程知識。** `name` 和 `description` 必定載入 context（用於發現），完整指令僅在觸發時載入（節省 context）。Skill 可以閱讀腳本也可以執行腳本。

### Custom commands 已合併為 Skills

`.claude/commands/deploy.md` 和 `.claude/skills/deploy/SKILL.md` 都會建立 `/deploy`，行為相同。既有的 commands 繼續有效，但 skills 提供額外功能：支援子目錄放置附檔、frontmatter 控制觸發方式、Claude 可自動載入。

---

## 2. 核心架構：漸進式載入

Skill 採用**三層漸進式載入（Progressive Disclosure）**，最大化 context 效率：

```
第一層：YAML metadata（~100 tokens）
  ↓ Claude 掃描所有 skill 的 name + description，判斷相關性
第二層：SKILL.md 正文（<5k tokens 建議）
  ↓ 只在 skill 被觸發時載入完整指令
第三層：附錄檔案（unlimited）
  ↓ 只在 SKILL.md 中被明確引用時才載入
```

### 為什麼這很重要

- **第一層永遠在 context 中**：所有 skill 的 description 佔用約 2% 的 context window（fallback 上限 16,000 字元）
- **第二層按需載入**：不需要的 skill 不會浪費 context
- **第三層延遲載入**：大型 API 文檔、範例集不必每次都載入

### Context 預算

Skill descriptions 的總量上限動態計算為 context window 的 2%，fallback 為 16,000 字元。超過時部分 skill 會被排除。可用 `/context` 檢查，或設定環境變數 `SLASH_COMMAND_TOOL_CHAR_BUDGET` 覆蓋。

---

## 3. SKILL.md 檔案格式

每個 Skill 必須有一個 `SKILL.md` 檔案，由兩部分組成：

```yaml
---
# ===== YAML Frontmatter =====
name: my-skill                    # 顯示名稱，小寫字母 + 數字 + 連字號（max 64 字元）
description: >                    # Claude 據此判斷是否觸發（max 1024 字元）
  Reviews Python code for bugs and readability issues.
  Use when user asks to review, check, or audit code.
---

# ===== Markdown 正文：Skill 指令 =====

## 工作流程

1. 第一步
2. 第二步

## 輸出格式

...
```

### 兩種內容類型

**Reference Content（參考型）**：提供知識，Claude 將其融入當前工作。適合內聯執行。

```yaml
---
name: api-conventions
description: API design patterns for this codebase
---

When writing API endpoints:
- Use RESTful naming conventions
- Return consistent error formats
- Include request validation
```

**Task Content（任務型）**：給 Claude 具體的步驟化指令。通常搭配 `disable-model-invocation: true`，由用戶手動觸發。

```yaml
---
name: deploy
description: Deploy the application to production
context: fork
disable-model-invocation: true
---

Deploy the application:
1. Run the test suite
2. Build the application
3. Push to the deployment target
```

---

## 4. 內容寫作原則

> 來源：[Lessons from Building Claude Code: How We Use Skills](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)（Thariq Shihipar, Anthropic）

### 4.1 Description 是給模型看的，不是給人看的

Claude 啟動會話時，會掃描所有 Skill 的 `description`，決定這個請求有沒有對應 Skill。因此 description 應寫**觸發時機**，而非功能摘要。

```yaml
# ❌ 不好的寫法 — 像產品說明書
description: A tool for monitoring pull requests

# ✅ 好的寫法 — 寫觸發時機和用戶會說的詞
description: >
  Trigger when user says babysit, watch CI, monitor PRs,
  or check pipeline status.
```

### 4.2 不陳述顯而易見的事

Claude 已經掌握大量通用程式設計知識。Skill 不該重複教材，而該補充 Claude **默認不知道**的內容：

| 該寫 | 不該寫 |
|------|--------|
| 你們團隊的特殊慣例和偏好 | 語言語法和標準庫用法 |
| 專案特有的上下文和歷史 | 通用設計模式教學 |
| 外部系統的連接方式和認證流程 | 框架基礎教程 |
| 踩過的坑和 workaround | 官方文檔已涵蓋的內容 |

### 4.3 構建 Gotchas 部分

任何 Skill 裡**信號最強**的，往往不是教程，而是 Gotchas（踩坑記錄）。因為只有你們團隊真正遇過的問題才是獨特知識。

```markdown
## Gotchas

- `api/v2/users` 返回的 `created_at` 是 UTC，但 `updated_at` 是本地時區（已提 issue，短期內不會修）
- 測試環境的 rate limit 是 10 req/s，不是文檔寫的 100 — 批量測試必須加 delay
- deploy 腳本在 macOS 上會靜默跳過 migration，必須加 `--force-migrate` flag
```

**迭代建議**：Gotchas 部分應隨使用持續更新。每次 Claude 在執行 Skill 時遇到非預期失敗，將失敗模式補入 Gotchas。

### 4.4 約束目標，不約束路徑

避免過度約束 Claude 的執行步驟。給出**要達成的目標**，而非固定的操作順序：

```markdown
# ❌ 過度約束 — 限制了靈活性
1. Run `npm test`
2. Run `npm run lint`
3. Run `npm run build`
4. Deploy

# ✅ 約束目標 — Claude 根據情況調整順序
Ensure the code passes all tests and lint checks, then build and deploy.
Adapt the order based on the current state (e.g., skip build if only docs changed).
```

---

## 5. Frontmatter 欄位完整參考

| 欄位 | 必填 | 說明 |
|------|------|------|
| `name` | 推薦（技術上可選） | 顯示名稱，省略則使用目錄名。小寫字母、數字、連字號（max 64 字元）。官方 Help Center 列為 required metadata |
| `description` | 推薦（技術上可選） | Skill 做什麼、何時使用。Claude 據此判斷是否觸發。省略則使用正文第一段（max 1024 字元）。官方 Help Center 列為 required metadata |
| `argument-hint` | 否 | 自動補全時顯示的提示。如 `[issue-number]`、`[filename] [format]` |
| `disable-model-invocation` | 否 | 設為 `true` 阻止 Claude 自動觸發，僅能手動 `/name`。預設 `false` |
| `user-invocable` | 否 | 設為 `false` 隱藏於 `/` 選單，僅 Claude 可觸發。預設 `true` |
| `allowed-tools` | 否 | Skill 執行時 Claude 可用的工具白名單（如 `Read, Grep, Glob`） |
| `model` | 否 | Skill 執行時使用的 model |
| `effort` | 否 | 推理力度：`low` / `medium` / `high` / `max`（`max` 僅 Opus 4.6） |
| `context` | 否 | 設為 `fork` 在 subagent 中隔離執行 |
| `agent` | 否 | `context: fork` 時指定使用的 subagent 類型（如 `Explore`、`Plan`、自訂 agent） |
| `hooks` | 否 | Skill 生命週期的 hooks 設定 |

> **以下欄位非 Claude Code 原生支援** — Claude Code 的 frontmatter 解析器不處理這些欄位，寫入後不會產生任何效果。列於此處僅供參考。

| 欄位 | 來源 | 說明 |
|------|------|------|
| `mode` | 第三方原始碼分析 | 設為 `true` 將 skill 歸類為 Mode Command。未列於官方 frontmatter reference，行為可能隨版本變動 |
| `version` | [Agent Skills](https://agentskills.io) 開放標準 | 版本追蹤用 metadata，如 `"1.0.0"` |
| `compatibility` | [Agent Skills](https://agentskills.io) 開放標準 | 聲明所需工具和依賴 |
| `license` | [Agent Skills](https://agentskills.io) 開放標準 | 授權聲明（如 `MIT`），用於可分享的 skill |

### 字串替換變數

| 變數 | 說明 |
|------|------|
| `$ARGUMENTS` | 調用 skill 時傳入的全部參數 |
| `$ARGUMENTS[N]` / `$N` | 按位置存取第 N 個參數（0-based） |
| `${CLAUDE_SESSION_ID}` | 當前 session ID |
| `${CLAUDE_SKILL_DIR}` | Skill 的 `SKILL.md` 所在目錄的絕對路徑 |

---

## 6. Skill 類型與調用控制

### 調用模式矩陣

| Frontmatter 設定 | 用戶可觸發 | Claude 可觸發 | Context 載入行為 |
|------------------|-----------|--------------|-----------------|
| （預設） | Yes | Yes | description 永遠在 context，完整內容觸發時載入 |
| `disable-model-invocation: true` | Yes | No | description **不在** context，用戶觸發時載入 |
| `user-invocable: false` | No | Yes | description 永遠在 context，Claude 觸發時載入 |

### 何時用哪種

| 類型 | 設定 | 適用場景 |
|------|------|---------|
| **雙向觸發** | 預設 | 通用工具、程式碼解釋、格式化 |
| **僅用戶觸發** | `disable-model-invocation: true` | 有副作用的操作：deploy、commit、send message |
| **僅 Claude 觸發** | `user-invocable: false` | 背景知識：legacy-system-context、coding-style |

### 關鍵原則

> **有副作用的 skill 必須設 `disable-model-invocation: true`。** 你不會希望 Claude 因為程式碼看起來準備好了就自動 deploy。

---

## 7. 目錄結構與存放位置

### Skill 目錄結構

```
my-skill/
├── SKILL.md              # 主指令（必要）— 控制在 500 行以內
├── reference.md          # 詳細 API 文檔（按需載入）
├── examples.md           # 使用範例（按需載入）
├── templates/
│   └── output-template.md  # 輸出模板
└── scripts/
    └── helper.py         # 可執行腳本
```

在 `SKILL.md` 中引用附檔，讓 Claude 知道何時載入：

```markdown
## Additional resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

### 存放位置與優先級

| 位置 | 路徑 | 適用範圍 |
|------|------|---------|
| Enterprise | 透過 managed settings 部署 | 組織所有用戶 |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | 個人所有專案 |
| Project | `.claude/skills/<skill-name>/SKILL.md` | 僅此專案 |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Plugin 啟用處 |

**優先級**：Enterprise > Personal > Project。同名 skill 高優先級覆蓋低優先級。Plugin skills 使用 `plugin-name:skill-name` 命名空間，不會衝突。

### Monorepo 支援

在子目錄中工作時，Claude 會自動發現巢狀的 `.claude/skills/` 目錄。例如編輯 `packages/frontend/` 中的檔案時，也會載入 `packages/frontend/.claude/skills/`。

### --add-dir 額外目錄

透過 `--add-dir` 加入的目錄中的 `.claude/skills/` 會自動載入，且支援即時變更偵測。

---

## 8. 進階模式

### 8.1 動態 Context 注入

`` !`<command>` `` 語法在 skill 送達 Claude 前先執行 shell 命令，輸出替換佔位符：

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

執行順序：
1. 每個 `` !`<command>` `` 立即執行（Claude 尚未看到任何東西）
2. 輸出替換 skill 中的佔位符
3. Claude 收到已渲染的完整 prompt

### 8.2 Subagent 隔離執行

`context: fork` 讓 skill 在獨立的 subagent context 中執行：

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:

1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**注意**：`context: fork` 只適用於有明確任務指令的 skill。如果 skill 只包含指南（如「使用這些 API 慣例」）而沒有具體任務，subagent 收到指南但沒有可執行的 prompt，會無意義地返回。

### 8.3 存儲腳本與視覺化輸出

**核心原則**：把穩定的能力封裝成腳本和輔助函數，讓 Claude 負責**組合**而非重造輪子。別讓 Claude 每次都從頭寫樣板代碼——給它代碼，不給它文檔。

Skill 可以打包並執行任何語言的腳本，產出互動式 HTML 等視覺化內容：

````yaml
---
name: codebase-visualizer
description: Generate an interactive tree visualization of your codebase
allowed-tools: Bash(python *)
---

# Codebase Visualizer

Run the visualization script:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```
````

這個模式適用於：依賴圖、測試覆蓋報告、API 文檔、資料庫 schema 視覺化等。

### 8.4 Extended Thinking

在 skill 內容中包含 "ultrathink" 一詞即可啟用 extended thinking。

### 8.5 Config 狀態管理（有狀態 Skill）

> 來源：[Lessons from Building Claude Code](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

Skill 每次運行都是無狀態的。用 `config.json` 存儲用戶偏好，讓 Skill 從**無狀態工具**變成**有狀態助手**：

```yaml
---
name: deploy
description: Deploy application. Trigger on deploy, ship, release.
disable-model-invocation: true
allowed-tools: Read, Write, Bash(npm *), Bash(git *)
---

# Deploy

## Setup (first run only)

Check if `${CLAUDE_SKILL_DIR}/config.json` exists.
If not, ask the user for:
- Default deploy target (staging / production)
- Notification channel (Slack webhook URL)
- Whether to run migrations automatically

Save answers to `${CLAUDE_SKILL_DIR}/config.json`.

## Subsequent runs

Read `${CLAUDE_SKILL_DIR}/config.json` and use saved preferences.
```

### 8.6 日誌記憶（跨次運行的增量報告）

> 來源：[Lessons from Building Claude Code](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

Skill 不記得上次做了什麼。解決方案：讓 Skill 寫日誌，下次運行時讀取日誌，只報告**增量變化**：

```yaml
---
name: babysit-prs
description: >
  Monitor open PRs and report status changes.
  Trigger on babysit, watch PRs, check pipeline.
allowed-tools: Read, Write, Bash(gh *)
---

# PR Babysitter

## Workflow

1. Read the log at `${CLAUDE_SKILL_DIR}/data/run-log.jsonl`
   (if it exists — first run will have no log)
2. Fetch current PR statuses: `gh pr list --json number,title,statusCheckRollup`
3. Compare with last log entry — identify what CHANGED since last run
4. Report only the deltas (new failures, newly passing, new PRs)
5. Append current state to `${CLAUDE_SKILL_DIR}/data/run-log.jsonl`
```

**關鍵**：日誌用 JSONL 格式（每行一條 JSON），方便追加和解析。每條記錄包含時間戳和完整狀態快照。

### 8.7 按需 Hooks（會話級護欄）

> 來源：[Lessons from Building Claude Code](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)

有些安全規則太嚴格，不適合一直開啟。用 Skill 動態註冊 Hook，會話結束後自動失效：

```yaml
---
name: careful
description: >
  Enable extra safety checks for the current session.
  Trigger on careful, safe mode, paranoid mode.
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: Bash
      command: |
        # Block dangerous commands in careful mode
        echo "$TOOL_INPUT" | grep -qE '(rm -rf|drop table|force push|--no-verify)' \
          && echo "BLOCKED: dangerous command detected in careful mode" \
          && exit 1
        exit 0
---

# Careful Mode Enabled

Extra safety hooks are now active for this session:

- `rm -rf` commands are blocked
- `drop table` SQL is blocked
- `git push --force` is blocked
- `--no-verify` flag is blocked

To disable, end the session or start a new one.
```

**設計理念**：不是永久限制能力，而是在高風險操作時臨時提升安全等級。會話結束後 Hook 自動失效，不影響日常工作流。

---

## 9. Skill vs Subagent vs CLAUDE.md 決策矩陣

| 因素 | Skill | Subagent | CLAUDE.md |
|------|-------|----------|-----------|
| **持久性** | 資料夾，自動載入 | Fork context，隔離執行 | 永遠載入 |
| **Context 成本** | 漸進式（按需載入） | 獨立 context window | 永遠佔用 context |
| **複用性** | Project / Personal / Enterprise 三級 | 專案級 | 專案級 |
| **自動化** | 支援自動觸發 | 由主 agent 委派 | 被動載入 |
| **適合內容** | 可重複的過程/工作流 | 需要 context 隔離的任務 | 全域規則和慣例 |

### 什麼時候用什麼

| 場景 | 選擇 | 原因 |
|------|------|------|
| 你經常重複輸入同一段 prompt | **Skill** | 封裝為可重複觸發的指令 |
| 需要 Claude 始終遵守的規則 | **CLAUDE.md** | 每次對話都載入 |
| 子任務會帶入大量不相關資訊 | **Subagent** | Context 隔離，只回傳摘要 |
| 需要執行腳本並產出檔案 | **Skill** | 支援打包腳本和 `allowed-tools` |
| 背景知識，但不是每次都需要 | **Skill**（`user-invocable: false`） | 按需載入，不浪費 context |
| 需要來回溝通的規劃任務 | **主對話 + Plan Mode** | 需要用戶即時參與 |

---

## 10. 最佳實踐設計模板

### 模板一：Reference Skill（背景知識型）

````yaml
---
name: coding-style
description: >
  Immutable coding patterns, naming conventions, and file organization rules.
  Use when writing or reviewing code in this project.
user-invocable: false
---

# Coding Style Guide

## Immutability (CRITICAL)

ALWAYS create new objects, NEVER mutate existing ones:

```
WRONG:  modify(original, field, value) -> changes original in-place
CORRECT: update(original, field, value) -> returns new copy with change
```

## File Organization

- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Organize by feature/domain, not by type

## Additional resources

- For complete patterns, see [reference.md](reference.md)
````

### 模板二：Task Skill（任務型，僅用戶觸發）

```yaml
---
name: deploy
description: Deploy the application to staging or production environment
disable-model-invocation: true
context: fork
allowed-tools: Bash(npm *), Bash(git *), Read, Grep
argument-hint: [environment]
---

# Deploy Application

Deploy to $ARGUMENTS environment.

## Pre-flight checks

1. Run the full test suite: `npm test`
2. Verify no uncommitted changes: `git status`
3. Confirm current branch is `main`

## Deploy steps

1. Build the application: `npm run build`
2. Run deployment script: `npm run deploy:$0`
3. Verify deployment health check

## Post-deploy

1. Run smoke tests against deployed environment
2. Report deployment status with version and timestamp

## Failure handling

If any step fails, STOP immediately and report:
- Which step failed
- The error output
- Suggested remediation
```

### 模板三：Research Skill（研究型，fork 執行）

```yaml
---
name: deep-research
description: >
  Research a library, framework, or technical topic thoroughly.
  Use when comparing technologies, investigating architecture, or
  answering "what should we use for X?" questions.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

# Deep Research

Research $ARGUMENTS thoroughly.

## Workflow

1. **Define scope**: Clarify what exactly needs to be researched
2. **Multi-source collection**: Search web, read docs, explore codebase
3. **Cross-validate**: Compare findings across at least 3 independent sources
4. **Synthesize**: Produce structured findings with specific references

## Output format

Return a structured summary:

### Key findings
- 3-5 bullet points of core discoveries

### Detailed analysis
- Comparison table if multiple options
- Pros/cons with concrete evidence

### Recommendation
- Specific, actionable recommendation with rationale

### Sources
- List all sources consulted
```

### 模板四：Workflow Skill（含腳本和模板）

```yaml
---
name: create-component
description: >
  Scaffold a new React component with tests, stories, and types.
  Use when user asks to create, scaffold, or generate a component.
allowed-tools: Read, Write, Bash(npm *)
argument-hint: [ComponentName]
---

# Create Component

Scaffold a new React component named `$0`.

## Steps

1. Read the template files in this skill directory:
   - [templates/component.tsx.md](templates/component.tsx.md)
   - [templates/component.test.tsx.md](templates/component.test.tsx.md)

2. Create the component directory: `src/components/$0/`

3. Generate files using the templates, replacing `{{ComponentName}}` with `$0`

4. Run type check: `npm run typecheck`

5. Run the new test: `npm test -- --testPathPattern=$0`

## Completion criteria

- [ ] Component file created and exports correctly
- [ ] Test file created and passes
- [ ] TypeScript compiles without errors
```

### 模板五：PR 審查 Skill（動態注入）

```yaml
---
name: review-pr
description: >
  Review the current pull request for quality, security, and best practices.
  Use when asked to review, check, or audit a PR.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(gh *)
---

# Pull Request Review

## Context (auto-injected)

- PR description: !`gh pr view --json title,body --jq '.title + "\n" + .body'`
- Changed files: !`gh pr diff --name-only`
- Diff stats: !`gh pr diff --stat`

## Review dimensions

You MUST review ALL of the following dimensions:

1. **Correctness**: Logic errors, edge cases, off-by-one errors
2. **Security**: OWASP Top 10 checks, input validation, secret exposure
3. **Performance**: Unnecessary computation, N+1 queries, memory leaks
4. **Readability**: Naming, structure, comments, complexity
5. **Testing**: Are changes covered by tests? Are edge cases tested?

## Output format

### Summary

| Dimension | Status | Issues |
|-----------|--------|--------|
| Correctness | PASS/FAIL | count |
| Security | PASS/FAIL | count |
| Performance | PASS/FAIL | count |
| Readability | PASS/FAIL | count |
| Testing | PASS/FAIL | count |

### Critical issues (must fix)
...

### Suggestions (nice to have)
...

## Anti-early-victory

You MUST complete ALL review dimensions before returning results.
Do NOT review only part of the diff and declare "looks good."
Each dimension must have a concrete finding (pass or issue found).
```

---

## 11. Skill 與 Subagent 的協作

Skill 和 Subagent 是互補的兩個系統，可以雙向整合：

### 方向一：Skill → Subagent（`context: fork`）

Skill 內容成為 subagent 的任務 prompt，由 `agent` 欄位決定執行環境：

```yaml
# SKILL.md
---
name: my-task
context: fork
agent: Explore      # 使用 Explore agent 的 model、工具和權限
---

（這裡的內容成為 subagent 收到的任務）
```

### 方向二：Subagent → Skill（`skills` 欄位）

Subagent 定義中用 `skills` 欄位預載 skill 作為參考知識：

```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
tools: Read, Grep, Glob, Write
skills: coding-style           # 預載 coding-style skill 的完整內容
---

（Subagent 的系統提示詞）
```

### 整合摘要

| 方向 | System Prompt | 任務 | 額外載入 |
|------|--------------|------|---------|
| Skill + `context: fork` | 來自 agent 類型 | SKILL.md 內容 | CLAUDE.md |
| Subagent + `skills` | Subagent 的 markdown body | Claude 的委派訊息 | 預載的 skills + CLAUDE.md |

> **WARNING**：`context: fork` 只適用於有**明確任務指令**的 skill。如果 skill 只包含指南（如「使用這些 API 慣例」）而沒有具體任務，subagent 收到指南但沒有可執行的 prompt，會無意義地返回。在「方向一」中使用 `context: fork` 時，SKILL.md 正文**必須包含可執行的任務描述**，不能只有參考知識。

### 分工原則

| 內容類型 | 放在哪裡 | 原因 |
|---------|---------|------|
| 輸出格式範例 | Skill 或 Subagent prompt | Agent 自身的工作規格 |
| 程式碼風格/慣例 | Skill（`user-invocable: false`） | 通用知識，多 agent 共用 |
| 函式庫用法範例 | MCP（如 Context7） | 即時取得最新文檔 |
| 可重複的工作流程 | Skill（task content） | 封裝為可觸發的指令 |
| 需要 context 隔離的重任務 | Subagent | 獨立 context window |

---

## 12. 安全守則

Skill 能運行腳本、存取檔案系統，安全意識必須同步升級。

### 三條安全紅線

| 紅線 | 說明 |
|------|------|
| **只安裝可信來源** | 不要執行來歷不明的技能包或腳本 |
| **使用前逐項檢查** | 仔細閱讀 skill 內所有檔案，尤其是腳本、依賴、外部連接 |
| **理解執行邏輯** | 分清哪些程式碼要跑、輸入輸出是什麼，避免誤觸 |

### 安全配置

| 手段 | 說明 |
|------|------|
| `allowed-tools` | 限縮 Claude 可用的工具範圍，防止未授權的 API 呼叫或檔案操作 |
| `disable-model-invocation: true` | 有副作用的 skill 必須手動觸發 |
| `context: fork` | Subagent 隔離，防止副作用污染主對話 |
| Permission rules | 用 `Skill(deploy *)` deny rule 封鎖特定 skill |

### 威脅意識

社群已追蹤數百種惡意 skill 模式（如 Unicode injection、隱藏指令、auto-execute 模式），相關統計可參見 [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) 等社群安全威脅資料庫，**數字為社群非官方統計，未經 Anthropic 官方驗證**。**安全不等於限制能力，而是保護信任。** Skill 的開放性讓 Claude 真能「做事」，但也意味著更大的攻擊面。

---

## 13. 迭代方法論

### 第一步：從評估開始（問題驅動）

1. 先讓 Claude 執行真實任務，**記錄出錯點和卡頓點**
2. 每個 Skill 都針對具體缺口，不要建「以防萬一」的 skill
3. 小步驗證、逐步擴展

### 第二步：為規模而設計（分層結構）

1. 主流程寫在 `SKILL.md`（<500 行）
2. 細節拆到 `reference/`、`templates/`、`examples/` 等附檔
3. 遵循漸進式載入：metadata（~100 tokens） → 正文（<5k） → 附錄（unlimited）

### 第三步：從 Claude 的視角命名與描述

1. `name` + `description` 決定 Claude 是否觸發，越精準越好
2. **description 寫觸發時機，不是功能摘要**（參見 §4.1）
3. description 包含用戶可能說的關鍵字，以動詞開頭
4. 監控實際使用：是否誤觸或漏觸，作為迭代依據
5. 用 `PreToolUse` hook 記錄 skill 觸發頻率，找出 undertrigger 的 skill

### 第四步：與 Claude 一起迭代

1. **成功時**：讓 Claude 總結「哪些做法有效」，寫回 Skill
2. **失敗時**：引導它反思缺口，再補入 SOP
3. 形成**人機共創的學習閉環**

---

## 14. 常見問題排查

| 問題 | 根因 | 解法 |
|------|------|------|
| Skill 不觸發 | description 模糊或關鍵字不匹配 | 重寫 description，包含用戶自然會說的詞。用 `/skill-name` 確認 skill 存在 |
| 錯誤的 Skill 觸發 | 多個 skill 的 description 重疊 | 提高各 skill description 的區分度 |
| Skill 過度觸發 | description 太寬泛 | 加 `disable-model-invocation: true`，或縮窄 description |
| Claude 看不到某些 Skill | Skill 總量超過 context 預算 | 用 `/context` 檢查，移除不需要的 skill，或調高 `SLASH_COMMAND_TOOL_CHAR_BUDGET` |
| 附檔沒被載入 | SKILL.md 未引用該檔案 | 在 SKILL.md 中明確用 markdown link 指向附檔 |
| 修改後不生效 | 編輯了錯誤位置的 skill | 確認路徑和優先級（Enterprise > Personal > Project） |
| `context: fork` 無輸出 | Skill 只有指南沒有任務 | `context: fork` 需要明確的任務指令，不能只有參考知識 |

---

## 15. 參考資源

### 官方文檔

- [Extend Claude with skills](https://code.claude.com/docs/en/skills) — 官方完整參考
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — 官方寫作指南
- [How to create custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) — Help Center 教學
- [Agent Skills open standard](https://agentskills.io) — 跨工具相容標準

### 官方團隊文章

- [Lessons from Building Claude Code: How We Use Skills](https://www.linkedin.com/pulse/lessons-from-building-claude-code-how-we-use-skills-thariq-shihipar-iclmc)（Thariq Shihipar, Anthropic）— 9 條實戰最佳實踐，涵蓋內容層、結構層、高級技術層。本指南 §4、§8.5-8.7 的主要來源
- [A complete guide to building skills for Claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude) — 官方完整建構指南

### 高星 GitHub 倉庫

| 倉庫 | 特點 |
|------|------|
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | 策展 Claude Skills 集合，分類清晰 |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 680+ agent skills，含官方團隊和社群貢獻 |
| [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) | 135 agents + 35 skills + 42 commands 的綜合工具包 |
| [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) | 14 個生產級 skill 範本，含安全威脅資料庫 |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 綜合策展，含 skills、hooks、plugins |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 社群策展 Skills 集合 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 17 個高品質 Skills — grill-me（設計樹質詢）、tdd（垂直切片 TDD）、write-a-prd / prd-to-plan（需求到實作計畫）等，設計模式值得參考 |

### 延伸閱讀

- [Claude Skills Explained (AnalyticsVidhya)](https://www.analyticsvidhya.com/blog/2026/03/claude-skills-custom-skills-on-claude-code/) — 架構深度解析
- [Essential Claude Code Skills and Commands](https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/) — 實用技巧
- [10 Must-Have Skills for Claude (Medium)](https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051) — 社群推薦
- [Skill Issue: Harness Engineering for Coding Agents (HumanLayer)](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — Skills 作為漸進式披露的實踐案例，含 context 腐蝕研究數據
- [Harness Engineering: leveraging Codex in an agent-first world (OpenAI)](https://openai.com/index/harness-engineering/) — OpenAI 的 agent 工程方法論

---

## 16. 快速檢查清單

設計一個新 Skill 時，逐項確認：

**內容層**
- [ ] `description` 寫**觸發時機**，不是功能摘要（§4.1）
- [ ] 不重複 Claude 已知的通用知識，只補專案特有上下文（§4.2）
- [ ] 包含 **Gotchas** 部分，記錄團隊踩過的坑（§4.3）
- [ ] 約束**目標**而非固定步驟順序（§4.4）

**結構層**
- [ ] `SKILL.md` 控制在 500 行以內，詳細參考資料放在附檔
- [ ] 附檔用**相對路徑**引用，在 SKILL.md 中說明各檔案用途
- [ ] 需要用戶偏好時，用 `config.json` 存儲配置（§8.5）

**觸發與安全**
- [ ] 有副作用的 skill 設 `disable-model-invocation: true`
- [ ] 背景知識型 skill 設 `user-invocable: false`
- [ ] 需要隔離的耗時任務用 `context: fork`
- [ ] `allowed-tools` 限縮可用工具，遵循最小權限

**驗收**
- [ ] 包含明確的**完成條件**（Definition of Done）
- [ ] 已用真實場景測試觸發和執行
- [ ] 無硬編碼密鑰或敏感資料
