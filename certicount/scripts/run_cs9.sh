#!/usr/bin/env bash
# CS9: (1) prompt-core ablation: does the curator still design the triangle / open-wedge programs when the
# prompt shows no program of them (core generic, leak-checked) instead of the v1-alt rewrites that contain them?
# (2) extension tasks PSC never ran. Settings of the CertiCount arms = CS7/CS8 sim (scripts/run_cs8.sh cc_run):
# Qwen3-8B thinking curator, temperature 0.6, per-node architecture α = 5 (cs0), simulated choice, own-row check,
# tighten 1, ε = 2, 100 runs per accepted design; only --prompt and the tasks change.
#
#   scripts/run_cs9.sh serve    vLLM Qwen3-8B on port 8003 (32k, MEM 0.90) in the foreground, restarted when it
#                               exits (tmux window llm); log results/logs/cs9_serve_8b.log
#   scripts/run_cs9.sh all      every stage below serially (tmux window certi); waits for the server
#
# Stages of `all` (each can also be run alone):
#   check    offline tests of the CS9 code
#   dry      planned model calls
#   g1       generic x triangle, open-wedge         x PM,CU,Do,ML,CS,EE x 20 designs  (ablation; v1-alt triangle = CS7/CS8)
#   g2       generic x degree-ge3, triangle-edge, triangle-node x 6 datasets x 20 designs (extension tasks)
#   g3       generic x 4-cycle x CU,ML,EE x 10 designs  (boundary case: certified, GS about D*dmax)
#   g4       v1-alt  x open-wedge x 6 datasets x 20 designs  (the leaked arm of the open-wedge ablation)
#   code     GT-Naive / GT-Rows / GT-DSL-node / GT-Select of all CS9 tasks, 1000 runs, CPU only, paired with g1-g3
#   summary  results/reports/cs9_summary.md
#
# Resumable: rerun the same command; finished stages are skipped. An interrupted design stage continues with
# run_dsl_design_eval.py --resume (finished dataset/task cells are kept, the cell that was running is redone);
# another half-written directory is moved to <dir>.incomplete-<time> and redone. A design stage that lost the server (connection errors in errors.jsonl)
# is moved to <dir>.serverdown-<time> and redone once. Stops (exit 3) on an unsound certificate.
# Every command is appended to results/logs/cscwd_commands.log.
# Environment: PY, VLLM_BIN, MODELS, URL_8B, WORKERS.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-../.venv/bin/python}
export VLLM_BIN=${VLLM_BIN:-/jizhicfs/leonlanli/envs/vllm/bin/vllm}
export MODELS=${MODELS:-/jizhicfs/leonlanli/models}
URL_8B=${URL_8B:-http://127.0.0.1:8003/v1}
WORKERS=${WORKERS:-64}
LOG=$PWD/results/logs/cscwd_commands.log
mkdir -p results/logs results/reports
export VLLM_CURATOR_BASE_URL=$URL_8B VLLM_NODE_BASE_URL=$URL_8B

EPS=2.0
MAXLEN=32768
CFG_DESIGN=configs/vllm_qwen3-8b-think_design.toml
ALPHA_FILE=results/execution/cs0_alpha_selection.json
DATASETS=PM,CU,Do,ML,CS,EE
EXT_TASKS=degree-ge3,triangle-edge,triangle-node
CODE_TASKS=triangle,open-wedge,degree-ge3,triangle-node,triangle-edge,4-cycle

T_G1=cs9_node_generic_sim_tri_ow
T_G2=cs9_node_generic_sim_ext
T_G3=cs9_node_generic_sim_4cycle
T_G4=cs9_node_v1alt_sim_ow
T_GT=cs9_gt_select_r1000

run() {  # log, echo and execute one command (in the current directory)
  local rev; rev=$(git rev-parse --short HEAD)$(git -C "$(git rev-parse --show-toplevel)" diff --quiet HEAD || echo "-dirty")
  printf '%s git=%s cwd=%s VLLM_CURATOR_BASE_URL=%s %s\n' "$(date -u +%FT%TZ)" "$rev" "$(pwd)" "$VLLM_CURATOR_BASE_URL" "$*" >> "$LOG"
  echo "+ $*"
  "$@"
}
done_or_reset() {  # $1 dir, $2 file written last: 0 if finished; a partial dir is moved aside (return 1)
  [ -f "$1/$2" ] && return 0
  if [ -d "$1" ]; then
    local aside; aside="$1.incomplete-$(date -u +%Y%m%dT%H%M%SZ)"
    echo "incomplete $1 -> $aside" >&2
    mv "$1" "$aside"
  fi
  return 1
}
alpha() {
  [ -f "$ALPHA_FILE" ] || { echo "missing $ALPHA_FILE (run_cscwd.sh cs0-alpha)" >&2; exit 1; }
  "$PY" -c "import json; print(json.load(open('$ALPHA_FILE'))['alpha'])"
}
maxlen() {  # max_model_len of the served model, empty if nothing answers
  curl -sf -m 5 "$URL_8B/models" 2>/dev/null \
    | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["data"][0].get("max_model_len") or "")' 2>/dev/null || true
}
wait_server() {
  local k=0 l
  until [ "$(maxlen)" = "$MAXLEN" ]; do
    l=$(maxlen)
    if [ $((k % 30)) = 0 ]; then
      if [ -n "$l" ]; then echo "[cs9] $URL_8B serves max_model_len $l, need $MAXLEN (start it with: scripts/run_cs9.sh serve)" >&2
      else echo "[cs9] $(date +%T) waiting for $URL_8B"; fi
    fi
    k=$((k + 1)); sleep 10
  done
}
privacy_guard() {  # stop on an unsound certificate
  "$PY" - "$1" <<'EOF' || { echo "PRIVACY CHECK FAILED in $1: stop and report this directory" >&2; exit 3; }
import json, sys
from pathlib import Path
cert = Path(sys.argv[1]) / "certification_ablation" / "summary.json"
bad = sum(row.get("certificate_unsound") or 0 for row in json.loads(cert.read_text())["table"]) if cert.exists() else 0
print(f"privacy guard {sys.argv[1]}: {bad} problem(s)")
sys.exit(1 if bad else 0)
EOF
}
server_errors() {  # $1 dir: errors.jsonl lines that mean the server was unreachable (timeouts are retried, not counted)
  [ -f "$1/errors.jsonl" ] || { echo 0; return; }
  grep -cE 'APIConnectionError|Connection error|InternalServerError|ServiceUnavailable|Connection refused' "$1/errors.jsonl" || true
}
design_args() {  # $1 prompt core: the CS7/CS8 sim command line with that core
  echo --runs 100 --eps "$EPS" --seed 0 --noisy-gate --design-concurrency 8 \
    --provider vllm --config "$CFG_DESIGN" --curator-model Qwen3-8B --temperature 0.6 \
    --node-bounds --clip-alpha "$(alpha)" --prompt "$1" --select simulated --own-row-check --tighten 1
}
cc_stage() {  # $1 tag, $2 prompt core, then run_dsl_design_eval options
  local t=$1 core=$2 d="results/dsl_eval/$1" n crash=0; shift 2
  for attempt in 1 2; do
    until [ -f "$d/table.md" ]; do
      wait_server
      if [ -f "$d/manifest.json" ]; then
        # interrupted run: keep its finished (dataset, task) cells, design the others again
        # shellcheck disable=SC2046
        run "$PY" scripts/run_dsl_design_eval.py $(design_args "$core") --tag "$t" "$@" --resume && continue
      else
        done_or_reset "$d" table.md || true
        # shellcheck disable=SC2046
        run "$PY" scripts/run_dsl_design_eval.py $(design_args "$core") --tag "$t" "$@" && continue
      fi
      crash=$((crash + 1))
      [ "$crash" -ge 3 ] && { echo "[cs9] $t crashed $crash times: stop, see results/logs/cs9_all.log" >&2; exit 7; }
      echo "[cs9] $(date -u +%FT%TZ) $t crashed (attempt $crash); resuming in 60 s" >&2
      sleep 60
    done
    echo "done: $t"
    n=$(server_errors "$d")
    if [ "$n" -gt 0 ]; then
      [ "$attempt" = 2 ] && { echo "[cs9] $t lost the server again ($n errors): stop, see $d/errors.jsonl" >&2; exit 6; }
      echo "[cs9] $t lost the server ($n connection errors): moving it aside and redoing it" >&2
      mv "$d" "$d.serverdown-$(date -u +%Y%m%dT%H%M%SZ)"
      continue
    fi
    break
  done
  [ -f "$d/certification_ablation/table.md" ] || run "$PY" scripts/analyze_design_certification.py "$d"
  privacy_guard "$d"
}

