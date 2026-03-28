#!/usr/bin/env python3
"""Advance an eval-driven SKILL.md body autopilot iteration."""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from scripts.improve_skill_body import improve_skill_body
from scripts.utils import ensure_proper_descendant, group_runs_by_eval, parse_skill_md, safe_rmtree


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_copytree(src: Path, dst: Path, fence: Path) -> None:
    """Copy *src* to *dst*, removing *dst* first only if it is under *fence*."""
    ensure_proper_descendant(dst, fence)
    dst.parent.mkdir(parents=True, exist_ok=True)
    safe_rmtree(dst, fence)
    shutil.copytree(src, dst)


def load_json(path: Path | None) -> dict | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text())


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def infer_iteration_number(benchmark_path: Path) -> int:
    for parent in [benchmark_path.parent, *benchmark_path.parents]:
        name = parent.name
        if name.startswith("iteration-"):
            suffix = name.split("iteration-", 1)[1]
            if suffix.isdigit():
                return int(suffix)
    return 1


def decide_candidate(
    benchmark: dict,
    candidate_config: str,
    baseline_config: str,
    min_pass_rate_gain: float,
    max_per_eval_regression: float,
    tie_epsilon: float,
) -> dict:
    run_summary = benchmark.get("run_summary", {})
    candidate = run_summary.get(candidate_config, {})
    baseline = run_summary.get(baseline_config, {})

    candidate_pass = float(candidate.get("pass_rate", {}).get("mean", 0.0))
    baseline_pass = float(baseline.get("pass_rate", {}).get("mean", 0.0))
    candidate_time = float(candidate.get("time_seconds", {}).get("mean", 0.0))
    baseline_time = float(baseline.get("time_seconds", {}).get("mean", 0.0))
    candidate_tokens = float(candidate.get("tokens", {}).get("mean", 0.0))
    baseline_tokens = float(baseline.get("tokens", {}).get("mean", 0.0))

    pass_rate_delta = round(candidate_pass - baseline_pass, 4)
    time_delta = round(candidate_time - baseline_time, 4)
    tokens_delta = round(candidate_tokens - baseline_tokens, 4)

    candidate_by_eval = group_runs_by_eval(benchmark, candidate_config)
    baseline_by_eval = group_runs_by_eval(benchmark, baseline_config)
    regressions = []
    for eval_id, candidate_eval in candidate_by_eval.items():
        baseline_eval = baseline_by_eval.get(eval_id)
        if not baseline_eval:
            continue
        delta = round(candidate_eval["mean_pass_rate"] - baseline_eval["mean_pass_rate"], 4)
        if delta < (-1 * max_per_eval_regression):
            regressions.append(
                {
                    "eval_id": candidate_eval["eval_id"],
                    "eval_name": candidate_eval["eval_name"],
                    "pass_rate_delta": delta,
                }
            )

    decision = "revert"
    decision_notes = []
    if regressions:
        decision_notes.append(
            f"Reverted because {len(regressions)} eval(s) regressed by more than {max_per_eval_regression:.2f}."
        )
    elif pass_rate_delta >= min_pass_rate_gain:
        decision = "keep"
        decision_notes.append(
            f"Kept because mean pass rate improved by {pass_rate_delta:+.2f}, meeting the +{min_pass_rate_gain:.2f} bar."
        )
    elif abs(pass_rate_delta) <= tie_epsilon and (time_delta < 0 or tokens_delta < 0):
        decision = "keep"
        decision_notes.append(
            "Kept because quality was effectively tied and the candidate reduced runtime or token usage."
        )
    else:
        decision_notes.append(
            f"Reverted because mean pass rate delta {pass_rate_delta:+.2f} did not clear the keep threshold."
        )

    metrics = {
        "candidate_pass_rate_mean": candidate_pass,
        "baseline_pass_rate_mean": baseline_pass,
        "pass_rate_delta": pass_rate_delta,
        "candidate_time_mean": candidate_time,
        "baseline_time_mean": baseline_time,
        "time_seconds_delta": time_delta,
        "candidate_tokens_mean": candidate_tokens,
        "baseline_tokens_mean": baseline_tokens,
        "tokens_delta": tokens_delta,
        "regressions": regressions,
    }

    return {
        "decision": decision,
        "decision_notes": decision_notes,
        "metrics": metrics,
    }


