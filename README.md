# 临床医学模拟问诊系统（vLLM + FastAPI）开发流程

> 目标：构建一个用于**临床医学教学**的模拟问诊系统
>
> - 学生负责诊断
> - 大模型**始终扮演病人**
> - 本地 Win11（RTX Pro 500）运行 vLLM 做开发
> - 生产环境 A/B 双机部署
> - 全流程 Docker 化，数据可用于后续比赛与评测

---

## 一、总体架构与原则

### 架构分层

- **A 服务器（入口层）**
  - Nginx（HTTPS / SSE 反代）
  - 静态前端（移动端适配 Web）
- **B 服务器（核心层，GPU）**
  - FastAPI（业务后端）
  - vLLM（Qwen，OpenAI 兼容接口）
  - PostgreSQL（核心数据）
  - MinIO（对象存储）

# 临床医学模拟问诊系统

用于临床医学教学的模拟问诊平台：学生负责诊断，LLM 始终扮演病人，完整流程可审计。

## 功能概览

- 登录认证（无注册，外部系统同步用户）
- 病例浏览与筛选（不暴露标准答案）
- 会话创建与历史查询
- SSE 流式对话（医生提问，病人回答）
- 检查申请与结果回显
- 诊断提交与规则评分
- 评分详情可追溯（维度分、关键点覆盖、检查合理性）

## 核心流程

登录 → 病例列表 → 创建会话 → 流式问诊 → 申请检查 → 提交诊断 → 查看评分 → 历史会话

## 系统组件

- 前端：Vue 3 + Vant（移动端友好）
- 后端：FastAPI + SQLAlchemy（异步）
- 模型：vLLM（OpenAI 兼容接口）
- 存储：PostgreSQL（业务数据）、MinIO（对象存储）
- 代理：Nginx（HTTPS 与 SSE 反代）

## 关键接口（摘要）

- 认证：`POST /api/auth/login`、`GET /api/auth/me`
- 病例：`GET /api/cases`、`GET /api/cases/{case_id}`、`GET /api/cases/{case_id}/available-tests`
- 会话：`POST /api/sessions`、`GET /api/sessions`、`GET /api/sessions/{session_id}`
- 对话：`POST /api/chat`（SSE）
- 检查：`POST /api/sessions/{session_id}/tests`、`GET /api/sessions/{session_id}/tests`
- 评分：`POST /api/sessions/{session_id}/submit`、`GET /api/sessions/{session_id}/score`

## 可审计数据

- messages（对话内容、token、延迟）
- sessions（状态、诊断提交、时间）
- scores（维度分与评分依据）
- audit_logs（用户行为）

## 测试

- 后端单元测试与集成测试使用 pytest
- 集成测试覆盖登录 → 会话 → 对话 → 检查 → 评分链路，LLM 调用使用 mock

---

## 本地开发与测试（标准流程）

> 适用于 Linux/WSL + 本地 vLLM 的开发环境

1. 启动本地 vLLM（OpenAI 兼容接口，端口 8001）

```bash
cd /home/malig/code-repos/clinic-sim
MODEL_PATH=/home/malig/.cache/modelscope/hub/models/Qwen/Qwen2___5-1___5B-Instruct \
  src/scripts/start_vllm_dev.sh
```

- 若模型路径不同，请替换 `MODEL_PATH`
- 可通过 `http://localhost:8001/v1/models` 查看模型 ID

2. 启动后端与基础服务（PostgreSQL、MinIO、API）

```bash
cd /home/malig/code-repos/clinic-sim
docker compose -f src/infra/compose/dev.yml up -d
```

3. 启动前端（Vite）

```bash
cd /home/malig/code-repos/clinic-sim/src/apps/web
npm install
npm run dev
```

4. 访问与测试

- 前端：http://localhost:5173/
- 后端：http://localhost:8000
- 仅 dev 可用 Swagger：http://localhost:8000/docs

5. 测试账号

- 用户名：`student1`
- 密码：`password123`

> 注意：Linux/WSL 下需保证 `host.docker.internal` 可解析；dev.yml 已通过 `extra_hosts` 处理。

---

## 生产部署调整（A/B 双机）

1. 采用生产编排

- 入口层（A 服务器）：`src/infra/compose/prod-a.yml`
- 核心层（B 服务器）：`src/infra/compose/prod-b.yml`

2. 关键环境变量（必须显式设置）

- `POSTGRES_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `JWT_SECRET`
- `LLM_BASE_URL`（指向 B 服务器 vLLM）
- `LLM_MODEL`（与 vLLM 暴露的模型 ID 完全一致）

3. Nginx 与 HTTPS

- 部署 `src/infra/compose/nginx/nginx.conf`
- 配置证书文件 `/etc/nginx/ssl/{cert.pem,key.pem}`
- 确保 SSE 路由 `/api/chat` 关闭缓冲

4. 前端发布方式

- 在 A 服务器构建：`npm run build`
- 将 `dist/` 挂载到 Nginx 的静态目录

5. 安全与运维

- 生产环境禁用 Swagger（ENV=production）
- 不使用 dev 默认密码
- 仅开放必要端口（80/443/8000/8001）

---

## 优雅关闭开发环境

测试完成后，按以下顺序关闭服务（先停止请求入口，再停止后端服务）：

```bash
# 1. 关闭前端（在前端终端按 Ctrl+C，或执行）
pkill -f "vite"

# 2. 关闭 Docker 容器（API + PostgreSQL + MinIO）
docker compose -f src/infra/compose/dev.yml down

# 3. 关闭 vLLM（在 vLLM 终端按 Ctrl+C，或执行）
pkill -f "vllm.entrypoints.openai.api_server"
```

**一键关闭**：

```bash
pkill -f "vite" 2>/dev/null
docker compose -f src/infra/compose/dev.yml down
pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null
```