cmd=${1:-}
case $cmd in
  serve)
    command -v "$VLLM_BIN" >/dev/null || { echo "vLLM not found: $VLLM_BIN (set VLLM_BIN)" >&2; exit 1; }
    [ -d "$MODELS/Qwen3-8B" ] || { echo "missing $MODELS/Qwen3-8B (set MODELS)" >&2; exit 1; }
    while true; do
      echo "[cs9 serve] $(date -u +%FT%TZ) start vLLM Qwen3-8B (max_model_len $MAXLEN, MEM 0.90)" | tee -a results/logs/cs9_serve_8b.log
      MEM=0.90 MAXLEN=$MAXLEN bash scripts/run_cscwd.sh serve 8b 2>&1 | tee -a results/logs/cs9_serve_8b.log || true
      echo "[cs9 serve] $(date -u +%FT%TZ) vLLM exited; restarting in 30 s (Ctrl+C to stop)" | tee -a results/logs/cs9_serve_8b.log
      sleep 30
    done ;;

  check)
    run "$PY" -m pytest tests/test_extension.py tests/test_dsl.py tests/test_selection.py tests/test_design_checks.py \
      -q -p no:cacheprovider ;;

  dry)
    # shellcheck disable=SC2046
    {
      run "$PY" scripts/run_dsl_design_eval.py $(design_args generic) --datasets "$DATASETS" --tasks triangle,open-wedge --designs 20 --dry-run
      run "$PY" scripts/run_dsl_design_eval.py $(design_args generic) --datasets "$DATASETS" --tasks "$EXT_TASKS" --designs 20 --dry-run
      run "$PY" scripts/run_dsl_design_eval.py $(design_args generic) --datasets CU,ML,EE --tasks 4-cycle --designs 10 --dry-run
      run "$PY" scripts/run_dsl_design_eval.py $(design_args v1-alt) --datasets "$DATASETS" --tasks open-wedge --designs 20 --dry-run
    } ;;

  g1) cc_stage "$T_G1" generic --datasets "$DATASETS" --tasks triangle,open-wedge --designs 20 ;;
  g2) cc_stage "$T_G2" generic --datasets "$DATASETS" --tasks "$EXT_TASKS" --designs 20 ;;
  g3) cc_stage "$T_G3" generic --datasets CU,ML,EE --tasks 4-cycle --designs 10 ;;
  g4) cc_stage "$T_G4" v1-alt --datasets "$DATASETS" --tasks open-wedge --designs 20 ;;

  code)
    if done_or_reset "results/execution/$T_GT" table.md; then echo "done: $T_GT"; exit 0; fi
    tags=()
    for t in "$T_G1" "$T_G2" "$T_G3"; do [ -f "results/dsl_eval/$t/runs.jsonl" ] && tags+=("$t"); done
    tagarg=$(IFS=,; echo "${tags[*]:-}")
    export OMP_NUM_THREADS=1
    run "$PY" scripts/run_gt_select.py --runs 1000 --workers "$WORKERS" --eps "$EPS" --seed 0 \
      --clip-alpha "$(alpha)" --datasets "$DATASETS" --tasks "$CODE_TASKS" --certicount-tags "$tagarg" --tag "$T_GT" ;;

  summary)
    run "$PY" scripts/summarize_cs9.py --g1 "$T_G1" --g2 "$T_G2" --g3 "$T_G3" --g4 "$T_G4" --gt "$T_GT" \
      --out results/reports/cs9_summary.md > /dev/null
    echo "wrote results/reports/cs9_summary.md" ;;

  all)
    echo "[cs9] $(date -u +%FT%TZ) start"
    for stage in check dry g1 g2 g3 g4 code summary; do
      echo "[cs9] $(date -u +%FT%TZ) $stage"
      "$0" "$stage"
    done
    echo "[cs9] $(date -u +%FT%TZ) done"
    echo "  summary:  results/reports/cs9_summary.md"
    echo "  designs:  results/dsl_eval/{$T_G1,$T_G2,$T_G3,$T_G4}/table.md"
    echo "  code:     results/execution/$T_GT/table.md" ;;

  *)
    sed -n '2,24p' "$0"; exit 2 ;;
esac
