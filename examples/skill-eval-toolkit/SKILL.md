---
name: skill-eval-toolkit
description: Evaluate, benchmark, compare, and optimize descriptions for existing skills. Use when users want to run evals to test a skill, benchmark skill performance with variance analysis, do blind A/B comparisons between skill versions, or optimize a skill's description for better triggering accuracy. Do NOT use for creating skills from scratch — see write-a-skill for that.
---

# Skill Eval Toolkit

An eval-driven workflow for testing, benchmarking, and optimizing existing skills. For how to *write* a skill from scratch, see the **write-a-skill** skill first — this toolkit picks up where that guide leaves off.

## When to Use This Toolkit

- You have a drafted skill and want to verify it actually works
- You're iterating on a skill and need to measure whether changes improve it
- You want to compare "with skill" vs "without skill" (or old vs new) performance
- The description needs trigger optimization
- You want rigorous blind A/B comparison between two skill versions

## Overview

The eval loop:

1. Create test prompts and run them (with-skill AND baseline, in parallel)
2. While runs execute, draft quantitative assertions
3. Grade outputs, aggregate into benchmarks, launch interactive viewer
4. User reviews outputs and leaves feedback
5. Improve skill based on feedback, repeat

Your job is to figure out where the user is in this process and help them progress.

## Communicating with the user

Pay attention to context cues to calibrate your language. "Evaluation" and "benchmark" are borderline but OK. For "JSON" and "assertion", check for cues that the user knows what those mean before using them unexplained. Briefly explain terms if in doubt.

---

## Test Cases

Come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user for confirmation, then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions while runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `reference/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Within the workspace, organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.). Create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. Launch everything at once so it all finishes around the same time.

**With-skill run:**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about>
```

**Baseline run** (same prompt, but the baseline depends on context):
- **New skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait — draft quantitative assertions for each test case and explain them to the user. Good assertions are objectively verifiable and have descriptive names that read clearly in the benchmark viewer.

Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with assertions once drafted.

### Step 3: As runs complete, capture timing data

When each subagent completes, you receive a notification containing `total_tokens` and `duration_ms`. Save immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — process each notification as it arrives.

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader subagent that reads `agents/grader.md` and evaluates each assertion against the outputs. Save results to `grading.json` in each run directory. The `expectations` array must use fields `text`, `passed`, and `evidence` — the viewer depends on these exact field names. For programmatically checkable assertions, write and run a script.

2. **Aggregate into benchmark** — run from the skill-eval-toolkit directory:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean +/- stddev and the delta. See `reference/schemas.md` for the exact schema.

3. **Analyst pass** — spawn a benchmark-analyzer subagent that reads `agents/benchmark-analyzer.md` and surfaces patterns: non-discriminating assertions, high-variance evals, time/token tradeoffs. The benchmark-analyzer analyzes benchmark.json only — do not pass skill contents or transcripts.

4. **Launch the viewer**:
   ```bash
   nohup python <skill-eval-toolkit-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, pass `--previous-workspace <workspace>/iteration-<N-1>`.

   Use `generate_review.py` to create the viewer — don't write custom HTML.

5. **Tell the user** the results are in their browser with two tabs: "Outputs" for qualitative review and "Benchmark" for quantitative comparison.

### What the user sees in the viewer

The "Outputs" tab shows one test case at a time:
- **Prompt**: the task given
- **Output**: files produced, rendered inline
- **Previous Output** (iteration 2+): collapsed, showing last iteration
- **Formal Grades**: collapsed assertion pass/fail
- **Feedback**: auto-saving textbox
- **Previous Feedback** (iteration 2+): comments from last time

The "Benchmark" tab shows stats: pass rates, timing, token usage per configuration, with per-eval breakdowns and analyst observations.

Navigation via prev/next buttons or arrow keys. "Submit All Reviews" saves to `feedback.json`.

### Step 5: Read the feedback

Read `feedback.json`. Empty feedback means the user thought it was fine. Focus improvements on test cases with specific complaints.

Kill the viewer server when done: `kill $VIEWER_PID 2>/dev/null`

---

## Improving the skill

### How to think about improvements

1. **Generalize from the feedback.** Skills will be used across many different prompts. Don't overfit to the few test examples — fiddly, overly constrictive changes help one case and hurt generalization.

2. **Keep the prompt lean.** Remove what isn't pulling its weight. Read transcripts, not just final outputs — if the skill makes the model waste time on unproductive steps, trim those parts.

3. **Explain the why.** Explain *why* behind everything you ask the model to do. If you find yourself writing ALWAYS or NEVER in caps, reframe and explain the reasoning instead.

4. **Look for repeated work across test cases.** If all test cases result in the subagent writing similar helper scripts, bundle that script in `scripts/` and tell the skill to use it.

### The iteration loop

1. Apply improvements to the skill
2. Rerun all test cases into `iteration-<N+1>/`, including baseline runs
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review
5. Read new feedback, improve again, repeat

Keep going until the user is happy, feedback is all empty, or you're not making meaningful progress.

---

## Autopilot Body Optimization

Use this mode when the skill is measurable enough that you want the agent to keep mutating the `SKILL.md` body on its own between eval rounds. This extends the normal eval loop — it does **not** replace your existing evals, grader, benchmark, or viewer.

Best fit:
- The skill has 3-6 discriminating assertions and stable test prompts
- Failures cluster into repeatable instruction problems
- You want small keep/revert prompt mutations, not a full rewrite

Avoid autopilot when:
- The skill is mostly subjective and depends on human taste
- Your evals are weak, flaky, or easy to game
- You still haven't established a baseline manually

### The loop

1. Run the normal iteration and produce `benchmark.json` (compare the candidate under `with_skill` against `old_skill` or `without_skill`)
2. Collect `feedback.json` if the user reviewed outputs
3. Advance the autopilot loop:

All `python -m scripts.*` commands assume the working directory is the skill-eval-toolkit root (i.e. the directory containing the `scripts/` package).

```bash
python -m scripts.body_autopilot \
  --workspace <skill-workspace> \
  --best-skill-path <accepted-best-skill-dir> \
  --candidate-skill-path <evaluated-candidate-skill-dir> \
  --benchmark <skill-workspace>/iteration-N/benchmark.json \
  --feedback <skill-workspace>/iteration-N/feedback.json \
  --candidate-config with_skill \
  --baseline-config old_skill \
  --model <model-id>
