# Eval Workflow

When a skill needs more than basic smoke testing, use this structured approach to validate and improve it.

## When to Use Formal Evals

Not every skill needs formal evaluation. Use this workflow when:
- The skill produces objectively verifiable outputs (file transforms, data extraction, code generation)
- You're iterating on a skill and need to measure whether changes improve it
- You want to compare "with skill" vs "without skill" performance
- The description needs trigger optimization

Skip formal evals for subjective skills (writing style, creative output) — human judgment is more reliable than assertions for those.

## Structured Test Cases

Define test cases as realistic prompts — the kind of thing a real user would type:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt — realistic, not abstract",
      "expected_output": "Description of expected result",
      "files": [],
      "assertions": [
        "The output file contains a summary section",
        "All input data points are accounted for"
      ]
    }
  ]
}
```

**Good test prompts** are concrete and specific — include file paths, personal context, column names, company names. Some should be casual or contain typos. A mix of lengths. Focus on edge cases rather than clear-cut happy paths.

**Bad test prompts**: `"Format this data"`, `"Create a chart"` — too abstract, too easy.

## Baseline Comparison

Run each test prompt twice:
1. **With skill** — Claude has access to the skill
2. **Without skill** (baseline) — same prompt, no skill

This tells you whether the skill actually adds value. If outputs are indistinguishable, the skill isn't pulling its weight.

When improving an existing skill, your baseline can be either:
- No skill at all (for new skills)
- The previous version of the skill (for iterations)

## Writing Good Assertions

Assertions should be objectively verifiable and discriminating:
- A **discriminating** assertion passes when the skill genuinely succeeds and fails when it doesn't
- A **non-discriminating** assertion passes regardless (e.g., "output file exists" — true even for empty files)

```
# Weak — would pass even for garbage output
"A PDF file was created"

# Strong — tests actual task completion
"The PDF contains all 5 form fields populated with data from the input"
```

Don't force assertions onto subjective qualities. If the output's value is "does it look good?", that's for human review, not assertions.

## Iteration Loop

After each round of testing:

1. **Read the results** — both outputs and execution traces
2. **Identify patterns** — what went wrong? What went right?
3. **Generalize** — don't patch for specific test cases. Ask: "What instruction change would help across *all* similar prompts?"
4. **Revise the skill** — improve instructions, add/modify scripts, update gotchas
5. **Rerun** — test the revised skill against the same prompts plus any new ones
6. **Repeat** until results stabilize or the user is satisfied

**Avoid overfitting**: If a change only helps one test case while hurting others, it's probably too specific. The skill will be used on prompts you haven't seen yet — optimize for the general case.

## Description Trigger Optimization

The description determines whether Claude invokes the skill. To optimize it systematically:

### Create Trigger Eval Queries

Write 16-20 test queries — a mix of should-trigger and should-not-trigger:

```json
[
  {"query": "realistic user prompt that should trigger the skill", "should_trigger": true},
  {"query": "similar-sounding prompt that should NOT trigger", "should_trigger": false}
]
```

**Should-trigger queries** (8-10): Different phrasings of the same intent. Include cases where the user doesn't name the skill but clearly needs it. Cover uncommon use cases.

**Should-not-trigger queries** (8-10): Near-misses are most valuable — queries that share keywords but need something different. Don't include obviously irrelevant queries like "write a fibonacci function" for a PDF skill.

### Test and Iterate

1. Split queries into 60% train / 40% test
2. Evaluate the current description against train queries (run each 3x for reliability)
3. Revise the description based on failures
4. Re-evaluate on both train and test sets
5. Select the best description by test score (not train score) to avoid overfitting

### How Triggering Works

Skills appear in Claude's `available_skills` list with their name + description. Claude only consults skills for tasks it can't easily handle on its own — simple one-step queries may not trigger even with a perfect description, because Claude handles them directly. Your eval queries should be substantive enough that Claude would benefit from consulting a skill.

## Blind A/B Comparison (Optional)

When you need high-confidence comparison between two skill versions — beyond what side-by-side human review provides — use blind comparison:

1. Run both skill versions on the same prompts
2. Present the two outputs to an independent evaluator *without revealing which is which*
3. Let the evaluator judge on content (correctness, completeness, accuracy) and structure (organization, formatting, usability)
4. After scoring, "unblind" the results and analyze why the winner won

**Lightweight version** (no tooling needed): Manually copy two outputs into a prompt, label them "Output A" and "Output B", and ask Claude to compare. This works for quick checks.

**Automated version**: The `skill-eval-toolkit` provides dedicated subagents (`comparator.md` for blind scoring, `comparison-analyzer.md` for post-hoc analysis) that formalize this process with structured rubrics and JSON output.

## Quantitative Benchmarking

For rigorous comparison, track these metrics across runs:

| Metric | What it tells you |
|--------|------------------|
| **Pass rate** (mean +/- stddev) | How reliably the skill produces correct output |
| **Time** (seconds) | Whether the skill adds unacceptable latency |
| **Tokens** | Cost implications of using the skill |
| **Tool calls** | Execution complexity — more calls may mean more failure points |

Look for:
- Assertions that always pass in both configs — they don't discriminate, consider replacing
- Assertions that always fail in both configs — may be broken or beyond capability
- High variance — indicates flaky behavior worth investigating
- Time/token tradeoffs — a skill that doubles execution time for a 5% pass rate improvement may not be worth it

## Scaling Up with skill-eval-toolkit

When manual eval cycles become insufficient — too many test cases, need for statistical rigor, or description optimization — consider the **skill-eval-toolkit** (`examples/skill-eval-toolkit/`). It provides:

- **Parallel test execution** with automated grading, aggregation, and an interactive HTML viewer
- **Benchmark statistics** (mean +/- stddev) with per-assertion variance analysis
- **Description optimization loop** that automatically iterates on trigger accuracy with train/test split
- **Body autopilot loop** that keeps or reverts small `SKILL.md` body mutations based on benchmark deltas
- **Blind A/B comparison** with dedicated subagents for unbiased scoring

The toolkit assumes you already know how to write skills (content types, frontmatter, progressive disclosure). Use this guide to design the skill, then the toolkit to validate and optimize it.
