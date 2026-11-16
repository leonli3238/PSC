#!/usr/bin/env bash
# CSCWD 2027 experiments on PM (ε = 2): every command, dataset, task, run count and tag is fixed here,
# so each result directory can be traced back to one stage of this file. Run from certicount/.
#
# Naming: stages are CS0..CS3b (not the E0..E7 of docs/PAPER_DIRECTION_SUMMARY_2026-11-15.md,
# not the A1..A5 of docs/QWEN_EXPERIMENT_ANALYSIS_2026-11-10.md). Result tags start with cs<k>_.
#
#   CS1   PSC, curator Qwen3-8B (thinking) + node agents Qwen3-1.7B: accuracy, error decomposition,
#         black-box audit of the node step (violations); PM: degree, 2-star, 3-star; triangle on CU/Do
#         (PM triangle prompts do not fit any Qwen3 context: reported as infeasible).
#         CS1s: 8B nodes (strong baseline, optional)
#   CS2   CertiCount + PSC architecture: Qwen3-8B (thinking) designs DSL programs, nodes run the interpreter
#   CS0   choice of the clipping margin α on CU and Do only (never on PM), fixed before CS3
#   CS3   CertiCount + per-node architecture (edge clipping + NAM-DPRD unbiased matrix A)
#   CS3c  code references on PM/CU/Do: GT-PSC, GT-DSL, GT-DSL-node, GT-TriTR (no model call)
#   CS3b  fair control: PSC agents (1.7B nodes) with the same per-node mechanism (method TriTR)
#
# Order:
#   scripts/run_cscwd.sh check                      # code version + offline tests (no GPU)
#   VLLM_BIN=... MODELS=... scripts/run_cscwd.sh serve 8b     # foreground; start first
#   VLLM_BIN=... MODELS=... scripts/run_cscwd.sh serve 1.7b   # foreground, second terminal
#   scripts/run_cscwd.sh wait
#   scripts/run_cscwd.sh dry                        # planned model calls of every stage
#   scripts/run_cscwd.sh cs1-pilot                  # 1 run of 3-star on PM: timing check
#   scripts/run_cscwd.sh cs1                        # PM, 30 runs
#   scripts/run_cscwd.sh cs1-small                  # CU/Do triangle, 20 runs
#   scripts/run_cscwd.sh cs1-decomp                 # no model call
#   scripts/run_cscwd.sh cs1-audit-dry              # audit call count (needs cs1); then:
#   scripts/run_cscwd.sh cs1-audit                  # ~52.8k calls, ~11M prompt tokens
#   scripts/run_cscwd.sh cs1-strong                 # optional
#   scripts/run_cscwd.sh cs2                        # 40 designs + certification ablation
#   scripts/run_cscwd.sh cs0-alpha                  # no model call; writes results/execution/cs0_alpha_selection.json
#   scripts/run_cscwd.sh cs3                        # 40 designs + certification ablation (reads α)
#   scripts/run_cscwd.sh cs3-code                   # no model call (reads α)
#   scripts/run_cscwd.sh cs3b                       # PM 2/3-star + CU/Do triangle (reads α)
#
# Every executed command is appended to results/cscwd_commands.log with UTC time and git revision.
# Existing tags are refused by the scripts (no overwrite): to rerun a stage, move its directory away.
# Environment: PY, VLLM_BIN, MODELS, URL_8B, URL_17B.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-../.venv/bin/python}
VLLM_BIN=${VLLM_BIN:-vllm}
MODELS=${MODELS:-/models}
URL_8B=${URL_8B:-http://127.0.0.1:8003/v1}
URL_17B=${URL_17B:-http://127.0.0.1:8001/v1}
LOG=$PWD/results/cscwd_commands.log

EPS=2.0
PM_TASKS=degree,2-star,3-star,triangle          # CertiCount stages (code execution)
PSC_PM_TASKS=degree,2-star,3-star               # PSC with LLM nodes on PM (triangle prompts overflow, see cs1)
CFG_CS1=configs/vllm_psc_qwen3-8b-think_curator_1.7b_node.toml   # curator 8B thinking, nodes 1.7B
CFG_8B=configs/vllm_psc_qwen3-8b_curator-think.toml              # curator 8B thinking, nodes 8B
ALPHA_GRID="0 2 5 10 20"
ALPHA_FILE=results/execution/cs0_alpha_selection.json

T_CS1=cs1_pm_8bthink-curator_1.7b-node
T_CS1_PILOT=cs1_pilot_pm_3-star
T_CS1_SMALL=cs1_cudo_triangle_8bthink-curator_1.7b-node
T_CS1S=cs1s_pm_8bthink-curator_8b-node
T_CS2=cs2_pm_psc-arch_d10

export VLLM_CURATOR_BASE_URL=$URL_8B VLLM_NODE_BASE_URL=$URL_17B

mkdir -p results
run() {  # log, echo and execute one command (in the current directory)
  local rev; rev=$(git rev-parse --short HEAD)$(git -C "$(git rev-parse --show-toplevel)" diff --quiet HEAD || echo "-dirty")
  printf '%s git=%s cwd=%s VLLM_CURATOR_BASE_URL=%s VLLM_NODE_BASE_URL=%s %s\n' \
    "$(date -u +%FT%TZ)" "$rev" "$(pwd)" "$VLLM_CURATOR_BASE_URL" "$VLLM_NODE_BASE_URL" "$*" >> "$LOG"
  echo "+ $*"
  "$@"
}
psc_run() { (cd ../psc && run "$PY" scripts/run_experiments.py "$@"); }   # PSC agents (psc/results/exp1/<tag>)
alpha() {
  [ -f "$ALPHA_FILE" ] || { echo "missing $ALPHA_FILE: run the cs0-alpha stage first" >&2; exit 1; }
  "$PY" -c "import json; print(json.load(open('$ALPHA_FILE'))['alpha'])"
}
served()    { case $1 in 1.7b) echo Qwen3-1.7B;; 8b) echo Qwen3-8B;; *) echo "unknown model $1" >&2; exit 2;; esac; }
model_dir() { echo "$MODELS/$(served "$1")"; }

