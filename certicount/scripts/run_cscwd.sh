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
#   CS4/5 design-loop checks online, prompt self-evolution (held-out tasks 3-star, 5-star, triangle, degree-moment2)
#   CS6   fixes of the four CS5 problems: tighter deriver, prompt core v1 + format repairs, evolution with
#         GS term / Pareto parents / confirmed replacement, min-GS selection + tighten round; CS6a compares
#         the prompt cores A v1 / B v1-repeat3 / C v1-alt
#   CS7   per-node architecture only: the curator writes one program per release (rows N / matrix A), the system
#         certifies both and chooses by simulating the release on public graphs (design time: Holme-Kim graphs of
#         the public n; run time: Chung-Lu graphs of the published noisy degrees); own-row check; fuzzing of A
#         programs and own bounds D != dmax; normalised GS ratio
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
#   MEM=0.90 MAXLEN=32768 scripts/run_cscwd.sh serve 8b   # then, unattended and resumable:
#   scripts/run_cscwd.sh cs45-all                   # check, cs4-replay (background), cs4-online, cs5-evolve-psc,
#                                                   # cs5-eval-psc, cs5-evolve-node, cs5-eval-node, summary
#   scripts/run_cscwd.sh cs6-all                    # CS6 (fixes of the four CS5 problems), same server:
#                                                   # check, cs6b (background, no model), cs6a, cs6c-evolve,
#                                                   # cs6c-eval, cs6-summary -> results/cs6_summary.md
#   scripts/run_cscwd.sh cs7-all                    # CS7, same server: check, cs7-offline (background, no model),
#                                                   # cs7-eval, cs7-summary -> results/cs7_summary.md
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
CFG_DESIGN=configs/vllm_qwen3-8b-think_design.toml               # design runs (reasoning budget 13000)
HELD_OUT=3-star,5-star,triangle,degree-moment2                   # never used by the evolution
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
done_or_reset() {  # $1 dir, $2 file written last: 0 if finished; a partial dir is moved aside (return 1)
  [ -f "$1/$2" ] && return 0
  if [ -d "$1" ]; then
    local aside; aside="$1.incomplete-$(date -u +%Y%m%dT%H%M%SZ)"
    echo "incomplete $1 -> $aside" >&2
    mv "$1" "$aside"
  fi
  return 1
}
privacy_guard() {  # stop on a falsifier refutation (evolution) or an unsound certificate (design run)
  "$PY" - "$1" <<'EOF' || { echo "PRIVACY CHECK FAILED in $1: stop and report this directory" >&2; exit 3; }
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
bad = 0
if (d / "lineage.jsonl").exists():
    for line in (d / "lineage.jsonl").read_text().splitlines():
        rec = json.loads(line)
        bad += rec.get("evaluation", {}).get("stages", {}).get("refuted", 0)
cert = d / "certification_ablation" / "summary.json"
if cert.exists():
    bad += sum(row.get("certificate_unsound") or 0 for row in json.loads(cert.read_text())["table"])
print(f"privacy guard {d}: {bad} problem(s)")
sys.exit(1 if bad else 0)
EOF
}
design_run() {  # $1 tag, then run_dsl_design_eval options; skips a finished run, redoes a partial one
  local t=$1; shift
  if ! done_or_reset "results/dsl_eval/$t" table.md; then
    run "$PY" scripts/run_dsl_design_eval.py --datasets PM --designs 10 --runs 100 --eps "$EPS" --seed 0 --noisy-gate \
      --design-concurrency 8 --provider vllm --config "$CFG_DESIGN" --curator-model Qwen3-8B --temperature 0.6 \
      --tag "$t" "$@"
  fi
  [ -f "results/dsl_eval/$t/certification_ablation/table.md" ] || \
    run "$PY" scripts/analyze_design_certification.py "results/dsl_eval/$t"
  privacy_guard "results/dsl_eval/$t"
}
served()    { case $1 in 1.7b) echo Qwen3-1.7B;; 8b) echo Qwen3-8B;; *) echo "unknown model $1" >&2; exit 2;; esac; }
model_dir() { echo "$MODELS/$(served "$1")"; }

