---
name: GovOps v3 Program-as-Primitive shipped
description: v3.0 cut over to main as v0.5.0 on 2026-04-30; phases A-I all closed; what shipped per phase
type: project
stage: 3
last_referenced: 2026-04-30
---

# v3 Program-as-Primitive -- shipped 2026-04-30

`v0.5.0` released on `main` at `6ce92f7` (`release(v3): bump version to 0.5.0 + charter Japan typo fix`). All nine phases closed in sequence.

## What v3 proved

`Program` is now a first-class declarable thing, the way v2 made `jurisdiction` one. A program is a YAML manifest under `lawcode/<jur>/programs/<program-id>.yaml`; the engine reads it; the substrate resolves its parameters. Adding a program once causes it to appear in every jurisdiction that adopts it.

The proof: **Employment Insurance** instantiated symmetrically across 6 active jurisdictions (CA, BR, ES, FR, DE, UA). **JP stays untouched** as the architectural control (locked by charter). Two new audiences entered the pipeline: government-leader cross-jurisdiction comparison surface; citizen entry with one life-event reassessment example.

## Per-phase ships (commit pointers)

| Phase | Commit | Title | What landed |
|---|---|---|---|
| A | (pre-Phase D) | Manifest substrate | `schema/program-manifest-v1.0.json`, `schema/shapes/*.yaml`, `src/govops/programs.py`, `lawcode/ca/programs/oas.yaml` -- ADR-014 + ADR-015 |
| B | (pre-Phase D) | Engine generalization | `OASEngine` -> `ProgramEngine` rename; pension-type logic moved to `src/govops/shapes/old_age_pension.py`; `Recommendation` gains `program_id` + `program_outcome_detail` -- ADR-016 |
| C | (pre-Phase D) | EI canonical shape + new primitives | `RuleType.BENEFIT_DURATION_BOUNDED`, `RuleType.ACTIVE_OBLIGATION`; `BenefitPeriod` + `ActiveObligation` models; `src/govops/shapes/unemployment_insurance.py` -- ADR-017 |
| D | `47c9c92` | EI rollout to 6 jurisdictions | `lawcode/<jur>/programs/ei.yaml` for CA / BR / ES / FR / DE / UA; per-jur ConfigValue records; i18n keys in 6 locales; 24 demo cases; §12.4 native-speaker review folded in |
| E | `ca9a762` | Cross-program evaluation API | `POST /api/cases/{id}/evaluate` body grows `programs: list[str]`; `AuditPackage.program_evaluations`; `ProgramInteractionWarning` -- ADR-018 |
| F | `924dfc2` | Government-leader comparison surface | `/compare/<program-id>` route + `GET /api/programs/{id}/compare?jurisdictions=...`; aligned parameter table + authority chain; empty state for JP |
| G | `dd5d926` | Citizen entry + life-event reassessment | `/check`, `/check/life-event?event=job_loss`; bounded-duration timeline + obligations; same privacy posture as `/api/screen` (no PII stored, no audit row) |
| H | `9337b08` | Adoption substrate | `govops init <iso-code> --shapes oas,ei` scaffolder; root `docker-compose.yml` + `docker/{api,web}.Dockerfile`; plain-language sidecars (`*.md` next to each `*.yaml`) via `govops docs` |
| I | `b2abea1` | Cutover | Drop deprecated `OASEngine` alias (callers all use `ProgramEngine`); demo seed extended for EI x 6 jurisdictions; `GOVOPS_SEED_DEMO=1` populates EI demo cases alongside OAS |

## Surfaces (v3)

- `/cases/<id>` -- officer view: per-case eligibility across every program in the jurisdiction
- `/compare/<program-id>` -- government-leader view: side-by-side parameter table across active jurisdictions
- `/check`, `/check/life-event?event=job_loss` -- citizen entry; declare facts -> qualifying programs (no PII stored)
- `/admin/federation` -- operator view: signed lawcode packs from peer publishers
- `/admin` -- operator surface (ConfigValue admin, federation, runbook)
- `/encode` -- rule encoding pipeline (legislative text -> proposals -> review -> YAML emission)

## Why v3 mattered

Before v3, GovOps could grow horizontally (more jurisdictions for the same program shape) but not vertically (more program shapes per jurisdiction). v3 made program-extension symmetric to jurisdiction-extension. The "Unix of Public Sector" thesis -- small composable primitives, universal interface, anyone can fork the shape library -- becomes load-bearing.

JP-EI absence is part of the proof. Symmetric extension is a *choice*, not a requirement.

## What was NOT in v3 (deferred to v4 or later)

- Citizen account / identity layer
- Proactive notifications
- Multi-life-event citizen flows (only `job_loss` was authored as the one example)
- Encoding pipeline upgrades for shape inference (still manual schema authoring)
- Federation pack signing UX improvements (functional but minimal)

These were explicitly out-of-scope per charter §"Citizen surface scoping" (gate 7) and the v3 non-goals list.

## Where to look next

Two candidate next-tracks; not yet selected:

- **v3.1 cleanup** -- enumerate remaining deprecation candidates beyond `OASEngine`; tighten v3 surfaces; close any gaps surfaced in early v3 use
- **v4.0 richer floor** -- charter the next layer: account / identity / proactive notifications -- the things v3 explicitly deferred
