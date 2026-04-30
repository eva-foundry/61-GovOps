---
name: P61 open follow-ups
description: i18n native-speaker re-look (5 cells); v3.1 cleanup track; v4.0 richer-floor charter
type: project
stage: 2
last_referenced: 2026-04-30
---

# Open follow-ups (non-blocking)

Three tracks live in the queue. None of them block v3.0 closure -- v3.0 is shipped on `main` as `v0.5.0`. These are the next things to charter / pick up.

## §12.1 -- i18n native-speaker re-look (5 cells)

The 2026-04-29 i18n round shipped **1,351 cells x 5 locales** (fr / de / es-MX / pt-BR / uk) -- 0 brand-token violations, 0 empties, 0 placeholder-name mismatches. Five cells are flagged for native-speaker re-look. Each is shipped and self-consistent; the local register is what a native reviewer might want to nudge.

| # | Cell(s) | Question for native reviewer | Status |
|---|---|---|---|
| 12.1.1 | `home.eyebrow` (all 5 locales) | Currently kept as the literal developer-only string `spec govops-002 -- law-as-code`. Localise or stay verbatim? | Open |
| 12.1.2 | `screen.benefit.op.*` (all 5 locales) | Operator/trace verb tags are lowercase verbs in fr / es / pt / uk and capitalised nouns in de (German noun convention). Confirm cross-locale consistency. | Open |
| 12.1.3 | `events.summary.add_evidence` (`+ {evidence_type}`), `events.summary.move_country` (`{from} -> {to}`) | Pure-placeholder by design (identical across locales). If runtime values for `evidence_type` are EN-only, the visible string is EN regardless of locale. Upstream concern, not a translation gap. | Open |
| 12.1.4 | `cases.detail.heading` fr (`Dossier {id}`) | Currently `Dossier {id}` to align with `nav.cases = Dossiers`. Product-team preference may be `Cas {id}` (literal cognate). | Open |
| 12.1.5 | `admin.federation.col.{actions [fr], name [de], status [de/pt-BR], version [fr/de]}` | Column headers re-emitted as loanwords / cognates because the EN sources are loans / cognates in those locales. Confirm the existing locale JSON did not intend a deeper localisation. | Open |

These are explicitly **shipped, not blocking**. Issue template at `.github/ISSUE_TEMPLATE/native_speaker_review.md` to surface a review pass when a native reviewer is available. Source-of-truth doc: `docs/i18n-rounds/2026-04-29/i18n-translation-notes.md` §4.

## v3.1 cleanup track (not yet chartered)

Phase I of v3 already removed the deprecated `OASEngine` alias. Other deprecation candidates have not been enumerated. Likely contents of a v3.1 charter:

- Sweep for any remaining v2-shape API or model that v3 should retire
- Strict-mode resolver gate (`AIA_CONFIG_STRICT=1`) -- evaluate whether to make it the default rather than CI-only
- Encoder pipeline -- shape inference (currently manual schema authoring), prompt audit re-pass post Phase 4 / Phase H
- v2 PLAN.md §12.1-12.5 -- review which line items have decayed and can close
- Documentation pruning -- v3 added a lot of docs; some pre-v3 docs may now be misleading
- `LEGACY_CONSTANTS` removal where the substrate fully covers the parameter

No charter committed yet. Defer until either (a) v3 use surfaces a real cleanup driver, or (b) bandwidth opens up.

## v4.0 richer floor (not yet chartered)

v3 explicitly scoped OUT (charter §"Citizen surface scoping", gate 7):

- Citizen account / identity layer
- Proactive notifications (e.g. "your benefit period is ending in 4 weeks")
- Multi-life-event citizen flows beyond `job_loss`
- Cross-program rules within a jurisdiction (today: pension + EI per jurisdiction; future: interactions like "EI claimant turning 65 transitions to OAS")

v4 charter would cover one or more of these. The "Unix of Public Sector" thesis from v3 should stay load-bearing -- v4 should not introduce monolithic surfaces that violate it.

No charter committed. v4 starts with a richer floor than v3 did because of v3's promotion of program-as-primitive (charter §"Act -- promote reusable primitives so v4 starts with a richer floor").

## How these tracks compete

Picking among these three is a planning call, not an architectural one. Likely sequencing:

1. **§12.1 i18n re-look** -- low-effort, recovers a visible signal of polish, does not block anything
2. **v4.0 charter** -- high-leverage, expands the audience pipeline; risk is scope-creep
3. **v3.1 cleanup** -- lowest-pull, do it when the boredom-bandwidth shows up

Open to reordering by Marco. The charter for whichever comes next will live in `docs/IDEA-GovOps-vN.0-*.md` following the v2.0 / v3.0 pattern.
