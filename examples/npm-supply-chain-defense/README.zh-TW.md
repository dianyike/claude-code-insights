# npm 供應鏈防禦 — Claude Code 三層架構

透過 Claude Code 的 Hook + MCP 機制建立 npm 供應鏈安全防線，在 AI 幫你安裝套件前自動攔截可疑目標。

## 架構概覽

```text
Claude 執行 npm install foo
        │
        ▼
┌─ 第一層：.npmrc ──────────────────┐
│  ignore-scripts=true              │
│  擋掉所有 preinstall/postinstall  │
└───────────────────────────────────┘
        │
        ▼
┌─ 第二層：PreToolUse Hook ─────────┐
│  npm-pkg-check.sh                 │
│  ✓ 安全 → 一行輸出，繼續          │
│  🚫 可疑 → exit 2，阻擋安裝       │
└───────────────────────────────────┘
        │
        ▼
┌─ 第三層：Semgrep Supply Chain ────┐
│  掃描 lockfile 中的已知 CVE       │
│  偵測 code-level 惡意行為         │
└───────────────────────────────────┘
```

## 每層防什麼

| 層 | 防禦目標 | 機制 |
|------|----------|------|
| **第一層** | `postinstall` / `preinstall` 惡意腳本 | `.npmrc` 全域封鎖 install scripts |
| **第二層** | Typosquatting、有漏洞的版本、不存在的套件、不明 CLI flag | Hook 查 npm registry + OSV.dev，解析版本，驗證 CLI 語法 |
| **第三層** | 已知 CVE、`import` 時執行的惡意程式碼 | Semgrep `semgrep_scan_supply_chain` MCP 工具 |

## 安裝步驟

### 1. 設定 `.npmrc`（第一層）

複製到你的專案根目錄：

```bash
cp .npmrc /path/to/your/project/.npmrc
```

需要 install scripts 的合法套件，安裝後手動放行：

```bash
npm rebuild esbuild
npm rebuild sharp
npx prisma generate  # Prisma 比較特殊
```

### 2. 安裝 Hook 腳本（第二層）

```bash
mkdir -p ~/.claude/scripts
cp scripts/npm-pkg-check.sh ~/.claude/scripts/
cp scripts/npm-safe-packages.txt ~/.claude/scripts/
chmod +x ~/.claude/scripts/npm-pkg-check.sh
```

把 `settings-snippet.jsonc` 中的 `hooks` 區段加入你的 `~/.claude/settings.json`。

### 3. 啟用 Semgrep Plugin（第三層）

在 `~/.claude/settings.json` 中：

```json
{
  "enabledPlugins": {
    "semgrep@claude-plugins-official": true
  }
}
```

Semgrep supply chain 掃描會在安裝完成、lockfile 更新後自動可用。

## 檔案結構

```text
npm-supply-chain-defense/
├── .npmrc                          # 第一層：ignore-scripts=true
├── scripts/
│   ├── npm-pkg-check.sh           # 第二層：安裝前檢查（Python 嵌入 bash）
│   └── npm-safe-packages.txt      # 白名單
├── tests/
│   └── run-tests.py               # 42 個回歸測試（31 unit + 11 live）
├── settings-snippet.jsonc          # Hook 設定片段
├── README.md                       # 英文版
└── README.zh-TW.md                # 本檔案
```

## Hook 行為說明

### 放行（exit 0）

| 場景 | 輸出 |
|------|------|
| `git status`（非 npm 指令） | 無 |
| `npm install`（bare，從 lockfile） | 無 |
| `npm install esbuild`（白名單） | `✓ esbuild (whitelisted)` |
| `npm install lodash`（知名且安全） | `✓ lodash — 125M/week, 3 maintainers` |
| `npm install express@latest`（dist-tag 解析） | `✓ express@5.2.1 — 91M/week, ...` |

### 阻擋（exit 2）

| 場景 | 輸出 |
|------|------|
| `npm install zzz-fake-pkg`（不存在） | `⚠ not found on npm registry` |
| `npm install lodash@4.17.20`（已知 CVE） | `🚫 BLOCKED (3 known vuln(s): GHSA-...)` |
| `npm install lodash@beta`（版本無法解析） | `🚫 BLOCKED (version not resolved)` |
| `npm install --mystery-flag lodash`（不明 CLI flag） | `🚫 BLOCKED (unrecognized option)` |
| 低下載量 + 有 install scripts | `🚫 BLOCKED (low downloads, has install scripts)` |
| 無效的 `TOOL_INPUT` JSON | `⚠ blocking as precaution` |
| Registry 無法連線（核心信號） | `🚫 BLOCKED (registry unreachable)` |

## 設計原則

### Fail-closed（預設阻擋）

核心信號失敗時阻擋，補充信號失敗時僅警告。

| 信號 | 類型 | 失敗時行為 |
|------|------|-----------|
| Registry 元資料 | 核心 | **阻擋** |
| 版本解析 | 核心 | **阻擋** |
| Install scripts 檢查 | 核心 | **阻擋** |
| OSV 漏洞查詢 | 補充 | 僅警告 |
| 下載量 | 補充 | 僅警告 |

### Per-PM option 解析

Hook 根據各 package manager（npm、yarn、pnpm、bun）的 arity table 驗證 CLI flag。不明 flag 會被阻擋以防止 parser 繞過。

會吃值的 flag（如 `--registry`、`--tag`、`--cwd`）會正確消耗下一個 token。Boolean flag（如 `--fund`、`--save-dev`）不會。`--flag=value` 語法會驗證 base flag 是否已知。

### 版本解析

| 版本指定 | 解析方式 |
|----------|----------|
| `4.17.21`（exact semver） | 直接使用 |
| `latest`、`beta`（dist-tag） | 從 registry `dist-tags` 查找 |
| `^4.17.0`、`~2.0`（range） | 透過 `npm view`（3 秒 timeout）解析 |
| 無法解析 | **阻擋** |

### 環境變數

| 變數 | 預設值 | 用途 |
|------|--------|------|
| `NPM_PKG_CHECK_SAFE_LIST` | `~/.claude/scripts/npm-safe-packages.txt` | 覆蓋白名單路徑 |

## 執行測試

```bash
# 只跑 unit 測試（不需網路，完全可重現）
python3 tests/run-tests.py

# unit + live 整合測試（需要網路）
python3 tests/run-tests.py --live
```

Unit 測試使用白名單套件隔離解析邏輯與網路。測試 harness 透過 `NPM_PKG_CHECK_SAFE_LIST` 環境變數指向 repo 內的白名單檔案，結果不受使用者家目錄影響。

```text
Result: 31 passed, 0 failed, 11 skipped / 42 total
All 31 executed tests passed. Run with --live for full suite.
```

## 限制

這三層無法防禦的攻擊：

- **RDD（Remote Dynamic Dependency）攻擊** — 惡意 payload 在執行時才從外部拉取，靜態分析掃不到
- **合法套件被劫持後的即時攻擊** — CVE 尚未發布的零日窗口
- **混淆過的惡意程式碼** — Semgrep 規則可能無法辨識高度混淆的 payload
- **未收錄的 PM flag** — 如果 package manager 新增 flag，在加入 arity table 前會被阻擋

這些需要執行期防禦（Docker network 限制、Node.js `--experimental-permission`）來補足，屬於 DevOps/infra 層面的責任。
