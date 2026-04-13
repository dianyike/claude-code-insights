# Claude Code Rules — 入門套件

[English](README.md) | 繁體中文

經實戰驗證的 `.claude/rules/` 規則集，用於引導 Claude Code 在真實專案中的行為。拿有用的，刪不需要的。

## 設計哲學

大多數規則集都會掉進兩種失敗模式：**太嚴格**（每條規則都全面執行，原型開發慢到爬）或**太鬆散**（規則寫在紙上但默默被忽略）。這套規則用一個 **pragmatism 層**來解決這個問題 — 一個後設規則（`pragmatism.md`）定義了三個風險等級，並據此調整執行強度：

| 等級 | 範圍舉例 | 執行方式 |
|------|---------|---------|
| 關鍵 | 認證、支付、資料遷移 | 最大強度，不允許捷徑 |
| 標準 | 產品功能、API | 完整執行，可以有記錄在案的例外 |
| 探索 | 原型、腳本、spike | 測試要求可放寬，但標記為 tech debt |

這意味著 `security.md` 在認證相關程式碼上嚴格執行，但不會擋住一個用完即棄的腳本。`testing.md` 要求業務邏輯有 80% 覆蓋率，但不會在一次性遷移 helper 上碎碎唸。規則不變 — 變的是執行力度。

### 其他關鍵設計決策

- **每條規則都有「Why」** — Claude 理解規則的理由時，更能遵循規則的精神。光靠命令式指令容易被鑽漏洞或過度套用。
- **Violation signals** — Golden rules 附帶可觀察的違規信號（例如「兩個檔案包含功能相同的邏輯」），讓 Claude 能自我偵測是否即將違規。
- **關注點分離** — 在地化設定獨立成一個檔案，不埋在 workflow 規則裡。團隊只需換一個檔案，不用翻找段落。

## 檔案一覽

| 檔案 | 用途 |
|------|------|
| `golden-rules.md` | 硬性約束，全域適用（DRY、範圍紀律、驗證外部存取） |
| `pragmatism.md` | 後設規則：風險分級，控制其他規則的執行強度 |
| `workflow.md` | 日常工作習慣：先讀再寫、重試紀律、驗證優先 |
| `coding-style.md` | 程式碼風格：不可變性、錯誤處理、語法偏好 |
| `testing.md` | TDD 工作流程、覆蓋率目標、反模式 |
| `security.md` | 安全檢查清單、金鑰管理、破壞性操作防護 |
| `localization.md` | 語言偏好模板 — 用你團隊的語言替換 placeholder |

### 相依關係圖

```text
golden-rules.md ──引用──► pragmatism.md
workflow.md     ──引用──► testing.md
```

其餘檔案皆可獨立使用。

## 安裝方式

### 方式 A：專案層級（推薦團隊使用）

```bash
# 從專案根目錄
mkdir -p .claude/rules
cp path/to/examples/rules/*.md .claude/rules/

# 編輯語言設定
$EDITOR .claude/rules/localization.md
```

放在 `.claude/rules/` 的規則會被 Claude Code 自動載入。如果 commit 進 repo，所有人都會套用；如果加進 `.gitignore`，就只有你自己用。

### 方式 B：使用者層級（個人預設值）

```bash
# 全域規則適用於你所有的專案
mkdir -p ~/.claude/rules
cp path/to/examples/rules/*.md ~/.claude/rules/

$EDITOR ~/.claude/rules/localization.md
```

### 方式 C：按需挑選

不一定要全部 7 個檔案。快速起步的最高價值子集：

1. `golden-rules.md` + `pragmatism.md` — 核心約束系統
2. `workflow.md` — 攔截最常見的 AI 寫程式錯誤
3. 其餘的 — 視需求再加

## 驗證過的技術棧

這套規則已在以下環境中使用過：

- **語言**：TypeScript/JavaScript、Python、Go、Rust
- **框架**：React、Next.js、Express、FastAPI
- **專案類型**：全端 Web 應用、CLI 工具、純文件 repo、MCP 伺服器
- **團隊規模**：個人開發者到小型團隊（1-5 人）

規則設計上與語言無關。`coding-style.md` 的語法偏好略偏 JS/TS — 若用在其他語言棧，可調整或移除該段落。

## 自訂指南

**新增規則**：加到最相關的檔案中，附上「Why:」說明理由，如果是硬性約束再加「Violation signal」。

**移除規則**：直接刪除。除了相依關係圖中標示的兩處交叉引用外，不會影響其他檔案。

**調整嚴格度**：編輯 `pragmatism.md` 中的風險等級表。例如，如果你的團隊把所有 API 工作都視為關鍵：

```markdown
| **關鍵** | 核心商業邏輯、支付流程、認證/身份、資料遷移、**所有 API 端點** | ... |
```

**新增等級**：有些團隊會加一個「Legacy」等級，用於無法重構但必須碰的程式碼：

```markdown
| **Legacy** | `src/old/` 中的程式碼、第三方 fork | 最低限度執行 — 求生存，能逃就逃 |
```
