# CLAUDE.md

Documentation-only repo — deliverables are Markdown files. No build, no tests, no dependencies.

## Content Conventions

- Guides and user-facing text: **Traditional Chinese (zh-TW)**
- Subagent definitions, SKILL.md files, MCP configs: **English**
- Three main guides (`claude-md-best-practices.md`, `skills-best-practices.md`, `subagent-best-practices.md`) cross-reference each other — keep links in sync when editing
- `examples/` are read-only references; `.claude/skills/` and `.claude/agents/` are the active copies

## Local-Only Files

`.claude/` and `.mcp.json` are gitignored — they are local working copies and do not need to be pushed to remote. Only `examples/` contains the versioned reference copies that get committed.

## MCP Servers

Configured in `.mcp.json` (local only):
- **codex** — OpenAI Codex for second-opinion security analysis
- **eslint** — ESLint MCP server

## Active Subagent

`security-reviewer` — dual-verification security audit (Semgrep + Codex). Writes reports to `.agents-output/security/`.
