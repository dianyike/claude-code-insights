# Security-Reviewer Plugin 化合併設計

> 日期：2026-03-31
> 狀態：提案 (Proposal)
> 範圍：將 codex-plugin-cc 的 UX/執行控制層合併至 security-reviewer，保留雙驗證協定核心

---

## 背景

### 兩個系統的定位

| 系統 | 定位 | 核心能力 |
|------|------|---------|
| [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) `/codex:review` | Codex review 能力的產品化接線插件 | CLI 外殼、背景執行、review gate、target resolution |
| 本 repo `security-reviewer` | 帶有明確安全方法論與驗證機制的審計流程 | Semgrep baseline、Codex second opinion、交叉驗證、fix-verify loop |

### 合併原則

**「Plugin 化我們的 security workflow」，而非「把 security workflow 一般化成普通 code review」。**

- 外殼：取 codex-plugin-cc 的指令介面、背景執行、job control
- 核心：保留 security-reviewer 的雙源驗證、衝突解決、信心公式、收斂式修復

### 關鍵邊界：review vs remediation

合併設計嚴格區分三個動作的邊界：

| 動作 | 入口 | 寫入權限 | 說明 |
|------|------|---------|------|
| **Review** | `/security:review` | **read-only** | 稽核、報告、verdict。永遠不修改工作樹 |
| **Remediation** | `/security:fix` | **write，需明確 opt-in** | fix-verify loop。只在使用者主動要求時執行 |
| **Gate** | Stop hook（自動） | **read-only** | 攔截高風險變更。最多觸發完整 read-only protocol，不得自動進修復 |

設計理由：`/codex:review` 是 read-only 稽核，`/codex:rescue` 才是寫入修復。我們的合併不應把這兩個語意混成同一入口，否則使用者無法預期副作用，gate 自動觸發時更危險——「自動檢查」和「自動改碼」是完全不同的信任等級。

注意：`/security:fix` 在主對話中直接執行，不委派給 subagent。原因：fix-verify 需要使用者確認每個修復、需要 review 階段的完整上下文（findings、Codex threadId）、且中間狀態（prediction block）必須對使用者可見。按角色拆分（reviewer → fixer）是 subagent anti-pattern（telephone game），按 context boundary 拆分才正確——review 的 context 可以隔離到 subagent，fix 的互動不行。

---

## 合併項目

### 合併項目總覽

| # | 項目 | Phase | 預期收益 | 實作成本 | 邊際效益風險 |
|---|------|-------|---------|---------|------------|
| 1 | `/security:review`（read-only 稽核指令） | 1 | 高 | 低 | 低 |
| 2 | `--base` target resolution | 1 | 高 | 低 | 低 |
| 3 | `--background` + job control | 1 | 高 | **中** | 低 |
| 4 | 分級 gate（read-only，輕量/重量） | 2 | 中高 | 中 | **中** |
| 5 | `/security:fix`（opt-in 修復指令） | 2 | 中 | 低 | 中低 |
| 6 | Codex session resume 深度整合 | 3 | 中低 | 中 | 中低 |

### 不合併的項目

| 項目 | 排除原因 |
|------|---------|
| 完整 protocol 掛到 Stop hook | 成本過高，Codex 自身文件也警告會產生長迴圈與 usage 暴增 |
| Adversarial-review 的廣泛品質維度 | Race conditions、schema drift 等非安全漏洞，混入會稀釋 Semgrep 交叉驗證的精準度 |
| Gate 自動觸發修復 | Gate 的職責是攔截，不是改碼。自動修復需要不同的信任模型與使用者確認點 |

---

## Phase 1：UX 外殼（read-only 稽核）

> 目標：拿 UX 紅利。review 永遠 read-only，不觸及修復。

### 1.1 `/security:review` 指令（read-only）

**現狀問題：** security-reviewer 只能透過觸發詞啟動（"security check"、"audit code" 等），沒有正式的 slash command。

**指令定義：**

```
/security:review [options] [path...]
  --base <branch>              # 對 base branch 做 merge-base diff
  --scope staged|working-tree  # 明確指定變更範圍（見下方語法定義）
  --background                 # 背景執行，回傳 job ID
  --wait                       # 前景等待（預設）
```

