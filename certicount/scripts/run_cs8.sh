#!/usr/bin/env bash
# CS8: complete the PSC (LLM agents) vs CertiCount comparison for the CSCWD paper
# (ε = 2, six datasets, tasks degree, 2-star, 3-star, triangle). Same settings as the earlier stages:
#   PSC         = CS1: curator / privacy controller Qwen3-8B thinking, node agents Qwen3-1.7B non-thinking, 10 runs
#   CertiCount  = CS7 sim: curator Qwen3-8B thinking writes the program, nodes run the interpreter (0 node LLM calls),
#                 per-node architecture α = 5 (cs0), prompt v1-alt, simulated choice, own-row check, 20 designs x 100 runs
#   code        = GT-PSC / GT-DSL / GT-DSL-node, 1000 runs, no model call (attribution of the improvement)
# Existing cells, not rerun: PSC PM degree/2-star/3-star (cs1_pm_*), PSC CU/Do triangle (cs1_cudo_triangle_*),
# CertiCount PM 3-star/triangle (cs7_node_v1alt_sim), CertiCount CU/Do triangle (cs7_node_v1alt_sim_cudo).
# PSC PM triangle does not fit any Qwen3 context (run_cscwd.sh, cs1): reported as infeasible.
#
#   scripts/run_cs8.sh all                  # everything serially, unattended; starts and stops the vLLM servers
#   SKIP_SERVE=1 scripts/run_cs8.sh all     # same, servers managed by hand (8B+1.7B for psc*, 8B 32k for cc-*)
#
# Stages of `all`, in order (each can also be run alone):
#   check       offline tests
#   dry         planned model calls (no server)
#   code        code references, CPU only (`all` starts it in the background and waits for it at the end)
#   serve-psc   8B (MEM 0.55, 16k) then 1.7B (MEM 0.35, 16k), in the background; waits until both answer
#   psc-pilot   1 run of EE triangle: does the largest new triangle prompt fit the context?
#   psc         CU,Do,ML,CS,EE x degree,2-star,3-star; ML,CS (+EE if the pilot passed) x triangle
#   psc-decomp  LLM execution error vs mechanism error of all CS1/CS8 PSC directories (no model call)
#   serve-cc    stop the servers, start 8B alone (MEM 0.90, 32k)
#   cc-pm       CertiCount PM degree, 2-star; stops if a task accepts < MIN_ACCEPT of its designs (FORCE=1: go on)
#   cc-cudo     CertiCount CU,Do x degree, 2-star, 3-star
#   cc-mlcsee   CertiCount ML,CS,EE x 4 tasks (DESIGNS_NEW designs per task, default 20; 10 halves the time)
#   stop        stop the servers started by this script
#
# Resumable: rerun the same command; finished stages are skipped, a half-written directory is moved to
# <dir>.incomplete-<time> and redone. Every command is appended to results/cscwd_commands.log.
# Environment: PY, VLLM_BIN, MODELS, URL_8B, URL_17B, SKIP_SERVE, DESIGNS_NEW, MIN_ACCEPT, FORCE.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-../.venv/bin/python}
VLLM_BIN=${VLLM_BIN:-vllm}
MODELS=${MODELS:-/models}
URL_8B=${URL_8B:-http://127.0.0.1:8003/v1}
URL_17B=${URL_17B:-http://127.0.0.1:8001/v1}
DESIGNS_NEW=${DESIGNS_NEW:-20}
MIN_ACCEPT=${MIN_ACCEPT:-0.8}
LOG=$PWD/results/cscwd_commands.log
STATE=$PWD/results/cs8_state
mkdir -p "$STATE"
export VLLM_BIN MODELS VLLM_CURATOR_BASE_URL=$URL_8B VLLM_NODE_BASE_URL=$URL_17B

EPS=2.0
CFG_PSC=configs/vllm_psc_qwen3-8b-think_curator_1.7b_node.toml
CFG_DESIGN=configs/vllm_qwen3-8b-think_design.toml
ALPHA_FILE=results/execution/cs0_alpha_selection.json
TASKS4=degree,2-star,3-star,triangle

T_CODE=cs8_code_all6_r1000
T_PILOT=cs8_pilot_ee_triangle
T_PSC_STAR=cs8_psc_5ds_kstar_8bthink-curator_1.7b-node
T_PSC_TRI=cs8_psc_triangle_8bthink-curator_1.7b-node
T_CC_PM=cs8_node_v1alt_sim_pm_deg2star
T_CC_CUDO=cs8_node_v1alt_sim_cudo_3tasks
T_CC_NEW=cs8_node_v1alt_sim_mlcsee

run() {  # log, echo and execute one command (in the current directory)
  local rev; rev=$(git rev-parse --short HEAD)$(git -C "$(git rev-parse --show-toplevel)" diff --quiet HEAD || echo "-dirty")
  printf '%s git=%s cwd=%s VLLM_CURATOR_BASE_URL=%s VLLM_NODE_BASE_URL=%s %s\n' \
    "$(date -u +%FT%TZ)" "$rev" "$(pwd)" "$VLLM_CURATOR_BASE_URL" "$VLLM_NODE_BASE_URL" "$*" >> "$LOG"
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
psc_exp1() {  # $1 tag, then run_experiments options; PSC agents, results in ../psc/results/exp1/<tag>
  local t=$1; shift
  done_or_reset "../psc/results/exp1/$t" table.md && { echo "done: $t"; return 0; }
  (cd ../psc && run "$PY" scripts/run_experiments.py --exp exp1 --methods PSC --runs 10 --seed 0 \
     --provider vllm --config "../certicount/$CFG_PSC" --tag "$t" "$@")
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
cc_run() {  # $1 tag, then run_dsl_design_eval options; CertiCount CS7 sim setting
  local t=$1; shift
  if ! done_or_reset "results/dsl_eval/$t" table.md; then
    run "$PY" scripts/run_dsl_design_eval.py --runs 100 --eps "$EPS" --seed 0 --noisy-gate --design-concurrency 8 \
      --provider vllm --config "$CFG_DESIGN" --curator-model Qwen3-8B --temperature 0.6 \
      --node-bounds --clip-alpha "$(alpha)" --prompt v1-alt --select simulated --own-row-check --tighten 1 \
      --tag "$t" "$@"
  fi
  [ -f "results/dsl_eval/$t/certification_ablation/table.md" ] || \
    run "$PY" scripts/analyze_design_certification.py "results/dsl_eval/$t"
  privacy_guard "results/dsl_eval/$t"
}
accept_check() {  # $1 tag: every task must accept >= MIN_ACCEPT of its designs (FORCE=1 skips the stop)
  "$PY" - "results/dsl_eval/$1/summary.json" "$MIN_ACCEPT" <<'EOF' || [ "${FORCE:-0}" = 1 ] || \
    { echo "low acceptance in $1: inspect designs.jsonl, then rerun with FORCE=1 to continue" >&2; exit 4; }
import json, sys
rows, low = json.load(open(sys.argv[1]))["summary"], float(sys.argv[2])
bad = [f'{r["dataset"]}/{r["task"]} {r["accept_rate"]:.2f}' for r in rows if (r.get("accept_rate") or 0) < low]
for r in rows:
    print(f'accept {r["dataset"]}/{r["task"]}: {r["accept_rate"]:.2f}')
sys.exit(1 if bad else 0)
EOF
}

# ---------------- vLLM servers (one GPU, as run_cscwd.sh) ----------------
up()   { until curl -sf "$1/models" >/dev/null; do sleep 10; done; }
serve_bg() {  # $1 = 8b | 1.7b, then env assignments (MEM=, MAXLEN=)
  local m=$1; shift
  [ -f "$STATE/serve_$m.pid" ] && kill -0 "$(cat "$STATE/serve_$m.pid")" 2>/dev/null && { echo "$m already served"; return 0; }
  env "$@" nohup scripts/run_cscwd.sh serve "$m" > "results/cs8_serve_$m.log" 2>&1 &
  echo $! > "$STATE/serve_$m.pid"
  echo "started vLLM $m (pid $!, log results/cs8_serve_$m.log)"
}
stop_servers() {
  for m in 1.7b 8b; do
    local f="$STATE/serve_$m.pid"
    [ -f "$f" ] || continue
    local pid; pid=$(cat "$f")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      for _ in $(seq 60); do kill -0 "$pid" 2>/dev/null || break; sleep 2; done
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid"
    fi
    rm -f "$f"
  done
  sleep 10   # let the GPU memory go
}

cmd=${1:-}; shift || true
case $cmd in
  check)
    run "$PY" -m pytest tests -q ;;

  dry)
    (cd ../psc && run "$PY" scripts/run_experiments.py --exp exp1 --methods PSC --runs 10 --provider vllm \
       --config "../certicount/$CFG_PSC" --datasets CU,Do,ML,CS,EE --tasks degree,2-star,3-star --dry-run
     run "$PY" scripts/run_experiments.py --exp exp1 --methods PSC --runs 10 --provider vllm \
       --config "../certicount/$CFG_PSC" --datasets ML,CS,EE --tasks triangle --dry-run)
    run "$PY" scripts/run_dsl_design_eval.py --datasets PM --tasks degree,2-star --designs 20 \
      --provider vllm --config "$CFG_DESIGN" --node-bounds --select simulated --dry-run
    run "$PY" scripts/run_dsl_design_eval.py --datasets CU,Do --tasks degree,2-star,3-star --designs 20 \
      --provider vllm --config "$CFG_DESIGN" --node-bounds --select simulated --dry-run
    run "$PY" scripts/run_dsl_design_eval.py --datasets ML,CS,EE --tasks "$TASKS4" --designs "$DESIGNS_NEW" \
      --provider vllm --config "$CFG_DESIGN" --node-bounds --select simulated --dry-run ;;

  code)
    done_or_reset "results/execution/$T_CODE" table.md && { echo "done: $T_CODE"; exit 0; }
    run "$PY" scripts/run_execution_compare.py --datasets PM,CU,Do,ML,CS,EE --tasks "$TASKS4" \
      --modes gt-psc,gt-dsl,gt-dsl-node --runs 1000 --eps "$EPS" --seed 0 --clip-alpha "$(alpha)" --tag "$T_CODE" ;;

  serve-psc)
    [ "${SKIP_SERVE:-0}" = 1 ] && { up "$URL_8B"; up "$URL_17B"; exit 0; }
    serve_bg 8b MEM=0.55 MAXLEN=16384;   up "$URL_8B"
    serve_bg 1.7b MEM=0.35 MAXLEN=16384; up "$URL_17B"
    echo "PSC servers up" ;;

  psc-pilot)
    psc_exp1 "$T_PILOT" --datasets EE --tasks triangle --runs 1 || echo "pilot run failed: EE triangle treated as infeasible"
    "$PY" - "../psc/results/exp1/$T_PILOT" "$STATE/ee_triangle" <<'EOF'
