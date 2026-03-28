#!/usr/bin/env python3
"""Generate a small SKILL.md body mutation from benchmark results."""

import argparse
import json
import shutil
from pathlib import Path

from scripts.utils import (
    call_claude,
    ensure_proper_descendant,
    extract_tagged_block,
    group_runs_by_eval,
    parse_skill_md,
    replace_skill_body,
    safe_rmtree,
    split_skill_md_content,
)


def infer_output_fence(benchmark_path: Path) -> Path:
    """Infer the workspace fence from a benchmark path under iteration-N/."""
    for parent in [benchmark_path.parent, *benchmark_path.parents]:
        if parent.name.startswith("iteration-"):
            return parent.parent
    raise ValueError(
        "Could not infer a safe workspace fence from benchmark path. "
        "Pass an explicit fence directory."
    )


def summarize_benchmark(benchmark: dict, candidate_config: str, baseline_config: str) -> dict:
    """Create a compact benchmark summary for the mutation prompt."""
    run_summary = benchmark.get("run_summary", {})
    candidate = run_summary.get(candidate_config, {})
    baseline = run_summary.get(baseline_config, {})

    per_eval_candidate = group_runs_by_eval(benchmark, candidate_config, include_details=True)
    per_eval_baseline = group_runs_by_eval(benchmark, baseline_config, include_details=True)

    eval_deltas = []
    for eval_id, candidate_eval in per_eval_candidate.items():
        baseline_eval = per_eval_baseline.get(eval_id, {})
        eval_deltas.append(
            {
                "eval_id": candidate_eval["eval_id"],
                "eval_name": candidate_eval["eval_name"],
                "candidate_mean_pass_rate": candidate_eval["mean_pass_rate"],
                "baseline_mean_pass_rate": baseline_eval.get("mean_pass_rate", 0.0),
                "pass_rate_delta": round(
                    candidate_eval["mean_pass_rate"] - baseline_eval.get("mean_pass_rate", 0.0), 4
                ),
                "failing_expectations": [
                    {
                        "text": expectation.get("text", ""),
                        "evidence": expectation.get("evidence", ""),
                    }
                    for expectation in candidate_eval.get("failing_expectations", [])[:5]
                ],
                "notes": candidate_eval.get("notes", [])[:5],
            }
        )

    return {
        "candidate_config": candidate_config,
        "baseline_config": baseline_config,
        "candidate_summary": candidate,
        "baseline_summary": baseline,
        "delta": {
            "pass_rate_mean": round(
                candidate.get("pass_rate", {}).get("mean", 0.0) - baseline.get("pass_rate", {}).get("mean", 0.0),
                4,
            ),
            "time_seconds_mean": round(
                candidate.get("time_seconds", {}).get("mean", 0.0)
                - baseline.get("time_seconds", {}).get("mean", 0.0),
                4,
            ),
            "tokens_mean": round(
                candidate.get("tokens", {}).get("mean", 0.0) - baseline.get("tokens", {}).get("mean", 0.0),
                4,
            ),
        },
        "eval_deltas": eval_deltas,
        "benchmark_notes": benchmark.get("notes", [])[:12],
    }


def _normalize_feedback(feedback: dict | None) -> list[dict]:
    if not feedback:
        return []
    reviews = feedback.get("reviews") or []
    normalized = []
    for review in reviews:
        text = (review.get("feedback") or "").strip()
        if not text:
            continue
        normalized.append(
            {
                "run_id": review.get("run_id", ""),
                "feedback": text,
                "timestamp": review.get("timestamp", ""),
            }
        )
    return normalized[:20]


def _history_for_prompt(history: list[dict]) -> list[dict]:
    trimmed = []
    for item in history[-5:]:
        trimmed.append(
            {
                "iteration": item.get("iteration"),
                "decision": item.get("decision"),
                "hypothesis": item.get("change_summary", {}).get("hypothesis"),
                "edits": item.get("change_summary", {}).get("edits", [])[:4],
                "pass_rate_delta": item.get("metrics", {}).get("pass_rate_delta"),
                "notes": item.get("decision_notes", [])[:4],
            }
        )
    return trimmed


