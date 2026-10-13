#!/usr/bin/env bash
# Run one paper experiment with hy3-ioa (config.hy3.toml; key and URL from .env).
# Run from anywhere; results go to results/<exp>/<TAG>/.
#
#   bash scripts/run_hy3.sh exp1   # Table 2: Naive / PSC (+ TriTR), six datasets
#   bash scripts/run_hy3.sh exp2   # Fig. 2: eps in {1.0, 1.5, 2.0, 2.5, 3.0}, CU / Do (+ TriTR)
#   bash scripts/run_hy3.sh exp3   # Table 3: PSC vs PSC-B (+ TriTR), CU / Do, triangle + 3-star
#   bash scripts/run_hy3.sh exp4   # Fig. 3: budget allocation r1 / r2, CU / ML, triangle
#   bash scripts/run_hy3.sh exp5   # Table 4: RAW / REFINED / PSC-noDP, six datasets
#   bash scripts/run_hy3.sh exp6   # Table 5: Naive+RAW vs Naive+REFINED, six datasets
#
# Datasets: --datasets CU,Do (or -d CU,Do, or DATASETS=CU,Do); choose from CU,Do,ML,CS,EE,PM.
#   bash scripts/run_hy3.sh exp1 --datasets CU,Do,ML --verbose
#
# Runs per method and setting: --runs 5 (or -n 5, or RUNS=5); default 10.
#
# exp1 / exp2 / exp3 also run the agent-based TriTR (WITH_TRITR=0 to skip; TRITR_ALPHA=0 is
# the projection margin) and append pure-Python GT-PSC / GT-TriTR over GT_RUNS=1000 runs
# (GT_RUNS=0 to skip). --methods (or -m, or METHODS=) picks the agent methods instead:
# exp1 / exp2 from Naive,PSC,TriTR, exp3 from PSC,PSC-B,TriTR, e.g.
#   bash scripts/run_hy3.sh exp1 -d CU,Do --methods Naive,TriTR --runs 5 --verbose
# Naive prompt: --naive-prompt paper (or NAIVE_PROMPT=paper) drops the curator system prompt and the
# step-by-step/JSON answer instruction, sending only the paper's prompt; the tag gets _paperprompt.
#   CONFIG=config.dsv3.toml bash scripts/run_hy3.sh exp1 -d CU,Do -m Naive --naive-prompt paper
# --naive-prompt paper-direct adds an instruction to answer with the final number only, without reasoning.
# Other overrides: TASKS=degree,2-star,3-star,triangle MECHANISM=floor_tight TAG=name
# The default tag starts with the config name: config.dsv3-1226.toml -> dsv3-1226_exp1_..., config.hy3.toml -> hy3-ioa_...
#   CONFIG=config.dsv3-1226.toml TASKS=2-star bash scripts/run_hy3.sh exp1 -d CU,Do -m Naive,PSC
# Unset TASKS keeps the experiment's default tasks of run_experiments.py.
# Further arguments go to run_experiments.py, e.g. --verbose, or --dry-run (exp1 only).
set -euo pipefail
cd "$(dirname "$0")/.."

ALL_DATASETS=CU,Do,ML,CS,EE,PM
EXP=${1:-}
case $EXP in
  exp1|exp5|exp6) default_datasets=$ALL_DATASETS ;;
  exp2|exp3)      default_datasets=CU,Do ;;
  exp4)           default_datasets=CU,ML ;;
  *) echo "usage: bash scripts/run_hy3.sh exp1|exp2|exp3|exp4|exp5|exp6 [--datasets CU,Do] [--methods ...] [--runs N] [run_experiments.py args]" >&2; exit 1 ;;
esac
shift

forward=()
while (($#)); do
  case $1 in
    -d|--d|--datasets|-m|--methods|-n|--runs|--naive-prompt)
      [[ $# -ge 2 ]] || { echo "$1 needs a value" >&2; exit 1; }
      case $1 in
        -d|--d|--datasets) DATASETS=$2 ;;
        -m|--methods)      METHODS=$2 ;;
        --naive-prompt)    NAIVE_PROMPT=$2 ;;
        *)                 RUNS=$2 ;;
      esac
      shift 2 ;;
    --datasets=*)     DATASETS=${1#*=}; shift ;;
    --methods=*)      METHODS=${1#*=}; shift ;;
    --runs=*)         RUNS=${1#*=}; shift ;;
    --naive-prompt=*) NAIVE_PROMPT=${1#*=}; shift ;;
    *)            forward+=("$1"); shift ;;
  esac
done

CONFIG=${CONFIG:-config.hy3.toml}
RUNS=${RUNS:-10}
MECHANISM=${MECHANISM:-floor_tight}
DATASETS=${DATASETS:-$default_datasets}
PYTHON=${PYTHON:-.venv/bin/python}

for ds in ${DATASETS//,/ }; do
  [[ ,$ALL_DATASETS, == *,$ds,* ]] || { echo "unknown dataset $ds; choose from $ALL_DATASETS" >&2; exit 1; }
done
ds_tag=${DATASETS//,/-}
[[ $DATASETS == "$ALL_DATASETS" ]] && ds_tag=all6
[[ -n ${TASKS:-} ]] && ds_tag+=_${TASKS//,/-}

args=(--exp "$EXP" --config "$CONFIG" --datasets "$DATASETS" --runs "$RUNS" --mechanism "$MECHANISM")
method_tag=
if [[ $EXP == exp1 || $EXP == exp2 || $EXP == exp3 ]]; then
  WITH_TRITR=${WITH_TRITR:-1}
  TRITR_ALPHA=${TRITR_ALPHA:-0}
  GT_RUNS=${GT_RUNS:-1000}
  if [[ -n ${METHODS:-} ]]; then
    args+=(--methods "$METHODS")
    method_tag=_${METHODS//,/-}
    if [[ ,$METHODS, == *,TriTR,* ]]; then
      args+=(--tritr-alpha "$TRITR_ALPHA")
      method_tag+=-a$TRITR_ALPHA
    fi
  elif [[ $WITH_TRITR == 1 ]]; then
    args+=(--with-tritr --tritr-alpha "$TRITR_ALPHA")
    method_tag=_tritr-a$TRITR_ALPHA
  fi
  args+=(--gt-runs "$GT_RUNS")
elif [[ -n ${METHODS:-} ]]; then
  echo "--methods applies to exp1, exp2, exp3" >&2; exit 1
fi
if [[ -n ${TASKS:-} ]]; then
  args+=(--tasks "$TASKS")
fi
NAIVE_PROMPT=${NAIVE_PROMPT:-default}
if [[ $NAIVE_PROMPT != default ]]; then
  args+=(--naive-prompt "$NAIVE_PROMPT")
  method_tag+=_${NAIVE_PROMPT}prompt
fi
model_tag=$(basename "$CONFIG" .toml)
model_tag=${model_tag#config.}
[[ $model_tag == hy3 ]] && model_tag=hy3-ioa
TAG=${TAG:-${model_tag}_${EXP}_${ds_tag}_r${RUNS}_${MECHANISM}${method_tag}}
args+=(--tag "$TAG")

echo "== $EXP: config=$CONFIG datasets=$DATASETS runs=$RUNS mechanism=$MECHANISM tasks=${TASKS:-default}${METHODS:+ methods=$METHODS}${GT_RUNS:+ gt_runs=$GT_RUNS} naive_prompt=$NAIVE_PROMPT -> results/$EXP/$TAG"
exec "$PYTHON" scripts/run_experiments.py "${args[@]}" "${forward[@]}"
