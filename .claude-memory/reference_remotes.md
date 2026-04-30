---
name: P61 remotes and source-of-truth posture
description: GovOps lives at agentic-state/GovOps-LaC + huggingface.co/spaces/agentic-state/govops-lac; independent of eva-foundry
type: reference
stage: 4
last_referenced: 2026-04-30
---

# P61 remotes

GovOps is an **independent open-source repo**. The local working copy at `c:/eva-foundry/61-GovOps/` is hosted under the `eva-foundry` workspace tree on this device for convenience -- it is NOT part of the eva-foundry GitHub org.

## Configured remotes

| Remote | URL | Role |
|---|---|---|
| `origin` | `https://github.com/agentic-state/GovOps-LaC.git` | source-of-truth for the public open-source repo |
| `hf` | `https://huggingface.co/spaces/agentic-state/govops-lac` | HF Space deploy track for the v2.1 hosted demo |

## Source-of-truth posture for this device

Per Marco's directive 2026-04-30: **the local copy at `c:/eva-foundry/61-GovOps/` is the source of truth on this device.** Do not pull from `origin/main` to overwrite local state without explicit go-ahead. This includes:

- Do NOT `git fetch && git reset --hard origin/main` opportunistically
- Do NOT pull "to get the latest" before a session
- DO push local commits to `origin/main` when the user asks

The reason: this device may carry uncommitted exploratory edits or in-flight work that has not yet been promoted upstream. The mirroring direction is **local -> origin**, not the reverse.

This is **the opposite** of the policy for the eva-foundry repos (`75-EVA-vNext`, `eva-foundation`), where the GitHub origin is source-of-truth and local copies should be brought in line.

## Why GovOps is on this disk under `eva-foundry`

Historical -- this device used to host GovOps under the eva-foundry tree because the workspace was a single VS Code workspace. It is preserved at that path so existing tooling (Claude session paths, VS Code workspace files, scripts) keeps working. There is no logical coupling to the eva-foundry portfolio:

- GovOps is Apache 2.0 public-good open-source; eva-foundry is Marco's private workspace
- GovOps has no dependency on `eva-foundation`, `75-EVA-vNext`, or any sibling
- GovOps has its own Python venv, its own dependencies, its own CI, its own remote, its own license
- GovOps has its own project-bound `.claude/agents/govops-delegate.md` subagent and its own `.claude/settings.json` with project hooks (pre-commit pytest gate; post-edit pycollect)

The eva-foundation memory features (`.claude-memory/`, log-event hook, retrieval scoring) were grafted onto GovOps on 2026-04-30 because they are useful to any project, not because GovOps is part of the eva-foundry portfolio.

## What this means for "do not let old stuff resurrect"

When Marco said "P75 + eva-foundation: GitHub is source of truth, clone on top of local, do not let old stuff resurrect" on 2026-04-30, that policy **does NOT apply to P61**. The opposite policy applies: the local copy carries the truth. Outbound (push) is allowed; inbound (pull) is opt-in only.