def improve_skill_body(
    skill_path: Path,
    benchmark: dict,
    candidate_config: str,
    baseline_config: str,
    model: str,
    output_dir: Path,
    output_fence: Path,
    feedback: dict | None = None,
    history: list[dict] | None = None,
    log_dir: Path | None = None,
    iteration: int | None = None,
) -> dict:
    """Create a new candidate skill directory with an updated SKILL.md body."""
    history = history or []
    name, description, content = parse_skill_md(skill_path)
    _, current_body = split_skill_md_content(content)
    benchmark_summary = summarize_benchmark(benchmark, candidate_config, baseline_config)
    feedback_summary = _normalize_feedback(feedback)

    prompt = f"""You are optimizing the body of a Claude Code skill called "{name}".

This is NOT description-trigger optimization. Preserve the existing frontmatter exactly. Only improve the SKILL.md body.

Your job:
- Study the current skill body
- Study the benchmark and reviewer feedback
- Make one small, coherent body change
- Optimize for generalization, not test-case overfitting

Hard constraints:
- Preserve the current `name` and `description` unchanged
- Do not rewrite the whole skill for style reasons
- Do not add speculative rules unsupported by the failures
- Prefer small edits to instructions, gotchas, examples, completion criteria, or script usage guidance
- If you add a rule, explain the why behind it
- Return only:
  1. `<change_summary_json>` with valid JSON
  2. `<new_body>` with the full replacement markdown body

Current description:
{description}

Current skill body:
<current_body>
{current_body}
</current_body>

Benchmark summary:
<benchmark_summary>
{json.dumps(benchmark_summary, indent=2)}
</benchmark_summary>

Human feedback:
<feedback_summary>
{json.dumps(feedback_summary, indent=2)}
</feedback_summary>

Previous autopilot history:
<history>
{json.dumps(_history_for_prompt(history), indent=2)}
</history>

Respond in this exact shape:
<change_summary_json>
{{
  "hypothesis": "one sentence",
  "change_scope": "small",
  "edits": ["specific edit 1", "specific edit 2"],
  "expected_benefits": ["benefit 1", "benefit 2"],
  "risk": "main risk or tradeoff"
}}
</change_summary_json>
<new_body>
# Skill body markdown here
</new_body>
"""

    response = call_claude(prompt, model)
    summary_block = extract_tagged_block(response, "change_summary_json")
    new_body = extract_tagged_block(response, "new_body")

    if not new_body:
        raise RuntimeError("Model response missing <new_body> block")

    try:
        change_summary = json.loads(summary_block) if summary_block else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid change_summary_json: {exc}") from exc

    ensure_proper_descendant(output_dir, output_fence)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    safe_rmtree(output_dir, must_be_under=output_fence)
    shutil.copytree(skill_path, output_dir)

    new_content = replace_skill_body(content, new_body)
    (output_dir / "SKILL.md").write_text(new_content)

    artifact = {
        "iteration": iteration,
        "skill_name": name,
        "source_skill_path": str(skill_path),
        "output_skill_path": str(output_dir),
        "candidate_config": candidate_config,
        "baseline_config": baseline_config,
        "change_summary": change_summary,
    }

    (output_dir / "autopilot_change.json").write_text(json.dumps(artifact, indent=2) + "\n")

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        transcript = {
            "iteration": iteration,
            "prompt": prompt,
            "response": response,
            "parsed_change_summary": change_summary,
            "parsed_new_body_chars": len(new_body),
            "output_skill_path": str(output_dir),
        }
        (log_dir / f"improve_skill_body_iter_{iteration or 'unknown'}.json").write_text(
            json.dumps(transcript, indent=2) + "\n"
        )

    return artifact


def main():
    parser = argparse.ArgumentParser(description="Improve a SKILL.md body from benchmark artifacts")
    parser.add_argument("--skill-path", required=True, help="Path to source skill directory")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark.json")
    parser.add_argument("--output-dir", required=True, help="Where to write the mutated candidate skill")
    parser.add_argument("--model", required=True, help="Model for improvement")
    parser.add_argument("--candidate-config", default="with_skill", help="Benchmark config for the candidate skill")
    parser.add_argument("--baseline-config", default="old_skill", help="Benchmark config to compare against")
    parser.add_argument("--feedback", default=None, help="Optional feedback.json path")
    parser.add_argument("--history", default=None, help="Optional autopilot state/history JSON path")
    parser.add_argument("--log-dir", default=None, help="Optional directory for prompt/response logs")
    parser.add_argument("--iteration", type=int, default=None, help="Optional iteration number")
    parser.add_argument(
        "--fence-dir",
        default=None,
        help="Safe deletion fence for output-dir. Defaults to inferring the workspace root from benchmark path.",
    )
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    benchmark = json.loads(benchmark_path.read_text())
    feedback = json.loads(Path(args.feedback).read_text()) if args.feedback else None
    history_data = json.loads(Path(args.history).read_text()) if args.history else {}
    history = history_data.get("iterations", []) if isinstance(history_data, dict) else []
    output_fence = Path(args.fence_dir) if args.fence_dir else infer_output_fence(benchmark_path)

    result = improve_skill_body(
        skill_path=Path(args.skill_path),
        benchmark=benchmark,
        candidate_config=args.candidate_config,
        baseline_config=args.baseline_config,
        model=args.model,
        output_dir=Path(args.output_dir),
        output_fence=output_fence,
        feedback=feedback,
        history=history,
        log_dir=Path(args.log_dir) if args.log_dir else None,
        iteration=args.iteration,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
