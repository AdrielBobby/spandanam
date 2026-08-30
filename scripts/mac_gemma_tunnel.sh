#!/usr/bin/env bash
# Run on the LAPTOP. Exposes the laptop's Ollama (with gemma3n:e4b) to the Pi as http://127.0.0.1:11435 via a reverse SSH tunnel.
# No firewall changes needed. Then on the Pi:  OLLAMA_URL=http://127.0.0.1:11435 python -m viral.server
# Mac dashboard with both engines:  GEMMA_ENGINES="laptop=http://127.0.0.1:11434|gemma3n:e4b,pi=http://127.0.0.1:11436|gemma3:1b" python -m viral.server --dry
PI=${1:-ryyan@192.168.11.93}
pgrep -x ollama >/dev/null || (nohup ollama serve >/tmp/ollama_serve.log 2>&1 &) && sleep 2
# -R: Pi sees the laptop's Ollama at 127.0.0.1:11435   -L: laptop sees the Pi's Ollama at 127.0.0.1:11436 (for the engine selector on the Mac dashboard)
exec ssh -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -N -R 11435:127.0.0.1:11434 -L 11436:127.0.0.1:11434 "$PI"
