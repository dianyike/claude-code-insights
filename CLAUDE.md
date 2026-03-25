# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **documentation-only** repository — a Chinese (zh-TW) best practices guide for Claude Code Skills and Subagents. There is no application code, no build system, no tests, and no dependencies. The deliverables are Markdown files.

## Repository Structure

```
├── skills-best-practices.md      # Skills guide: file format, loading, writing, advanced patterns
├── subagent-best-practices.md    # Subagent guide: black-box solutions, persistence, architecture
├── examples/                     # Standalone reference examples (copy to .claude/skills/ to use)
│   ├── security-reviewer/        # Dual-verification security subagent (Semgrep + Codex)
│   ├── grill-me/                 # Design interrogation skill
│   ├── tdd/                      # TDD red-green-refactor skill
│   ├── prd-to-plan/              # PRD to implementation plan skill
│   └── write-a-skill/            # Meta-skill for building new skills
├── .claude/
│   ├── rules/                    # Project rules (coding-style, workflow, testing, security, etc.)
│   ├── agents/security-reviewer.md  # Active subagent definition
│   └── skills/                   # Active skills (mirrors examples/)
```

Key distinction: `examples/` are read-only references; `.claude/skills/` and `.claude/agents/` are the active copies Claude Code loads.

## Content Conventions

- All guides and user-facing text are written in **Traditional Chinese (zh-TW)**
- Subagent definitions, skill SKILL.md files, and MCP configs are written in **English**
- Two main guides cross-reference each other — keep links in sync when editing

## MCP Servers

Configured in `.mcp.json`:
- **codex** — OpenAI Codex for second-opinion security analysis
- **eslint** — ESLint MCP server

## Active Subagent

`security-reviewer` — dual-verification security audit using Semgrep + Codex cross-validation. Writes reports to `.agents-output/security/`. Uses the `security-review-protocol` skill.

## Working With This Repo

Since this is a docs-only repo, common tasks are:
- Editing Markdown guides and keeping cross-references consistent
- Adding/updating examples under `examples/` and syncing to `.claude/skills/`
- Updating `.claude/rules/` project rules

There are no build, lint, or test commands.
