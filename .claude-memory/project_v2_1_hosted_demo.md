---
name: v2.1 hosted demo
description: live HF Space deploy at agentic-state-govops-lac.hf.space; multi-stage build + uvicorn-served SPA; LLM provider failover; daily age-based GC
type: project
stage: 3
last_referenced: 2026-04-30
---

# v2.1 hosted demo -- live HF Space

**URL**: https://agentic-state-govops-lac.hf.space/
**Image SHA at last verified stable point**: `b08779c` (post-`VITE_API_BASE_URL=""` rebuild)
**Source SHA at that image**: `fc19f64` on `agentic-state/GovOps-LaC@main`

This is a separate deploy track from v2.1 the operational plan. The Dockerfile at the repo root is the **single-container hosted-demo image** (FastAPI serves built React SPA + the JSON API + an LLM proxy). It is **distinct from** the `docker-compose.yml` + `docker/{api,web}.Dockerfile` pair shipped in Phase H of v3 (which is the two-process developer demo). Don't confuse them.

## What lives in the container

- FastAPI + uvicorn serves both `/api/*` (JSON) and the built TanStack SPA (`/`)
- LLM provider failover: Groq -> OpenRouter -> Gemini -> Mistral (free-tier-only sequence)
- Daily age-based GC (transient case data; no PII retention)
- SQLite (`var/govops.db`) for ConfigStore persistence

## Bug history during v2.1 stabilization

The path to a stable image is preserved in the commit log because the deploys taught real lessons:

1. `683b185` -- pivot Dockerfile from production SSR to vite dev server (initial workaround for build-target mismatch)
2. `b862792` -- allowlist HF Space hostname in vite dev server
3. `199a70d` -- proxy `/api/*` through vite dev to the FastAPI backend
4. `fc19f64` -- set `VITE_API_BASE_URL=""` so browser uses same-origin relative URLs (correct for Vite proxy)
5. `8f6ffcf` -- disable vite HMR + log which child died on container restart
6. `8a0d55a` -- resilient supervisor + drop vite watcher (survive both known killers)
7. `35fb187` -- kill vite dev -- multi-stage build + SPA served by uvicorn (final shape)
8. `f3c1a64` -- SSR-aware api BASE + add JP to SCREEN_JURISDICTIONS allowlist (fixes the two browser-only bugs caught in `project_v2_1_smoke_test_2026-04-29.md`)

## Operating notes

- Free-tier HF Space sleeps when idle -- first load may take ~30s
- LLM keys are HF Space secrets; failover sequence prevents single-provider rate-limit fatal failure
- Age-based GC runs daily; demo cases survive ~24h (longer than a typical interactive demo session)
- Memory event log (`.claude-events/`) is gitignored locally; never lands in the deploy

## Reference

- `docs/v2.1-deploy-test-2026-04-29.md` -- the smoke-test runbook + result trail (uncommitted edit on this device adds the two post-curl-pass browser bugs)
- `memory/v2_1_hosted_demo_plan.md` -- pre-deploy planning notes (older, kept for archaeology)

## Boundary

The v2.1 hosted demo is a **public proof point**, not the development primary. Local development uses `govops-demo` + `cd web && npm run dev` (two-process). The HF Space is for visitors / SPRIND-curious / SecOps showcase / "yes it actually runs end-to-end."
