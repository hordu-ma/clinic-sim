# Startup Commands

## vLLM

`src/scripts/start_vllm_dev.sh`

Common env vars:

- `MODEL_PATH`
- `PORT`
- `MAX_MODEL_LEN`
- `GPU_MEMORY_UTILIZATION`

## API + DB + MinIO

`docker compose -f src/infra/compose/dev.yml up -d`

## Frontend

From `src/apps/web`:

- `npm install`
- `npm run dev`

## Shutdown

- Stop frontend process
- `docker compose -f src/infra/compose/dev.yml down`
- Stop vLLM process
