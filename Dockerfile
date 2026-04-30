# GovOps v2.1 — single-container hosted demo image (HF Spaces / generic Docker)
#
# Two processes inside the container, supervised by a tiny shell wrapper:
#   1. uvicorn → FastAPI on internal port 8000
#      Serves /api/* (the JSON API + LLM proxy + admin GC) plus the Jinja
#      legacy fallback UI at "/jinja/*"
#   2. vite dev server → TanStack Start (React) on port 7860 (HF Spaces requirement)
#      Serves the v2 React UI at "/" and proxies /api/* to uvicorn via
#      VITE_API_BASE_URL
#
# Why vite dev (not the production build): the @lovable.dev/vite-tanstack-config
# preset emits a Cloudflare Workers bundle (uses worker-entry, wrangler.json,
# nodejs-compat shims) that needs the Workers runtime to execute. Running the
# vite dev server in the container is the simplest way to ship a working v2 UI
# without rewriting the build target. HF Spaces' 16 GB RAM is more than enough
# for the dev server's HMR overhead. A future commit can switch to a real Node
# SSR target if the perf cost matters; for an MVP free-tier demo this is fine.
#
# Required env vars (set as Space secrets — see DEPLOY.md):
#   DEMO_ADMIN_TOKEN=...                 (any random string)
#   GROQ_API_KEY=...                     (at least one provider required)
#   OPENROUTER_API_KEY=...               (recommended — fail-over)
#   GEMINI_API_KEY=...                   (optional — fail-over)
#   MISTRAL_API_KEY=...                  (optional — fail-over)
# Vars BAKED INTO the image (do NOT add as Space secrets — collision):
#   GOVOPS_DEMO_MODE=1, GOVOPS_SEED_DEMO=1, GOVOPS_DB_PATH=/data/govops.db,
#   PORT=7860, LLM_PROVIDERS=groq,openrouter,gemini,mistral

FROM python:3.12-slim-bookworm AS runtime

# Install Node.js (for vite dev) + curl for healthchecks
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps first — pyproject + src for layer cache
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Static lawcode YAML + schemas the runtime reads
COPY lawcode/ ./lawcode/
COPY schema/ ./schema/

# Web source — vite dev needs the full source, not just dist/
COPY web/ ./web/
RUN cd /app/web && npm ci --no-audit --no-fund || cd /app/web && npm install --no-audit --no-fund

# Persistent SQLite path (HF Spaces persistent disk lives at /data on paid
# Spaces; on free Spaces, /data isn't persistent across restarts but the
# substrate re-hydrates from lawcode/ on every cold-boot per ADR-010)
RUN mkdir -p /data
ENV GOVOPS_DB_PATH=/data/govops.db
ENV GOVOPS_DEMO_MODE=1
ENV GOVOPS_SEED_DEMO=1
# Tell vite.config.ts that this is the hosted-demo container. Two effects:
#   1. server.hmr=false   — HF's proxy closes idle websockets, vite's reconnect
#                           path puts the page in a broken state mid-session
#   2. server.watch.ignored=["**"]  — chokidar's growing FD/heap is one of the
#                           known vite-dev memory crash patterns (vite #8341)
# Local dev (env unset) keeps both at vite defaults.
ENV VITE_HOSTED_DEMO=1
# HF Spaces requires the public process to listen on 0.0.0.0:7860
ENV PORT=7860
EXPOSE 7860

# Resilient supervisor — see scripts/hosted-demo-start.sh for the full
# rationale. Respawns dead children instead of letting one death kill the
# container, which survives both vite-dev memory crashes (~20-30s) and the
# HF Spaces free-tier random SIGTERM at 3-5min.
COPY scripts/hosted-demo-start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
