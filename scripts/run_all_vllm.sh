#!/usr/bin/env bash
# Run every experiment against the local vLLM servers (serve_node.sh / serve_curator.sh),
# on CU, Do, ML, CS, EE. PM is left out: its prompts (~100k tokens) exceed Qwen3's 32k context.
#
# Run from the repository root with the PSC environment active:
#   bash scripts/run_all_vllm.sh
#   ONLY="gt exp1" bash scripts/run_all_vllm.sh      # a subset of the steps below
#
# A step whose results/<exp>/<tag>/summary.json exists is skipped, so the script
# can be restarted after an interruption. An interrupted step leaves a directory
# without summary.json; move or delete it before restarting.
set -euo pipefail
cd "$(dirname "$0")/.."

CONFIG=${CONFIG:-config.vllm.toml}
PREFIX=${PREFIX:-qwen3-8b+32b}
DATASETS=${DATASETS:-CU,Do,ML,CS,EE}
RUNS=${RUNS:-10}
ONLY=${ONLY:-gt smoke exp1 exp3 exp2 exp4 exp5 exp6}

python -c "import agentscope" 2>/dev/null || { echo "agentscope missing; activate the PSC environment (e.g. source ~/venvs/psc/bin/activate)" >&2; exit 1; }

mapfile -t URLS < <(python -c "
from psc.models import ModelConfig
c = ModelConfig.from_env(None, config_path='$CONFIG')
print(c.endpoint('node')); print(c.endpoint('curator'))")
for url in "${URLS[@]}"; do
  curl -sf -m 10 "$url/models" > /dev/null || { echo "vLLM server not reachable at $url (start scripts/serve_node.sh and scripts/serve_curator.sh)" >&2; exit 1; }
done
echo "node=${URLS[0]} curator=${URLS[1]} datasets=$DATASETS runs=$RUNS steps: $ONLY"

step() {  # step <name> <results subdir> <tag> <command...>
  local name=$1 dir=results/$2/$3; shift 3
  [[ " $ONLY " == *" $name "* ]] || return 0
  if [[ -f $dir/summary.json ]]; then
    echo "== $name: done ($dir), skipped"; return 0
  fi
  if [[ -e $dir ]]; then
    echo "== $name: $dir exists without summary.json (interrupted run); move or delete it, then rerun" >&2; exit 1
  fi
  echo "== $name: $(date '+%F %T') -> $dir"
  "$@"
}

run() { python scripts/run_experiments.py --config "$CONFIG" "$@"; }

# Ground truth of the LDP mechanisms, no LLM (CPU only, minutes)
step gt    ground_truth gt_5ds_r1000 python scripts/run_ground_truth.py --datasets "$DATASETS" --runs 1000 --tag gt_5ds_r1000
# 1 run per setting on CU, Do: checks both servers, parsing and speed before the long runs
step smoke pilot "${PREFIX}_smoke"     run --exp pilot --runs 1 --tag "${PREFIX}_smoke"
step exp1  exp1  "${PREFIX}_exp1_5ds"  run --exp exp1 --datasets "$DATASETS" --runs "$RUNS" --tag "${PREFIX}_exp1_5ds"
step exp3  exp3  "${PREFIX}_exp3"      run --exp exp3 --runs "$RUNS" --tag "${PREFIX}_exp3"
step exp2  exp2  "${PREFIX}_exp2"      run --exp exp2 --runs "$RUNS" --tag "${PREFIX}_exp2"
step exp4  exp4  "${PREFIX}_exp4"      run --exp exp4 --runs "$RUNS" --tag "${PREFIX}_exp4"
step exp5  exp5  "${PREFIX}_exp5_5ds"  run --exp exp5 --datasets "$DATASETS" --runs "$RUNS" --tag "${PREFIX}_exp5_5ds"
step exp6  exp6  "${PREFIX}_exp6_5ds"  run --exp exp6 --datasets "$DATASETS" --runs "$RUNS" --tag "${PREFIX}_exp6_5ds"

echo "== all requested steps finished: $(date '+%F %T')"
