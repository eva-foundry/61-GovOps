---
name: GovOps disclaimer is load-bearing
description: the "not gov-affiliated, statutory text is illustrative" framing must be preserved in any user-facing change
type: feedback
stage: 4
last_referenced: 2026-04-30
---

# Disclaimer is load-bearing

GovOps is an **independent open-source prototype**. It is **not affiliated with, endorsed by, or representing any government, department, or public agency** -- including SPRIND, the Agentic State paper authors (Ilves / Kilian / Parazzoli / Peixoto / Velsberg), or any of the seven jurisdictions used as illustrative case studies. The `agentic-state` GitHub organization is an independent open-source implementation effort whose name signals framework alignment, **not authorship or endorsement** by the Agentic State paper authors.

Legislative text used in the demo (including the Old Age Security Act and equivalents in BR / ES / FR / DE / UA / JP) is publicly available law interpreted by the author for illustrative purposes. It is **NOT authoritative operational guidance** and should not be relied upon for actual eligibility determinations.

## Why this is load-bearing (not just polite)

**How to apply**: preserve this framing in any user-facing change. The reasons:

1. Legal exposure -- "decisions support" framing keeps the project on the right side of unauthorized-practice-of-law concerns
2. Endorsement boundary -- the project's name (GovOps), org name (agentic-state), and SPRIND alignment all create proximity to authoritative voices that have NOT signed off
3. Citizen safety -- a non-trivial fraction of visitors land via "OAS calculator" search; keeping them aware that the eligibility output is illustrative protects them
4. Contributor onboarding -- jurisdictions added in the future will inherit this same framing; if it weakens, every downstream country-pack inherits the weaker framing

**Where this rule binds**:

- `README.md` (top of file)
- `CLAUDE.md` -- bridge file restates it
- Every new jurisdiction's `lawcode/<jur>/jurisdiction.yaml` should NOT claim authority
- Decision notice templates -- the rendered output should carry the disclaimer
- API responses -- never claim "approved" / "denied" without a recommendation framing
- Any new public surface (CLI, sidecar docs, `/check`, `/check/life-event`, `/compare`) -- carry the framing

## What this rule says NO to

- Removing the disclaimer because it makes the demo "feel less polished"
- Saying "the system decides" rather than "the system recommends"
- Citizen-facing copy that sounds authoritative ("you qualify for X")
- Government-customer copy that implies certification or endorsement
- Removing the SPRIND / Agentic State proximity disclaimer because it is wordy

## What this rule says YES to

- "Decision support" / "recommendation" / "illustrative" / "for educational use" framings
- Citation chains visible to the user (every output traces to statute)
- Human-in-the-loop on every consequential surface
- Explicit framing of uncertainty (missing evidence -> review, not false certainty)

When in doubt, choose the framing that makes the human reviewer the final decision-maker, and that makes the citation chain inspectable. That is the boundary the disclaimer protects.