注意：此指令**不包含** `--deep`、`--remediate` 或任何修復相關 flag。修復由 `/security:fix` 處理（Phase 2）。

**指令定義格式（Claude Code plugin command）：**

```yaml
---
name: security:review
description: 雙驗證安全審計（Semgrep + Codex cross-validation），read-only
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, "Bash(git:*)",
  mcp__plugin_semgrep-plugin_semgrep__semgrep_scan,
  mcp__plugin_semgrep-plugin_semgrep__semgrep_scan_with_custom_rule,
  mcp__plugin_semgrep-plugin_semgrep__semgrep_findings,
  mcp__plugin_semgrep-plugin_semgrep__semgrep_scan_supply_chain,
  mcp__plugin_semgrep-plugin_semgrep__get_abstract_syntax_tree,
  mcp__codex__codex, mcp__codex__codex-reply]
---
```

注意：subagent frontmatter 的 `tools:` 仍保留 `Write`——因為 subagent 需要 Write 來將報告寫入 `.agents-output/security/`。read-only 約束是透過 agent prompt 中的行為指令（「MUST NOT modify any source code files」）實施的，而非透過移除 Write 工具。`Write` 的用途被限定為「只寫報告檔案」。

**觸發詞相容：** 原有觸發詞（"security check"、"audit code" 等）保留為別名，行為等同 `/security:review`（無 flag 時走自動模式）。

### 1.2 Target Resolution 統一

**現狀問題：** security-reviewer 依賴 `git diff --staged` / `git diff` / `git log`，沒有統一的目標選取邏輯。

**`--scope` 語法定義（收斂為單一規格）：**

| `--scope` 值 | 含義 | 對應 git 操作 |
|--------------|------|-------------|
| `staged` | 只看已 stage 的變更 | `git diff --staged` |
| `working-tree` | staged + unstaged + untracked | `git diff` + `git ls-files --others --exclude-standard` |
| （未指定） | 自動模式（見下方） | — |

**自動模式選取邏輯（沿用 codex-plugin-cc 的 `resolveReviewTarget`）：**

```
if --base specified:
    mode = branch diff (merge-base against --base)
elif --scope specified:
    mode = 使用指定的 scope
elif working tree is dirty:
    mode = working-tree (staged + unstaged + untracked)
else:
    mode = branch diff (merge-base against default branch)
```

**路徑參數：** `[path...]` 作為額外過濾器，在上述模式選取結果上再篩選路徑前綴。例如：

```
/security:review --base develop src/auth/    # branch diff，只看 src/auth/ 下的變更
/security:review src/auth/ src/middleware/    # 自動模式，限定兩個目錄
```

**選取結果交給現有 protocol：**
1. 解析出變更檔案列表（絕對路徑）
2. 餵入 Semgrep scan
3. 組裝 diff context 送 Codex

### 1.3 背景執行與 Job Control

**現狀問題：** 完整 security scan 動輒 2-3 分鐘，阻塞主對話。

**指令介面：**

```
/security:review --background    # 背景執行，回傳 job ID
/security:status [job-id]        # 查詢進度（無 ID 時列出所有 active jobs）
/security:result <job-id>        # 取得結果
/security:cancel <job-id>        # 取消執行中的 scan
```

**成本評估修正：** 此項目的實作成本為**中**，不是低。原因：Claude Code subagent 的 `run_in_background` 支援非同步執行，但**不等於**「自然擁有可追蹤、可取消、可恢復的 job system」。需要額外建構：

**Job 狀態機：**

```
                 ┌─ cancel ─┐
                 ▼           │
QUEUED → RUNNING → COMPLETED
              │        │
              │        └─→ 報告寫入 .agents-output/security/
              │
              └─→ FAILED（Semgrep/Codex 連線失敗、timeout 等）
                     │
                     └─→ 錯誤摘要寫入 job 狀態檔
```

| 狀態 | 說明 | 使用者可見行為 |
|------|------|-------------|
| `QUEUED` | 已接受，等待執行 | `/security:status` 顯示 "queued" |
| `RUNNING` | subagent 執行中 | `/security:status` 顯示 "running" + 已完成步驟 |
| `COMPLETED` | 報告已產出 | `/security:result` 回傳 verdict + report path |
| `FAILED` | 執行失敗 | `/security:result` 回傳錯誤摘要 |
| `CANCELLED` | 使用者取消 | `/security:status` 顯示 "cancelled" |

