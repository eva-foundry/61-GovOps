---
name: pre-commit pytest gate
description: project-level Claude PreToolUse hook that runs pytest -q before a git commit and blocks on failure
type: feedback
stage: 4
last_referenced: 2026-04-30
---

# Pre-commit pytest gate

The repo's `.claude/settings.json` has a project-level **PreToolUse hook** on `Bash` that intercepts any `git commit` invocation, runs `scripts/claude-hooks/pre-commit-pytest.sh`, and **blocks the commit (exit 2)** on test failure. There is also a PostToolUse hook on `Edit|Write` that runs `pytest --collect-only -q` to catch import / syntax breaks (warns but does not block).

**Why**: GovOps is fork-bait public-good code. A green test suite is the floor of trust the repo owes contributors. Letting a broken commit land on `main` would corrupt that signal in a way that is expensive to recover from.

**How to apply**:

- **Do not bypass with `--no-verify`** unless there is an explicit, documented reason (and even then, fix-forward immediately). Bypass is denied by repo convention; my own instructions say never use it without explicit user request.
- **Verify deps in `.venv` before committing** -- the hook autodetects `.venv/Scripts/activate` (Windows) or `.venv/bin/activate` (macOS / Linux). If `.venv` is missing or stale, the hook runs against the wrong interpreter and either fails confusingly or false-passes.
- **The PostToolUse pycollect hook is a soft check** -- it warns on import / syntax breakage but does not block. Treat the warning as if it were a hard fail; do not commit through it.
- **Run `pytest -q` manually before staging** if you have made non-trivial changes. The hook is the safety net, not the primary gate.

## Hook scripts

- `scripts/claude-hooks/pre-commit-pytest.sh` -- the blocking pytest gate
- `scripts/claude-hooks/post-edit-pycollect.sh` -- the soft import-break warner

Both autodetect Windows vs Unix venv layout.

## Interaction with the workspace memory hooks

This is **distinct from** the workspace-level `~/.claude/settings.json` hooks (SessionStart `load-project-memory.sh` + PostToolUse / SessionStop `log-event.sh`). They coexist:

- **Workspace SessionStart**: loads `.claude-memory/MEMORY.md` for the current project (this repo's project memory)
- **Project PreToolUse Bash**: runs `pytest -q` before `git commit` and blocks on failure
- **Project PostToolUse Edit/Write**: warns on import / syntax break
- **Workspace PostToolUse / SessionStop**: writes `.claude-events/events.jsonl`

All four can fire on the same tool use (PostToolUse) without conflict; they have different commands and write to different places.

## When tests fail under the hook

1. Read the failure -- the hook prints the pytest output before exiting
2. Fix the failing test (do not skip it; do not delete it without an ADR)
3. Re-stage and try the commit again -- the hook re-runs pytest fresh
4. If pytest is slow enough that this loop is painful, that is a signal to break the work into smaller commits

The hook costs ~30s per attempt on a clean v3 baseline (640 tests). Worth it.
