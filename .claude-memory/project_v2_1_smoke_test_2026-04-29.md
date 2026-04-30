---
name: v2.1 hosted-demo smoke test 2026-04-29
description: 35/35 curl pass; 2 browser-only bugs caught after-the-fact; lesson on parameterised UI routes
type: project
stage: 2
last_referenced: 2026-04-30
---

# v2.1 hosted-demo smoke test 2026-04-29

35/35 endpoint smoke test passed clean against the HF Space (image `b08779c`, source `fc19f64`). Then a manual browser pass through the app surfaced two bugs the curl-only test missed.

**Lesson**: parameterised UI routes need their own pass. Static `/cases` (the list route) is NOT the same as `/cases/demo-case-001` (the detail route). Curl was hitting the API endpoints directly, not the SSR loader paths. The browser pass exercised the SSR route loaders.

Both fixed in `f3c1a64` (post-smoke-test commit).

## Bug 1 -- `/cases/demo-case-001` returned 500 (SSR loader couldn't reach the API)

**Symptom**: clicking a case from the `/cases` list loaded a 500-status SSR page; React app never mounted; inline `$_TSR.e` payload contained `Error("Case demo-case-001 not found")`.

**Reproduction**: `curl -i "$BASE/cases/demo-case-001"` -> HTTP/1.1 500.

**Root cause**: the earlier `VITE_API_BASE_URL=""` fix (`fc19f64`) made browser-side fetches use same-origin relative URLs (correct, since Vite's dev proxy forwards `/api/*` to FastAPI). But the same `BASE=""` was being read by the **server-side SSR Node process** when it pre-rendered route loaders. Node's `fetch()` cannot resolve relative URLs. The route loader threw, the error boundary returned "not found".

**Fix**: branch on `import.meta.env.SSR`. Server-side always uses `http://127.0.0.1:8000` (FastAPI on container loopback); browser-side honours `VITE_API_BASE_URL` (empty -> relative).

```ts
// web/src/lib/api.ts
const BASE = import.meta.env.SSR
  ? "http://127.0.0.1:8000"
  : ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8000");
```

## Bug 2 -- JP missing from screen allowlist

The 7th jurisdiction (Japan) shipped to the engine but was not added to `SCREEN_JURISDICTIONS`, so `/screen/jp` 404'd even though `/api/jurisdiction/jp` and the engine itself worked.

**Fix**: add JP to the screen allowlist in the same commit (`f3c1a64`).

## Pattern to remember

- **Test the SSR route, not just the API endpoint** for any TanStack Start surface. `curl /api/cases/X` ≠ `curl /cases/X` -- the latter exercises the SSR loader.
- **Allowlists are easy to miss** when adding a jurisdiction or program. Have a CI parity test that asserts the engine's `JURISDICTION_REGISTRY` matches every allowlist downstream.
- **Same source code, different runtimes** (browser vs Node SSR) is a real bug-class for Vite-based SSR. `import.meta.env.SSR` is the discriminator.

## Why this lives in memory

This pair of bugs is the canonical example of "the curl-pass said it worked, the browser-pass said it didn't." Anyone running a smoke test against a future deploy of GovOps should read this first and add a parameterised-route browser pass to their checklist. The bugs are fixed; the lesson should not have to be relearned.

## Reference

- `docs/v2.1-deploy-test-2026-04-29.md` -- runbook + result trail (uncommitted local edits add the post-curl-pass section that documents both bugs in long form; that file is the durable record, this memory entry is the index pointer)
- Commit `f3c1a64` -- the fix