**需要定義的實作細節：**

- **執行體：** 每個 job 是一個背景 subagent invocation，以 UUID 作為 job ID
- **狀態持久化：** `.agents-output/security/jobs/<job-id>.json`，包含 `{ status, created_at, scope, report_path, error }`
- **取消語義：** 設定 job 狀態為 CANCELLED。由於 subagent 不支援中途中斷，實際行為是「不再等待結果、不顯示報告」，subagent 可能仍會跑完
- **Session 結束後：** job 狀態檔和報告留存在磁碟上，下次 session 可透過 `/security:result` 讀取。但 RUNNING 狀態的 job 在 session 結束後無法繼續——需標記為 `STALE` 供使用者辨識
- **STALE 偵測機制：** 由 `/security:status` 被呼叫時主動檢查。邏輯：讀取 `.agents-output/security/jobs/` 下所有 JSON 檔，若 `status == "RUNNING"` 且 `created_at` 早於當前 session 啟動時間（透過 `${CLAUDE_SESSION_ID}` 判斷，或退而求其次比較 `created_at` 是否超過 30 分鐘），則將 status 改為 `STALE`。不使用 SessionStart hook——因為 hook 在每次 session 啟動時都會跑，即使使用者不使用 security 功能也會掃描 job 目錄，產生不必要的 I/O
- **並行限制：** 同時最多 1 個 RUNNING job（避免 Semgrep/Codex 資源競爭），後續請求排入 QUEUED

**與 codex-plugin-cc 的差異：**
- codex-plugin-cc 用 Unix socket broker 管理 app-server 多工存取，我們不需要 broker 層
- 但 codex-plugin-cc 的 broker 解決了一個我們也會遇到的問題：多個 scan 同時存取 Codex 的並行控制。上述 QUEUED 機制是我們的替代方案

---

## Phase 2：自動觸發 + 明確修復入口

> 目標：gate 自動觸發（read-only）+ `/security:fix` 明確 opt-in 修復

### 2.1 分級 Gate（永遠 read-only）

**核心問題：** 自動觸發是採用率的關鍵驅動力，但完整 protocol 不適合每次 stop 都跑。

**關鍵約束：Gate 永遠是 read-only。Gate 不得自動進入修復流程。** Gate 的職責是「攔截並通知」，不是「攔截並修改」。即使 Level 2 觸發完整 protocol，也只執行到報告產出（Step 1-3），不進入 fix-verify loop（Step 4）。

**分級設計：**

```
Level 0: 無 gate（預設）
Level 1: 輕量 gate — 只跑 Semgrep quick scan
Level 2: 完整 gate — 雙驗證 protocol（Step 1-3，不含 fix-verify）
```

**升級規則（Level 1 → Level 2 的觸發條件）：**

變更檔案匹配以下任一 pattern 時自動升級：

```
# 認證/授權相關
**/auth/**  **/session/**  **/token/**  **/credential/**  **/permission/**

# 機密管理
**/.env*  **/secrets/**  **/config/production.*

# 供應鏈
**/package.json  **/package-lock.json  **/yarn.lock  **/pnpm-lock.yaml
**/Gemfile.lock  **/go.sum  **/requirements*.txt  **/Pipfile.lock

# 危險操作
檔案內容包含: exec(  eval(  spawn(  shell=True  dangerouslySetInnerHTML
檔案內容包含: rawQuery  $where  innerHTML  document.write

# SQL/ORM
**/*query*  **/*migration*  **/*schema*
```

**輕量 gate 的行為（Level 1）：**

```
1. 對變更檔案執行 semgrep_scan（~10 秒）
2. 如果 0 findings → ALLOW（附帶 "Semgrep clean" 訊息）
3. 如果有 findings → BLOCK + 報告 finding 數量 + 嚴重度
   → 建議使用者執行 /security:review（完整稽核）
   → 或執行 /security:fix <report>（修復）
```

**完整 gate 的行為（Level 2）：**