cmd=${1:-}; shift || true
case $cmd in
  check)
    [ -f tests/test_matrix.py ] && [ -f certicount/dsl/matrix.py ] \
      || { echo "this checkout lacks the per-node architecture (dsl/matrix.py, tests/test_matrix.py)" >&2; exit 1; }
    git --no-pager log --oneline -1; git --no-pager status --short -- . ../psc | head -30
    run "$PY" -m pytest tests -q ;;                                   # expected: 243 passed, 1 skipped

  serve)  # $1 = 8b | 1.7b; both on one GPU: 8B first (0.55), then 1.7B (0.35)
    m=$1
    if [ "$m" = 8b ]; then port=8003 mem=${MEM:-0.55} seqs=128; else port=8001 mem=${MEM:-0.35} seqs=256; fi
    exec "$VLLM_BIN" serve "$(model_dir "$m")" --served-model-name "$(served "$m")" \
      --max-model-len 16384 --enable-prefix-caching --gpu-memory-utilization "$mem" \
      --max-num-seqs "$seqs" --host 127.0.0.1 --port "$port" ;;

  wait)
    for u in "$URL_8B" "$URL_17B"; do until curl -sf "$u/models" >/dev/null; do sleep 10; done; curl -s "$u/models"; echo; done ;;

  dry)  # model calls of cs1, cs1-small, cs2, cs3, cs3b (the audit needs cs1: cs1-audit-dry)
    psc_run --exp exp1 --methods PSC --datasets PM --tasks "$PSC_PM_TASKS" --runs 10 --provider vllm \
      --config "../certicount/$CFG_CS1" --dry-run
    psc_run --exp exp1 --methods PSC --datasets CU,Do --tasks triangle --runs 10 --provider vllm \
      --config "../certicount/$CFG_CS1" --dry-run
    run "$PY" scripts/run_dsl_design_eval.py --datasets PM --tasks "$PM_TASKS" --designs 10 \
      --provider vllm --config "$CFG_8B" --dry-run
    run "$PY" scripts/run_dsl_design_eval.py --datasets PM --tasks "$PM_TASKS" --designs 10 --node-bounds \
      --provider vllm --config "$CFG_8B" --dry-run
    psc_run --exp exp1 --methods TriTR --datasets PM --tasks 2-star,3-star --runs 10 --provider vllm \
      --config "../certicount/$CFG_CS1" --dry-run
    psc_run --exp exp1 --methods TriTR --datasets CU,Do --tasks triangle --runs 10 --provider vllm \
      --config "../certicount/$CFG_CS1" --dry-run ;;

  # ---------------- CS1: PSC with 1.7B node agents (exp1 of psc is ε = 2) ----------------
  # PM triangle is not run with LLM nodes: every one of the 453 update prompts is >= 63.6k characters
  # (mostly digits, ~1 token each), far above the 16k context; triangle is run on CU and Do (<= 4.6k).
  cs1-pilot)
    psc_run --exp exp1 --methods PSC --datasets PM --tasks 3-star --runs 1 \
      --provider vllm --config "../certicount/$CFG_CS1" --tag "$T_CS1_PILOT" ;;
  cs1)
    psc_run --exp exp1 --methods PSC --datasets PM --tasks "$PSC_PM_TASKS" --runs 10 \
      --provider vllm --config "../certicount/$CFG_CS1" --tag "$T_CS1" ;;
  cs1-small)  # triangle with LLM nodes where the prompts fit
    psc_run --exp exp1 --methods PSC --datasets CU,Do --tasks triangle --runs 10 \
      --provider vllm --config "../certicount/$CFG_CS1" --tag "$T_CS1_SMALL" ;;
  cs1-decomp)  # LLM execution error vs mechanism error on the same noise
    run "$PY" scripts/analyze_errors.py "../psc/results/exp1/$T_CS1" "../psc/results/exp1/$T_CS1_SMALL" \
      --tag cs1_decomposition ;;
  cs1-audit-dry|cs1-audit)  # degree: reuse results/audit/sensitivity/probe_pm_degree_qwen3-1.7b (A1)
    extra=(); [ "$cmd" = cs1-audit-dry ] && extra=(--dry-run)
    run "$PY" scripts/run_sensitivity_audit.py --source "../psc/results/exp1/$T_CS1" \
      --datasets PM --tasks 2-star,3-star --runs 1 --nodes 40 --pairs 2 --select 20 --eval 200 \
      --alpha 0.05 --seed 0 --provider vllm --config "$CFG_CS1" --node-model Qwen3-1.7B --concurrency 128 \
      --tag cs1_audit_pm_1.7b "${extra[@]}" ;;
  cs1-strong)  # 8B nodes on the 8B server
    (export VLLM_NODE_BASE_URL=$URL_8B
     psc_run --exp exp1 --methods PSC --datasets PM --tasks 2-star,3-star --runs 5 \
       --provider vllm --config "../certicount/$CFG_8B" --tag "$T_CS1S") ;;

  # ---------------- CS2: CertiCount, PSC architecture ----------------
  cs2)
    run "$PY" scripts/run_dsl_design_eval.py --datasets PM --tasks "$PM_TASKS" --designs 10 --runs 100 \
      --eps "$EPS" --seed 0 --provider vllm --config "$CFG_8B" --curator-model Qwen3-8B --temperature 0.6 \
      --tag "$T_CS2"
    run "$PY" scripts/analyze_design_certification.py "results/dsl_eval/$T_CS2" ;;

  # ---------------- CS0: α on CU and Do only ----------------
  cs0-alpha)
    [ -f "$ALPHA_FILE" ] && { echo "$ALPHA_FILE exists (α is fixed once): $(alpha)" >&2; exit 1; }
    for a in $ALPHA_GRID; do
      [ -d "results/execution/cs0_alpha_a$a" ] && continue
      run "$PY" scripts/run_execution_compare.py --datasets CU,Do --tasks 2-star,3-star,triangle \
        --modes gt-dsl-node --runs 200 --eps "$EPS" --seed 0 --clip-alpha "$a" --tag "cs0_alpha_a$a"
    done
    # criterion fixed in advance: geometric mean of the mean relative error over the 6 cells (CU, Do x 3 tasks)
    run "$PY" - "$ALPHA_FILE" $ALPHA_GRID <<'EOF'
