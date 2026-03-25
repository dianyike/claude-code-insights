# Subagent 最佳實踐指南

> 本指南的啟發來源：[【詳細攻略】Claude Code SubAgent](https://www.bilibili.com/video/BV1B6YpzFENd/)
>
> 基於官方文檔、高星 GitHub 倉庫及社群經驗整理

---

## 目錄

1. [Subagent 是什麼](#1-subagent-是什麼)
2. [核心問題：黑箱與一次性](#2-核心問題黑箱與一次性)
3. [解決方案：結果持久化](#3-解決方案結果持久化)
4. [Subagent 檔案格式](#4-subagent-檔案格式)
5. [最佳實踐設計模板](#5-最佳實踐設計模板)
6. [範例與 Skills 的分離策略](#6-範例與-skills-的分離策略)
7. [工具範圍策略](#7-工具範圍策略)
8. [Model 選擇策略](#8-model-選擇策略)
9. [架構模式](#9-架構模式)
10. [參考倉庫](#10-參考倉庫)
11. [快速檢查清單](#11-快速檢查清單)

---

## 1. Subagent 是什麼

Subagent 是獨立於主對話的**隔離工作者**，每個 subagent：

- 擁有**獨立的 context window**（不佔用主對話上下文）
- 可使用 skills 和 MCP tools
- 由 Claude 根據 `description` 自動委派，或透過 `@agent-name` 明確呼叫
- 執行完畢後回傳**單一訊息**給主 agent

**發明原因**：主 agent 在研究 codebase 時會讀大量檔案，全部塞進主 context 會快速耗盡視窗。Subagent 在獨立 context 中完成工作，只回傳摘要。

### Anthropic 官方觀點：大多數場景不需要 multi-agent

> 來源：[When to use multi-agent systems (and when not to)](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)（2026-01-23 發表）

Anthropic 明確指出：**「Most teams don't need multi-agent systems.」** 改善單 agent 的 prompting 常常就能達到同等效果。Multi-agent 系統通常消耗 **3-10 倍的 tokens**。

只有在以下三種情況才值得使用 subagent：

| 情境 | 說明 | 範例 |
|------|------|------|
| **Context 污染** | 子任務會帶入大量不相關資訊，拖垮主 agent 品質 | 研究 codebase 時讀入大量檔案 |
| **可並行化** | 多個獨立路徑可同時探索，提升**全面性**（非速度） | 同時審查安全性、效能、型別 |
| **專業化** | 工具超過 15-20 個，或需要衝突的行為模式 | 同理心客服 vs 嚴格程式碼審查 |

**關鍵原則：按 context 邊界拆分，不是按角色拆分。** 把工作拆成 planner → implementer → tester 是**反模式**，會造成「電話遊戲」——每次 handoff 都損失資訊保真度。工作只有在 context 可以真正隔離時才該拆分。

---

## 2. 核心問題：黑箱與一次性

### 黑箱問題

| 問題 | 說明 |
|------|------|
| 用戶不可見 | subagent 回傳的結果**只有主 agent 看得到**，用戶無法檢視 |
| 無中間輸出 | 執行過程中沒有「思考中」的透明輸出 |
| 除錯困難 | 無法知道 subagent 用了哪個 model、讀了哪些檔案 |
| 結果消失 | context 壓縮後，subagent 的回傳結果可能被丟棄 |

### 一次性問題

| 問題 | 說明 |
|------|------|
| 無法連續對話 | 每次呼叫都是**全新 instance**，沒有記憶 |
| 無法追問 | 主 agent 無法基於上次結果追問（除非用 `SendMessage` 繼續） |
| 結果不可重用 | 下一輪對話無法取得上次 subagent 的結論 |

---

## 3. 解決方案：結果持久化

核心思路：**讓 subagent 將結果寫入檔案系統**，使其可被用戶、主 agent、和未來對話存取。

### 方案一：寫入約定目錄（推薦）

```
專案根目錄/
├── .agents-output/           # subagent 輸出根目錄
│   ├── research/             # 研究類結果
│   │   └── 2026-03-23-auth-library-comparison.md
│   ├── review/               # 程式碼審查結果
│   │   └── 2026-03-23-auth-module-review.md
│   └── test/                 # 測試報告
│       └── 2026-03-23-integration-test-report.md
```

**優點**：
- 用戶可直接閱讀檔案
- 主 agent 可在後續對話中 `Read` 取回結果
- Git 可追蹤變更歷史
- 可加入 `.gitignore` 避免提交（視需求）

### 方案二：使用官方 `memory` 欄位

```yaml
---
name: research-agent
memory: project   # 結果存入 .claude/agent-memory/research-agent/（官方推薦預設 scope）
---
```

記憶目錄對應：
- `user` → `~/.claude/agent-memory/<agent-name>/`（跨專案共用）
- `project` → `.claude/agent-memory/<agent-name>/`（專案級，可進版控，**官方推薦預設**）
- `local` → `.claude/agent-memory-local/<agent-name>/`（專案級，不進版控）
- 省略 → 不啟用持久記憶

**優點**：原生支援，subagent 下次被呼叫時自動載入前 200 行 MEMORY.md

### 方案三：Hook 系統監控

```json
// settings.json
{
  "hooks": {
    "SubagentStop": [{
      "type": "command",
      "command": "echo '[SUBAGENT DONE]' && cat .agents-output/latest.md"
    }]
  }
}
```

透過 `SubagentStop` hook 在 subagent 結束時自動將結果輸出到 STDOUT。

### 方案四：SendMessage 繼續對話

```
// 主 agent 可用 SendMessage 對已完成的 subagent 追問
SendMessage(to: 'agent-id', message: '請補充安全性分析')
```

每個 Agent 呼叫完畢後會回傳 `agentId`，可用來恢復上下文繼續對話。

---

## 4. Subagent 檔案格式

放置於 `~/.claude/agents/`（全域）或 `.claude/agents/`（專案）。

```yaml
---
name: agent-name              # 必填，小寫加連字號
description: 何時使用此 agent  # 必填，Claude 據此自動委派
model: sonnet                 # 可選：sonnet / opus / haiku / inherit（省略 = inherit）
tools: Read, Grep, Glob       # 可選：工具白名單（省略 = 繼承全部）
disallowedTools: Write, Edit  # 可選：工具黑名單
maxTurns: 15                  # 可選：最大迭代次數
permissionMode: default       # 可選：default / acceptEdits / dontAsk / bypassPermissions / plan
memory: project               # 可選：user / project / local（省略 = 不啟用）
skills: my-skill              # 可選：注入的 skill
background: false             # 可選：背景執行
effort: medium                # 可選：推理力度
isolation: worktree           # 可選：git worktree 隔離
hooks:                        # 可選：生命週期鉤子
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
mcpServers:                   # 可選：MCP 伺服器
  context7:
    type: stdio
    command: npx
    args: ["-y", "@anthropic-ai/context7-mcp"]
---

（以下為系統提示詞，即 agent 的行為指令）
```

### 欄位完整參考

| 欄位 | 必填 | 說明 |
|------|------|------|
| `name` | 是 | 唯一識別符，小寫字母 + 連字號 |
| `description` | 是 | 觸發條件描述，決定 Claude 何時自動委派 |
| `model` | 否 | `sonnet`、`opus`、`haiku`、`inherit`、或完整 model ID。**省略時預設為 `inherit`**（使用主對話相同的模型） |
| `tools` | 否 | 工具白名單（逗號分隔），省略則繼承全部 |
| `disallowedTools` | 否 | 工具黑名單 |
| `maxTurns` | 否 | 最大 agentic 迭代次數 |
| `permissionMode` | 否 | `default` / `acceptEdits` / `dontAsk` / `bypassPermissions` / `plan`。**`bypassPermissions` 會跳過所有權限提示，使用時需格外小心** |
| `memory` | 否 | `user` / `project` / `local`。`user` → `~/.claude/agent-memory/<name>/`（跨專案）、`project` → `.claude/agent-memory/<name>/`（可進版控，官方推薦預設）、`local` → `.claude/agent-memory-local/<name>/`（不進版控）。省略則不啟用持久記憶 |
| `skills` | 否 | 注入的 skill 名稱 |
| `mcpServers` | 否 | 範圍限定的 MCP 伺服器 |
| `hooks` | 否 | 生命週期鉤子 |
| `background` | 否 | `true` 則始終在背景執行 |
| `effort` | 否 | `low` / `medium` / `high` / `max` |
| `isolation` | 否 | `worktree` 以 git worktree 隔離，subagent 在獨立 repo 副本中工作，無變更時自動清理 |

**Plugin 限制**：從 plugin 載入的 subagent **不支援** `hooks`、`mcpServers`、`permissionMode` 三個欄位，這些欄位會被靜默忽略。

---

## 5. 最佳實踐設計模板

### 模板：研究型 Agent（帶檔案輸出）

````yaml
---
name: researcher
description: >
  Use proactively when the user needs library comparison, technology research,
  or architecture investigation. Writes results to .agents-output/research/.
model: sonnet
tools: Read, Grep, Glob, WebSearch, WebFetch, Write,
       mcp__context7__resolve-library-id, mcp__context7__query-docs
maxTurns: 20
---

# 研究型 Agent

你是一個專注於技術研究的 agent。

## 工作流程

1. **理解需求**：分析研究主題和範圍
2. **多源收集**：使用 WebSearch、Context7、codebase 搜尋收集資訊
3. **交叉驗證**：比較多個來源的一致性
4. **撰寫報告**：產出結構化的研究文件
5. **寫入檔案**：將結果寫入 `.agents-output/research/` 目錄

## 輸出格式

將研究結果寫入 `.agents-output/research/YYYY-MM-DD-<topic-slug>.md`：

```markdown
# <研究主題>

> 研究日期：YYYY-MM-DD
> 研究範圍：<簡述>

## 摘要
<3-5 句核心發現>

## 詳細分析
<結構化的分析內容>

## 建議
<具體可行的建議>

## 參考來源
<使用的來源清單>
```

## 完成條件

- [ ] 至少 3 個獨立來源交叉驗證
- [ ] 結果已寫入 `.agents-output/research/` 目錄
- [ ] 回傳摘要和檔案路徑給主 agent
````

### 模板：程式碼審查 Agent（唯讀）

````yaml
---
name: code-reviewer
description: >
  Use after writing or modifying code. Reviews for quality, security,
  performance, and best practices. Writes review report to .agents-output/review/.
model: sonnet
tools: Read, Grep, Glob, Write
maxTurns: 15
---

# 程式碼審查 Agent

你是一個嚴格的程式碼審查者。

## 審查維度

1. **正確性**：邏輯是否正確，邊界案例是否處理
2. **安全性**：OWASP Top 10 檢查
3. **效能**：是否有不必要的計算或記憶體浪費
4. **可讀性**：命名、結構、註解是否清晰
5. **不可變性**：是否遵循 immutable 原則

## 輸出格式

將審查結果寫入 `.agents-output/review/YYYY-MM-DD-<module-name>-review.md`：

```markdown
# Code Review: <模組名稱>

> 審查日期：YYYY-MM-DD
> 審查範圍：<檔案清單>

## 問題摘要

| 等級 | 數量 |
|------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## CRITICAL 問題
<必須修復的問題>

## HIGH 問題
<強烈建議修復>

## 建議改善
<可選的改善建議>
```

## 防止 Early Victory

你**必須**完成所有審查維度才能宣布審查完成。
不可以只看部分檔案就下結論。
每個維度都必須有具體的檢查結果（通過或發現問題），不可以跳過。

## 回傳內容

回傳給主 agent 時只需包含：
1. 問題摘要（各等級數量）
2. CRITICAL 和 HIGH 問題的一行描述
3. 完整報告的檔案路徑
````

### 不適合 Subagent 的場景

以下任務應留在**主對話**中進行，不要委派給 subagent：

| 場景 | 原因 |
|------|------|
| **規劃與架構設計** | 需要用戶來回溝通、即時調整方向，subagent 的黑箱性質會造成資訊不對等 |
| **需求釐清** | 用戶需要看到中間推理過程，才能判斷方向是否正確 |
| **有爭議的技術決策** | 需要用戶參與 trade-off 討論，不能由 subagent 單方面決定 |
| **除錯複雜問題** | 除錯是探索性過程，需要用戶提供即時反饋和上下文 |

**判斷原則**：如果任務的結果需要用戶**審閱、討論、或修改**才能繼續下一步，就不應該用 subagent。Subagent 適合「給明確指令、拿回明確結果」的任務。

主對話中可使用 **Plan Mode**（`/plan`）來進行規劃，這樣用戶能完整參與討論過程。

> **Anthropic 官方佐證**：按工作類型拆分（planner → implementer → tester）是反模式。原文指出這種拆分「creates constant coordination overhead」，形成「電話遊戲」效應——每次 handoff 都損失資訊保真度，agent 缺少前一階段的決策脈絡。應按 **context 邊界**而非角色拆分。([來源](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)，2026-01-23)

### 最適合 Subagent 的場景：驗證型 Agent

Anthropic 官方明確推薦的 subagent 模式是**驗證型（Verification Subagent）**，原因是：

- 驗證只需要「產出物 + 成功條件」，**不需要完整的建構上下文**
- 是真正的 blackbox 測試，context 可以完全隔離
- 成功條件明確，不需要來回討論

這正是本指南保留**研究型**和**審查型**模板的原因——它們都符合「明確輸入 → 明確輸出」的特性。

#### Early Victory Problem（提前勝利問題）

Anthropic 特別警告：驗證型 agent 容易**跑一兩個測試就宣布通過**，跳過全面驗證。

**緩解策略**（務必寫在 subagent prompt 中）：
- 使用強制語言：「你**必須**執行完整測試套件才能宣布通過」
- 指定具體檢查項目，不要寫「確認它能運作」這種模糊條件
- 要求包含**負面測試**（應該失敗的輸入）
- 在完成條件中列出所有必須通過的檢查清單

---

## 6. 範例與 Skills 的分離策略

Subagent prompt 應保持精簡，**程式碼範例和風格指南不放在 subagent 裡，放在 skills 裡**。

### 原則：Subagent prompt 只管四件事

```
角色定義 → 工作流程 → 輸出格式 → 完成條件
```

範例和通用知識會膨脹 prompt、浪費 context，而且 model 本身就知道怎麼寫程式碼。

### 為什麼用 Skills 而非直接寫在 Subagent 裡

| 理由 | 說明 |
|------|------|
| **可複用** | 同一份 skill 可被多個 subagent 共用（`skills: coding-style`） |
| **按需載入** | 不需要範例的任務就不注入，省 context |
| **獨立維護** | 範例更新時改一個 skill 檔案，不用改 N 個 subagent |

### Skills 目錄結構

```
~/.claude/skills/
├── coding-style.md        # 程式碼風格範例（immutable patterns、命名慣例等）
├── output-format.md       # 輸出報告的格式範例
└── testing-patterns.md    # 測試寫法範例
```

### Subagent 按需引用

```yaml
---
name: code-reviewer
tools: Read, Grep, Glob, Write
skills: coding-style          # 審查時需要知道風格規範
---
```

```yaml
---
name: researcher
tools: Read, Grep, Glob, WebSearch, Write
# 研究型不需要 coding-style，不注入
---
```

### 唯一例外：輸出格式範例

**輸出格式的範例**可以留在 subagent prompt 裡，因為那是該 agent 自己的「工作規格」，不是通用知識：

```markdown
## 輸出格式

寫入 `.agents-output/review/YYYY-MM-DD-<name>.md`：

| 等級 | 數量 |
|------|------|
| CRITICAL | 0 |
| HIGH | 0 |
```

這定義的是「這個 agent 的產出長什麼樣」，屬於 agent 自身職責，留在 prompt 裡合理。

### 判斷規則

> 完整的「內容類型放在哪裡」決策矩陣，請見 [Skills 最佳實踐指南 § 11. Skill 與 Subagent 的協作](skills-best-practices.md#11-skill-與-subagent-的協作)。
>
> 簡要原則：**輸出格式**留在 Subagent prompt（agent 自身的工作規格）；**程式碼風格/測試模式**放在 Skills（通用知識，多 agent 共用）；**函式庫文檔**透過 MCP 即時取得。

---

## 7. 工具範圍策略

**核心原則：最小權限（Principle of Least Privilege）**

| Agent 類型 | 建議工具 | 說明 |
|-----------|---------|------|
| 唯讀研究/審查 | `Read, Grep, Glob` | 分析但不修改 |
| 研究 + 外部資料 | `Read, Grep, Glob, WebSearch, WebFetch` | 加上網路存取 |
| 研究 + 寫報告 | `Read, Grep, Glob, WebSearch, Write` | 加上寫檔能力 |
| 實作/修復 | `Read, Write, Edit, Bash, Grep, Glob` | 完整開發能力 |
| 協調/編排 | `Read, Glob, Grep, Bash` | 不給 Write/Edit |
| MCP 整合 | 基礎工具 + `mcp__<server>__*` | 按需加入 MCP |

**重要**：省略 `tools` 欄位 = 繼承全部工具。務必明確列出。

---

## 8. Model 選擇策略

```
成本：Haiku <<< Sonnet < Opus

Opus  → 複雜審查、團隊協調（用於主對話中的規劃和架構決策）
Sonnet → 主要開發、研究分析、程式碼審查（researcher, code-reviewer）
Haiku  → 高頻輕量操作、快速探索（explore, lint-checker）
```

**省錢技巧**：設定環境變數 `CLAUDE_CODE_SUBAGENT_MODEL` 可全域控制 subagent 的 model。
主對話用 Opus 做複雜推理，subagent 用 Sonnet 做聚焦任務。

---

## 9. 架構模式

### 模式一：Hub-and-Spoke（推薦）

```
                    ┌─────────────┐
                    │  用戶請求    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  主 Agent    │  ← Opus，負責路由和整合
                    │ (Hub)       │
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────┘   │   └────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
        │ researcher │ │reviewer│ │  tester   │  ← Sonnet，各司其職
        │  (Spoke)   │ │(Spoke) │ │  (Spoke)  │
        └─────┬──────┘ └───┬────┘ └─────┬─────┘
              │            │            │
              ▼            ▼            ▼
        .agents-output/ .agents-output/ .agents-output/
        research/       review/         test/
```

**特點**：
- 主 agent 負責路由決策和結果整合
- 每個 spoke 只做一件事
- 所有結果寫入統一的 `.agents-output/` 目錄

### 模式二：Pipeline（串行流水線）⚠️ 需謹慎

> **警告**：Pipeline 本質上是按工作類型拆分，Anthropic 官方明確指出這種拆分「creates constant coordination overhead」，屬於反模式（見[第 1 節](#1-subagent-是什麼)）。每次 handoff 都損失 context 保真度：test agent 不知道 implementation 的設計取捨，reviewer 不知道 test 的覆蓋意圖。
>
> **僅在以下條件同時成立時考慮使用**：每個階段的輸入/輸出可以完全序列化為檔案（如 spec.md → code → report.md），且各階段不需要回溯前一階段的推理過程。大多數情況下，Hub-and-Spoke 搭配主對話協調是更好的選擇。

```
PM-spec → Architect → Implementer → Tester → Reviewer
   │          │           │            │          │
   ▼          ▼           ▼            ▼          ▼
 spec.md   adr.md      code        report.md  review.md
```

透過 hooks 串接，每個 agent 的 `SubagentStop` hook 建議下一步。

### 模式三：Parallel Workers（並行工作者）

```javascript
// 在主 agent 中同時啟動多個 subagent
Agent({ type: "security-reviewer", prompt: "審查 auth 模組" })
Agent({ type: "perf-reviewer", prompt: "審查 cache 模組" })
Agent({ type: "type-checker", prompt: "審查 utilities" })
// 三個並行執行，各自寫入 .agents-output/
```

---

## 10. 參考倉庫

### 官方文檔

- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — 官方完整參考
- [Building multi-agent systems: when and how to use them](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them) — Anthropic 官方指南，何時該用/不該用 multi-agent，驗證型 agent 模式，Early Victory Problem

### 高星 GitHub 倉庫

| 倉庫 | Stars | 特點 |
|------|-------|------|
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | ~9.6k | 127+ agent 策展集合，分類清晰 |
| [wshobson/agents](https://github.com/wshobson/agents) | — | Plugin 架構，72 個 plugin，平均 3.4 元件 |
| [vanzan01/claude-code-sub-agent-collective](https://github.com/vanzan01/claude-code-sub-agent-collective) | — | Hub-and-Spoke 模式，強制 TDD，研究快取 |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | — | 綜合策展，含 skills、hooks、plugins |
| [supatest-ai/awesome-claude-code-sub-agents](https://github.com/supatest-ai/awesome-claude-code-sub-agents) | — | 強調單一職責和安全優先 |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | ~100k | 最大規模配置專案，28 agents + 125 skills + 60 commands，覆蓋 10+ 語言。廣度極佳但 subagent 未做結果持久化，且將規劃/架構放在 subagent 中（有黑箱風險） |

### 延伸閱讀

- [Best practices for Claude Code subagents (PubNub)](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)
- [Sub-Agent vs. Agent Team (Medium)](https://medium.com/data-science-collective/sub-agent-vs-agent-team-in-claude-code-pick-the-right-pattern-in-60-seconds-e856e5b4e5cc)
- [Claude Code Deep Dive - Subagents in Action (Medium)](https://medium.com/@the.gigi/claude-code-deep-dive-subagents-in-action-703cd8745769)
- [Subagent Parallel vs Sequential Patterns (claudefast)](https://claudefa.st/blog/guide/agents/sub-agent-best-practices)

---

## 11. 快速檢查清單

設計一個新 subagent 時，逐項確認：

- [ ] `name` 和 `description` 明確且具體（description 決定自動委派）
- [ ] `tools` 使用白名單，遵循最小權限
- [ ] `model` 根據任務複雜度選擇（不要全用 Opus）
- [ ] 系統提示詞包含**明確的輸出格式**
- [ ] 指定**寫入檔案的目錄和命名規則**
- [ ] 定義**完成條件**（Definition of Done）
- [ ] 回傳內容精簡（摘要 + 檔案路徑，不要塞入完整報告）
- [ ] `maxTurns` 設定合理上限，防止失控
