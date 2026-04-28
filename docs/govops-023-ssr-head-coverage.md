# GovOps Spec — SSR `<head>` coverage on Phase 6 routes
<!-- type: route, priority: p2, depends_on: [govops-014] -->
type: route
priority: p2
depends_on: [govops-014]
spec_id: govops-023

## Intent

`/impact` (govops-014) ships a TanStack Start `head()` hook that emits
a `<title>` and `<meta name="description">` into the SSR HTML. The
other Phase 6 routes — `/config`, `/authority`, `/encode` — already
have `head()` hooks but they emit **hardcoded English strings**, not
i18n-keyed copy. A locale-switched user sees a French page body under
an English `<title>`. The SSR meta is the slow-leak place where
hardcoded copy survives an i18n cutover.

This spec aligns those three routes (and any Phase 6 route discovered
in the audit step that still uses hardcoded English) with the same
i18n posture as the page bodies: every user-visible string flows
through `react-intl` keys. Where TanStack Start's `head()` cannot
reach `useIntl()` directly (it runs at route-match time, before the
component mounts), it reads the locale from the request via the same
cookie path the i18n provider uses (`govops-locale`), then resolves
the key against the locale's message catalog imported statically.

The driver is consistency. PLAN §12 7.x.8 already names this; it has
been a known gap since impact landed.

## Acceptance criteria

- [ ] `web/src/routes/config.tsx`, `web/src/routes/authority.tsx`,
      `web/src/routes/encode.tsx` each have a `head()` hook that
      returns a `meta: [{ title }, { name: "description", content }]`
      block whose strings are resolved from the active locale's
      message catalog at SSR time, not hardcoded English. The same
      treatment applies to any other Phase 6 route the audit step
      surfaces (`/cases`, `/admin`, `/admin/federation`,
      `/about`) — preserve in scope every route that currently emits
      hardcoded English in its `head()`
- [ ] Resolution path: `head()` reads the locale from the request
      cookie (`govops-locale`), defaults to `en`, then looks up the
      key in the locale's static catalog (the same `messages/<locale>.json`
      bundle `IntlProvider` consumes). Missing keys log a dev warning
      and fall back to the English string for that key
- [ ] No new i18n keys. Reuse existing per-route copy keys whenever
      they exist (e.g. `nav.config`, `nav.impact`, `config.heading`).
      Where no suitable key exists, **stop and request one in the
      spec response** — do not invent new keys without an explicit
      decision
- [ ] `web/e2e/smoke.spec.ts` gains a one-liner per Phase 6 route
      asserting `<title>` is non-empty after SSR. Suggested form:
      ```ts
      const title = await page.title();
      expect(title.trim().length).toBeGreaterThan(0);
      ```
      The assertion must run against the SSR HTML, not the
      post-hydration DOM (Playwright's `page.title()` after
      `page.goto(route, { waitUntil: 'commit' })` reads the
      pre-hydration `<title>`)
- [ ] The locale-switched assertion: at least one smoke case sets
      `govops-locale=fr` via `page.context().addCookies(...)` and
      confirms the `<title>` for `/impact` differs from the `en`
      title. (One route is enough — the resolution path is shared)
- [ ] No SSR regressions: the existing Playwright suite stays green
      across chromium / firefox / webkit
- [ ] The `head()` hooks remain pure functions of route + locale —
      they do not depend on loader data. Per-route titles that need
      a parameter (`/cases/:id` rendering the case ID in the title)
      are out of scope for this spec; track separately if needed

## Files to create / modify

```
web/src/routes/config.tsx                          (modify — head() i18n)
web/src/routes/authority.tsx                       (modify — head() i18n)
web/src/routes/encode.tsx                          (modify — head() i18n)
web/src/routes/impact.tsx                          (modify — head() i18n,
                                                    aligning with the
                                                    rest)
web/src/routes/about.tsx                           (modify if hardcoded)
web/src/routes/cases.tsx                           (modify if hardcoded)
web/src/routes/admin.tsx                           (modify if hardcoded)
web/src/routes/admin.federation.tsx                (modify if hardcoded)
web/src/lib/head-i18n.ts                           (new — small helper:
                                                    `headTitle(key, locale?)`,
                                                    reads cookie, looks
                                                    up key in message
                                                    catalog, falls back
                                                    to en)
web/e2e/smoke.spec.ts                              (modify — non-empty
                                                    <title> assertion
                                                    per route + one
                                                    locale-switched
                                                    case)
```

Do not touch `routeTree.gen.ts`. Do not modify
`web/src/messages/<locale>.json` — no new keys. If a needed key is
missing, surface that in the spec response and stop.

## Reference implementation

```ts
// web/src/lib/head-i18n.ts
import en from "@/messages/en.json";
import fr from "@/messages/fr.json";
import ptBR from "@/messages/pt-BR.json";
import esMX from "@/messages/es-MX.json";
import de from "@/messages/de.json";
import uk from "@/messages/uk.json";

const CATALOGS: Record<string, Record<string, string>> = {
  en, fr, "pt-BR": ptBR, "es-MX": esMX, de, uk,
};

const COOKIE_NAME = "govops-locale";

function readLocaleCookie(): string {
  if (typeof document === "undefined") {
    // SSR: read from request context if available; otherwise default.
    // TanStack Start exposes the request via `getRequestHeaders()`-style
    // helpers — wire to the existing i18n provider's cookie reader.
    return "en";
  }
  const m = document.cookie.match(/(?:^|;\s*)govops-locale=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "en";
}

export function t(key: string, locale: string = readLocaleCookie()): string {
  const catalog = CATALOGS[locale] ?? CATALOGS.en;
  return catalog[key] ?? CATALOGS.en[key] ?? key;
}
```

```tsx
// web/src/routes/config.tsx — replacing the hardcoded head()
import { t } from "@/lib/head-i18n";

export const Route = createFileRoute("/config")({
  head: () => ({
    meta: [
      { title: t("config.head.title") },                       // new key only if missing
      { name: "description", content: t("config.head.description") },
    ],
  }),
  // … rest unchanged
});
```

If `config.head.title` and `config.head.description` already exist
under a different name (likely candidates: `config.heading`,
`config.lede`, `nav.config`), reuse those keys verbatim and log the
chosen mapping in the spec response.

## Tokens / data

No new tokens. No data changes.

## i18n

```yaml
locales_required: [en, fr, pt-BR, es-MX, de, uk]
rtl_mirroring: not_applicable
copy_keys: existing_only
```

**Hard rule**: this spec adds zero new copy keys. If audit shows a
route lacks a per-route copy key suitable for the `<title>` slot,
stop and request the key explicitly. PLAN §11 forbids loose new
strings during structural work.

## a11y

```yaml
contrast: not_applicable
focus_visible: not_applicable
keyboard: not_applicable
aria_live: not_applicable
reduced_motion: not_applicable
```

`<head>` content is not user-visible.

## Out of scope

- Per-route OpenGraph / Twitter meta tags
- Dynamic `<title>` for parameterized routes
  (`/cases/:id`, `/encode/:batchId`, `/screen/:jurisdictionId`) —
  track separately
- Per-locale URL canonicalization (`<link rel="canonical">`,
  `hreflang` alternates) — separate spec
- Crawl-friendly `robots` / `noindex` posture — separate spec
- Adding head() hooks to routes that don't have one yet (the audit
  step expects every Phase 6 route already has one; if any are
  missing, surface and stop, do not invent)

provenance: hybrid
  # Page surfaces are unchanged; this is purely a meta-string
  # alignment, no provenance shift.
