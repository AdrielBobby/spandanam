#!/usr/bin/env bash
# Run on the LAPTOP. Keeps a two-way SSH tunnel to the Pi alive (retries every 5 s):
#   -R 11435: Pi reaches the laptop's Ollama (gemma3n:e4b) at http://127.0.0.1:11435
#   -L 11436: laptop reaches the Pi's Ollama (gemma2:2b) at http://127.0.0.1:11436
PI=${1:-ryyan@192.168.11.93}
pgrep -x ollama >/dev/null || (nohup ollama serve >/tmp/ollama_serve.log 2>&1 &) && sleep 2
while true; do
  # free a stale remote listener left by a dead tunnel, then connect
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$PI" 'P=$(sudo ss -ltnp 2>/dev/null | grep ":11435 " | grep -oE "pid=[0-9]+" | head -1 | cut -d= -f2); [ -n "$P" ] && sudo kill $P' 2>/dev/null
  ssh -o BatchMode=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes \
      -N -R 11435:127.0.0.1:11434 -L 11436:127.0.0.1:11434 "$PI"
  echo "$(date +%H:%M:%S) tunnel dropped, retrying in 5 s" >&2
  sleep 5
done