cmd=${1:-}; shift || true
case $cmd in
  check)
    [ -f tests/test_matrix.py ] && [ -f certicount/dsl/matrix.py ] \
      || { echo "this checkout lacks the per-node architecture (dsl/matrix.py, tests/test_matrix.py)" >&2; exit 1; }
    git --no-pager log --oneline -1; git --no-pager status --short -- . ../psc | head -30
    run "$PY" -m pytest tests -q ;;                                   # expected: 332 passed, 1 skipped

  serve)  # $1 = 8b | 1.7b; both on one GPU: 8B first (0.55), then 1.7B (0.35)
    # MAXLEN: context length (default 16384, as CS1-CS3). CS4/CS5 design and reflection prompts (up to ~4k
    # tokens) plus the 13000-token reasoning budget need MAXLEN=32768 (Qwen3-8B's native context).
    m=$1
    if [ "$m" = 8b ]; then port=8003 mem=${MEM:-0.55} seqs=128; else port=8001 mem=${MEM:-0.35} seqs=256; fi
    exec "$VLLM_BIN" serve "$(model_dir "$m")" --served-model-name "$(served "$m")" \
      --max-model-len "${MAXLEN:-16384}" --enable-prefix-caching --gpu-memory-utilization "$mem" \
      --max-num-seqs "$seqs" --host 127.0.0.1 --port "$port" ;;

  wait)  # wait8b: only the 8B server (CS4/CS5 need no node model)
    for u in "$URL_8B" "$URL_17B"; do until curl -sf "$u/models" >/dev/null; do sleep 10; done; curl -s "$u/models"; echo; done ;;
  wait8b)
    until curl -sf "$URL_8B/models" >/dev/null; do sleep 10; done; curl -s "$URL_8B/models"; echo ;;

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

  # ---------------- CS4 (step 1a): design-loop fixes, offline replay of the recorded drafts ----------------
  # Reader (reasoning block skipped, truncation detected, several for clauses = nested sums), repair hints,
  # GS-growth check and noise-aware gate (certicount/dsl/noisy_gate.py). No model call.
  cs4-replay)
    done_or_reset results/dsl_eval/cs4_step1a_replay table.md && { echo "cs4-replay: done"; exit 0; }
    run "$PY" scripts/replay_design_drafts.py "results/dsl_eval/$T_CS2" "results/dsl_eval/cs3_pm_node-arch_d10_a$(alpha)" \
      results/dsl_eval/A3_pm_design_8bthink_d10 --tau 2.0 --reps 8 --runs 20 --tag cs4_step1a_replay ;;
  # Online check of the step-1a loop: the CS2 / CS3 settings (same tasks, prompt v0, seed, temperature) with the
  # new checks and gate on, so the drafts can be rewritten after the new feedback (stages noisy -> accepted).
  cs4-online)
    for arch in psc node; do
      extra=(); t=cs4_online_psc-arch_d10
      if [ "$arch" = node ]; then extra=(--node-bounds --clip-alpha "$(alpha)"); t="cs4_online_node-arch_d10_a$(alpha)"; fi
      design_run "$t" --tasks "$PM_TASKS" --prompt v0 --restarts 1 "${extra[@]}"
    done ;;

  # ---------------- CS5: prompt self-evolution (certicount/dsl/evolve.py) ----------------
  # Evolution uses the training tasks only (degree, 2-star, 4-star; public n = 400, synthetic graphs);
  # evaluation uses the held-out tasks on PM. Arms per architecture:
  #   v0       original prompt + checks + gate (feedback rewrites within a design only)
  #   evolved  best_prompt.json of the evolution
  #   v0-r2    original prompt with 2 restarts (more tries at evaluation time, no learning)
  cs5-evolve-psc|cs5-evolve-node)
    extra=(); tag=cs5_evolve_psc
    if [ "$cmd" = cs5-evolve-node ]; then extra=(--node-bounds --clip-alpha "$(alpha)"); tag=cs5_evolve_node; fi
    done_or_reset "results/evolve/$tag" best_prompt.json && { echo "$cmd: done"; exit 0; }
    run "$PY" scripts/run_prompt_evolution.py --start v0 --train-tasks degree,2-star,4-star --n 400 --eps "$EPS" \
      --designs 4 --generations 5 --children 3 --patience 2 --design-concurrency 8 --seed 0 "${extra[@]}" \
      --provider vllm --config "$CFG_DESIGN" --curator-model Qwen3-8B --temperature 0.6 --tag "$tag"
    privacy_guard "results/evolve/$tag" ;;
  cs5-eval-psc|cs5-eval-node)
    extra=(); arch=psc
    if [ "$cmd" = cs5-eval-node ]; then extra=(--node-bounds --clip-alpha "$(alpha)"); arch=node; fi
    best="results/evolve/cs5_evolve_$arch/best_prompt.json"
    [ -f "$best" ] || { echo "missing $best: run cs5-evolve-$arch first" >&2; exit 1; }
    for arm in v0 evolved v0-r2; do
      prompt=v0; restarts=1
      [ "$arm" = evolved ] && prompt=$best
      [ "$arm" = v0-r2 ] && restarts=2
      design_run "cs5_eval_${arch}_$arm" --tasks "$HELD_OUT" --prompt "$prompt" --restarts "$restarts" "${extra[@]}"
    done ;;

  # ---------------- everything of steps CS4 + CS5 in one unattended run ----------------
  # Needs the 8B server (serve 8b with MAXLEN=32768). Resumable: rerun the same command after an interruption;
  # finished stages are skipped, a half-written result directory is moved to <dir>.incomplete-<time> and redone.
  # Stops at the first error and at any falsifier refutation / unsound certificate.
  cs45-all)
    echo "[cs45-all] $(date -u +%FT%TZ) start"
    "$0" check
    until curl -sf "$URL_8B/models" >/dev/null; do echo "waiting for $URL_8B"; sleep 15; done
    "$0" cs4-replay > results/cs4_replay.log 2>&1 &
    replay_pid=$!
    for stage in cs4-online cs5-evolve-psc cs5-eval-psc cs5-evolve-node cs5-eval-node; do
      echo "[cs45-all] $(date -u +%FT%TZ) $stage"
      "$0" "$stage"
    done
    wait "$replay_pid" || { echo "[cs45-all] cs4-replay failed, see results/cs4_replay.log" >&2; exit 1; }
    run "$PY" scripts/summarize_cs45.py --out results/cs45_summary.md
    echo "[cs45-all] $(date -u +%FT%TZ) done: results/cs45_summary.md" ;;

  # ---------------- CS6: the fixes of the four CS5 problems (PSC architecture, held-out tasks on PM) ----------------
  # CS6a  prompt cores, one loop per design (the parse question): A = v1, B = v1-repeat3 (the prohibition paragraph
  #       three times), C = v1-alt (rewrites of the Python constructs + closing checklist + rewrite hints).
  #       20 designs per task; format repairs on in every arm; A is also the v1 arm of CS6c.
  cs6a)
    for core in v1 v1-repeat3 v1-alt; do
      design_run "cs6a_psc_$core" --tasks "$HELD_OUT" --designs 20 --prompt "$core" --restarts 1
    done ;;
  # CS6b  no model call: replay of the recorded CS2/CS4/CS5 runs through the current reader and deriver
  #       (problem 2: rescued parse failures and the categories left; problem 1: GS and paired RE of every accepted
  #       program), and fuzzing of the tighter deriver (must report 0 refuted programs).
  cs6b)
    done_or_reset results/dsl_eval/cs6b_offline_replay table.md || \
      run "$PY" scripts/replay_fixes_offline.py "results/dsl_eval/$T_CS2" results/dsl_eval/cs4_online_psc-arch_d10 \
        results/dsl_eval/cs5_eval_psc_v0 results/dsl_eval/cs5_eval_psc_v0-r2 results/dsl_eval/cs5_eval_psc_evolved \
        --tag cs6b_offline_replay
    for spec in "cs6b_fuzz_shapes 0 1.0" "cs6b_fuzz_mixed 1 0.3"; do
      set -- $spec
      done_or_reset "results/dsl/$1" table.md || \
        run "$PY" scripts/run_dsl_fuzz.py --tag "$1" --count 3000 --seed "$2" --shapes "$3" --workers 8
      "$PY" -c "import json, sys; f = json.load(open('results/dsl/$1/summary.json'))['failures']; \
print('$1: refuted or failing programs', f); sys.exit(1 if f else 0)" \
        || { echo "PRIVACY CHECK FAILED in results/dsl/$1" >&2; exit 3; }
    done ;;
  # CS6c  the fixes online (10 designs per task, 100 paired code runs, as CS5):
  #   legacy          CS5 prompt byte for byte, no format repairs (current deriver: problem 1 against cs5_eval_psc_v0)
  #   v1-r4-first     v1, up to 4 restarts, first accepted program (CS5 v0-r2 style: restarts only)
  #   v1-r4-mings     v1, up to 4 restarts, smallest GS among 3 accepted programs, 1 tighten round, early stop (problem 4)
  #   evolve          evolution from v0 (core v1) with GS in the score, Pareto parents, confirmed replacement (problem 3)
  #   evolved(-r4-mings)  its best prompt, one loop / with the selection of v1-r4-mings
  cs6c-evolve)
    tag=cs6c_evolve_psc
    done_or_reset "results/evolve/$tag" best_prompt.json && { echo "$cmd: done"; exit 0; }
    run "$PY" scripts/run_prompt_evolution.py --start v0 --train-tasks degree,2-star,4-star,open-wedge --n 400 \
      --eps "$EPS" --designs 8 --generations 5 --children 3 --patience 2 --confirm-evals 2 --z 1.0 --nu-gs 0.1 \
      --max-rules 4 --design-concurrency 8 --seed 0 --provider vllm --config "$CFG_DESIGN" --curator-model Qwen3-8B \
      --temperature 0.6 --tag "$tag"
    privacy_guard "results/evolve/$tag" ;;
  cs6c-eval)
    SELECT=(--restarts 4 --select min_gs --min-accepted 3 --tighten 1 --early-stop noisy,gs_loose)
    design_run cs6c_psc_legacy --tasks "$HELD_OUT" --prompt legacy --no-normalize --restarts 1
    design_run cs6c_psc_v1-r4-first --tasks "$HELD_OUT" --prompt v1 --restarts 4 --select first
    design_run cs6c_psc_v1-r4-mings --tasks "$HELD_OUT" --prompt v1 "${SELECT[@]}"
    best=results/evolve/cs6c_evolve_psc/best_prompt.json
    [ -f "$best" ] || { echo "missing $best: run cs6c-evolve first" >&2; exit 1; }
    design_run cs6c_psc_evolved --tasks "$HELD_OUT" --prompt "$best" --restarts 1
    design_run cs6c_psc_evolved-r4-mings --tasks "$HELD_OUT" --prompt "$best" "${SELECT[@]}" ;;
  cs6-summary)
    run "$PY" scripts/summarize_cs6.py --out results/cs6_summary.md ;;
  # Everything of CS6 unattended and resumable (8B server with MAXLEN=32768); stops at any privacy-check failure.
  cs6-all)
    echo "[cs6-all] $(date -u +%FT%TZ) start"
    "$0" check
    "$0" cs6b > results/cs6b.log 2>&1 &
    offline_pid=$!
    until curl -sf "$URL_8B/models" >/dev/null; do echo "waiting for $URL_8B"; sleep 15; done
    for stage in cs6a cs6c-evolve cs6c-eval; do
      echo "[cs6-all] $(date -u +%FT%TZ) $stage"
      "$0" "$stage"
    done
    wait "$offline_pid" || { echo "[cs6-all] cs6b failed, see results/cs6b.log" >&2; exit 1; }
    "$0" cs6-summary
    echo "[cs6-all] $(date -u +%FT%TZ) done: results/cs6_summary.md" ;;

  # ---------------- CS7: per-node architecture only; release rounds + simulated choice ----------------
  # CS7-offline (no model): fuzzing of the deriver on programs that read A and on own bounds D != dmax (must report
  #       0 refuted), and the replay of the CS4/CS5 per-node runs through the new checks (own-row check, no gate,
  #       simulated choice between pairs of designs).
  cs7-offline)
    for spec in "cs7_fuzz_matrix 2 0 1.0 5x3,7x4:200,7x4d2:200,6x3d5:200" \
                "cs7_fuzz_node_rows 3 0.5 0 5x3d2,7x4d2:200,6x3d5:200"; do
      set -- $spec
      done_or_reset "results/dsl/$1" table.md || \
        run "$PY" scripts/run_dsl_fuzz.py --tag "$1" --count 3000 --seed "$2" --shapes "$3" --matrix "$4" \
          --checks "$5" --workers 8
      "$PY" -c "import json, sys; f = json.load(open('results/dsl/$1/summary.json'))['failures']; \
print('$1: refuted or failing programs', f); sys.exit(1 if f else 0)" \
        || { echo "PRIVACY CHECK FAILED in results/dsl/$1" >&2; exit 3; }
    done
    done_or_reset results/dsl_eval/cs7_offline_replay table.md || \
      run "$PY" scripts/replay_selection_offline.py results/dsl_eval/cs4_online_node-arch_d10_a5.0 \
        results/dsl_eval/cs5_eval_node_v0 results/dsl_eval/cs5_eval_node_evolved results/dsl_eval/cs5_eval_node_v0-r2 \
        --tag cs7_offline_replay ;;
  # CS7-eval: held-out tasks on PM, per-node architecture (alpha of cs0), prompt core v1-alt, 20 designs per task:
  #   gate        one loop, noise-free gate (the CS6 setting moved to the per-node architecture)
  #   sim         one loop per release (rows, matrix), own-row check, 1 tighten round, simulated choice (no gate)
  #   sim-noown   the same without the own-row check (its ablation)
  #   small       sim on CU and Do triangle (the graphs where the row program beats the matrix program)
  cs7-eval)
    NODE=(--node-bounds --clip-alpha "$(alpha)" --tasks "$HELD_OUT" --designs 20 --prompt v1-alt)
    design_run cs7_node_v1alt_gate "${NODE[@]}" --restarts 1
    design_run cs7_node_v1alt_sim "${NODE[@]}" --select simulated --own-row-check --tighten 1
    design_run cs7_node_v1alt_sim-noown "${NODE[@]}" --select simulated --tighten 1
    design_run cs7_node_v1alt_sim_cudo "${NODE[@]}" --datasets CU,Do --tasks triangle --select simulated \
      --own-row-check --tighten 1 ;;
  cs7-summary)
    run "$PY" scripts/summarize_cs7.py --out results/cs7_summary.md ;;
  cs7-all)
    echo "[cs7-all] $(date -u +%FT%TZ) start"
    "$0" check
    "$0" cs7-offline > results/cs7_offline.log 2>&1 &
    offline_pid=$!
    until curl -sf "$URL_8B/models" >/dev/null; do echo "waiting for $URL_8B"; sleep 15; done
    "$0" cs7-eval
    wait "$offline_pid" || { echo "[cs7-all] cs7-offline failed, see results/cs7_offline.log" >&2; exit 1; }
    "$0" cs7-summary
    echo "[cs7-all] $(date -u +%FT%TZ) done: results/cs7_summary.md" ;;

  *)
    sed -n '2,55p' "$0"; exit 2 ;;
esac
