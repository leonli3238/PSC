#!/usr/bin/env bash
# Degree violation probe on one GPU (H20): serve a local model with vLLM and run the stages of
# scripts/run_degree_probe.py.  Run from certicount/.  Every stage is resumable (rerun = continue).
#
#   VLLM_BIN=/opt/vllm-env/bin/vllm MODELS=/models scripts/probe_h20.sh serve 1.7b      # foreground server
#   scripts/probe_h20.sh wait 1.7b                 # block until the server answers
#   scripts/probe_h20.sh offline                   # tests + mock negative controls (no GPU)
#   scripts/probe_h20.sh pilot 1.7b                # init + pilot, prints the time forecast
#   scripts/probe_h20.sh main 1.7b                 # screen + confirm main (top 40) + confirm random
#   scripts/probe_h20.sh transfer 8b               # confirm the 1.7B violations + same random pairs
#   scripts/probe_h20.sh rescreen 8b [N]           # independent hub screen (N = max pairs per node, default all)
#   scripts/probe_h20.sh boundary 8b               # screen if missing + diversified top 40 + node-level design
#   scripts/probe_h20.sh report 1.7b 4b 8b         # cross-model tables, joint Bonferroni over all sets
#
# Environment: PY (project python), VLLM_BIN, MODELS (model directories), OUT (result root).
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-../.venv/bin/python}
VLLM_BIN=${VLLM_BIN:-vllm}
MODELS=${MODELS:-/models}
OUT=${OUT:-results/audit/sensitivity}
SRC=${SRC:-1.7b}          # model whose confirmed pairs are transferred
CONC=${CONC:-128}

model_dir()  { case $1 in 1.7b) echo "$MODELS/Qwen3-1.7B";; 4b) echo "$MODELS/Qwen3-4B-Instruct-2507";; 8b) echo "$MODELS/Qwen3-8B";; *) echo "unknown model $1" >&2; exit 2;; esac; }
served()     { case $1 in 1.7b) echo Qwen3-1.7B;; 4b) echo Qwen3-4B;; 8b) echo Qwen3-8B;; esac; }
port()       { case $1 in 1.7b) echo 8001;; 4b) echo 8002;; 8b) echo 8003;; esac; }
config()     { case $1 in 1.7b) echo configs/vllm_probe_qwen3-1.7b.toml;; 4b) echo configs/vllm_probe_qwen3-4b-instruct.toml;; 8b) echo configs/vllm_probe_qwen3-8b.toml;; esac; }
rundir()     { echo "$OUT/probe_pm_degree_qwen3-$1"; }
url()        { echo "http://127.0.0.1:$(port "$1")/v1"; }
probe()      { "$PY" scripts/run_degree_probe.py "$@"; }

init_run() {  # $1 model; the first model builds the plan, the others copy it
  local m=$1 d; d=$(rundir "$m")
  [ -f "$d/settings.json" ] && return 0
  local from=()
  if [ "$m" != "$SRC" ]; then from=(--plan-from "$(rundir "$SRC")"); fi
  probe init --out "$d" "${from[@]}" --provider vllm --config "$(config "$m")" \
    --node-model "$(served "$m")" --base-url "$(url "$m")" --concurrency "$CONC"
}

cmd=${1:-}; shift || true
case $cmd in
  serve)
    m=$1
    exec "$VLLM_BIN" serve "$(model_dir "$m")" --served-model-name "$(served "$m")" \
      --max-model-len 8192 --enable-prefix-caching --gpu-memory-utilization 0.90 \
      --max-num-seqs 256 --host 127.0.0.1 --port "$(port "$m")" ;;
  wait)
    m=$1
    until curl -sf "http://127.0.0.1:$(port "$m")/v1/models" >/dev/null; do sleep 10; done
    curl -s "http://127.0.0.1:$(port "$m")/v1/models"; echo ;;
  offline)
    "$PY" -m pytest tests -q
    for mode in exact bias edge; do
      d=$OUT/_probe_mock_$mode
      [ -f "$d/settings.json" ] || probe init --out "$d" --provider mock --mock-mode "$mode" --mock-trigger 7
      probe screen --out "$d"
      if [ -s "$d/screen/candidates.jsonl" ]; then probe confirm --out "$d" --name main --pairs top:40; fi
      probe confirm --out "$d" --name random --pairs random
    done
    echo "expected: exact/bias 0 violations everywhere; edge: violations only on flips of vertex 7" ;;
  pilot)
    init_run "$1"; probe pilot --out "$(rundir "$1")" ;;
  main)
    init_run "$1"; d=$(rundir "$1")
    probe screen --out "$d"
    if [ -s "$d/screen/candidates.jsonl" ]; then probe confirm --out "$d" --name main --pairs top:40
    else echo "no screen candidate (|Δ| > 1 never observed): report the screen tables"; fi
    probe confirm --out "$d" --name random --pairs random ;;
  transfer)
    init_run "$1"; d=$(rundir "$1"); src=$(rundir "$SRC")/confirm_main
    if [ -s "$src/confirmed.jsonl" ]; then probe confirm --out "$d" --name transfer --pairs "confirmed:$src" --select 30
    else echo "no confirmed violation in $src: nothing to transfer"; fi
    probe confirm --out "$d" --name random --pairs random --select 30 ;;
  rescreen)
    init_run "$1"; d=$(rundir "$1"); cap=${2:-}
    probe screen --out "$d" --only hub ${cap:+--max-per-node "$cap"}
    if [ -s "$d/screen/candidates.jsonl" ]; then probe confirm --out "$d" --name rescreen --pairs top:40; fi ;;
  boundary)
    # full screen of this model if missing, then the diversified top-40 (≤ 2 pairs per node) and the
    # node-level design (one most suspicious pair per selected node)
    init_run "$1"; d=$(rundir "$1")
    [ -s "$d/screen/pairs.jsonl" ] || probe screen --out "$d"
    if [ -s "$d/screen/candidates.jsonl" ]; then
      probe confirm --out "$d" --name main_div --pairs top:40 --per-node 2
      probe confirm --out "$d" --name nodes --pairs nodes
    else echo "no screen candidate for $1"; fi ;;
  report)
    runs=(); for m in "$@"; do runs+=("$(rundir "$m")"); done
    probe report --runs "${runs[@]}" --report-dir "$OUT/probe_pm_degree_report" --family-alpha 0.05 ;;
  *) sed -n '2,15p' "$0"; exit 2 ;;
esac
