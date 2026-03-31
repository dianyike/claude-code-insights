# Security Reviewer — 雙重驗證 Subagent 範例

一個可直接使用的安全審查 subagent 範例，透過 MCP 交叉驗證 Semgrep（靜態分析）與 Codex（LLM 第二意見）的發現，產出附信心分數的安全報告。修復流程（Fix-Verify Loop）透過 `/security:fix` 在主對話中執行，需使用者明確觸發。

## 架構

```
你 → Claude Code（主 Agent）
       │
       ├─ /security:review [--base] [--scope] [--background]
       │       ↓
       │   security-reviewer（Subagent, Sonnet, 唯讀）
       │       ↓
       │   ═══════════════════════════════════════
       │     唯讀邊界（review 永遠不跨越）
       │   ═══════════════════════════════════════
       │       ↓
       │   ┌──────────────────────────────┐
       │   │ 第一步：Semgrep 基準分析      │  semgrep_scan + semgrep_findings
       │   │ 先建立獨立判斷                │  + supply chain + 手動 Grep
       │   └──────────┬───────────────────┘
       │              ↓
       │   ┌──────────────────────────────┐
       │   │ 第二步：Codex 第二意見        │  mcp__codex__codex（唯讀）
       │   │ MCP tool call                │  mcp__codex__codex-reply（追問）
       │   └──────────┬───────────────────┘
       │              ↓
       │   ┌──────────────────────────────┐
       │   │ 第三步：交叉驗證              │  security-review-protocol skill
       │   │ 信心分數計算                  │  Semgrep 60% / Codex 40% 權重
       │   │ 衝突 → 保守原則               │  寧可誤報不漏報
       │   └──────────┬───────────────────┘
       │              ↓
       │   報告 → .agents-output/security/
       │   回傳 → verdict + 計數 + 建議的 /security:fix 指令
       │
       ├─ /security:fix <report> [--finding] [--deep]
       │       ↓
       │   ═══════════════════════════════════════
       │     寫入邊界（需使用者明確觸發）
       │   ═══════════════════════════════════════
       │       ↓
       │   在主對話中執行（非 subagent）
       │       ↓
       │   ┌──────────────────────────────┐
       │   │ 第四步：Fix-Verify Loop       │  收斂強化：
       │   │ Known Fix Gate → Codex 修復   │  - 可反駁預測區塊
       │   │ 預測 → Semgrep 驗證           │  - 每次修復前需使用者確認
       │   │ 假設帳本                      │  - Fresh-session 策略切換
       │   └──────────┬───────────────────┘  - 分級回退規則
       │              ↓
       │   修改的檔案 + 假設帳本附加至報告
       │
       └─ /security:status / result / cancel   ← 任務管理
```

## 檔案結構

```
.claude/
├── agents/
│   └── security-reviewer.md              # Subagent：唯讀稽核（第 1-3 步）
└── skills/
    ├── security-review/
    │   └── SKILL.md                       # /security:review 指令（target resolution）
    ├── security-fix/
    │   └── SKILL.md                       # /security:fix 指令（主對話修復）
    └── security-review-protocol/
        ├── SKILL.md                       # 核心邏輯：交叉驗證 + 信心分數 + fix-verify
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

使用 slash command：

```
/security:review                         # 自動偵測範圍
/security:review --base develop          # 對 develop branch 做 diff
/security:review --scope staged          # 只看已 stage 的變更
/security:review src/auth/               # 限定特定路徑
/security:review --background            # 背景執行
```

或對 Claude Code 說以下任一句（觸發詞）：

- 「安全檢查」
- 「audit code」
- 「掃描漏洞」
- 「這段程式碼安全嗎」
- 「檢查有沒有 secrets」
- 「合併前的安全掃描」

或直接指定：`@security-reviewer`

### 3. 閱讀報告

報告會寫入 `.agents-output/security/YYYY-MM-DD-<scope>-security-review.md`。

### 4. 修復發現（需明確觸發）

```
/security:fix .agents-output/security/2026-03-31-auth-security-review.md
/security:fix .agents-output/security/2026-03-31-auth-security-review.md --finding F-003
/security:fix .agents-output/security/2026-03-31-auth-security-review.md --dry-run
```

修復在主對話中執行（非 subagent），你可以在每次修改前確認。

## 設計原則

### Review/Fix 邊界

| 動作 | 入口 | 寫入權限 | 執行環境 |
| ---- | ---- | ------- | ------- |
| **Review** | `/security:review` | 唯讀 | Subagent（隔離 context） |
| **Fix** | `/security:fix` | 寫入（需 opt-in） | 主對話（使用者可見） |
| **Gate** | Stop hook | 唯讀 | Subagent |

為什麼 `/security:fix` 在主對話中執行而非 subagent：

- Fix-verify 需要使用者在每次程式碼修改前確認
- 預測區塊必須對使用者可見（不能藏在黑箱裡）
- 修復需要 review 的完整上下文（findings、Codex threadId）
- 按角色拆分（reviewer → fixer）是 subagent 反模式（telephone game）

### 內容分層（零重複）

| 層級 | 包含 | 不包含 |
| ---- | ---- | ------ |
| Subagent prompt | 角色、工作流步驟、輸出位置、完成條件 | 業務邏輯、計分公式、MCP 參數 |
| /security:review skill | 指令介面、target resolution | 業務邏輯、MCP 參數 |
| /security:fix skill | 修復指令介面、確認流程 | 計分公式、MCP 參數 |
| security-review-protocol SKILL.md | 交叉驗證邏輯、衝突處理、信心分數、Fix-Verify Loop | MCP 呼叫範例、報告模板 |
| reference/ | MCP 工具呼叫格式和參數 | 業務邏輯 |
| templates/ | 報告 markdown 結構 | 分析邏輯 |

每項資訊只存在於一個地方。Subagent 引用 protocol skill；指令 skill 定義使用者介面。

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

### 擴充 Known Fix Gate

在 `SKILL.md` 第 4.1 節的 canonical fix pattern 表格中加入你的 codebase 常見漏洞類別（如 SSRF、反序列化）。

### 調整回退敏感度

編輯 `SKILL.md` 第 4.5 節的分級回退表。在較嚴格的環境中，可將「rule 轉移」從「保留變更」提升為「回退」。

### 變更迭代上限

預設為 3 輪後升級至人工審查（`SKILL.md` 第 4.4 節）。可縮減至 2 輪以加快回饋，或增加以允許更多探索空間。
