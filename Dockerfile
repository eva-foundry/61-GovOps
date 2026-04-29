# GovOps v2.1 — single-container hosted demo image (HF Spaces / generic Docker)
#
# Two processes inside the container, supervised by a tiny shell wrapper:
#   1. uvicorn → FastAPI on internal port 8000
#      Serves /api/* (the JSON API + LLM proxy + admin GC) plus the Jinja
#      legacy fallback UI at "/jinja/*"
#   2. node    → TanStack Start SSR server on port 7860 (HF Spaces requirement)
#      Serves the v2 React UI at "/" and reverse-proxies "/api/*" to uvicorn
#
# Why two processes (Plan §5 said "SPA build, FastAPI serves StaticFiles" —
# revised here): TanStack Start's production build is SSR-only and does not
# emit a standalone index.html. Configuring a static SPA fork would break the
# SSR-dependent features the v2 product already relies on (locale-aware
# <head>, route-level data loaders, etc.). HF Spaces' 16 GB RAM budget makes
# the second process a non-issue for a free-tier demo.
#
# Required env vars (set as Space secrets — see DEPLOY.md):
#   GOVOPS_DEMO_MODE=1
#   DEMO_ADMIN_TOKEN=...                 (any random string)
#   GROQ_API_KEY=...                     (at least one provider required)
#   OPENROUTER_API_KEY=...               (recommended — fail-over)
#   GEMINI_API_KEY=...                   (optional — fail-over)
#   MISTRAL_API_KEY=...                  (optional — fail-over)

FROM node:20-bookworm-slim AS web-build
WORKDIR /web
# Install web deps first for layer-cache friendliness
COPY web/package.json web/package-lock.json* web/bun.lockb* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
# Copy the web source and build the production SSR bundle
COPY web/ ./
ENV VITE_API_BASE_URL=""
ENV VITE_DEMO_MODE=1
RUN npm run build

# ---------------------------------------------------------------------------

FROM python:3.12-slim-bookworm AS runtime

# Install Node.js (for serving the TanStack SSR bundle) + curl for healthchecks
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps — copy pyproject first for layer cache
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Web build artefacts from the previous stage
COPY --from=web-build /web/dist ./web/dist
COPY --from=web-build /web/node_modules ./web/node_modules
COPY web/package.json ./web/package.json
COPY web/start.config.ts* ./web/
COPY web/vite.config.ts ./web/

# Static lawcode YAML + schemas + docs the runtime reads
COPY lawcode/ ./lawcode/
COPY schema/ ./schema/

# Persistent SQLite path (HF Spaces persistent disk lives at /data on paid
# Spaces; on free Spaces, /data isn't persistent across restarts but the
# substrate re-hydrates from lawcode/ on every cold-boot per ADR-010)
RUN mkdir -p /data
ENV GOVOPS_DB_PATH=/data/govops.db
ENV GOVOPS_DEMO_MODE=1
ENV GOVOPS_SEED_DEMO=1
# HF Spaces requires the public process to listen on 0.0.0.0:7860
ENV PORT=7860
EXPOSE 7860

# Tiny supervisor: starts uvicorn (8000, internal) + node SSR (7860, public).
# If either dies, the script exits → HF Spaces auto-restarts the whole
# container. Acceptable for a free-tier MVP demo.
RUN printf '#!/bin/bash\n\
set -e\n\
echo "[demo] booting GovOps v2.1 — uvicorn + TanStack SSR"\n\
\n\
# 1. Backend on internal port 8000\n\
uvicorn govops.api:app --host 127.0.0.1 --port 8000 --log-level warning &\n\
UVICORN_PID=$!\n\
\n\
# 2. Wait for backend health before starting the SSR (which calls /api/health on boot)\n\
for i in 1 2 3 4 5 6 7 8 9 10; do\n\
  if curl -fsS http://127.0.0.1:8000/api/health > /dev/null; then\n\
    echo "[demo] uvicorn healthy"\n\
    break\n\
  fi\n\
  sleep 1\n\
done\n\
\n\
# 3. Frontend SSR on the public port. Proxy /api → 127.0.0.1:8000 via env.\n\
cd /app/web && \\\n\
  VITE_API_BASE_URL=http://127.0.0.1:8000 \\\n\
  VITE_DEMO_MODE=1 \\\n\
  PORT=7860 \\\n\
  HOST=0.0.0.0 \\\n\
  npm run start &\n\
NODE_PID=$!\n\
\n\
# 4. Wait for either process; exit when either dies\n\
wait -n "$UVICORN_PID" "$NODE_PID"\n\
EXIT_CODE=$?\n\
echo "[demo] one process exited with code $EXIT_CODE — terminating container"\n\
kill "$UVICORN_PID" "$NODE_PID" 2>/dev/null || true\n\
exit "$EXIT_CODE"\n' > /app/start.sh \
  && chmod +x /app/start.sh

CMD ["/app/start.sh"]
