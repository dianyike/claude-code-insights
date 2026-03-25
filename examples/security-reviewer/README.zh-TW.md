# Security Reviewer — 雙重驗證 Subagent 範例

一個可直接使用的安全審查 subagent 範例，透過 MCP 交叉驗證 Semgrep（靜態分析）與 Codex（LLM 第二意見）的發現，產出附信心分數的安全報告。

## 架構

```
你 → Claude Code（主 Agent）
       ↓
   security-reviewer（Subagent, Sonnet）
       ↓
   ┌─────────────────────────────┐
   │ 第一步：Semgrep 基準分析     │  semgrep_scan + semgrep_findings
   │ 先建立獨立判斷               │  + supply chain + 手動 Grep
   └──────────┬──────────────────┘
              ↓
   ┌─────────────────────────────┐
   │ 第二步：Codex 第二意見       │  mcp__codex__codex（唯讀）
   │ MCP tool call，無需自訂      │  mcp__codex__codex-reply（追問）
   │ 通訊協議                     │
   └──────────┬──────────────────┘
              ↓
   ┌─────────────────────────────┐
   │ 第三步：交叉驗證             │  security-review-protocol skill
   │ 信心分數計算                 │  Semgrep 60% / Codex 40% 權重
   │ 衝突 → 保守原則              │  寧可誤報不漏報
   └──────────┬──────────────────┘
              ↓
   報告 → .agents-output/security/
   回傳 → verdict + 計數 + 檔案路徑
```

## 檔案結構

```
.claude/
├── agents/
│   └── security-reviewer.md              # Subagent：角色 + 工作流 + 完成條件
└── skills/
    └── security-review-protocol/
        ├── SKILL.md                       # 核心邏輯：交叉驗證 + 信心分數
        ├── reference/
        │   └── mcp-tools.md               # MCP 呼叫格式參考（按需載入）
        └── templates/
            └── report-template.md         # 報告結構模板（按需載入）
```

## 前置需求

- **Semgrep MCP plugin**：在 Claude Code 中設定好 `semgrep-plugin`
- **Codex MCP server**：在 Claude Code 中設定好 `codex`
- 兩者都必須出現在 `/tools` 的輸出中

## 使用方式

### 1. 複製檔案到你的專案

```bash
# 複製 subagent
cp agents/security-reviewer.md YOUR_PROJECT/.claude/agents/

# 複製 skill（整個目錄）
cp -r skills/security-review-protocol YOUR_PROJECT/.claude/skills/
```

### 2. 觸發安全審查

對 Claude Code 說以下任一句：

- 「安全檢查」
- 「audit code」
- 「掃描漏洞」
- 「這段程式碼安全嗎」
- 「檢查有沒有 secrets」
- 「合併前的安全掃描」

或直接指定：`@security-reviewer`

### 3. 閱讀報告

報告會寫入 `.agents-output/security/YYYY-MM-DD-<scope>-security-review.md`。

## 設計原則

### 內容分層（零重複）

| 層級 | 包含 | 不包含 |
| ---- | ---- | ------ |
| Subagent prompt | 角色、工作流步驟、輸出位置、完成條件 | 業務邏輯、計分公式、MCP 參數 |
| SKILL.md | 交叉驗證邏輯、衝突處理、信心分數 | MCP 呼叫範例、報告模板 |
| reference/ | MCP 工具呼叫格式和參數 | 業務邏輯 |
| templates/ | 報告 markdown 結構 | 分析邏輯 |

每項資訊只存在於一個地方。Subagent 引用 skill；skill 引用附檔。

### 信任但驗證協議

核心思路：**先自己分析，再取得第二意見，然後交叉比對。**

| 情境 | 處理方式 |
| ---- | -------- |
| 雙方同意 | 高信心（80%+），直接報告 |
| Semgrep 發現、Codex 沒發現 | 報告 — 工具結果可重現（60%） |
| Codex 發現、Semgrep 沒發現 | 先用 Grep/AST 驗證，再報告（40%+） |
| 衝突 | 深度驗證，偏向保守 |

### 保守原則

當 Semgrep 和 Codex 意見相左時，寧可誤報也不要漏報。誤報只是浪費時間；漏報會造成實際損害。

## 範例輸出

參見 [sample-output/2026-03-25-test-vuln-security-review.md](sample-output/2026-03-25-test-vuln-security-review.md)，這是用一個包含故意漏洞的測試檔案（hardcoded secret、SQL injection、XSS）產生的真實報告。

從範例中觀察到的重點：

- 3 個 HIGH 發現由雙方確認（各 90% 信心）
- 1 個 MEDIUM 發現由 Codex 獨家發現，再透過自訂 Semgrep 規則驗證（75% 信心）
- Parameterized query 被正確辨識為安全（負面檢查）
- XSS 嚴重度衝突以保守原則解決（Semgrep WARNING → Codex HIGH → 保留 HIGH）

## 自訂調整

### 調整信心權重

編輯 `SKILL.md` 第 3.2 節，修改 Semgrep/Codex 的權重比例（預設 60/40）。

### 新增專案特有的檢查模式

在 `security-reviewer.md` Step 1.5 的手動模式檢查中加入自訂 Semgrep 規則。

### 變更 Codex prompt 策略

編輯 `reference/mcp-tools.md` 的 Codex 區段，調整送給 Codex 的 prompt 內容。
