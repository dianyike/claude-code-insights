# CLAUDE.md 最佳實踐指南

> 基於 Anthropic 官方文檔、社群經驗及學術研究整理
>
> 相關研究：[Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?](https://arxiv.org/html/2602.11988v1)

---

## 目錄

1. [CLAUDE.md 是什麼](#1-claudemd-是什麼)
2. [從零開始的正確姿勢](#2-從零開始的正確姿勢)
3. [載入機制與優先順序](#3-載入機制與優先順序)
4. [該寫什麼](#4-該寫什麼)
5. [不該寫什麼](#5-不該寫什麼)
6. [學術研究：上下文檔案的真實效果](#6-學術研究上下文檔案的真實效果)
7. [撰寫原則：少即是多](#7-撰寫原則少即是多)
8. [確定性執行：用 Hooks 取代指令](#8-確定性執行用-hooks-取代指令)
9. [三層架構模型](#9-三層架構模型)
10. [從零開始的範例模板](#10-從零開始的範例模板)
11. [進階模式](#11-進階模式)
12. [常見反模式](#12-常見反模式)
13. [維護實務](#13-維護實務)
14. [常見痛點與解法](#14-常見痛點與解法)
15. [CLAUDE.md vs Skills vs Subagent 的分工](#15-claudemd-vs-skills-vs-subagent-的分工)
16. [參考資源](#16-參考資源)
17. [快速檢查清單](#17-快速檢查清單)

---

## 1. CLAUDE.md 是什麼

CLAUDE.md 是 Claude Code 的**專案上下文檔案**，告訴 Claude「這個專案是什麼、怎麼跑、有什麼規則」。它在**每次對話開始時自動載入**，相當於你每次都在對話開頭貼上的系統提示。

### 核心定位

| 特性 | 說明 |
|------|------|
| **自動載入** | 不需要手動引用，Claude Code 啟動時自動讀取 |
| **全域影響** | 載入後的所有指令都受其約束 |
| **靜態上下文** | 不像 Skills 可以按需觸發，CLAUDE.md 永遠在 context 中 |
| **累積消耗** | 每多寫一行，每次對話都多消耗一點 context window |

### 與其他 AI 編碼工具的對應

| Claude Code | Cursor | Windsurf | GitHub Copilot |
|------------|--------|----------|----------------|
| `CLAUDE.md` | `.cursorrules` | `.windsurfrules` | `.github/copilot-instructions.md` |

---

## 2. 從零開始的正確姿勢

> **CLAUDE.md 不是一開始就寫好的，是用出來的。**

### 為什麼不建議用 `/init` 自動生成

Claude Code 提供了 `/init` 指令，讓 Claude 分析你的 codebase 後自動生成 CLAUDE.md。聽起來很方便，但根據研究（見[第 6 節](#6-學術研究上下文檔案的真實效果)），**LLM 自動生成的上下文檔會降低任務成功率 2-3%、增加推理成本 20%+**。

原因很簡單：`/init` 生成的 200 行裡，可能只有 10 行是 Claude 真正無法從程式碼推斷的。剩下的 190 行都是冗餘——Claude 看 `package.json`、檔案結構、程式碼本身就能知道的資訊。這些冗餘不僅浪費 context window，還會干擾 Claude 的判斷。

### 正確的起步流程

```text
第一步：先不寫
  ↓ 直接開始用 Claude Code 做你的任務
第二步：觀察問題
  ↓ 它用了 npm 而你要 pnpm？記下來
  ↓ 它不知道你的測試指令？記下來
  ↓ 它改了不該動的 generated 檔案？記下來
第三步：針對問題加規則
  ↓ 每次只加解決具體問題的最小內容
  ↓ 一條規則解決一個問題，不要預防性地塞一堆
第四步：累積後整理
  ↓ 用三層架構分配（見第 9 節）
  ↓ 能轉成 Hook/Linter 的就轉出去
```

### 對比

| 方式 | 第一天就有 | 精準度 | 長期維護 |
|------|----------|--------|---------|
| `/init` 自動生成 | 200 行 | 低（90% 冗餘） | 難（不知道哪些有用） |
| 從問題出發手動累積 | 0 行 | 高（每行都解決真實問題） | 易（每條規則都有存在理由） |

**這個流程比 `/init` 慢，但每一行都是你真正需要的。**

---

## 3. 載入機制與優先順序

### 載入位置（由高到低）

```text
~/.claude/CLAUDE.md          ← 全域：所有專案共用（個人偏好、通用規則）
├── /project/CLAUDE.md       ← 專案根目錄：專案級設定
├── /project/src/CLAUDE.md   ← 子目錄：模組級覆寫
└── /project/.claude/rules/  ← Rules 目錄：分檔管理規則
```

### 載入規則

1. **全域檔案**（`~/.claude/CLAUDE.md`）：永遠載入，適合放個人偏好
2. **專案根目錄**（`/project/CLAUDE.md`）：在該專案工作時載入
3. **子目錄檔案**：只在 Claude 存取該目錄下的檔案時才載入
4. **Rules 目錄**（`.claude/rules/*.md`）：所有 `.md` 檔案都會載入，適合分類管理

### 多檔案策略：何時拆分

| 場景 | 建議 |
|------|------|
| 內容 < 200 行 | 單一 `CLAUDE.md` 就好 |
| 內容 > 200 行 | 拆到 `.claude/rules/` 下分檔管理 |
| 前端 / 後端規則差異大 | 各自子目錄放 `CLAUDE.md` |
| 團隊 vs 個人偏好 | 團隊規則進 `CLAUDE.md`（進版控），個人偏好進 `~/.claude/CLAUDE.md` |

---

## 4. 該寫什麼

**核心原則：只寫 Claude 無法從程式碼本身推斷的資訊。**

### 4.1 建置與執行指令

Claude 最常需要但最難猜到的資訊——你的專案怎麼跑：

```markdown
## 開發指令

- 安裝依賴：`pnpm install`
- 開發模式：`pnpm dev`
- 跑測試：`pnpm test`
- 跑單一測試：`pnpm test -- --filter=<test-name>`
- 建置：`pnpm build`
- Lint：`pnpm lint --fix`
```

### 4.2 不明顯的架構決策

那些「為什麼這樣做」而非「做了什麼」的決策：

```markdown
## 架構決策

- 使用 monorepo（pnpm workspaces），packages/ 下每個子目錄是獨立套件
- API 層使用 tRPC，不寫 REST endpoints
- 狀態管理用 Zustand，不用 Redux（團隊決策，不要改）
- 資料庫遷移用 Drizzle，不用 Prisma
```

### 4.3 程式碼慣例（非顯而易見的）

只寫那些從程式碼中不容易看出來的規則：

```markdown
## 慣例

- 元件檔名用 PascalCase，工具函數用 camelCase
- 所有 API 回應必須包含 `{ success, data, error }` 結構
- 錯誤碼定義在 `src/constants/errors.ts`，不要硬編碼
- commit message 格式：`type(scope): description`
```

### 4.4 重要的邊界條件

```markdown
## 注意事項

- 不要修改 `src/generated/` 下的檔案，它們由 codegen 自動產生
- 環境變數定義在 `.env.example`，必須同步更新
- CI 會跑 `pnpm typecheck`，型別錯誤會阻擋合併
```

---

## 5. 不該寫什麼

**核心原則：如果資訊可以從程式碼、git 歷史、或既有文件中得到，就不要重複。**

### 5.1 泛泛的專案描述

```markdown
<!-- 不要寫這些 -->
## 專案簡介
這是一個使用 React 和 TypeScript 建構的前端應用程式，
採用 Next.js 框架，搭配 Tailwind CSS 進行樣式設計...
```

為什麼不要？Claude 看 `package.json` 和檔案結構就知道了。

### 5.2 語言或框架的通用知識

```markdown
<!-- 不要寫這些 -->
## TypeScript 規範
- 使用 interface 而非 type（除非需要 union）
- 啟用 strict mode
- 避免使用 any
```

為什麼不要？這是 TypeScript 社群共識，Claude 訓練資料裡已經有了。**除非**你的專案刻意違反慣例（例如「我們這裡偏好用 `type` 而非 `interface`」），才需要寫。

### 5.3 程式碼中已經表達的資訊

```markdown
<!-- 不要寫這些 -->
## 資料庫 Schema
users 表有 id, name, email, created_at 欄位...
```

為什麼不要？Claude 可以直接讀 schema 檔案，而且 CLAUDE.md 裡的描述可能過時。

### 5.4 冗長的 API 文檔

```markdown
<!-- 不要寫這些 -->
## API 端點
GET /api/users - 取得所有用戶
POST /api/users - 建立用戶
...（50 行）
```

為什麼不要？這些資訊應該放在程式碼註解或獨立文檔中，由 Claude 按需讀取。每次對話都載入 50 行 API 文檔是浪費。

---

## 6. 學術研究：上下文檔案的真實效果

### 論文概要

[Evaluating AGENTS.md](https://arxiv.org/html/2602.11988v1)（2026）首次以實證方式評估了上下文檔案對 coding agents 的影響。結果令人意外：

| 設定 | 任務成功率變化 | 推理成本變化 |
|------|--------------|-------------|
| LLM 自動生成的上下文檔 | **下降 2-3%** | **增加 20-23%** |
| 開發者手寫的上下文檔 | 提升約 4% | 增加約 19% |
| 無上下文檔（基準） | — | — |

### 為什麼會有害？

1. **資訊冗餘**：LLM 生成的檔案與既有文件（README、docstring）高度重複，沒有新價值
2. **干擾導航**：代碼庫概述並沒有幫助 agent 更快找到相關檔案，反而多走了 2-4 步
3. **推理成本暴增**：額外的 context 讓模型需要處理更多 tokens，但品質沒有提升

### 唯一有幫助的情境

當專案**完全沒有其他文件**（移除所有 markdown 文檔）時，LLM 生成的上下文檔才有正面效果（+2.7%），因為它成為唯一的文件來源。

### 對 CLAUDE.md 的啟示

| 做法 | 效果 |
|------|------|
| 用 LLM 自動生成 CLAUDE.md | 大概率有害，避免 |
| 把 README 的內容貼進 CLAUDE.md | 冗餘，有害 |
| 只寫 Claude 從程式碼中推斷不出的資訊 | 手寫 +4%，值得投入 |
| 極簡、具體、可操作的指令 | 最大化收益，最小化成本 |

---

## 7. 撰寫原則：少即是多

### 原則一：每一行都有成本

CLAUDE.md 在**每次對話**都會載入。100 行的 CLAUDE.md 意味著你每次對話都預先消耗了 ~1000 tokens 的 context window。問自己：「這一行值得在每次對話中都出現嗎？」

### 原則二：具體指令 > 泛泛描述

```markdown
<!-- 差：泛泛描述 -->
本專案使用 monorepo 架構，請遵循相關最佳實踐。

<!-- 好：具體指令 -->
跑測試時用 `pnpm --filter=<package> test`，不要用 `pnpm test`（會跑全部套件）。
```

### 原則三：約束 > 建議

Claude 對明確的約束（「不要做 X」）比模糊的建議（「盡量做 Y」）反應更好：

```markdown
<!-- 差：模糊建議 -->
盡量保持程式碼簡潔。

<!-- 好：明確約束 -->
不要在元件中直接呼叫 fetch，所有 API 請求必須通過 src/lib/api.ts。
```

### 原則四：維護紀律

CLAUDE.md 的內容會隨專案演進而過時。過時的指令比沒有指令更糟——它會讓 Claude 做出錯誤判斷。

- 每次重大架構變更後更新 CLAUDE.md
- 定期審視：刪除已經不適用的規則
- 如果某條規則已經被程式碼（linter、CI）強制執行，就從 CLAUDE.md 移除

---

## 8. 確定性執行：用 Hooks 取代指令

> 來源：[Matt Pocock — 如何強迫 Claude Code 使用正確的 CLI](https://www.youtube.com/watch?v=3CSi8QAoN-s)

這是最容易被忽略的優化：**能用確定性機制（Hooks、Linter、CI）執行的規則，就不要放在 CLAUDE.md 裡。**

### 問題：CLAUDE.md 指令是非確定性的

```markdown
# CLAUDE.md
- 使用 pnpm，不要用 npm
- 不要執行 git push
```

這些指令只是「建議」——Claude 大多數時候會遵守，但不保證。同時它們永遠佔用指令預算，即使大部分對話根本不涉及安裝套件或 git 操作。

### 解決方案：轉成 Hooks

Claude Code Hooks 在工具執行前/後跑確定性的腳本，可以**真正阻擋**命令並引導 Claude 自動修正：

```bash
# .claude/hooks/block-npm.sh
#!/bin/bash
if [[ "$TOOL_INPUT" =~ ^npm ]]; then
  echo "使用 pnpm，不要用 npm"
  exit 2  # exit 2 = 阻擋並回饋錯誤訊息給 Claude
fi
```

```jsonc
// .claude/settings.json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": { "tool_name": "bash" },
        "command": ".claude/hooks/block-npm.sh"
      }
    ]
  }
}
```

**效果**：Claude 嘗試跑 `npm install react-query` → Hook 阻擋 → Claude 自動改用 `pnpm install react-query`。完全確定性，零指令預算消耗。

### 決策流程：指令 vs Hook vs Linter

```text
這條規則可以被機器確定性執行嗎？
├── 是：CLI 命令偏好（npm→pnpm）→ 轉成 Hook
├── 是：程式碼風格（禁止 positional params）→ 轉成 ESLint 規則
├── 是：禁止危險操作（git push）→ 轉成 Hook
└── 否：架構決策、上下文資訊 → 留在 CLAUDE.md
```

### 常見可轉換的規則

| CLAUDE.md 指令 | 轉換目標 | 方式 |
|----------------|---------|------|
| 「用 pnpm 不要用 npm」 | Hook | `pre-tool-use` 攔截 bash 命令 |
| 「不要 git push」 | Hook | `pre-tool-use` 攔截 bash 命令 |
| 「用我們的 wrapper script 跑測試」 | Hook | 攔截 `npx jest` → 改跑 `./scripts/test.sh` |
| 「函數參數不要超過 3 個」 | ESLint | `max-params` 規則 |
| 「不要用 any」 | TSConfig | `"strict": true` + `@typescript-eslint/no-explicit-any` |
| 「import 要排序」 | ESLint | `eslint-plugin-import` |

### 核心理念

> **「把指令從指令預算中釋放出來，用確定性機制執行。這樣 CLAUDE.md 中剩下的指令，都是真正需要 LLM 思考的上下文。」**
> — Matt Pocock

這與第 6 節的論文研究結論一致：CLAUDE.md 的內容越少、越精準，效果越好。能用 Hooks 和 Linter 處理的規則移出去，讓 CLAUDE.md 只保留 Claude 真正需要「理解」的資訊。

---

## 9. 三層架構模型

不是所有規則都應該放在 CLAUDE.md 裡。根據規則的**執行方式**，應該分配到不同的層級：

### 第一層：強制執行層（確定性）

| 該放什麼 | 為什麼 |
|---------|--------|
| 程式碼格式規範 → ESLint / Prettier | Claude 可能忘記規則，但程式碼永遠不會忘 |
| 型別檢查 → TypeScript strict mode | 編譯器比指令更可靠 |
| 測試覆蓋 → CI/CD pipeline | 自動化驗證，不依賴 LLM 記憶 |
| CLI 偏好 → Hooks（見第 8 節） | 確定性攔截，零指令預算消耗 |

**原則**：凡是能用程式碼強制執行的，就不要用自然語言指示。

### 第二層：高頻召回層（CLAUDE.md 核心區）

| 該放什麼 | 字數限制 |
|---------|---------|
| 專案架構概述（精簡版） | 100-200 行以內 |
| 關鍵技術棧版本 | |
| 核心編程約定（5 條以內） | |
| 建置與測試指令 | |

**原則**：這裡的內容每次對話都會載入，所以每一行都必須值得這個成本。

### 第三層：按需查閱層（參考文檔）

| 該放什麼 | 存放位置 |
|---------|---------|
| 詳細架構文檔 | `docs/architecture.md` |
| API 參考 | `docs/api.md` |
| 歷史決策記錄 | `docs/decisions/` |

**關鍵**：用連結引用，不要全塞進 CLAUDE.md：

```markdown
# CLAUDE.md 中這樣寫
## 架構
本專案架構詳見 `docs/architecture.md`，修改 API 端點前請先查閱。
```

### 三層全景圖

```text
第一層：強制執行（ESLint、TypeScript、CI/CD、Hooks）
  ↓ 程式碼自動驗證，Claude 做錯會立刻收到回饋
第二層：高頻召回（CLAUDE.md 核心區，<200 行）
  ↓ 每次對話自動載入，只放真正高頻且無法自動化的資訊
第三層：按需查閱（docs/、獨立 .md 檔案）
  ↓ Claude 需要時才去讀，用連結引用而非內嵌
```

### 判斷流程

```text
遇到需要告訴 Claude 的事情
├── 能用程式碼強制執行嗎？
│   └── 是 → 寫成 Linting 規則 / 測試 / Hook（第一層）
├── 每次對話都需要嗎？
│   └── 是 → 放進 CLAUDE.md 核心區（第二層）
└── 偶爾需要？
    └── 是 → 放進參考文檔，用連結引用（第三層）
```

---

## 10. 從零開始的範例模板

### 最小可行模板（適合大多數專案）

```markdown
# CLAUDE.md

## 開發指令

- 安裝：`pnpm install`
- 開發：`pnpm dev`
- 測試：`pnpm test`
- 建置：`pnpm build`

## 重要約束

- 不要修改 `src/generated/` 下的檔案
- API 請求統一通過 `src/lib/api.ts`
- commit message 格式：`type(scope): description`
```

這就夠了。30 行以內，只包含 Claude 真正需要的資訊。

### 中型專案模板

```markdown
# CLAUDE.md

## 開發指令

- 安裝：`pnpm install`
- 開發：`pnpm dev`（啟動 Next.js dev server + API）
- 測試：`pnpm test`（Jest + React Testing Library）
- 單一測試：`pnpm test -- --testPathPattern=<pattern>`
- 型別檢查：`pnpm typecheck`
- Lint：`pnpm lint --fix`

## 架構

- Monorepo：`packages/web`（前端）、`packages/api`（後端）、`packages/shared`（共用型別）
- 資料庫：PostgreSQL + Drizzle ORM，migration 在 `packages/api/drizzle/`
- 狀態管理：Zustand（不用 Redux）
- API 通信：tRPC（不寫 REST）

## 約束

- 不要修改 `packages/shared/generated/` — 由 codegen 產生
- 新 API endpoint 必須加在 `packages/api/src/routers/` 下
- 前端元件放 `packages/web/src/components/`，按 feature 分目錄
- 所有環境變數在 `.env.example` 中有定義，新增時必須同步
- CI 會跑 typecheck + lint + test，全過才能合併
```

### 全域模板（`~/.claude/CLAUDE.md`）

```markdown
# 全域偏好

- 回覆使用繁體中文
- commit message 用英文
- 優先使用 function 宣告而非箭頭函數
- 不要在回覆結尾加總結
```

---

## 11. 進階模式

### 11.1 Rules 目錄分檔管理

當 CLAUDE.md 超過 200 行時，拆分到 `.claude/rules/` 下：

```text
.claude/rules/
├── coding-style.md    # 程式碼風格
├── testing.md         # 測試規範
├── security.md        # 安全守則
├── workflow.md        # 工作流程
└── pragmatism.md      # 例外處理規則
```

所有 `.claude/rules/*.md` 會自動載入，不需要在 CLAUDE.md 中引用。

**注意**：拆分後仍然是全部載入，並不會節省 context。拆分的好處是**可讀性和可維護性**。

### 11.2 子目錄覆寫

針對 monorepo 中不同模組設定不同規則：

```text
/project/CLAUDE.md                  # 共用規則
/project/packages/web/CLAUDE.md     # 前端專用規則
/project/packages/api/CLAUDE.md     # 後端專用規則
```

子目錄的 CLAUDE.md 只在 Claude 存取該目錄下的檔案時才載入。

### 11.3 與 Skills 搭配

CLAUDE.md 放**永遠需要的**上下文，Skills 放**按需觸發的**指令：

```markdown
# CLAUDE.md 中引用 skill
## 程式碼審查
使用 `/review` 觸發程式碼審查流程（詳見 .claude/skills/review/）
```

### 11.4 敏感資訊處理

```markdown
<!-- 不要放在 CLAUDE.md 中 -->
API_KEY=sk-xxxxx

<!-- 應該這樣寫 -->
## 環境變數
所有 API keys 定義在 `.env`（已加入 .gitignore），
參考 `.env.example` 瞭解需要哪些變數。
```

---

## 12. 常見反模式

### 反模式一：百科全書型

```markdown
<!-- 反模式：把所有知識都塞進去 -->
# CLAUDE.md（800+ 行）
## 專案歷史
本專案始於 2023 年...
## 完整 API 文檔
### GET /api/users
### POST /api/users
### PUT /api/users/:id
...（200 行）
## TypeScript 風格指南
...（150 行）
## Git 工作流程
...（100 行）
```

**問題**：每次對話浪費大量 context，且大部分內容 Claude 用不到。

**修正**：精簡到 50 行以內，詳細內容移到獨立文件或 Skills。

### 反模式二：LLM 自動生成型

```markdown
<!-- 反模式：讓 Claude 自己生成 CLAUDE.md -->
"Claude，幫我分析這個 codebase 然後生成 CLAUDE.md"
```

**問題**：研究顯示 LLM 生成的上下文檔會降低 2-3% 成功率、增加 20%+ 成本。生成的內容大多是 Claude 已經能從程式碼推斷的資訊。

**修正**：手動撰寫，只寫 Claude 推斷不出的資訊。

### 反模式三：過時不更新型

```markdown
<!-- 反模式：半年沒更新 -->
## 技術棧
- 使用 Webpack（已改用 Vite 三個月了）
- 測試用 Jest（已換成 Vitest）
- 部署到 Heroku（已遷移到 Vercel）
```

**問題**：過時的指令比沒有指令更糟，Claude 會遵循錯誤的指引。

**修正**：架構變更時同步更新，定期審視刪除過時內容。

### 反模式四：重複 README 型

```markdown
<!-- 反模式：把 README 的內容複製一份 -->
# CLAUDE.md
## 關於本專案
（和 README.md 一模一樣的內容...）
```

**問題**：資訊冗餘，增加 context 消耗但不增加價值。Claude 可以自己讀 README。

**修正**：CLAUDE.md 與 README 的定位不同——README 寫給人看，CLAUDE.md 寫給 Claude 看。

### 反模式五：讓 Claude 維護 CLAUDE.md

```markdown
<!-- 反模式：讓 Claude 自己更新 CLAUDE.md -->
"Claude，根據我們剛才的對話更新 CLAUDE.md"
```

**問題**：Claude 傾向於把所有學到的東西都塞進去，導致 CLAUDE.md 膨脹失控。

**修正**：CLAUDE.md 應由人工維護。如果需要自動捕捉修正，使用專門的工具如 [claude-reflect](https://github.com/BayramAnnakov/claude-reflect)，它會經過人工審查階段才寫入。

> **gingersnap 的經驗**：「讓 Claude 寫程式碼，但絕不讓 Claude 碰 CLAUDE.md。」

---

## 13. 維護實務

CLAUDE.md 不是寫完就不管的檔案。沒有維護紀律，它會快速腐化。

### 13.1 定期清理

- **每週 review** CLAUDE.md 內容
- 刪除過時和重複的內容
- 確認每條規則仍然有效且有必要

### 13.2 分層管理

```text
CLAUDE.md              # 核心規則，<200 行
├── docs/arch.md       # 架構文檔（第三層）
├── docs/api.md        # API 參考（第三層）
└── .cursorrules       # 編輯器規則（如果同時用 Cursor）
```

### 13.3 版本控制

CLAUDE.md **必須進 git 管理**：

- 團隊成員可以 review CLAUDE.md 的變更
- 可以追溯何時加入、何時移除了哪條規則
- 避免個人偏好污染團隊共用的 CLAUDE.md（個人偏好放 `~/.claude/CLAUDE.md`）

### 13.4 更好的替代方案

| 方案 | 優點 | 缺點 |
|------|------|------|
| **階段性復盤** | 人工篩選，品質高 | 需要紀律 |
| **Linting 優先** | 強制執行 | 只適用於格式類問題 |
| **會話日誌分析** | 全面 | 資訊過載 |
| **claude-reflect** | 自動捕捉修正，經審查後寫入 | 需要額外設置 |

---

## 14. 常見痛點與解法

### 痛點一：Claude 不去查閱參考文檔

> 「我的問題是 Claude 經常不去查閱參考文檔。」

**解法**：

1. 在 CLAUDE.md 中**明確指出何時查閱**，使用具體觸發條件：

```markdown
## 參考文檔
- 修改 API 端點前，**必須**先讀 `docs/api.md`
- 修改資料庫 schema 前，**必須**先讀 `docs/database.md`
```

2. 使用更明確的觸發條件（而非泛泛的「請參考 docs/」）
3. 考慮將參考文檔封裝成 Claude Skills，利用 `description` 自動觸發

### 痛點二：CLAUDE.md 越來越長

**解法**：套用三層架構模型（第 9 節），把內容按層級分配：

- 能自動化的 → 第一層（Hooks / Linter）
- 高頻必要的 → 第二層（CLAUDE.md，控制在 200 行內）
- 偶爾需要的 → 第三層（獨立文檔，用連結引用）

### 痛點三：不確定該寫什麼

**解法**：先不寫。觀察 Claude 在什麼地方犯錯或偏離你的期望，**只在出問題時才加規則**。這比預先猜測 Claude 需要什麼更有效。

---

## 15. CLAUDE.md vs Skills vs Subagent 的分工

| 維度 | CLAUDE.md | Skills | Subagent |
|------|-----------|--------|----------|
| **載入時機** | 每次對話自動載入 | 觸發時按需載入 | 被委派時啟動 |
| **適合放** | 建置指令、架構決策、全域約束 | 具體工作流程、步驟化指令 | 獨立的研究或分析任務 |
| **Context 消耗** | 永久佔用 | 觸發時才佔用 | 使用獨立 context window |
| **更新頻率** | 架構變更時 | 工作流程變更時 | 需求變更時 |
| **誰維護** | 團隊共同 | 流程負責人 | 任務負責人 |

### 決策流程

```text
這個資訊需要在每次對話中都出現嗎？
├── 是 → 放 CLAUDE.md（但確認真的每次都需要）
└── 否 → 這是一個可重複的工作流程嗎？
    ├── 是 → 寫成 Skill（/skill-name 觸發）
    └── 否 → 這個任務需要大量 context 且可獨立完成嗎？
        ├── 是 → 寫成 Subagent
        └── 否 → 可能不需要持久化，口頭告訴 Claude 就好
```

---

## 16. 參考資源

- [Claude Code 官方文檔：Memory](https://docs.anthropic.com/en/docs/claude-code/memory)
- [Evaluating AGENTS.md（學術論文）](https://arxiv.org/html/2602.11988v1)
- [Matt Pocock — 如何強迫 Claude Code 使用正確的 CLI（避免使用 CLAUDE.md）](https://www.youtube.com/watch?v=3CSi8QAoN-s)
- [claude-reflect — Claude Code 自學習系統（自動捕捉修正並寫入記憶）](https://github.com/BayramAnnakov/claude-reflect)
- [為什麼你的 CLAUDE.md 越寫越爛？90% 的人搞錯了邊界](https://www.bilibili.com/video/BV1K7rSBJEPb/)
- [Harness Engineering: leveraging Codex in an agent-first world（OpenAI）](https://openai.com/index/harness-engineering/) — AGENTS.md 當目錄而非百科、用 linter 強制規則
- [Skill Issue: Harness Engineering for Coding Agents（HumanLayer）](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — HumanLayer CLAUDE.md 不超過 60 行的實踐
- [Skills 最佳實踐指南](./skills-best-practices.md)
- [Subagent 最佳實踐指南](./subagent-best-practices.md)

---

## 17. 快速檢查清單

撰寫或審視 CLAUDE.md 時，逐項確認：

- [ ] **行數 < 100**：超過就考慮拆到 `.claude/rules/` 或移到 Skills
- [ ] **無冗餘**：沒有與 README、package.json、程式碼重複的內容
- [ ] **非 LLM 生成**：是人工撰寫的，不是讓 AI 自動產生的
- [ ] **有建置指令**：至少包含安裝、開發、測試、建置指令
- [ ] **有明確約束**：使用「不要」「必須」等明確用詞，而非「盡量」「建議」
- [ ] **無過時資訊**：所有提到的工具、路徑、指令都是當前有效的
- [ ] **無敏感資訊**：沒有 API keys、密碼、tokens
- [ ] **已轉移確定性規則**：CLI 偏好、禁止命令等已轉成 Hooks 或 Linter
- [ ] **三層分配**：內容按強制執行 / 高頻召回 / 按需查閱正確分層
- [ ] **人工維護**：CLAUDE.md 由人工撰寫和更新，不是由 Claude 自動生成
- [ ] **有維護機制**：進 git 版控、定期 review、團隊知道何時該更新
