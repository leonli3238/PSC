#!/usr/bin/env bash
# vLLM server for the curator agent / privacy controller (also the Naive answer):
# Qwen3-32B, tensor parallel over the given GPUs.
# Run on the GPU host:  bash scripts/serve_curator_qwen3_32b.sh
# Override e.g.:        GPUS=2,3 PORT=8001 MODEL_PATH=/models/Qwen3-32B bash scripts/serve_curator_qwen3_32b.sh
# The served name must match curator_model in config.vllm.toml; the URL goes in
# VLLM_CURATOR_BASE_URL of .env (http://<host>:$PORT/v1).
set -euo pipefail

MODEL_PATH=${MODEL_PATH:-/models/Qwen3-32B}
GPUS=${GPUS:-3}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8001}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
# BF16 weights take ~66 GB of an H20's 96 GB; the rest is KV cache
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.92}

if ! command -v vllm > /dev/null; then
  echo "vllm not found; activate the vLLM environment first, e.g. source ~/venvs/vllm/bin/activate" >&2
  exit 1
fi
if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "no model at $MODEL_PATH; download it first, e.g." >&2
  echo "  huggingface-cli download Qwen/Qwen3-32B --local-dir $MODEL_PATH" >&2
  echo "  modelscope download --model Qwen/Qwen3-32B --local_dir $MODEL_PATH" >&2
  exit 1
fi

NUM_GPUS=$(awk -F, '{print NF}' <<< "$GPUS")
# Qwen3-32B has 8 KV heads, so the tensor-parallel size must divide 8
case $NUM_GPUS in
  1|2|4|8) ;;
  *) echo "GPUS must list 1, 2, 4 or 8 GPUs, got $NUM_GPUS ($GPUS)" >&2; exit 1 ;;
esac
# GPU indices as listed by nvidia-smi
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=$GPUS
echo "Qwen3-32B on GPUs $GPUS (tensor parallel $NUM_GPUS), http://$HOST:$PORT/v1"

exec vllm serve "$MODEL_PATH" \
  --served-model-name Qwen3-32B \
  --tensor-parallel-size "$NUM_GPUS" \
  --max-model-len "$MAX_MODEL_LEN" \
  --enable-prefix-caching \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --host "$HOST" --port "$PORT"
