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
# Disable vite HMR in the hosted demo. HF Spaces' reverse proxy closes idle
# websockets after ~30s; with HMR enabled, vite's client tries to reconnect
# and the page falls into a broken mid-session state ("time-based crash").
# HMR has no value in a deployed demo. Local dev (env unset) keeps HMR.
ENV VITE_DISABLE_HMR=1
# HF Spaces requires the public process to listen on 0.0.0.0:7860
ENV PORT=7860
EXPOSE 7860

# Tiny supervisor: starts uvicorn (8000, internal) + vite dev (7860, public).
# If either dies, the script exits → HF Spaces auto-restarts the whole
# container. Acceptable for a free-tier MVP demo.
RUN printf '#!/bin/bash\n\
set -e\n\
echo "[demo] booting GovOps v2.1 — uvicorn + vite dev"\n\
\n\
# 1. Backend on internal port 8000 (info level so request lines reach HF logs)\n\
uvicorn govops.api:app --host 127.0.0.1 --port 8000 --log-level info &\n\
UVICORN_PID=$!\n\
\n\
# 2. Wait for backend health (up to 30s) before starting the frontend.\n\
for i in $(seq 1 30); do\n\
  if curl -fsS http://127.0.0.1:8000/api/health > /dev/null 2>&1; then\n\
    echo "[demo] uvicorn healthy after ${i}s"\n\
    break\n\
  fi\n\
  sleep 1\n\
done\n\
\n\
# 3. Frontend on the public port. Vite dev binds to 0.0.0.0:7860.\n\
cd /app/web && \\\n\
  VITE_API_BASE_URL="" \\\n\
  VITE_DEMO_MODE=1 \\\n\
  npm run dev -- --host 0.0.0.0 --port 7860 --strictPort &\n\
VITE_PID=$!\n\
\n\
# 4. Wait for either process; identify WHICH one died so HF container logs\n\
#    tell us if recurring deaths are uvicorn or vite (different fix paths).\n\
wait -n "$UVICORN_PID" "$VITE_PID"\n\
EXIT_CODE=$?\n\
if ! kill -0 "$UVICORN_PID" 2>/dev/null; then DIED=uvicorn; else DIED=vite; fi\n\
echo "[demo] $DIED died (exit=$EXIT_CODE) at $(date -u +%FT%TZ) - container will restart"\n\
kill "$UVICORN_PID" "$VITE_PID" 2>/dev/null || true\n\
exit "$EXIT_CODE"\n' > /app/start.sh \
  && chmod +x /app/start.sh

CMD ["/app/start.sh"]