import json, sys
from pathlib import Path
d, out = Path(sys.argv[1]), Path(sys.argv[2])
errs = [json.loads(l) for l in (d / "errors.jsonl").read_text().splitlines() if l.strip()] if (d / "errors.jsonl").exists() else []
failed = [e for e in errs if e.get("kind") == "call_failed"
          or "context" in str(e.get("message", "")).lower() or "max_tokens" in str(e.get("message", "")).lower()]
ok = not failed and (d / "runs.jsonl").exists() and (d / "runs.jsonl").read_text().strip() != ""
out.write_text("fits" if ok else "infeasible")
print(f"EE triangle with 1.7B nodes: {'fits' if ok else 'INFEASIBLE (reported as such)'}; failing calls {len(failed)}")
EOF
    ;;

  psc)
    psc_exp1 "$T_PSC_STAR" --datasets CU,Do,ML,CS,EE --tasks degree,2-star,3-star
    tri=ML,CS
    [ "$(cat "$STATE/ee_triangle" 2>/dev/null || echo fits)" = fits ] && tri=ML,CS,EE
    psc_exp1 "$T_PSC_TRI" --datasets "$tri" --tasks triangle ;;

  psc-decomp)
    done_or_reset results/evaluation/cs8_psc_decomposition table.md && { echo "done: decomposition"; exit 0; }
    run "$PY" scripts/analyze_errors.py \
      ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node ../psc/results/exp1/cs1_cudo_triangle_8bthink-curator_1.7b-node \
      "../psc/results/exp1/$T_PSC_STAR" "../psc/results/exp1/$T_PSC_TRI" --tag cs8_psc_decomposition ;;

  serve-cc)
    [ "${SKIP_SERVE:-0}" = 1 ] && { up "$URL_8B"; exit 0; }
    stop_servers
    serve_bg 8b MEM=0.90 MAXLEN=32768; up "$URL_8B"
    echo "CertiCount server up" ;;

  cc-pm)
    cc_run "$T_CC_PM" --datasets PM --tasks degree,2-star --designs 20
    accept_check "$T_CC_PM" ;;
  cc-cudo)
    cc_run "$T_CC_CUDO" --datasets CU,Do --tasks degree,2-star,3-star --designs 20
    accept_check "$T_CC_CUDO" ;;
  cc-mlcsee)
    cc_run "$T_CC_NEW" --datasets ML,CS,EE --tasks "$TASKS4" --designs "$DESIGNS_NEW"
    accept_check "$T_CC_NEW" ;;

  stop)
    stop_servers ;;

  all)
    echo "[cs8] $(date -u +%FT%TZ) start"
    "$0" check
    "$0" dry
    "$0" code > results/cs8_code.log 2>&1 &
    code_pid=$!
    echo "[cs8] code references in the background (pid $code_pid, log results/cs8_code.log)"
    for stage in serve-psc psc-pilot psc psc-decomp serve-cc cc-pm cc-cudo cc-mlcsee; do
      echo "[cs8] $(date -u +%FT%TZ) $stage"
      "$0" "$stage"
    done
    [ "${SKIP_SERVE:-0}" = 1 ] || "$0" stop
    wait "$code_pid" || { echo "[cs8] code stage failed, see results/cs8_code.log" >&2; exit 1; }
    echo "[cs8] $(date -u +%FT%TZ) done"
    echo "  code:       results/execution/$T_CODE/table.md"
    echo "  PSC:        ../psc/results/exp1/{$T_PSC_STAR,$T_PSC_TRI}/table.md, results/evaluation/cs8_psc_decomposition/table.md"
    echo "  CertiCount: results/dsl_eval/{$T_CC_PM,$T_CC_CUDO,$T_CC_NEW}/table.md" ;;

  *)
    sed -n '2,31p' "$0"; exit 2 ;;
esac
