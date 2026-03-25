# Advanced Skill Patterns

## 1. Dynamic Context Injection

Inject live data into skill content before Claude sees it using `` !`command` `` syntax:

```yaml
---
name: pr-summary
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## PR context
- PR diff: !`gh pr diff`
- Changed files: !`gh pr diff --name-only`

Summarize this pull request...
```

Execution order:
1. Each `` !`command` `` runs immediately (before Claude sees anything)
2. Output replaces the placeholder in the skill content
3. Claude receives the fully rendered prompt

## 2. Config-Based State Management

Skills are stateless by default. Use `config.json` to persist user preferences across runs:

```yaml
---
name: deploy
disable-model-invocation: true
allowed-tools: Read, Write, Bash(npm *), Bash(git *)
---

## Setup (first run only)

Check if `${CLAUDE_SKILL_DIR}/config.json` exists.
If not, ask the user for:
- Default deploy target (staging / production)
- Notification channel (Slack webhook URL)
- Whether to run migrations automatically

Save answers to `${CLAUDE_SKILL_DIR}/config.json`.

## Subsequent runs

Read `${CLAUDE_SKILL_DIR}/config.json` and use saved preferences.
```

## 3. Log-Based Incremental Reports

Let skills write logs so the next run only reports what changed:

```yaml
---
name: babysit-prs
allowed-tools: Read, Write, Bash(gh *)
---

1. Read the log at `${CLAUDE_SKILL_DIR}/data/run-log.jsonl`
   (if it exists — first run has no log)
2. Fetch current PR statuses
3. Compare with last log entry — identify CHANGES since last run
4. Report only deltas (new failures, newly passing, new PRs)
5. Append current state to `${CLAUDE_SKILL_DIR}/data/run-log.jsonl`
```

Use JSONL format (one JSON per line) for easy append and parse.

## 4. Session-Scoped Hooks

Register hooks that only last for the current session:

```yaml
---
name: careful
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: Bash
      command: |
        echo "$TOOL_INPUT" | grep -qE '(rm -rf|drop table|force push)' \
          && echo "BLOCKED: dangerous command" && exit 1
        exit 0
---

Extra safety hooks are now active for this session.
To disable, end the session or start a new one.
```

## 5. Extended Thinking

Include the word "ultrathink" in skill content to enable extended thinking for complex reasoning tasks.
