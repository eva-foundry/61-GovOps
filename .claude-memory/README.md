# P61 GovOps -- project memory

This directory holds Claude Code's project-bound memory entries for the GovOps repo. It loads on top of the workspace memory (`eva-foundation/.claude-memory/`) when CWD is inside `61-GovOps/`. Loaded by `~/.claude/hooks/load-project-memory.sh` (SessionStart hook).

**Important**: GovOps is a **separate, independent open-source repo** at `agentic-state/GovOps-LaC` -- not part of the `eva-foundry` org. The local working directory `c:/eva-foundry/61-GovOps/` is **the source of truth for this device**; do not pull from `agentic-state/GovOps-LaC` to overwrite local state without explicit go-ahead. (See `reference_remotes.md`.)

## Layout

| File | Auto-loaded? | Content |
|---|---|---|
| `MEMORY.md` | YES (every session inside `61-GovOps/`) | Tight project index -- active state, recent ships, project-specific rules, pointers |
| `project_*.md` / `feedback_*.md` / `reference_*.md` | NO (read by name on demand) | Topic files; durable detail behind index entries |

## Canonical sources (do NOT duplicate -- point to them)

- `CLAUDE.md` -- Claude Code bridge for this repo (current state, key paths, design rules)
- `PLAN-v3.md` -- v3 operational plan (the executed work; phase history)
- `PLAN.md` -- v2.0 operational plan (released as v0.4.0; retained for §12 follow-ups)
- `README.md` -- public-facing description + disclaimer (load-bearing)
- `docs/IDEA-GovOps-v3.0-ProgramAsPrimitive.md` -- v3 charter (strategic argument)
- `docs/design/ADRs/` -- 18 ADRs; load-bearing decisions (ADR-014..018 are v3-specific)

## Memory event log

`.claude-events/events.jsonl` (gitignored) is written by the workspace `log-event.sh` hook (PostToolUse + SessionStop). Used by `eva-foundation/scripts/memory-reflect.py` to score memory entries by activity. Per-project log when CWD is inside this repo.

## Frontmatter convention (Phase 0 partial)

New topic files written from 2026-04-28 onward should carry:

```yaml
---
name: short title
description: one-line description used to decide relevance in future sessions
type: project | feedback | reference
stage: 0..4   # P62 plasticity ladder; default 1 for newly-written entries
last_referenced: YYYY-MM-DD   # reflection ritual updates this
---
```

## Disclaimer (preserve in any user-facing change)

GovOps is an **independent open-source prototype**. Not affiliated with, endorsed by, or representing any government, department, or public agency. Legislative text used in the demo is publicly available law interpreted by the author for illustrative purposes. See `feedback_disclaimer_load_bearing.md`.