import json, math, subprocess, sys
out, grid = sys.argv[1], sys.argv[2:]
scores = {}
for a in grid:
    rows = [r for r in json.load(open(f"results/execution/cs0_alpha_a{a}/summary.json"))["rows"]
            if r["method"] == "GT-DSL-node"]
    assert len(rows) == 6, f"alpha {a}: {len(rows)} cells, expected 6"
    scores[a] = {"geomean_re": math.exp(sum(math.log(r["relative_error"]) for r in rows) / len(rows)),
                 "cells": {f'{r["dataset"]}/{r["task"]}': r["relative_error"] for r in rows}}
best = min(grid, key=lambda a: scores[a]["geomean_re"])
rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
json.dump({"alpha": float(best), "criterion": "argmin geometric mean of mean RE over CU,Do x 2-star,3-star,triangle "
           "(GT-DSL-node, eps 2, 200 runs, seed 0)", "grid": [float(a) for a in grid], "scores": scores,
           "git": rev}, open(out, "w"), indent=2)
for a in grid:
    print(f"alpha {a:>4}: geomean RE {scores[a]['geomean_re']:.4f}")
print(f"selected alpha = {best} -> {out}")
EOF
    ;;

  # ---------------- CS3: CertiCount, per-node architecture ----------------
  cs3)
    A=$(alpha)
    run "$PY" scripts/run_dsl_design_eval.py --datasets PM --tasks "$PM_TASKS" --designs 10 --runs 100 \
      --eps "$EPS" --seed 0 --node-bounds --clip-alpha "$A" --provider vllm --config "$CFG_8B" \
      --curator-model Qwen3-8B --temperature 0.6 --tag "cs3_pm_node-arch_d10_a$A"
    run "$PY" scripts/analyze_design_certification.py "results/dsl_eval/cs3_pm_node-arch_d10_a$A" ;;
  cs3-code)
    A=$(alpha)
    run "$PY" scripts/run_execution_compare.py --datasets PM,CU,Do --tasks "$PM_TASKS" \
      --modes gt-psc,gt-dsl,gt-dsl-node,gt-tritr --runs 200 --eps "$EPS" --seed 0 --clip-alpha "$A" \
      --tag "cs3c_code_a$A" ;;
  cs3b)  # PM triangle with TriTR LLM nodes: 36/453 update prompts > 12k characters, so CU/Do as in cs1-small
    A=$(alpha)
    psc_run --exp exp1 --methods TriTR --tritr-alpha "$A" --datasets PM --tasks 2-star,3-star --runs 10 \
      --provider vllm --config "../certicount/$CFG_CS1" --tag "cs3b_pm_psc-agent_node-arch_a$A"
    psc_run --exp exp1 --methods TriTR --tritr-alpha "$A" --datasets CU,Do --tasks triangle --runs 10 \
      --provider vllm --config "../certicount/$CFG_CS1" --tag "cs3b_cudo_triangle_psc-agent_node-arch_a$A" ;;

  *)
    sed -n '2,40p' "$0"; exit 2 ;;
esac
