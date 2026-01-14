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

### 核心原则

- 后端**只依赖 OpenAI 兼容接口**
- 推理服务地址通过 `LLM_BASE_URL` 切换
- 开发 / 生产架构保持一致
- 所有用户行为与结果**可审计、可复现**

---

## 二、阶段 1：本地开发基座搭建

### 1. 运行环境

- Windows 11
- WSL2 + Ubuntu
- Docker Desktop（WSL2 backend）
- NVIDIA RTX Pro 500（CUDA 可用）

> 建议：**所有服务运行在 WSL2 内**，避免 Windows/WSL CUDA 混用问题

### 2. 仓库结构（建议）

```
clinic-sim/
├─ apps/
│  ├─ api/              # FastAPI 后端
│  └─ web/              # 前端
├─ infra/
│  ├─ compose/
│  │  ├─ dev.yml        # 本地开发
│  │  ├─ prod-b.yml     # 生产 B（GPU）
│  │  └─ prod-a.yml     # 生产 A（前端）
│  └─ nginx/
├─ cases/               # 病例 JSON
├─ docs/
└─ scripts/
```

### 3. 本地 Docker Compose（dev）

- postgres
- minio
- api（FastAPI）
- vLLM **先独立运行（非 compose）**

---

## 三、阶段 2：本地 vLLM（GPU）推理服务

### 1. 模型选择建议

- Qwen 小参量模型（1.5B / 3B / 7B）
- 显存不足时：
  - 降低 `max_model_len`
  - 控制并发
  - 使用量化模型

### 2. 启动 vLLM

- 运行于 WSL2
- 提供 OpenAI 兼容接口：
  - `/v1/models`
  - `/v1/chat/completions`
- 示例环境变量：

```env
LLM_BASE_URL=http://127.0.0.1:8001
LLM_MODEL=qwen-xxx
```

### 3. 验证

- curl / Postman 调用
- 确认：
  - 流式输出
  - 首 token 延迟
  - 并发不 OOM

---

## 四、阶段 3：FastAPI 后端骨架

### 1. 技术栈

- FastAPI
- uv（依赖管理）
- SQLAlchemy 2.x + Alembic
- httpx（调用 vLLM）
- SSE（Streaming Response）

### 2. 必要配置（.env）

```env
DATABASE_URL=postgresql+psycopg://...
MINIO_ENDPOINT=...
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
LLM_BASE_URL=http://127.0.0.1:8001
LLM_MODEL=qwen-xxx
JWT_SECRET=...
ENV=dev
```

### 3. 核心 API（MVP）

- `POST /api/auth/login`
- `GET /api/cases`
- `POST /api/sessions`
- `POST /api/chat`（SSE，核心）

> `/api/chat` 职责：
>
> - 构造 Prompt
> - 调用 vLLM（stream）
> - 流式返回给前端
> - 同步落库（消息、token、耗时）

---

## 五、阶段 4：病例系统与病人角色常驻

### 1. 病例数据结构（JSON）

- 基本信息（年龄、性别、职业）
- 主诉 / 现病史
- 既往史 / 用药 / 过敏
- 体征（可见 / 需询问）
- 可申请检查清单
- 标准答案（诊断 / 鉴别）

### 2. 检查解锁机制

- `POST /api/actions/request-test`
- 后端校验合法性
- 返回检查结果并记录

### 3. Prompt 结构

- **System**：永远是病人，不做诊断
- **Developer**：病例约束 + 可回答范围
- **User**：学生提问
- **Context**：已解锁信息摘要

> 建议：每轮对话后生成“结构化摘要状态”，避免上下文爆炸

---

## 六、阶段 5：数据层（PostgreSQL + MinIO）

### 1. 核心表

- users
- cases
- sessions
- messages
- test_requests
- scores
- audit_logs

### 2. MinIO 用途

- 会话导出（PDF / JSON）
- 比赛提交产物
- 教师端报告

---

## 七、阶段 6：评分系统

### 1. 规则评分（优先）

- 关键问诊点覆盖率
- 红旗症状识别
- 鉴别诊断关键词
- 检查申请合理性

### 2. 模型点评（后置）

- 输出结构化 JSON
- 保存上下文与模型版本
- 可回放、可审计

### 3. 评估与排行榜工作流（与病人 persona 解耦）

- 主对话链路：系统/开发者 Prompt 固化“只当病人、不做诊断”，历史上下文仅含 user/assistant 消息，避免评分语境污染。
- 评估链路：后台任务读取病例标准答案/关键点 + 会话摘要或最近 N 轮 + 用户诊断 + 已申请检查，优先规则评分，可选 LLM 点评输出结构化 JSON，写入 scores（含规则/模型版本、trace_id、输入摘要）。
- 持久化：messages 落 tokens/latency，sessions 管状态，scores 存评分 JSON，audit_logs 记触发与 trace_id。
- 排行榜：批处理或视图聚合用户平均分、最近 N 次平均、完成场次，写入 leaderboard 表/物化视图；提供 `/api/leaderboard` 供前端读取。

---

## 八、阶段 7：前端联调（简述）

- 移动端聊天 UI
- SSE 流式渲染
- 病例选择 / 会话历史
- 检查申请面板

---

## 九、阶段 8：工程化与质量

### 必须项

- 请求日志与 trace_id
- 限流（用户 / IP）
- 超时与断流处理
- Alembic 数据迁移
- 单元测试 / 集成测试

### 可观测性（生产）

- QPS / 延迟 / 错误率
- GPU 利用率
- OOM 监控

---

## 十、阶段 9：生产部署（A/B 双机）

### B 服务器（GPU）

- Docker Compose：
  - api
  - vllm
  - postgres
  - minio
- vLLM 参数按 GPU 调优

### A 服务器（入口）

- Nginx
- 静态前端
- SSE 反代（禁用缓冲）

---

## 十一、推荐推进顺序（重要）

1. 稳定 vLLM（本地 GPU）
2. FastAPI SSE 转发
3. 病例 + 检查解锁
4. 会话与消息落库
5. 规则评分
6. 评估与排行榜落库/聚合（不干扰病人 persona）
6. 前端体验
7. 比赛与教师端能力

---

## 说明

本文档适合直接存入 **Obsidian**，作为：

- 项目总设计文档
- 实施检查清单
- 后续迭代的基准版本
