# Scripts Index

脚本统一入口说明，命令以 uv run 或现有脚本为准。

当前脚本均位于 src/scripts。

- 本地模型启动：src/scripts/start_vllm_dev.sh
- 主要参数（环境变量）：
  - MODEL_PATH：本地模型路径（默认 Qwen2.5-1.5B-Instruct）
  - HOST：服务监听地址（默认 0.0.0.0）
  - PORT：服务端口（默认 8001）
  - MAX_MODEL_LEN：模型最大上下文长度（默认 2048）
  - GPU_MEMORY_UTILIZATION：显存占用比例（默认 0.7）
  - MAX_NUM_SEQS：并发序列数上限（默认 2）
  - TENSOR_PARALLEL_SIZE：张量并行（默认 1）
  - ATTN_BACKEND：注意力后端（默认 TRITON_ATTN）
  - ENFORCE_EAGER：是否禁用 CUDA graphs（默认 1）
  - DTYPE：推理精度（默认 float16）
  - EXTRA_ARGS：额外 vLLM 参数（默认空）
  - 示例：
    MODEL_PATH=/home/malig/.cache/modelscope/hub/models/Qwen/Qwen2.5-1.5B-Instruct \
     PORT=8001 MAX_MODEL_LEN=1024 GPU_MEMORY_UTILIZATION=0.8 \
     src/scripts/start_vllm_dev.sh
- 病例导入：src/scripts/import_cases.py
- 主要参数：
  - 无
  - 示例：
    uv run python src/scripts/import_cases.py
- 用户同步：src/scripts/sync_users.py
- 主要参数：
  - 可选参数：CSV 文件路径（格式：username,password,full_name,role,external_user_id）
  - 示例（导入演示用户）：
    uv run python src/scripts/sync_users.py
  - 示例（从 CSV 导入）：
    uv run python src/scripts/sync_users.py /path/to/users.csv

## 参数速查表

以下默认值来自 src/scripts/start_vllm_dev.sh。

- MODEL_PATH：/home/malig/.cache/modelscope/hub/models/Qwen/Qwen2.5-1.5B-Instruct
- HOST：0.0.0.0
- PORT：8001
- MAX_MODEL_LEN：2048
- GPU_MEMORY_UTILIZATION：0.7
- MAX_NUM_SEQS：2
- TENSOR_PARALLEL_SIZE：1
- ATTN_BACKEND：TRITON_ATTN
- ENFORCE_EAGER：1
- DTYPE：float16
- EXTRA_ARGS：空