```
1. 執行 read-only security-reviewer protocol Step 1-3（不含 fix-verify）
2. CRITICAL findings → BLOCK + 顯示摘要 + 建議 /security:fix
3. HIGH findings → WARNING + 建議檢視報告
4. 其他 → ALLOW + 報告路徑
```

**Gate 絕對不做的事：**
- 不修改原始碼
- 不自動進入 fix-verify loop
- 不呼叫需要 Write 權限的工具

**邊際效益拐點警告：**

```
風險判定過鬆 → gate 形同虛設 → 不如不做
風險判定過嚴 → 每次都跑完整 protocol → 開發者疲勞 → 開始忽略警告
```

建議上線後追蹤兩個指標：
- **Gate 升級率**：Level 1 → Level 2 的比例，理想值 15-25%
- **False alarm rate**：完整 gate BLOCK 後人工判定為誤報的比例，超過 30% 需調整規則

### 2.2 `/security:fix`（opt-in 修復指令）

**設計理由：** 修復是一個需要使用者明確同意的動作。它會修改工作樹，需要不同的信任等級和工具權限。從指令層面就分開，比用 flag 更不容易誤觸。

**指令定義：**

```
/security:fix [options]
  <report>                     # 必填：要修復的 security review 報告路徑
  --finding <id>               # 可選：只修復特定 finding（報告中的 finding ID）
  --deep                       # 啟用第 3 輪 fix-verify（預設 2 輪上限）
  --dry-run                    # 只顯示修復計畫，不實際修改
```

**典型工作流：**

```
1. /security:review                    # read-only 稽核 → 產出報告
2. （使用者檢視報告，決定哪些需要修復）
3. /security:fix .agents-output/security/2026-03-31-auth-security-review.md
   # 或
   /security:fix .agents-output/security/2026-03-31-auth-security-review.md --finding F-003
```

**工具權限（與 review 的差異）：**

```yaml
---
name: security:fix
description: 根據 security review 報告執行修復（fix-verify loop）
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, "Bash(git:*)", Write, Edit,
  mcp__plugin_semgrep-plugin_semgrep__semgrep_scan,
  mcp__plugin_semgrep-plugin_semgrep__semgrep_scan_with_custom_rule,
  mcp__plugin_semgrep-plugin_semgrep__get_abstract_syntax_tree,
  mcp__codex__codex, mcp__codex__codex-reply]
---
```

注意：相比 `/security:review`，增加了 `Write` 和 `Edit`——因為修復需要修改檔案。

**Fix-Verify 輪數：**

| 模式 | 上限 | 說明 |
|------|------|------|
| 預設 | 2 輪 | 覆蓋 ~90% 的問題，假設漂移風險可控 |
| `--deep` | 3 輪 | Round 3 需 fresh Codex session，token 消耗 +50-80% |

**依據：**

| 輪次 | 預估解決比例 | 累積解決率 | 假設漂移風險 |
|------|------------|-----------|------------|
| Round 1 | ~70% | 70% | 低 |
| Round 2 | ~20% | 90% | 中 |
| Round 3 | ~5-8% | 95-98% | 高（需 fresh session reset） |

Round 3 的增量收益（5-8%）相對於假設漂移風險和 token 消耗，在多數場景下不划算。保留 `--deep` 讓使用者在 CRITICAL 場景下手動啟用。

**使用者確認點：** `/security:fix` 在套用每個修復之前，應顯示 prediction block 摘要並等待使用者確認，除非使用者明確指定 `--yes`（靜默模式）。這確保使用者始終知道哪些檔案即將被修改。

---

## Phase 3：視採用數據決定

> 目標：深度整合，需要 Phase 1-2 的使用數據支撐決策

### 3.1 Codex Session Resume 深度整合

**現狀：** fix-verify loop 已有 `threadId` / `codex-reply` 概念。

**合併設計：**

```
# 接續上次的 security review session
/security:resume <session-id>

# 在 protocol 內部的行為
Round 1-2: 使用同一 threadId，透過 codex-reply 追加上下文
Round 3 (--deep): 強制 fresh session（新 codex 呼叫），注入前兩輪失敗假設
```

