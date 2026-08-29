#!/usr/bin/env bash
# Run on the PI. Uses the laptop's Gemma through the tunnel if present, else the local Ollama.
cd "$(dirname "$0")/../hub" && . .venv/bin/activate
if curl -s -m 2 http://127.0.0.1:11435/api/tags >/dev/null; then export OLLAMA_URL=http://127.0.0.1:11435; echo "using laptop Gemma via tunnel"; else export GEMMA_MODEL=${GEMMA_MODEL:-gemma3n:e2b}; echo "using local $GEMMA_MODEL"; fi
exec python -m viral.server "$@"
