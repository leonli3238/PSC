#!/usr/bin/env bash
# CSCWD feedback ablation: does the checker's diagnosis help the curator, or do the checks alone do the work?
# Three arms with the CS9 settings (Qwen3-8B thinking curator, temperature 0.6, prompt core generic, per-node
# architecture α from cs0, simulated choice, own-row check, ε = 2) that differ only in what a redraft's prompt
# shows of the rejected drafts (run_dsl_design_eval.py --feedback):
#   full    every rejected draft with the checker's diagnosis (the CertiCount loop)
#   binary  every rejected draft with the bare verdict "rejected"
#   none    nothing: every draft is an independent sample of the first prompt (matched resampling)
# Same budget in every arm: 3 drafts per release (rows, matrix), so at most 6 calls per design; tighten 0 in
# every arm (a tighten request is feedback). Tasks triangle (main task) and triangle-edge (lowest first-try
# rate in CS9) on CU, ML, EE, 30 designs per cell, 20 code runs per accepted design.
#
#   scripts/run_cscwd_fb.sh all        check, dry run, the six (arm, task) stages in parallel, summary
#   scripts/run_cscwd_fb.sh stage <arm> <task>   one stage (resumable: rerun the same command)
#   scripts/run_cscwd_fb.sh summary    results/reports/fb_ablation.md
#
# Extension batch (the primary comparison full vs none on the other three datasets, new directories
# fb_<arm>_<task>_ext that the summary pools with the first batch):
#   ARMS="full none" DATASETS=PM,Do,CS SUFFIX=_ext scripts/run_cscwd_fb.sh all
#
# Needs the Qwen3-8B server of scripts/run_cs9.sh serve (port 8003, max_model_len 32768).
# Every command is appended to results/logs/cscwd_commands.log; stage logs in results/logs/fb_<arm>_<task>.log.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-../.venv/bin/python}
URL_8B=${URL_8B:-http://127.0.0.1:8003/v1}
LOG=$PWD/results/logs/cscwd_commands.log
mkdir -p results/logs results/reports
export VLLM_CURATOR_BASE_URL=$URL_8B VLLM_NODE_BASE_URL=$URL_8B

EPS=2.0
MAXLEN=32768
CFG_DESIGN=configs/vllm_qwen3-8b-think_design.toml
ALPHA_FILE=results/execution/cs0_alpha_selection.json
DATASETS=${DATASETS:-CU,ML,EE}
DESIGNS=${DESIGNS:-30}
RUNS=${RUNS:-20}
CONC=${CONC:-8}
ARMS=${ARMS:-full binary none}
TASKS=${TASKS:-triangle triangle-edge}
SUFFIX=${SUFFIX:-}
export ARMS TASKS SUFFIX DATASETS DESIGNS RUNS CONC  # the stages are this script run again

tag() { echo "fb_${1}_${2//-/_}${SUFFIX}"; }  # fb_<arm>_<task><suffix>
run() {
  local rev; rev=$(git rev-parse --short HEAD)$(git -C "$(git rev-parse --show-toplevel)" diff --quiet HEAD || echo "-dirty")
  printf '%s git=%s cwd=%s VLLM_CURATOR_BASE_URL=%s %s\n' "$(date -u +%FT%TZ)" "$rev" "$(pwd)" "$VLLM_CURATOR_BASE_URL" "$*" >> "$LOG"
  echo "+ $*"
  "$@"
}
alpha() {
  [ -f "$ALPHA_FILE" ] || { echo "missing $ALPHA_FILE" >&2; exit 1; }
  "$PY" -c "import json; print(json.load(open('$ALPHA_FILE'))['alpha'])"
}
maxlen() {
  curl -sf -m 5 "$URL_8B/models" 2>/dev/null \
    | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["data"][0].get("max_model_len") or "")' 2>/dev/null || true
}
wait_server() {
  local k=0
  until [ "$(maxlen)" = "$MAXLEN" ]; do
    [ $((k % 30)) = 0 ] && echo "[fb] $(date +%T) waiting for $URL_8B (max_model_len $MAXLEN; start: scripts/run_cs9.sh serve)"
    k=$((k + 1)); sleep 10
  done
}
server_errors() {  # model calls that failed after all retries; an api_error line is a retry that may have succeeded
  [ -f "$1/errors.jsonl" ] || { echo 0; return; }
  "$PY" -c 'import json, sys; print(sum(json.loads(l).get("kind") == "call_failed" for l in open(sys.argv[1]) if l.strip()))' \
    "$1/errors.jsonl"
}
privacy_guard() {
  "$PY" - "$1" <<'EOF' || { echo "PRIVACY CHECK FAILED in $1: stop and report this directory" >&2; exit 3; }
import json, sys
from pathlib import Path
cert = Path(sys.argv[1]) / "certification_ablation" / "summary.json"
bad = sum(row.get("certificate_unsound") or 0 for row in json.loads(cert.read_text())["table"]) if cert.exists() else 0
print(f"privacy guard {sys.argv[1]}: {bad} problem(s)")
sys.exit(1 if bad else 0)
EOF
}
design_args() {  # $1 arm, $2 task
  echo --datasets "$DATASETS" --tasks "$2" --designs "$DESIGNS" --runs "$RUNS" --eps "$EPS" --seed 0 \
    --design-concurrency "$CONC" --provider vllm --config "$CFG_DESIGN" --curator-model Qwen3-8B --temperature 0.6 \
    --node-bounds --clip-alpha "$(alpha)" --prompt generic --select simulated --own-row-check \
    --max-iterations 3 --tighten 0 --feedback "$1" --tag "$(tag "$1" "$2")"
}

