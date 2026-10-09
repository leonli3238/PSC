#!/usr/bin/env bash
# vLLM server for the node agents: Qwen3-8B, one data-parallel replica per GPU.
# Run on the GPU host:  bash scripts/serve_node.sh
# Override e.g.:        GPUS=0,1,2,3 PORT=8000 MODEL_PATH=/models/Qwen3-8B bash scripts/serve_node.sh
# The served name must match node_model in config.vllm.toml; the URL goes in
# VLLM_NODE_BASE_URL of .env (http://<host>:$PORT/v1).
set -euo pipefail

MODEL_PATH=${MODEL_PATH:-/models/Qwen3-8B}
GPUS=${GPUS:-0,1,2}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.90}

if ! command -v vllm > /dev/null; then
  echo "vllm not found; activate the vLLM environment first, e.g. source ~/venvs/vllm/bin/activate" >&2
  exit 1
fi
if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "no model at $MODEL_PATH; download it first, e.g." >&2
  echo "  huggingface-cli download Qwen/Qwen3-8B --local-dir $MODEL_PATH" >&2
  echo "  modelscope download --model Qwen/Qwen3-8B --local_dir $MODEL_PATH" >&2
  exit 1
fi

NUM_GPUS=$(awk -F, '{print NF}' <<< "$GPUS")
# GPU indices as listed by nvidia-smi
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=$GPUS
echo "Qwen3-8B on GPUs $GPUS (data parallel $NUM_GPUS), http://$HOST:$PORT/v1"

exec vllm serve "$MODEL_PATH" \
  --served-model-name Qwen3-8B \
  --data-parallel-size "$NUM_GPUS" \
  --max-model-len "$MAX_MODEL_LEN" \
  --enable-prefix-caching \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --host "$HOST" --port "$PORT"
