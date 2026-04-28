# GovOps Spec — Mock-federation cleanup
<!-- type: route, priority: p2, depends_on: [govops-020] -->
type: route
priority: p2
depends_on: [govops-020]
spec_id: govops-021

## Intent

govops-020 shipped the admin federation surface against a mock fallback
because the backend admin endpoints were not yet live. They now are
(`GET /api/admin/federation/registry`, `GET /api/admin/federation/packs`,
`POST /api/admin/federation/fetch/{publisher_id}`,
`POST /api/admin/federation/packs/{publisher_id}/{enable|disable}` —
PLAN §12 8.x.3, 14 backend tests in `tests/test_api_federation.py`).
The mock module `web/src/lib/mock-federation.ts` and its four fallback
import sites in `web/src/lib/api.ts` are dead weight. This spec deletes
them. No UX change.

The driver is hygiene, not function: every fallback branch the page
keeps after a backend ships becomes a place where divergence can hide.
PLAN §12 8.x.3 already names this as the follow-up; this spec is the
landing instructions.

## Acceptance criteria

- [ ] `web/src/lib/mock-federation.ts` deleted
- [ ] In `web/src/lib/api.ts`: the `loadFederationMocks` constant is
      removed; the four federation client functions (`listFederationRegistry`,
      `listFederationPacks`, `fetchFederationPack`, `setFederationPackEnabled`)
      no longer wrap their `fetcher(...)` call in a `try { ... } catch
      { mockX(...) }`. The functions become single-line passthroughs that
      surface backend errors through the standard `fetcher()` error path
      (the same path every other admin call uses)
- [ ] No remaining string `mock-federation` in `web/src/`
- [ ] `web/src/routes/admin.federation.tsx` is unchanged at the source
      level (it never imported the mock directly — all references went
      through `api.ts`)
- [ ] `npm run build` green
- [ ] `npm run lint` green
- [ ] Smoke test against the real backend with `E2E_BACKEND_URL`
      injection: the existing Playwright `admin-flow.spec.ts` (or a
      one-liner addition under `e2e/admin-federation.spec.ts`) confirms
      `/admin/federation` renders the registry list returned by the
      backend, not the deterministic mock fixture
- [ ] `VITE_USE_MOCK_API=true` mode is unaffected — that toggle reads
      `isMockMode()` and short-circuits at the top of every `api.ts`
      function via the existing pattern; the federation calls inherit
      the same posture by adding the same `if (isMockMode()) { … }`
      guard that other admin calls already use *if and only if* a mock
      branch is required for preview parity. If preserving preview
      parity is preferred, keep a tiny `isMockMode()` branch and inline
      a 1–2 row deterministic stub directly inside `api.ts`. The goal
      is to remove the *dead-after-backend-ships* fallback path, not
      the explicit mock-mode toggle

## Files to create / modify

```
web/src/lib/mock-federation.ts                    (delete)
web/src/lib/api.ts                                 (modify — remove
                                                    loadFederationMocks
                                                    + four catch-fallback
                                                    branches; if preview
                                                    parity needed, inline
                                                    a 1–2 row stub)
web/e2e/admin-federation.spec.ts                   (optional new — single
                                                    spec asserting the
                                                    real backend's
                                                    response renders)
```

Do not touch `routeTree.gen.ts`. Do not modify
`web/src/routes/admin.federation.tsx`. Do not change the federation
TypeScript types in `web/src/lib/federation-types.ts` — the contract is
stable.

## Out of scope

- No UX changes (rows, chips, copy, layout, focus order — all
  unchanged)
- No new endpoints (backend already shipped them)
- No i18n changes (no new keys; no removed keys; no copy edits)
- No changes to `web/src/lib/api.ts` for non-federation client
  functions (`mockListPolicies`, `mockListConfigValues`, etc. — those
  follow their own follow-up cadence)
- No change to `VITE_USE_MOCK_API=true` semantics — the explicit
  mock-mode toggle remains a first-class preview path

## Tokens / data

No new tokens. No data changes.

## i18n

```yaml
locales_required: [en, fr, pt-BR, es-MX, de, uk]
rtl_mirroring: not_applicable
copy_keys: []
```

No copy changes. No new keys. No removed keys.

## a11y

```yaml
contrast: AA
focus_visible: required
keyboard: unchanged
aria_live: polite
reduced_motion: respect
```

No a11y changes — the page surface is unchanged.

provenance: hybrid
  # Same provenance as govops-020 — the federation page renders human-
  # authored ConfigValues fetched from a publisher repo alongside agent-
  # authored ones; deletion of the mock shim does not change the
  # surface's provenance.
