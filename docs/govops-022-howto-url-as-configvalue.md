# GovOps Spec — Move HOWTO_URL into the substrate
<!-- type: route, priority: p2, depends_on: [govops-015, govops-015a] -->
type: route
priority: p2
depends_on: [govops-015, govops-015a]
spec_id: govops-022

## Intent

The `/screen/$jurisdictionId` result card renders a "How to apply"
external link per jurisdiction. Today the URL lives in a hardcoded
`HOWTO_URLS: Record<string, string>` table at the top of
`web/src/components/govops/ScreenResult.tsx`. That table is the last
remaining piece of jurisdiction-scoped knowledge in the citizen-facing
surface that bypasses the substrate — a 6-row stand-in that contradicts
the load-bearing v2.0 success criterion ("every value the system uses
… becomes a dated `ConfigValue` record").

This spec moves the URL into the substrate as
`jurisdiction.<code>.howto_url` ConfigValue records and surfaces it on
the existing `/api/jurisdiction/{code}` payload as
`howto_url: string | null`. The Lovable surface reads the field from
the existing route loader and falls back to the current `HOWTO_URLS`
table only when the API returns `null` (preview-mode safety).

The driver is consistency, not function. After Phase 7 (citation
impact) and Phase 8 (federation), every authoritative pointer the
citizen surface renders should be queryable, dated, and citable. The
URL belongs in the same shape.

PLAN §12 10A.x.9.

## Backend prelude (already shipped)

This spec ships in two halves. The backend half is **already in main
under the commit titled `feat(api): jurisdiction.<code>.howto_url
ConfigValue + GET /api/jurisdiction/{code}.howto_url field`** —
authored as the prelude before Lovable picks up the UI half. What
shipped:

1. `GET /api/jurisdiction/{jur_code}` now exists (sibling of the
   pre-existing POST switch endpoint). It returns:
   ```json
   {
     "id": "jur-ca-federal",
     "jurisdiction_label": "Government of Canada",
     "program_name": "Old Age Security (OAS)",
     "default_language": "en",
     "howto_url": "https://www.canada.ca/en/services/benefits/publicpensions/cpp/old-age-security.html"
   }
   ```
   `howto_url` is `string | null`. Resolution path: `ConfigStore.resolve(
   "jurisdiction.<code>.howto_url", evaluation_date=today, jurisdiction_id=
   pack.jurisdiction.id)`. Missing record → `null`.
2. Six new `ConfigValue` records seeded in `lawcode/<jur>/config/
   rules.yaml` for ca / br / es / fr / de / ua. Each has
   `effective_from: '1900-01-01'`, a citation pointing at the source
   government landing page, and a rationale paragraph naming this spec.
3. Backend tests (`tests/test_api_jurisdiction_howto.py`): 7 tests
   covering the GET 200 happy path, the unknown-jurisdiction 404, the
   `howto_url=null` posture when the substrate has no record, and the
   substrate-as-truth invariant (changing the URL via the admin draft
   flow flips the GET response without restart).

The backend half stays out of Lovable's perimeter. **The Lovable spec
below is what Lovable picks up.**

## Acceptance criteria (Lovable scope)

- [ ] `web/src/components/govops/ScreenResult.tsx`: the `HOWTO_URLS`
      record is **kept** but renamed `HOWTO_URLS_FALLBACK` and
      relegated to a fallback role. The component now reads the URL
      from a new `howto_url?: string | null` prop on `ScreenResult`
      itself, falling back to `HOWTO_URLS_FALLBACK[jurisdictionId]` only
      when the prop is `null` or `undefined`
- [ ] `web/src/routes/screen.$jurisdictionId.tsx`: the route loader
      (which already calls `fetchJurisdiction(code)` per 015a) passes
      `howto_url={data.howto_url}` down to `<ScreenResult … />`
- [ ] `web/src/lib/types.ts`: the `JurisdictionResponse` interface
      gains `howto_url: string | null`
- [ ] `web/src/lib/mock-jurisdiction.ts`: every fixture in
      `MOCK_JURISDICTIONS` gains a `howto_url` field matching the
      current `HOWTO_URLS_FALLBACK` table verbatim (preview parity)
- [ ] When `data.howto_url` is a non-empty string, the rendered link
      uses it verbatim. Existing markup, target, rel, and copy stay
      identical
- [ ] When `data.howto_url` is `null` or `undefined`, the rendered link
      uses `HOWTO_URLS_FALLBACK[jurisdictionId] ?? "#"` (today's
      behaviour, unchanged)
- [ ] No new i18n keys; no copy changes; no a11y changes; no token
      changes
- [ ] A unit test in `web/src/components/govops/__tests__/
      ScreenResult.test.tsx` (create if missing) covers both branches:
      backend-supplied URL, and the fallback path when the prop is
      `null`
- [ ] The existing Playwright `screen.spec.ts` continues to pass
      against both `VITE_USE_MOCK_API=true` and a real backend run

## Files to create / modify

```
web/src/lib/types.ts                              (modify)
web/src/lib/mock-jurisdiction.ts                  (modify — add howto_url
                                                    to every fixture)
web/src/routes/screen.$jurisdictionId.tsx         (modify — pass howto_url
                                                    prop into ScreenResult)
web/src/components/govops/ScreenResult.tsx        (modify — accept
                                                    howto_url prop;
                                                    rename HOWTO_URLS to
                                                    HOWTO_URLS_FALLBACK)
web/src/components/govops/__tests__/
  ScreenResult.test.tsx                           (new or modify — assert
                                                    both branches)
```

Do not touch `routeTree.gen.ts`. Do not modify the backend
(`/api/jurisdiction/{code}` GET shape is now frozen — see prelude).

## Tokens / data

Backend contract (already shipped — copied here for the Lovable agent's
convenience):

```ts
// src/lib/types.ts addition
export interface JurisdictionResponse {
  id: string;
  jurisdiction_label: string;
  program_name: string;
  default_language: string;
  howto_url: string | null;             // NEW — substrate-resolved per
                                        //       jurisdiction.<code>.howto_url
}
```

```ts
// src/lib/mock-jurisdiction.ts shape (every entry)
export const MOCK_JURISDICTIONS: Record<string, JurisdictionResponse> = {
  ca: { …existing fields, howto_url: "https://www.canada.ca/en/services/benefits/publicpensions/cpp/old-age-security.html" },
  br: { …existing fields, howto_url: "https://www.gov.br/inss/pt-br" },
  es: { …existing fields, howto_url: "https://www.seg-social.es/" },
  fr: { …existing fields, howto_url: "https://www.service-public.fr/" },
  de: { …existing fields, howto_url: "https://www.deutsche-rentenversicherung.de/" },
  ua: { …existing fields, howto_url: "https://www.pfu.gov.ua/" },
};
```

```tsx
// web/src/components/govops/ScreenResult.tsx — top of file
const HOWTO_URLS_FALLBACK: Record<string, string> = {
  ca: "https://www.canada.ca/en/services/benefits/publicpensions/cpp/old-age-security.html",
  br: "https://www.gov.br/inss/pt-br",
  es: "https://www.seg-social.es/",
  fr: "https://www.service-public.fr/",
  de: "https://www.deutsche-rentenversicherung.de/",
  ua: "https://www.pfu.gov.ua/",
};

export function ScreenResult({
  data,
  stale,
  jurisdictionId,
  onRerun,
  howto_url,                              // NEW prop, optional
}: {
  data: ScreenResponse;
  stale: boolean;
  jurisdictionId: string;
  onRerun: () => void;
  howto_url?: string | null;
}) {
  const resolvedHowtoUrl =
    typeof howto_url === "string" && howto_url.length > 0
      ? howto_url
      : (HOWTO_URLS_FALLBACK[jurisdictionId] ?? "#");
  // … existing body, replace HOWTO_URLS[jurisdictionId] with resolvedHowtoUrl
}
```

```tsx
// web/src/routes/screen.$jurisdictionId.tsx — at the result-card site
<ScreenResult
  data={result}
  stale={stale}
  jurisdictionId={jurisdictionId}
  onRerun={handleRerun}
  howto_url={jurisdiction?.howto_url ?? null}
/>
```

## i18n

```yaml
locales_required: [en, fr, pt-BR, es-MX, de, uk]
rtl_mirroring: not_applicable
copy_keys: []
```

No new keys. No copy changes. The link's user-visible label
(`screen.result.howto.cta` or whatever it is today) stays unchanged —
only the `href` source moves.

## a11y

```yaml
contrast: AA
focus_visible: required
keyboard: unchanged
aria_live: polite
reduced_motion: respect
```

No a11y change — link target only.

## Out of scope

- The backend half of this spec is **already shipped** as a prelude
  commit (see "Backend prelude" above). Lovable does not touch it
- Renaming the underlying ConfigValue key (`jurisdiction.<code>.howto_url`
  is frozen — federation packs may reference it)
- Per-locale URL variants. Some governments serve EN / FR landing
  pages on different paths; today the substrate stores one URL per
  jurisdiction. Locale-aware variants are a separate spec when the
  demand surfaces — track via PLAN §12 if accepted on merit
- Removing `HOWTO_URLS_FALLBACK` from the component. Preview-mode
  parity (no backend, mocks-off) requires the fallback table; deleting
  it is a follow-up after the substrate has shipped through enough
  channels that fallbacks are no longer needed
- Validating that the URL resolves (HEAD-check). Out of scope; cite-
  rot is a separate concern handled by the citation tooling

provenance: hybrid
  # Same as govops-015 — the page renders human-authored ConfigValues
  # alongside agent-authored ones. Substrate-driven URL doesn't change
  # the provenance ribbon.
