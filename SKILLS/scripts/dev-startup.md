# Dev Startup

1. 启动 vLLM

- src/scripts/start_vllm_dev.sh

2. 启动后端与依赖

- docker compose -f src/infra/compose/dev.yml up -d

3. 启动前端

- cd src/apps/web
- npm install
- npm run dev
