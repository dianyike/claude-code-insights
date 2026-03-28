# Environment-Specific Instructions

## Claude.ai

The core workflow is the same (test -> review -> improve -> repeat), but without subagents some mechanics change:

**Running test cases**: No subagents means no parallel execution. For each test case, read the skill's SKILL.md, then follow its instructions yourself, one at a time. Skip baseline runs.

**Reviewing results**: If no browser is available, present results directly in the conversation. For file outputs (e.g., .docx, .xlsx), save to filesystem and tell the user where to find them. Ask for feedback inline.

**Benchmarking**: Skip quantitative benchmarking — it relies on baseline comparisons which aren't meaningful without subagents. Focus on qualitative feedback.

**Description optimization**: Requires the `claude` CLI tool (`claude -p`), only available in Claude Code. Skip on Claude.ai.

**Body autopilot optimization**: Also requires `claude -p`, plus reliable benchmark artifacts (`benchmark.json`, ideally `feedback.json`). Skip on Claude.ai.

**Blind comparison**: Requires subagents. Skip.

**Packaging**: `package_skill.py` works anywhere with Python and a filesystem. The user can download the resulting `.skill` file.

**Updating an existing skill**:
- Preserve the original name — use the directory name and `name` frontmatter field unchanged.
- Copy to a writeable location before editing (`/tmp/skill-name/`), as the installed skill path may be read-only.
- If packaging manually, stage in `/tmp/` first, then copy to the output directory.

## Cowork

- Subagents work, so the main workflow (parallel test cases, baselines, grading) all works. If timeouts are severe, run test prompts in series.
- No browser/display — use `--static <output_path>` with `generate_review.py` to write standalone HTML. Proffer a link for the user to open in their browser.
- GENERATE THE EVAL VIEWER *BEFORE* evaluating outputs yourself. Get results in front of the human ASAP.
- Feedback: "Submit All Reviews" downloads `feedback.json` as a file. Read it from there (may need to request access first).
- Packaging: `package_skill.py` works with Python and a filesystem.
- Description optimization (`run_loop.py` / `run_eval.py`) uses `claude -p` via subprocess. Save it until the skill is finalized and user agrees it's in good shape.
- Body autopilot optimization (`body_autopilot.py` / `improve_skill_body.py`) also uses `claude -p` via subprocess. Only use it after the eval set is stable enough that keep/revert decisions mean something.
- **Updating an existing skill**: Follow the update guidance in the Claude.ai section above.
