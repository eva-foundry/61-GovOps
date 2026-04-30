# P61 GovOps -- project memory

This file loads on top of the workspace `eva-foundation/.claude-memory/MEMORY.md` when CWD is inside `61-GovOps/`. Loaded by `~/.claude/hooks/load-project-memory.sh` (SessionStart hook). EPISODIC tier; decays with release cadence.

GovOps is an independent open-source repo (`agentic-state/GovOps-LaC`), not part of `eva-foundry`. **This device's local copy is source of truth.**

## Active state (2026-04-30)

- **v3.0 Program-as-Primitive is shipped on `main`** at `6ce92f7` (release `0.5.0`). Phases A-I all closed.
- **Live demo**: https://agentic-state-govops-lac.hf.space/ -- single-container HF Space (FastAPI + uvicorn serves SPA + JSON API + LLM proxy). See `project_v2_1_hosted_demo.md`.
- **Test count**: 640 backend (pytest) + Playwright/axe E2E suite under `web/e2e/` covering smoke / admin-flow / approval-actions / a11y / i18n / SSR head coverage.
- **Stack**: Python 3.10/3.11/3.12 + FastAPI + Pydantic + embedded SQLite (Phase 6+, ADR-010); web is Vite + TanStack Start (SSR) + React 19 + TS + Tailwind v4 + shadcn/ui + react-intl ICU + 6 locales.
- **No active sprint** -- v3.0 just cut over; next track (v3.1 cleanup vs v4.0 richer floor) not yet decided.

## Recent ships (most recent first)

- `6ce92f7` (2026-04-30) release(v3): bump version to 0.5.0 + charter Japan typo fix
- `b2abea1` Phase I cutover -- drop deprecated `OASEngine` alias; extend demo seed for EI cases x 6 jurisdictions (`GOVOPS_SEED_DEMO=1`)
- `9337b08` Phase H adoption substrate -- `govops init <iso-code>` scaffolder + `docker compose up` + plain-language sidecars (`govops docs <manifest>`)
- `dd5d926` Phase G citizen entry + life-event reassessment (`/check`, `/check/life-event?event=job_loss`)
- `924dfc2` Phase F government-leader cross-jurisdiction comparison surface (`/compare/<program-id>`, `GET /api/programs/{id}/compare?jurisdictions=...`)
- `ca9a762` Phase E cross-program evaluation API + `ProgramInteractionWarning` (`POST /api/cases/{id}/evaluate` accepts `programs: [...]`, returns `program_evaluations`)
- `47c9c92` Phase D Employment Insurance rollout to 6 jurisdictions (CA / BR / ES / FR / DE / UA). JP excluded as architectural control.
- `bc5ae5b` v2.1 hosted-demo smoke test against live HF Space at `b08779c` (35/35 green); follow-up `f3c1a64` fixed two browser-only bugs (SSR API base + JP screen allowlist) -- see `project_v2_1_smoke_test_2026-04-29.md`

## Programs and jurisdictions modelled

- **2 programs**: `old_age_pension` (lifetime monthly benefit) + `unemployment_insurance` (bounded-duration)
- **7 jurisdictions** for OAS: CA / BR / ES / FR / DE / UA / JP -- each encoded from its own statutes (NOT literal Canada law applied elsewhere)
- **6 jurisdictions** for EI: same minus JP. **JP-EI is the v3 architectural control** (locked by charter); proves symmetric extension is a choice, not a requirement. Do not add JP-EI -- it is load-bearing as an absence.

## Key paths (canonical sources -- do NOT duplicate state here)

| What | Where |
|---|---|
| ProgramEngine (v3 dispatch; was `OASEngine`, alias dropped Phase I) | `src/govops/engine.py` |
| Program manifest loader (ADR-014) | `src/govops/programs.py` |
| Shape evaluators (ADR-015) | `src/govops/shapes/` (`old_age_pension.py`, `unemployment_insurance.py`) |
| Cross-program interaction registry (ADR-018) | `src/govops/program_interactions.py` |
| `govops init` + plain-language docs (Phase H) | `src/govops/cli_init.py` |
| docker-compose stack (Phase H, distinct from v2.1 hosted-demo `Dockerfile`) | `docker-compose.yml`, `docker/{api,web}.Dockerfile` |
| ConfigValue substrate (v2.0) | `src/govops/config.py` -- two-tier resolver: substrate first, then `LEGACY_CONSTANTS` |
| Authored YAML source-of-truth | `lawcode/<jur>/{jurisdiction.yaml, programs/*.yaml, config/*.yaml}` |
| API + UI (Jinja legacy + TanStack SPA at `/web`) | `src/govops/api.py` + `web/src/routes/` |

## Project-specific rules (load-bearing -- do not soften)

1. **Disclaimer is load-bearing**: not gov-affiliated, not endorsed, statutory text is illustrative only. Preserve in any user-facing change. See `feedback_disclaimer_load_bearing.md`.
2. **JP-EI absence is permanent for v3** -- architectural control. Charter §"The proof"; gate 6 in PLAN-v3 §3.
3. **Pre-commit hook is `pytest -q`** -- a `git commit` triggers `scripts/claude-hooks/pre-commit-pytest.sh` (PreToolUse); commit blocks on test failure. `.venv/Scripts/python.exe` is used on Windows. See `feedback_pre_commit_pytest_gate.md`.
4. **Strict-mode resolver gate in CI**: `AIA_CONFIG_STRICT=1` raises on any `LEGACY_CONSTANTS` hit -- substrate must resolve everything. Tests-pass is necessary, not sufficient -- match each PLAN.md / PLAN-v3.md Phase Exit individually.
5. **No emojis in files. No comments unless the *why* is non-obvious.** (Per `.claude/agents/govops-delegate.md`.)
6. **Conventional Commits from Phase 0** -- `type(scope): subject`; types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `phase-N`.
7. **Apache 2.0** -- preserved across v2 and v3.

## Open follow-ups (non-blocking)

- §12.1 i18n native-speaker re-look -- 5 cells flagged in PLAN.md after the 2026-04-29 round (1,351 cells x 5 locales shipped). Each is shipped + self-consistent; native reviewer might nudge tone. Issue template at `.github/ISSUE_TEMPLATE/native_speaker_review.md`. See `project_open_followups.md`.
- v3.1 cleanup track -- removal of `OASEngine` alias is done (Phase I); other deprecation candidates not yet enumerated.
- v4.0 richer floor -- account / identity / proactive notifications were explicitly scoped OUT of v3 (charter §"Citizen surface scoping", gate 7). v4.0 is the next charter to write.

## Cross-links

- `project_v3_shipped_2026-04-30.md` -- detailed v3 cutover state
- `project_v2_1_hosted_demo.md` -- HF Space deploy: multi-stage build + uvicorn-served SPA + LLM-provider failover (Groq -> OpenRouter -> Gemini -> Mistral) + daily age-based GC
- `project_v2_1_smoke_test_2026-04-29.md` -- 35/35 curl-pass + 2 browser-only bugs caught and fixed
- `feedback_disclaimer_load_bearing.md` -- the disclaimer rule and why it is non-negotiable
- `feedback_pre_commit_pytest_gate.md` -- the project-level PreToolUse hook
- `reference_remotes.md` -- `agentic-state/GovOps-LaC` (origin) + `huggingface.co/spaces/agentic-state/govops-lac` (hf); independent of eva-foundry
- `project_open_followups.md` -- the i18n re-look list + v3.1/v4.0 staging