**決策條件：** 只在以下數據成立時推進 Phase 3：
- Phase 1-2 的 fix-verify 使用率 > 20%
- 跨 session resume 的需求在使用者回饋中被提及

---

## 合併後架構

```text
使用者
  │
  ├─ /security:review [--base] [--scope] [--background]     ← read-only 稽核
  ├─ /security:fix <report> [--finding] [--deep]             ← opt-in 修復
  ├─ /security:status / result / cancel                      ← job 管理
  │
  ▼
指令解析層（Phase 1）
  │
  ├─ Target Resolution ─── git diff / branch diff / path filter
  ├─ Job Control ────────── background / status / result / cancel
  │
  ▼
═══════════════════════════════════════════════════════════════
  READ-ONLY 邊界（review + gate 永遠不跨越此線）
═══════════════════════════════════════════════════════════════
  │
  ▼
  ┌─────────────────────────────────┐
  │ Step 1: Semgrep Baseline         │  ← 不變
  │ 獨立分析，CWE 參照，supply chain │
  └──────────┬──────────────────────┘
             ▼
  ┌─────────────────────────────────┐
  │ Step 2: Codex Second Opinion     │  ← 不變
  │ read-only sandbox, 實際程式碼    │
  └──────────┬──────────────────────┘
             ▼
  ┌─────────────────────────────────┐
  │ Step 3: Cross-Validation         │  ← 不變
  │ 60/40 加權, 衝突解決, 信心公式   │
  └──────────┬──────────────────────┘
             ▼
  輸出層（review 到此為止）
  ├─ 終端：verdict + counts + report path
  └─ 檔案：.agents-output/security/YYYY-MM-DD-<scope>-security-review.md

═══════════════════════════════════════════════════════════════
  WRITE 邊界（只有 /security:fix 才進入，需使用者明確觸發）
═══════════════════════════════════════════════════════════════
             │
             ▼
  ┌─────────────────────────────────┐
  │ Step 4: Fix-Verify Loop          │  ← 預設 2 輪, --deep 啟用第 3 輪
  │ prediction block + hypothesis    │     每個修復前需使用者確認
  │ ledger + rollback rules          │
  └──────────┬──────────────────────┘
             ▼
  修復輸出
  ├─ 修改的檔案 + Semgrep re-scan 驗證
  └─ Hypothesis ledger 附加至原報告
```

```text
分級 Gate（Phase 2，Stop hook 觸發）— 永遠在 READ-ONLY 邊界內
  │
  ├─ Level 1: Semgrep only (~10s)
  │     ├─ 0 findings → ALLOW
  │     └─ N findings → BLOCK + 建議 /security:review 或 /security:fix
  │
  └─ Level 2: 完整 Protocol Step 1-3（不含 Step 4）
        ├─ CRITICAL → BLOCK + 建議 /security:fix
        ├─ HIGH → WARNING + 報告路徑
        └─ 其他 → ALLOW
```

---

## 邊際效益遞減分析

### 三個關鍵拐點

**拐點 1：分級 gate 的閾值設定**

最容易過度設計的環節。升級規則太鬆等於沒做，太嚴則造成 alert fatigue。

建議：
- 上線時從嚴開始，逐步放寬（寧可初期多觸發幾次完整 protocol，也不要一開始就漏掉真正的風險）
- 每兩週檢視一次 gate 升級率與 false alarm rate
- 目標穩態：升級率 15-25%、false alarm rate < 30%

**拐點 2：fix-verify 超過 2 輪**

| 指標 | 2 輪內 | 第 3 輪 | 說明 |
|------|--------|---------|------|
| 問題解決率 | ~90% | +5-8% | 增量極小 |
| Token 消耗 | 基準 | +50-80% | fresh session 需重新注入完整上下文 |
| 假設漂移風險 | 低-中 | 高 | 容易偏離原始問題 |
| 結論 | 預設足夠 | `--deep` 按需啟用 | 保守但務實 |

**拐點 3：雙源 vs 多源驗證**

如果未來考慮加入第三驗證源（例如 CodeQL）：

```
2 sources → 3 種衝突類型 (A, B, C)     ← 目前設計
3 sources → 7 種衝突組合               ← 複雜度指數增長
```

