"""Shared utilities for skill-eval-toolkit scripts."""

import os
import shutil
import subprocess
from pathlib import Path
import re


def call_claude(prompt: str, model: str | None, timeout: int = 300) -> str:
    """Run ``claude -p`` and return the response body.

    Prompt goes over stdin (not argv) because it can embed full SKILL.md
    content and easily exceed comfortable argv length.  The CLAUDECODE env
    var is stripped so that ``claude -p`` can be nested inside a running
    Claude Code session without triggering the interactive-terminal guard.
    """
    cmd = ["claude", "-p", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude -p exited {result.returncode}\nstderr: {result.stderr}"
        )
    return result.stdout


def ensure_proper_descendant(target: Path, must_be_under: Path) -> Path:
    """Return the resolved target path if it is a proper descendant of the fence."""
    resolved = target.resolve()
    fence = must_be_under.resolve()
    try:
        resolved.relative_to(fence)
    except ValueError as exc:
        raise ValueError(
            f"Refusing to operate on '{resolved}': not inside '{fence}'"
        ) from exc
    if resolved == fence:
        raise ValueError(
            f"Refusing to operate on '{resolved}': target must be a proper descendant of '{fence}'"
        )
    return resolved


def safe_rmtree(target: Path, must_be_under: Path) -> None:
    """Remove a directory tree only if it lives under the expected root.

    Raises ValueError if *target* is not a proper descendant of
    *must_be_under*, preventing accidental deletion of unrelated paths
    when CLI arguments are mis-typed.
    """
    resolved = ensure_proper_descendant(target, must_be_under)
    if resolved.exists():
        shutil.rmtree(resolved)


def split_skill_md_content(content: str) -> tuple[str, str]:
    """Split SKILL.md content into (frontmatter_with_fences, body)."""
    lines = content.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    frontmatter = "\n".join(lines[: end_idx + 1]).rstrip() + "\n"
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    return frontmatter, body


def extract_frontmatter_value(frontmatter: str, key: str) -> str:
    """Extract a simple or block-scalar YAML value from SKILL.md frontmatter."""
    lines = frontmatter.splitlines()
    if lines and lines[0].strip() == "---":
        lines = lines[1:]
    if lines and lines[-1].strip() == "---":
        lines = lines[:-1]

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(f"{key}:"):
            value = line[len(key) + 1 :].strip()
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                    continuation_lines.append(lines[i].strip())
                    i += 1
                return " ".join(continuation_lines)
            return value.strip('"').strip("'")
        i += 1
    return ""


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    frontmatter, _ = split_skill_md_content(content)
    name = extract_frontmatter_value(frontmatter, "name")
    description = extract_frontmatter_value(frontmatter, "description")
    return name, description, content


def render_skill_md(frontmatter: str, body: str) -> str:
    """Render full SKILL.md content from frontmatter and body."""
    body = body.strip("\n")
    if body:
        return frontmatter.rstrip() + "\n\n" + body + "\n"
    return frontmatter.rstrip() + "\n"


def replace_skill_body(content: str, new_body: str) -> str:
    """Replace only the markdown body, preserving frontmatter exactly."""
    frontmatter, _ = split_skill_md_content(content)
    return render_skill_md(frontmatter, new_body)


def group_runs_by_eval(benchmark: dict, config: str, *, include_details: bool = False) -> dict[str, dict]:
    """Group benchmark runs by eval_id for a given configuration.

    Returns ``{eval_id: {eval_id, eval_name, mean_pass_rate, ...}}``.

    When *include_details* is True the entries also contain
    ``mean_passed``, ``mean_failed``, ``notes``, and
    ``failing_expectations`` — useful for building mutation prompts.
    """
    grouped: dict[str, dict] = {}
    for run in benchmark.get("runs", []):
        if run.get("configuration") != config:
            continue
        key = str(run.get("eval_id"))
        entry = grouped.setdefault(
            key,
            {
                "eval_id": run.get("eval_id"),
                "eval_name": run.get("eval_name") or f"eval-{run.get('eval_id')}",
                "_pass_rates": [],
                "_passed": [],
                "_failed": [],
                "_notes": set(),
                "_expectations": [],
            },
        )
        result = run.get("result", {})
        entry["_pass_rates"].append(float(result.get("pass_rate", 0.0)))
        entry["_passed"].append(int(result.get("passed", 0)))
        entry["_failed"].append(int(result.get("failed", 0)))
        entry["_notes"].update(run.get("notes") or [])
        if include_details:
            for expectation in run.get("expectations") or []:
                if not expectation.get("passed"):
                    entry["_expectations"].append(expectation)

    output: dict[str, dict] = {}
    for key, entry in grouped.items():
        pass_rates = entry.pop("_pass_rates")
        passed = entry.pop("_passed")
        failed = entry.pop("_failed")
        notes = entry.pop("_notes")
        expectations = entry.pop("_expectations")
        entry["mean_pass_rate"] = round(sum(pass_rates) / len(pass_rates), 4) if pass_rates else 0.0
        if include_details:
            entry["mean_passed"] = round(sum(passed) / len(passed), 2) if passed else 0.0
            entry["mean_failed"] = round(sum(failed) / len(failed), 2) if failed else 0.0
            entry["notes"] = sorted(notes)
            entry["failing_expectations"] = expectations
        output[key] = entry
    return output


def extract_tagged_block(text: str, tag: str) -> str | None:
    """Extract content inside XML-like tags.

    Prefer tags that appear on their own lines, which avoids truncating body
    content if a literal closing-tag string appears inline inside the block.
    Fall back to a generic same-line matcher for shorter responses.
    """
    block_pattern = rf"(?ms)^[ \t]*<{tag}>[ \t]*\n(.*?)\n[ \t]*</{tag}>[ \t]*$"
    match = re.search(block_pattern, text)
    if not match:
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()
