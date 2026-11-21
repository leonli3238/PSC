#!/usr/bin/env bash
# CS8 vLLM servers only (start / switch / stop); the experiments run separately with scripts/cs8_exp.sh.
#   scripts/cs8_llm.sh psc      8B (port 8003, 16k, MEM 0.55) + 1.7B (port 8001, 32k, MEM 0.90 cumulative)
#   scripts/cs8_llm.sh cc       8B alone (port 8003, 32k, MEM 0.90); stops the PSC servers first
#   scripts/cs8_llm.sh status   what answers on 8003 / 8001, GPU memory
#   scripts/cs8_llm.sh stop     stop the servers started by these scripts
# Returns once the servers answer; they keep running in their own session (Ctrl+C does not stop them).
# Logs: results/logs/cs8_serve_{8b,1.7b}.log. Environment: VLLM_BIN, MODELS (defaults below), URL_8B, URL_17B, PY.
set -euo pipefail
cd "$(dirname "$0")/.."

export VLLM_BIN=${VLLM_BIN:-/jizhicfs/leonlanli/envs/vllm/bin/vllm}
export MODELS=${MODELS:-/jizhicfs/leonlanli/models}
export URL_8B=${URL_8B:-http://127.0.0.1:8003/v1}
export URL_17B=${URL_17B:-http://127.0.0.1:8001/v1}
PY=${PY:-../.venv/bin/python}

maxlen() {  # $1 url: max_model_len of the served model, empty if nothing answers
  curl -sf -m 5 "$1/models" 2>/dev/null \
    | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["data"][0].get("max_model_len") or "")' 2>/dev/null || true
}
free_ports() {  # stop our servers, then make sure nothing else holds the ports
  bash scripts/run_cs8.sh stop
  for u in "$URL_8B" "$URL_17B"; do
    [ -z "$(maxlen "$u")" ] || { echo "$u still answers (not started by these scripts?): stop it by hand" >&2; exit 1; }
  done
}
stop_17b() {  # stop only the 1.7B started by these scripts (the 8B keeps serving)
  local f=results/cs8_state/serve_1.7b.pid pid
  if [ -f "$f" ]; then
    pid=$(cat "$f")
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 60); do kill -0 "$pid" 2>/dev/null || break; sleep 2; done
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$f"
  fi
  for _ in $(seq 30); do [ -z "$(maxlen "$URL_17B")" ] && break; sleep 2; done
  [ -z "$(maxlen "$URL_17B")" ] || { echo "$URL_17B still answers (not started by these scripts?): stop it by hand" >&2; exit 1; }
  sleep 10   # let the GPU memory go
}

status() {
  for u in "$URL_8B" "$URL_17B"; do
    l=$(maxlen "$u"); if [ -n "$l" ]; then echo "$u: up, max_model_len $l"; else echo "$u: down"; fi
  done
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null || true
}

cmd=${1:-}
case $cmd in
  psc|cc)
    command -v "$VLLM_BIN" >/dev/null || { echo "vLLM not found: $VLLM_BIN (set VLLM_BIN)" >&2; exit 1; }
    [ -d "$MODELS/Qwen3-8B" ] || { echo "missing $MODELS/Qwen3-8B (set MODELS)" >&2; exit 1; }
    l8=$(maxlen "$URL_8B"); l17=$(maxlen "$URL_17B")
    if [ "$cmd" = psc ]; then
      [ -d "$MODELS/Qwen3-1.7B" ] || { echo "missing $MODELS/Qwen3-1.7B (set MODELS)" >&2; exit 1; }
      [ "$l8" = 16384 ] && [ "$l17" = 32768 ] && { echo "PSC servers already up"; exit 0; }
      if [ -n "$l8" ] && [ "$l8" != 16384 ]; then
        echo "8B served with max_model_len $l8: restarting both for PSC"; free_ports
      elif [ -n "$l17" ] && [ "$l17" != 32768 ]; then
        echo "1.7B served with max_model_len $l17: restarting the 1.7B only"; stop_17b
      fi
      bash scripts/run_cs8.sh serve-psc
    else
      [ "$l8" = 32768 ] && [ -z "$l17" ] && { echo "CertiCount server already up"; exit 0; }
      free_ports
      bash scripts/run_cs8.sh serve-cc
    fi
    status ;;

  status)
    status ;;

  stop)
    bash scripts/run_cs8.sh stop
    status ;;

  *)
    sed -n '2,8p' "$0"; exit 2 ;;
esac