除非第三源覆蓋的 CWE 類別與 Semgrep + Codex **完全不重疊**，否則增加的衝突解決成本會大於驗證收益。**目前不建議擴展至三源。**

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| Gate 噪音導致使用者忽略警告 | 真正的 CRITICAL 被淹沒 | 分級設計 + false alarm rate 監控 |
| 背景執行的 security scan 結果被忽略 | 安全問題未被處理 | CRITICAL 結果強制前景通知 |
| 指令介面改變破壞現有觸發詞工作流 | 使用者困惑 | 保留觸發詞作為別名，兩種方式並存 |
| Phase 2 的規則維護成本 | 規則過時 → 升級邏輯失準 | 規則與 Semgrep ruleset 同步更新 |
| RUNNING job 在 session 結束後成為孤兒 | 使用者看到 STALE 狀態感到困惑 | 下次 session 啟動時自動標記 STALE + 提示重新執行 |
| review/fix 拆分增加使用者操作步驟 | 簡單修復需要兩個指令 | `/security:fix` 支援直接指定 finding ID，減少往返 |

---

## 實作順序與驗收標準

### Phase 1 驗收標準

- [ ] `/security:review` 可正常觸發 read-only protocol（Step 1-3），產出報告
- [ ] `/security:review` **不會**修改工作樹中的任何原始碼檔案
- [ ] `--base <branch>` 正確選取 merge-base diff
- [ ] `--scope staged` 和 `--scope working-tree` 正確篩選變更範圍
- [ ] `[path...]` 參數正確過濾路徑前綴
- [ ] `--background` 回傳 job ID，不阻塞主對話
- [ ] `/security:status` 正確顯示 QUEUED/RUNNING/COMPLETED/FAILED/CANCELLED/STALE 狀態
- [ ] `/security:result` 正確回傳 verdict + report path
- [ ] `/security:cancel` 將 job 標記為 CANCELLED
- [ ] Session 結束後重啟，RUNNING job 被標記為 STALE
- [ ] 原有觸發詞（"security check" 等）仍可正常運作，行為等同 `/security:review`

### Phase 2 驗收標準

- [ ] Level 1 gate 在 <15 秒內完成
- [ ] Level 2 gate 執行完整 Step 1-3，**不進入** Step 4 fix-verify
- [ ] 升級規則正確觸發 Level 2
- [ ] Gate BLOCK 訊息包含 `/security:fix` 建議指令
- [ ] `/security:fix <report>` 正確讀取報告並進入 fix-verify loop
- [ ] `/security:fix --finding <id>` 只修復指定 finding
- [ ] `/security:fix --dry-run` 只顯示計畫，不修改檔案
- [ ] 預設 2 輪上限，`--deep` 啟用第 3 輪
- [ ] 每個修復前顯示 prediction block 等待使用者確認
- [ ] Gate 升級率與 false alarm rate 可被量測

### Phase 3 進入條件

- Phase 1-2 上線至少 2 週
- fix-verify 使用率 > 20%
- 使用者回饋中出現跨 session resume 需求

---

## 附錄：與 codex-plugin-cc 的功能對照

| codex-plugin-cc 功能 | 合併決策 | 對應 Phase |
|---------------------|---------|-----------|
| `/codex:review`（read-only） | 合併為 `/security:review`（同樣 read-only） | 1 |
| `--base` / `--scope` | 沿用 target resolution 邏輯，scope 收斂為 `staged` 和 `working-tree` | 1 |
| `--background` / `--wait` | 合併，補齊 job 狀態機與生命週期管理 | 1 |
| `/codex:status` / `/codex:result` / `/codex:cancel` | 合併為 `/security:*` 系列 | 1 |
| `/codex:adversarial-review` | **不合併**。品質維度超出安全範疇 | — |
| Stop hook review gate | 合併為分級 gate（永遠 read-only，不進 fix-verify） | 2 |
| `/codex:rescue`（寫入修復） | 概念對應為 `/security:fix`（opt-in，獨立指令） | 2 |
| Codex session resume | 深度整合至 `/security:fix` 的 fix-verify loop | 3 |
| App-server broker | **不合併**。subagent 架構不需要，用 QUEUED 機制替代並行控制 | — |
