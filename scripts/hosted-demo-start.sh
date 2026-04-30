#!/bin/bash
# v2.1 hosted-demo supervisor — resilient against child death.
#
# Two known killers we have to survive (researched 2026-04-30, see
# docs/v2.1-deploy-test-2026-04-29.md "Post-deploy stability" section):
#
#   1. vite dev's growing memory pressure crashes its child after ~20-30s of
#      a 253-request cold-load page (vite issues #21473, #6815, #8341 — the
#      module graph never GCs and chokidar holds growing FD pressure).
#   2. HF Spaces free-tier sends an unexplained SIGTERM 3-5 minutes after
#      launch (https://discuss.huggingface.co/t/133530), reproducible across
#      restarts. HF staff never RCA'd it; community workaround is to make
#      the supervisor resilient instead of preventing the kill.
#
# Strategy: respawn dead children up to MAX_RESPAWNS, then give up and let
# HF restart the whole container. Trap TERM/INT so HF's lifecycle signals
# shut both processes down cleanly instead of leaving zombies.

set -uo pipefail

UVICORN_PID=""
VITE_PID=""
UVICORN_RESPAWNS=0
VITE_RESPAWNS=0
MAX_RESPAWNS=10

log() {
  printf '[demo %s] %s\n' "$(date -u +%FT%TZ)" "$*"
}

start_uvicorn() {
  uvicorn govops.api:app --host 127.0.0.1 --port 8000 --log-level info &
  UVICORN_PID=$!
  log "uvicorn started pid=$UVICORN_PID"
}

start_vite() {
  cd /app/web
  VITE_API_BASE_URL="" \
    VITE_HOSTED_DEMO=1 \
    npm run dev -- --host 0.0.0.0 --port 7860 --strictPort &
  VITE_PID=$!
  log "vite started pid=$VITE_PID"
}

cleanup() {
  log "received TERM/INT — shutting down both children"
  [[ -n "$UVICORN_PID" ]] && kill "$UVICORN_PID" 2>/dev/null || true
  [[ -n "$VITE_PID" ]] && kill "$VITE_PID" 2>/dev/null || true
  exit 0
}
trap cleanup TERM INT

log "booting GovOps v2.1 — uvicorn + vite dev (resilient supervisor)"

start_uvicorn

# Wait up to 30s for the backend to become healthy before starting vite.
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    log "uvicorn healthy after ${i}s"
    break
  fi
  sleep 1
done

start_vite

# Watch loop — respawn whichever child dies, log the death, give up if
# either process burns through its respawn budget (signals a real bug we
# can't paper over).
while true; do
  sleep 5
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    UVICORN_RESPAWNS=$((UVICORN_RESPAWNS + 1))
    log "uvicorn died (respawn $UVICORN_RESPAWNS/$MAX_RESPAWNS)"
    if [[ "$UVICORN_RESPAWNS" -ge "$MAX_RESPAWNS" ]]; then
      log "uvicorn respawn budget exhausted — exiting container"
      cleanup
    fi
    start_uvicorn
  fi
  if ! kill -0 "$VITE_PID" 2>/dev/null; then
    VITE_RESPAWNS=$((VITE_RESPAWNS + 1))
    log "vite died (respawn $VITE_RESPAWNS/$MAX_RESPAWNS)"
    if [[ "$VITE_RESPAWNS" -ge "$MAX_RESPAWNS" ]]; then
      log "vite respawn budget exhausted — exiting container"
      cleanup
    fi
    start_vite
  fi
done
