---
name: commit-style
description: >
  Project-specific commit message format (verb-led, sentence case, single line,
  no conventional-commits prefix). Use when drafting a commit message, staging
  changes for commit, amending, squashing, or when user asks to commit, or runs
  git commit.
---

# Commit Message Style

## Format

`<Verb> <what changed>`

- **Sentence case**: capitalize the first letter only
- **Verb-led**: start with an imperative verb (see the verb table below)
- **Single line**: no body or footer unless the user explicitly asks for one
- **No type prefix**: do not use conventional-commits `type:` or `type(scope):` format
- **Concise**: aim for under 72 characters

Why: This matches the project's existing git history. Consistent verb-led messages make `git log --oneline` scannable without extra ceremony.

## Parallel items

Use commas to list related changes in one commit:

```
Consolidate rules: add examples, merge TDD/error sections, reduce overlap
```

A colon separates the high-level intent from the details when a commit touches multiple concerns.

## Common verbs and when to use them

| Verb | Use when |
|------|----------|
| Add | Introducing something new |
| Fix | Correcting broken behavior |
| Update | Changing existing content or config |
| Remove | Deleting code, files, or features |
| Refactor | Restructuring without behavior change |
| Rework | Significant redesign of an existing piece |
| Standardize | Making things consistent |
| Harden | Strengthening security or robustness |
| Trim | Removing unnecessary parts |

## Scope

This skill applies only when the user asks for a commit. Claude does not create commits unsolicited (see `workflow.md`). The format here applies to commit subjects — not PR titles, branch names, or tag annotations unless the user asks for consistency.

## Gotchas

- Do not append `🤖 Generated with Claude Code` footers or `Co-Authored-By:` trailers unless the user explicitly requests them — the project's git log is clean and this repo's convention is trailer-free
- When unsure of tone or verb choice, run `git log --oneline -20` and mirror recent style rather than guessing
- The verb table is a starting set, not exhaustive — pick a better-fitting imperative verb when the listed ones don't match the change