```

What it does:
- Reads benchmark deltas and per-eval regressions
- Decides `keep` or `revert`
- Snapshots the accepted skill under `autopilot/accepted/iteration-N/`
- Writes `autopilot/state.json` and `autopilot/decisions/iteration-N.{json,md}`
- Generates the next candidate skill under `iteration-(N+1)/candidate_skill/`

### Keep / revert policy

The script defaults to a conservative policy:
- Keep only when mean pass rate clearly improves, or quality is tied and efficiency improves
- Revert if any eval regresses past the configured threshold
- Stop automatically once the accepted winner hits the target pass rate enough times in a row
- Hard-stop at `--max-iterations` (default 20) as a safety fuse, even if target is not yet met

Tune with flags if needed:
- `--min-pass-rate-gain`
- `--max-per-eval-regression`
- `--target-pass-rate`
- `--target-hit-streak`
- `--max-iterations`

### Mutation guardrails

The body optimizer intentionally stays narrow:
- Preserves frontmatter exactly — no description churn here
- Mutates the markdown body only
- Makes one small coherent change per round
- Logs the hypothesis and edits to `autopilot_change.json`

If you also need to optimize triggering, run the description loop separately. Don't mix body changes and description changes in the same benchmark round or you won't know which one helped.

---

## Advanced: Blind comparison

For rigorous comparison between two skill versions, use the blind comparison system. Read `agents/comparator.md` and `agents/comparison-analyzer.md` for details. The basic idea: give two outputs to an independent agent without revealing which is which, let it judge quality, then analyze why the winner won. Always pass an explicit `output_path` to both comparator and comparison-analyzer — do not rely on implicit defaults.

This is optional and requires subagents. The human review loop is usually sufficient.

---

## Description Optimization

The description field is the primary mechanism determining whether Claude invokes a skill. After creating or improving a skill, offer to optimize it.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Queries must be realistic — include file paths, personal context, column names, company names, backstory. Mix lengths, focus on edge cases. Some should be lowercase, contain abbreviations, typos, or casual speech.

**Should-trigger** (8-10): Different phrasings of the same intent. Include cases where the user doesn't name the skill but clearly needs it. Cover uncommon use cases.

**Should-not-trigger** (8-10): Near-misses — queries sharing keywords but needing something different. Don't include obviously irrelevant queries.

### Step 2: Review with user

Present the eval set using the HTML template:

1. Read `assets/eval_review.html`
2. Replace placeholders: `__EVAL_DATA_PLACEHOLDER__`, `__SKILL_NAME_PLACEHOLDER__`, `__SKILL_DESCRIPTION_PLACEHOLDER__`
3. Write to temp file and open it
4. User edits queries, toggles should-trigger, exports eval set
5. Check `~/Downloads/` for the exported `eval_set.json`

### Step 3: Run the optimization loop

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

This splits the eval set 60% train / 40% test, evaluates the current description (3 runs per query), proposes improvements via Claude, re-evaluates, and iterates up to 5 times. Selects best by test score to avoid overfitting. Opens an HTML report showing per-iteration results.

### How skill triggering works

Skills appear in Claude's `available_skills` list with name + description. Claude only consults skills for tasks it can't easily handle on its own — simple one-step queries may not trigger even with a perfect description. Eval queries should be substantive enough that Claude would benefit from consulting a skill.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report scores.

---

### Package and Present (only if `present_files` tool is available)

If you have the `present_files` tool:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

Direct the user to the resulting `.skill` file path.

---

## Environment-specific instructions

See `reference/environments.md` for adaptations when running in Claude.ai or Cowork.

---

## Reference files

The `agents/` directory contains instructions for specialized subagents:

- `agents/grader.md` — Evaluate assertions against outputs
- `agents/comparator.md` — Blind A/B comparison between two outputs
- `agents/comparison-analyzer.md` — Post-hoc analysis of why one version beat another
- `agents/benchmark-analyzer.md` — Surface patterns and anomalies in benchmark data

The `reference/` directory has additional documentation:
- `reference/schemas.md` — JSON structures for evals.json, grading.json, etc.
- `reference/environments.md` — Claude.ai and Cowork adaptations
