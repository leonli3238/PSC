#!/usr/bin/env bash
# CS8 experiments only; the vLLM servers are managed by scripts/cs8_llm.sh and are never started or stopped here.
#   scripts/cs8_exp.sh code    code references (GT-PSC / GT-DSL / GT-DSL-node), CPU only, no server
#   scripts/cs8_exp.sh psc     needs `cs8_llm.sh psc`: psc-pilot, psc, psc-decomp
#   scripts/cs8_exp.sh cc      needs `cs8_llm.sh cc`:  cc-pm, cc-cudo, cc-mlcsee
# Order:  cs8_llm.sh psc -> cs8_exp.sh psc -> cs8_llm.sh cc -> cs8_exp.sh cc -> cs8_llm.sh stop  (code: any time)
# Stops at the first failing stage; rerun the same command to resume (finished stages are skipped).
# Environment: as run_cs8.sh (DESIGNS_NEW, MIN_ACCEPT, FORCE, URL_8B, URL_17B, PY).
set -euo pipefail
cd "$(dirname "$0")/.."

export URL_8B=${URL_8B:-http://127.0.0.1:8003/v1}
export URL_17B=${URL_17B:-http://127.0.0.1:8001/v1}
PY=${PY:-../.venv/bin/python}

maxlen() {  # $1 url: max_model_len of the served model, empty if nothing answers
  curl -sf -m 5 "$1/models" 2>/dev/null \
    | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["data"][0].get("max_model_len") or "")' 2>/dev/null || true
}
require() {  # $1 url, $2 wanted max_model_len, $3 cs8_llm.sh mode
  local l; l=$(maxlen "$1")
  [ "$l" = "$2" ] || { echo "need $1 with max_model_len $2 (now: ${l:-down}); run: bash scripts/cs8_llm.sh $3" >&2; exit 1; }
}
stages() {
  for s in "$@"; do
    echo "[cs8] $(date +%FT%T) $s"
    bash scripts/run_cs8.sh "$s" || { rc=$?; echo "[cs8] $s failed (exit $rc)" >&2; exit "$rc"; }
  done
  echo "[cs8] $(date +%FT%T) finished: $*"
}

cmd=${1:-}
case $cmd in
  code)
    stages code ;;
  psc)
    require "$URL_8B" 16384 psc; require "$URL_17B" 32768 psc
    stages psc-pilot psc psc-decomp ;;
  cc)
    require "$URL_8B" 32768 cc
    stages cc-pm cc-cudo cc-mlcsee ;;
  *)
    sed -n '2,8p' "$0"; exit 2 ;;
esac
