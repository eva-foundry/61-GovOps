// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - tanstackStart, viteReact, tailwindcss, tsConfigPaths, cloudflare (build-only),
//     componentTagger (dev-only), VITE_* env injection, @ path alias, React/TanStack dedupe,
//     error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... } }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

// `allowedHosts` opens the dev server to non-localhost callers — required when
// the dev server is the public-facing process inside the v2.1 hosted-demo
// container (Dockerfile runs `npm run dev -- --host 0.0.0.0`). Without this,
// vite refuses requests with a Host header that doesn't match its known list
// and returns 403 to anyone hitting the HF Space URL. Local dev is unaffected
// (localhost is always allowed).
//
// `hmr: false` (gated on VITE_DISABLE_HMR=1, set in the Dockerfile) is the
// fix for the v2.1 hosted-demo "time-based crash": HF Spaces' reverse proxy
// closes idle websockets after ~30s, vite's client tries to reconnect, and
// the page can end up in a broken mid-session state. HMR has zero value in a
// deployed demo — disabling it removes the failure surface entirely. Local
// dev keeps HMR (env unset → undefined → vite default behaviour).
const disableHmr = process.env.VITE_DISABLE_HMR === "1";

export default defineConfig({
  vite: {
    server: {
      allowedHosts: [
        "agentic-state-govops-lac.hf.space",
        ".hf.space", // future-proof for any HF Space URL pattern
      ],
      hmr: disableHmr ? false : undefined,
      // Reverse-proxy /api/* to the FastAPI backend running on the same
      // container at port 8000. Without this, vite would serve the SPA
      // index.html for /api/* requests (its catch-all SPA fallback) and the
      // browser would never reach the JSON API. Enabled in dev only — the
      // Dockerfile is the only consumer that needs it (local dev uses two
      // separate ports per CONTRIBUTING.md and doesn't go through this
      // proxy).
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        },
      },
    },
  },
});