def load_state(path: Path, skill_name: str, original_skill_path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {
        "schema_version": 1,
        "skill_name": skill_name,
        "started_at": utc_now(),
        "original_skill_path": str(original_skill_path),
        "current_best_path": str(original_skill_path),
        "target_hit_streak": 0,
        "iterations": [],
    }


def render_decision_markdown(entry: dict, next_candidate_dir: Path | None) -> str:
    regressions = entry.get("metrics", {}).get("regressions", [])
    lines = [
        f"# Iteration {entry['iteration']} decision",
        "",
        f"- Decision: `{entry['decision']}`",
        f"- Candidate config: `{entry['candidate_config']}`",
        f"- Baseline config: `{entry['baseline_config']}`",
        f"- Candidate pass rate: `{entry['metrics']['candidate_pass_rate_mean']:.2f}`",
        f"- Baseline pass rate: `{entry['metrics']['baseline_pass_rate_mean']:.2f}`",
        f"- Pass rate delta: `{entry['metrics']['pass_rate_delta']:+.2f}`",
        f"- Time delta (s): `{entry['metrics']['time_seconds_delta']:+.2f}`",
        f"- Tokens delta: `{entry['metrics']['tokens_delta']:+.0f}`",
        "",
        "## Notes",
    ]
    for note in entry.get("decision_notes", []):
        lines.append(f"- {note}")
    if regressions:
        lines.extend(["", "## Regressions"])
        for regression in regressions:
            lines.append(
                f"- Eval {regression['eval_id']} ({regression['eval_name']}): {regression['pass_rate_delta']:+.2f}"
            )
    if entry.get("change_summary"):
        summary = entry["change_summary"]
        lines.extend(["", "## Candidate hypothesis", f"- {summary.get('hypothesis', 'n/a')}"])
        for edit in summary.get("edits", []):
            lines.append(f"- {edit}")
    if next_candidate_dir:
        lines.extend(["", "## Next candidate", f"- {next_candidate_dir}"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Advance the skill body autopilot loop")
    parser.add_argument("--workspace", required=True, help="Skill workspace root containing iteration-N directories")
    parser.add_argument("--best-skill-path", required=True, help="Currently accepted best skill directory")
    parser.add_argument("--candidate-skill-path", required=True, help="Evaluated candidate skill directory")
    parser.add_argument("--benchmark", required=True, help="Path to iteration benchmark.json")
    parser.add_argument("--model", required=True, help="Model for generating the next candidate")
    parser.add_argument("--feedback", default=None, help="Optional feedback.json path")
    parser.add_argument("--candidate-config", default="with_skill", help="Benchmark config for the evaluated candidate")
    parser.add_argument("--baseline-config", default="old_skill", help="Benchmark config for the baseline")
    parser.add_argument("--iteration", type=int, default=None, help="Override iteration number")
    parser.add_argument("--min-pass-rate-gain", type=float, default=0.01, help="Minimum mean pass-rate gain to keep")
    parser.add_argument(
        "--max-per-eval-regression",
        type=float,
        default=0.05,
        help="Maximum allowed mean pass-rate regression on any single eval",
    )
    parser.add_argument("--tie-epsilon", type=float, default=0.005, help="Treat pass-rate deltas within this as a tie")
    parser.add_argument("--target-pass-rate", type=float, default=0.95, help="Stop when winner meets this pass rate enough times")
    parser.add_argument("--target-hit-streak", type=int, default=3, help="Required consecutive target hits before stopping")
    parser.add_argument("--max-iterations", type=int, default=20, help="Hard cap on total autopilot iterations (safety fuse)")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    benchmark_path = Path(args.benchmark)
    best_skill_path = Path(args.best_skill_path)
    candidate_skill_path = Path(args.candidate_skill_path)
    feedback_path = Path(args.feedback) if args.feedback else None

    iteration = args.iteration or infer_iteration_number(benchmark_path)
    benchmark = json.loads(benchmark_path.read_text())
    feedback = load_json(feedback_path)

    skill_name, _, _ = parse_skill_md(best_skill_path)

    autopilot_root = workspace / "autopilot"
    state_path = autopilot_root / "state.json"
    logs_dir = autopilot_root / "logs"
    accepted_root = autopilot_root / "accepted"
    decision_root = autopilot_root / "decisions"
    state = load_state(state_path, skill_name, best_skill_path)

    if not (autopilot_root / "original_skill").exists():
        safe_copytree(best_skill_path, autopilot_root / "original_skill", fence=workspace)

    decision = decide_candidate(
        benchmark=benchmark,
        candidate_config=args.candidate_config,
        baseline_config=args.baseline_config,
        min_pass_rate_gain=args.min_pass_rate_gain,
        max_per_eval_regression=args.max_per_eval_regression,
        tie_epsilon=args.tie_epsilon,
    )

    candidate_change = load_json(candidate_skill_path / "autopilot_change.json") or {}
    chosen_skill_path = candidate_skill_path if decision["decision"] == "keep" else best_skill_path
    chosen_pass_rate = (
        decision["metrics"]["candidate_pass_rate_mean"]
        if decision["decision"] == "keep"
        else decision["metrics"]["baseline_pass_rate_mean"]
    )

    if chosen_pass_rate >= args.target_pass_rate:
        state["target_hit_streak"] = int(state.get("target_hit_streak", 0)) + 1
    else:
        state["target_hit_streak"] = 0

    chosen_snapshot = accepted_root / f"iteration-{iteration}"
    safe_copytree(chosen_skill_path, chosen_snapshot, fence=workspace)
    safe_copytree(chosen_skill_path, autopilot_root / "current_best", fence=workspace)
    state["current_best_path"] = str(chosen_snapshot)

    entry = {
        "iteration": iteration,
        "timestamp": utc_now(),
        "benchmark_path": str(benchmark_path),
        "feedback_path": str(feedback_path) if feedback_path else None,
        "best_skill_path_before": str(best_skill_path),
        "candidate_skill_path": str(candidate_skill_path),
        "chosen_skill_path": str(chosen_snapshot),
        "candidate_config": args.candidate_config,
        "baseline_config": args.baseline_config,
        "decision": decision["decision"],
        "decision_notes": decision["decision_notes"],
        "metrics": decision["metrics"],
        "change_summary": candidate_change.get("change_summary", {}),
    }

    next_candidate_dir = None
    stop_reason = None
    if state["target_hit_streak"] >= args.target_hit_streak:
        stop_reason = (
            f"winner met target pass rate {args.target_pass_rate:.2f} "
            f"for {state['target_hit_streak']} consecutive iterations"
        )
    elif iteration >= args.max_iterations:
        stop_reason = (
            f"reached max iterations cap ({args.max_iterations})"
        )
    else:
        next_candidate_dir = workspace / f"iteration-{iteration + 1}" / "candidate_skill"
        improve_skill_body(
            skill_path=chosen_snapshot,
            benchmark=benchmark,
            candidate_config=args.candidate_config,
            baseline_config=args.baseline_config,
            model=args.model,
            output_dir=next_candidate_dir,
            output_fence=workspace,
            feedback=feedback,
            history=state.get("iterations", []),
            log_dir=logs_dir,
            iteration=iteration + 1,
        )

    if stop_reason:
        entry["decision_notes"].append(f"Stopping autopilot: {stop_reason}.")
    if next_candidate_dir:
        entry["next_candidate_path"] = str(next_candidate_dir)

    state.setdefault("iterations", []).append(entry)
    state["last_updated_at"] = utc_now()
    save_json(state_path, state)

    decision_json_path = decision_root / f"iteration-{iteration}.json"
    decision_md_path = decision_root / f"iteration-{iteration}.md"
    save_json(decision_json_path, entry)
    decision_md_path.parent.mkdir(parents=True, exist_ok=True)
    decision_md_path.write_text(render_decision_markdown(entry, next_candidate_dir))

    result = {
        "decision": entry["decision"],
        "decision_path": str(decision_json_path),
        "state_path": str(state_path),
        "chosen_skill_path": str(chosen_snapshot),
        "next_candidate_path": str(next_candidate_dir) if next_candidate_dir else None,
        "target_hit_streak": state["target_hit_streak"],
        "stop_reason": stop_reason,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
