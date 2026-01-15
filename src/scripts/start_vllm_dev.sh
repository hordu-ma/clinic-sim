#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for local vLLM (OpenAI compatible) on WSL/Linux.
# Designed for small GPUs (e.g., 6GB) to run Qwen2.5-1.5B-Instruct first.

# Default to downloaded Qwen2.5-1.5B-Instruct under ModelScope cache; override via MODEL_PATH if needed.
MODEL_PATH="${MODEL_PATH:-/home/malig/.cache/modelscope/hub/models/Qwen/Qwen2.5-1.5B-Instruct}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8001}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-1024}"          # shrink further if OOM
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.7}"  # lower for 6GB GPUs
MAX_NUM_SEQS="${MAX_NUM_SEQS:-2}"               # concurrent sequences cap
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
ATTN_BACKEND="${ATTN_BACKEND:-TRITON_ATTN}"  # TRITON_ATTN avoids flash PTX issues
ENFORCE_EAGER="${ENFORCE_EAGER:-1}"             # disable CUDA graphs by default
DTYPE="${DTYPE:-float16}"                       # prefer smaller memory footprint
EXTRA_ARGS="${EXTRA_ARGS:-}"                    # e.g., "--enable-metrics"

if [ ! -d "$MODEL_PATH" ]; then
  echo "Model path not found: $MODEL_PATH" >&2
  echo "Set MODEL_PATH to your local model directory (HuggingFace/modelscope layout)." >&2
  exit 1
fi

echo "Starting vLLM with model: $MODEL_PATH"
echo "Host: $HOST  Port: $PORT  Max len: $MAX_MODEL_LEN  GPU mem util: $GPU_MEMORY_UTILIZATION  Max seqs: $MAX_NUM_SEQS"

# 使用项目虚拟环境中的 python
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"

if [ ! -f "$PYTHON_CMD" ]; then
  echo "Project venv not found: $PYTHON_CMD" >&2
  echo "Please run 'uv sync' first." >&2
  exit 1
fi

$PYTHON_CMD -m vllm.entrypoints.openai.api_server \
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