stage() {  # $1 arm, $2 task: resumable, redone once if the server was lost
  local arm=$1 task=$2 t d crash=0 n
  t=$(tag "$arm" "$task"); d="results/dsl_eval/$t"
  for attempt in 1 2; do
    until [ -f "$d/table.md" ]; do
      wait_server
      # shellcheck disable=SC2046
      if [ -f "$d/manifest.json" ]; then
        run "$PY" scripts/run_dsl_design_eval.py $(design_args "$arm" "$task") --resume && continue
      else
        [ -d "$d" ] && mv "$d" "$d.incomplete-$(date -u +%Y%m%dT%H%M%SZ)"
        run "$PY" scripts/run_dsl_design_eval.py $(design_args "$arm" "$task") && continue
      fi
      crash=$((crash + 1))
      [ "$crash" -ge 3 ] && { echo "[fb] $t crashed $crash times: stop" >&2; exit 7; }
      echo "[fb] $(date -u +%FT%TZ) $t crashed (attempt $crash); resuming in 60 s" >&2
      sleep 60
    done
    n=$(server_errors "$d")
    if [ "$n" -gt 0 ]; then
      [ "$attempt" = 2 ] && { echo "[fb] $t lost the server again ($n failed calls): stop, see $d/errors.jsonl" >&2; exit 6; }
      echo "[fb] $t lost the server ($n calls failed after all retries): moving it aside and redoing it" >&2
      mv "$d" "$d.serverdown-$(date -u +%Y%m%dT%H%M%SZ)"
      continue
    fi
    break
  done
  [ -f "$d/certification_ablation/table.md" ] || run "$PY" scripts/analyze_design_certification.py "$d" --allow-missing
  privacy_guard "$d"
  echo "[fb] $(date -u +%FT%TZ) done: $t"
}

cmd=${1:-}
case $cmd in
  check)
    run "$PY" -m pytest tests/test_design_checks.py tests/test_selection.py -q -p no:cacheprovider ;;
  dry)
    for arm in $ARMS; do for task in $TASKS; do
      # shellcheck disable=SC2046
      run "$PY" scripts/run_dsl_design_eval.py $(design_args "$arm" "$task") --dry-run
    done; done ;;
  stage)
    stage "$2" "$3" ;;
  summary)
    run "$PY" scripts/summarize_fb_ablation.py --out results/reports/fb_ablation.md ;;
  all)
    echo "[fb] $(date -u +%FT%TZ) start"
    "$0" check
    "$0" dry
    pids=()
    for arm in $ARMS; do for task in $TASKS; do
      "$0" stage "$arm" "$task" > "results/logs/$(tag "$arm" "$task").log" 2>&1 &
      pids+=($!)
      echo "[fb] started $(tag "$arm" "$task") (pid $!, log results/logs/$(tag "$arm" "$task").log)"
      sleep 20
    done; done
    fail=0
    for p in "${pids[@]}"; do wait "$p" || fail=$((fail + 1)); done
    echo "[fb] $(date -u +%FT%TZ) stages finished, $fail failed"
    "$0" summary || true
    echo "[fb] $(date -u +%FT%TZ) done: results/reports/fb_ablation.md" ;;
  *)
    sed -n '2,20p' "$0"; exit 2 ;;
esac
