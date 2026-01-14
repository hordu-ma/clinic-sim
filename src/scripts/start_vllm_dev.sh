#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for local vLLM (OpenAI compatible) on WSL/Linux.
# Designed for small GPUs (e.g., 6GB) to run Qwen2.5-1.5B-Instruct first.

# Default to downloaded Qwen2.5-1.5B-Instruct under ModelScope cache; override via MODEL_PATH if needed.
MODEL_PATH="${MODEL_PATH:-/home/malig/.cache/modelscope/hub/models/Qwen/Qwen2.5-1.5B-Instruct}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8001}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-2048}"          # shrink to 1536/1024 if OOM
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.85}"  # lower to 0.75 if tight
MAX_NUM_SEQS="${MAX_NUM_SEQS:-3}"               # concurrent sequences cap
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
ATTN_BACKEND="${ATTN_BACKEND:-}"                # e.g., TRITON_ATTN to avoid flash kernels
ENFORCE_EAGER="${ENFORCE_EAGER:-}"              # set to 1 to disable CUDA graphs
DTYPE="${DTYPE:-}"                              # e.g., float16/bfloat16/auto
EXTRA_ARGS="${EXTRA_ARGS:-}"                    # e.g., \"--enable-metrics\"

if [ ! -d "$MODEL_PATH" ]; then
  echo "Model path not found: $MODEL_PATH" >&2
  echo "Set MODEL_PATH to your local model directory (HuggingFace/modelscope layout)." >&2
  exit 1
fi

echo "Starting vLLM with model: $MODEL_PATH"
echo "Host: $HOST  Port: $PORT  Max len: $MAX_MODEL_LEN  GPU mem util: $GPU_MEMORY_UTILIZATION  Max seqs: $MAX_NUM_SEQS"

python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
  ${ATTN_BACKEND:+--attention-backend "$ATTN_BACKEND"} \
  ${ENFORCE_EAGER:+--enforce-eager} \
  ${DTYPE:+--dtype "$DTYPE"} \
  $EXTRA_ARGS
