# ADR-013 — Event-driven reassessment with supersession chain

**Status**: Accepted
**Date**: 2026-04-27
**Track / Gate**: Law-as-Code v2.0 / Phase 10D (life-event reassessment)

## Context

Phase 10D adds the loop a real benefits system needs: a citizen's circumstances change after their case was last evaluated (they move, their legal status changes, they gain new evidence, the statute is amended), and the case must be **re-evaluated against the rules in effect on the relevant date** with the new outcome **linking back to the old** via supersession. Without this loop, a GovOps case is a snapshot, not a record.

Three design questions need a load-bearing answer:

1. **What is an event — a delta to the case, a trigger to re-evaluate, or both?**
2. **Should posting an event automatically trigger re-evaluation, or stay decoupled?**
3. **What "rules in effect on date D" means when the substrate has dated supersession (configs change quarterly) AND when seed-time Python rule definitions are static?**

## Decision

### An event is a typed delta with an effective date

```python
class EventType(str, Enum):
    MOVE_COUNTRY = "move_country"           # close current residency, optionally open new one
    CHANGE_LEGAL_STATUS = "change_legal_status"   # applicant.legal_status update as-of date
    ADD_EVIDENCE = "add_evidence"           # new EvidenceItem
    RE_EVALUATE = "re_evaluate"             # marker: re-run with no state delta
```

Each event carries `event_type`, `effective_date`, `payload` (a typed dict whose shape depends on the event_type), `recorded_at` (UTC timestamp of when the event was captured), and `actor` (who recorded it — `"citizen"` for self-service, `"officer:<id>"` for caseworker). Events are **append-only**: posting an event never modifies a prior event; corrections are new events with `event_type=RE_EVALUATE` plus a `supersedes_event_id` payload field.

Applying an event to a case is deterministic: the engine has an `apply_event(case, event)` helper that returns a *new* `CaseBundle` (immutable transition). The event log is the source-of-truth for case state at any historical time D — a reassessment as-of D replays events whose `effective_date <= D`. This mirrors event-sourcing patterns without committing to a full event-store; the case row remains the materialized projection for fast reads.

### Posting an event triggers re-evaluation by default

`POST /api/cases/{case_id}/events` accepts the event body and **runs the engine in the same request**, producing a new `Recommendation` whose `supersedes` field points at the previous recommendation's `id`. The response carries both the event and the new recommendation. A `?reevaluate=false` query parameter opts out — useful for batch event imports where the caller wants to evaluate once at the end.

The reasoning for "trigger by default":

- The thesis of Sprint 3 is *"life changed → here's the new answer"*. Two-step (post event, then post evaluate) is easy to forget; the resulting case state is half-applied (event recorded, recommendation stale) and harder to reason about.
- The audit trail captures both the event and the re-evaluation as separate entries, so coupling them at the API surface doesn't conflate them in the record.
- Decoupled is recoverable as `?reevaluate=false`. Coupled-as-default is the right ergonomic.

### Supersession chain on Recommendation

`Recommendation.supersedes: Optional[str] = None`. On a fresh case, the first recommendation has `supersedes=None`. Every subsequent recommendation produced by `POST /events` sets `supersedes` to the id of the recommendation it replaces. The store keeps **all** recommendations per case (not just the latest), so the audit endpoint and the event-timeline endpoint can render the full chain.

Reading the chain backwards reconstructs every prior decision. Reading it forward shows what changed at each life event and why. The chain is the audit of *what changed* in the same shape that the substrate's effective-from windows are the audit of *what the rules were*. Both are linear, both are append-only, both are queryable by date.

### "Rules in effect on date D" applies to derived facts, not seed-time config (yet)

The engine's existing `evaluation_date` parameter already gates **derived facts**: age computation, residency-years aggregation, formula `field` resolution. A reassessment with `evaluation_date = 2024-09-01` against a 2026 case correctly sees the case as it stood on that date *if events have been applied chronologically*.

What it does **not** today gate is **seed-time-resolved scalar parameters** like `min_age=65` or `full_years=40`. These are baked into `LegalRule.parameters` at module import via `resolve_param()`, which always queries the substrate at "now". If `ca.rule.age-65.min_age` were to change from 65 to 67 effective 2027-01-01, a reassessment of a 2025 case would still see 65 (correct), but only because the supersession hasn't happened yet — a 2030 reassessment of the same 2025 case would (incorrectly) see 67 unless the engine re-resolves at the case's evaluation date.

Closing this gap requires a refactor: the engine should hold a `ConfigContext` it can re-resolve through, indexed by evaluation_date, instead of receiving frozen scalar parameters. That refactor is a **Phase 11** concern (the v2.0 PLAN preserves it as out-of-scope for 10A–10D). Sprint 3 ships the case-history mechanics; substrate-time-travel for scalar parameters is a separate ADR when the first real supersession lands.

The boundary stated:

> Phase 10D reassessment is fact-time-travel. A future ADR + refactor introduces config-time-travel.

For the calc rule (ADR-011), the formula's `ref` nodes already resolve through `_ref_resolver` at evaluate time; making *that* path date-aware is a one-line change when needed (pass `evaluation_date` through `_ref_resolver`). This is the seam where config-time-travel will first land.

## Consequences

**Positive**:

- The case becomes a record over time, not a snapshot. An auditor can ask "what was the answer on 2025-06-01?" and get a real answer by replaying events to that date and reading the recommendation produced.
- Two real demo flows light up: (a) a CA citizen who moves to Brazil mid-pension sees the recalculation tied to the move date; (b) an applicant who later supplies missing evidence sees `INSUFFICIENT_EVIDENCE` flip to `ELIGIBLE` with a supersession chain that shows when and why.
- The supersession chain on Recommendation mirrors the supersession chain on ConfigValue. The same "dated record, never edit in place" discipline applies at both layers; reviewers learn one mental model.

**Negative**:

- Every event triggers a recommendation by default — so a case with N events has N+1 recommendations. Storage cost is trivial in-memory; even at 10× the rate of real-world events, a case stays under 1KB. The visible cost is more: future "case detail" UI must surface the chain without overwhelming the reader. Lovable spec govops-019 handles this.
- The boundary between fact-time-travel (shipped) and config-time-travel (deferred) is real. Demos that bump a config retroactively (e.g. "the OAS amount was $700 on the move date") will produce a current-config answer until Phase 11. This is documented and stated, not silent.

**Neutral**:

- The `apply_event()` helper is small (~40 lines for v1's four event types). Each new event type adds one branch + one test; the API stays the same.

## Cross-references

- [PLAN.md](../../../PLAN.md) §Phase 10D — entry/exit
- [ADR-006](ADR-006-per-parameter-granularity.md) — config supersession (the analogue to recommendation supersession)
- [ADR-011](ADR-011-calculation-rules-as-typed-ast.md) — the formula's `ref` resolution is the seam for future config-time-travel
- [ADR-012](ADR-012-notice-rendering.md) — re-rendering a notice for a superseded recommendation produces the same supersession chain in its trace
- `src/govops/events.py` (new) — Event model + apply_event helper
- `src/govops/api.py` — `POST /api/cases/{id}/events`, `GET /api/cases/{id}/events`
- `tests/test_events.py` (new) — event application + supersession + temporal correctness
