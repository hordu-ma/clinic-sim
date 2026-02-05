# Full-Stack LLM Engineering Skill（Production-Ready）

---

## 0. Skill Identity

- **Skill Name**: Full-Stack LLM Engineering Skill
- **Owner**: Project Maintainer
- **Execution Environment**: WSL2 + VS Code + Agent (Claude / Codex)
- **Primary Goal**: 在不破坏既有系统的前提下，稳定、高质量地交付 LLM 驱动的 Web 服务

---

## 1. 技术栈边界（已固化，不再讨论）

- Backend: FastAPI
- LLM: HTTP / SDK 调用（禁止直写在 route 中）
- Database: PostgreSQL
- Cache / Queue（可选）: Redis
- Reverse Proxy: Nginx
- Container: Docker / docker-compose
- Frontend: Vue 3 + TypeScript
- OS: Linux（WSL / Server）

---

## 2. 强制工程结构（执行前即约束）

```text
project-root/
├── main.py                     # 可选：最小入口/本地跑
├── pyproject.toml
├── src/
│   ├── apps/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py          # FastAPI 应用入口
│   │   │   ├── config.py        # 配置加载（pydantic-settings）
│   │   │   ├── dependencies.py  # 依赖注入（DB session / JWT 鉴权）
│   │   │   ├── exceptions.py    # 统一异常处理
│   │   │   ├── middleware.py    # 中间件（Trace ID / 日志）
│   │   │   ├── logging_config.py
│   │   │   ├── rate_limit.py
│   │   │   ├── routes/          # 路由层（只做参数与响应）
│   │   │   ├── schemas/         # Pydantic models
│   │   │   ├── services/        # 业务 + LLM 调用（核心）
│   │   │   ├── models/          # SQLAlchemy ORM 模型
│   │   │   ├── migrations/      # Alembic 迁移
│   │   │   └── utils/           # 工具函数（JWT 等）
│   │   └── web/
│   │       └── src/
│   │           ├── api/         # 所有接口封装
│   │           └── types/       # 接口类型定义
│   ├── infra/
│   │   └── compose/             # dev/prod compose & nginx 配置
│   ├── cases/
│   ├── docs/
│   └── scripts/
├── tests/                       # pytest 测试（项目根目录）
└── SKILL.md
```

❗ 禁止在 route 中直接调用 LLM  
❗ 禁止在业务逻辑中直接写 Nginx / Docker 细节

---

## 3. 本 Skill 可执行的任务类型

执行前必须明确属于以下哪一类（可多选）：

- [ ] 新增 FastAPI 接口
- [ ] 修改 / 重构已有接口
- [ ] 接入 / 调整大模型调用
- [ ] PostgreSQL 数据结构或访问逻辑调整
- [ ] Redis 引入（缓存 / 锁 / 队列）
- [ ] Docker / docker-compose 调整
- [ ] Nginx 反向代理配置调整
- [ ] 前后端接口对齐
- [ ] 排障（dev / prod）

---

## 4. 执行输入（必须给齐）

Agent 在执行前，必须确认以下信息：

1. 任务目标（一句话）
2. 影响范围（backend / frontend / infra）
3. 是否允许：
   - 修改数据库结构
   - 修改 nginx
   - 修改 docker-compose
4. 运行环境：dev / prod
5. 是否涉及 LLM 推理或 RAG

缺失任何一项 → 先询问，不执行

---

## 5. FastAPI 执行规范（硬约束）

### 5.1 Route 层

- 只做：
  - 参数校验
  - Dependency 注入
  - Response 返回
- 不做：
  - 业务判断
  - LLM 调用
  - SQL 查询

### 5.2 Service 层（核心）

- 所有 LLM 调用必须：
  - 有 timeout
  - 有异常捕获
  - 有日志
- 必须显式区分：
  - prompt 构造
  - 模型调用
  - 结果后处理

### 5.3 Schema

- 所有 API：
  - 必须有 request / response schema
  - 不允许返回裸 dict

---

## 6. LLM 调用专用规则

- 模型配置统一放在 `src/apps/api/app/core/config.py`
- 不在代码中硬编码：
  - API Key
  - Base URL
- 必须考虑：
  - 超时（默认 ≤ 60s）
  - 重试（最多 2 次）
  - 错误映射为业务错误

---

## 7. PostgreSQL 规则

- 使用 ORM 或封装层
- 不在 service 中直接写 SQL（除非说明）
- 生产环境：
  - ❌ 禁止自动 migration
  - ❌ 禁止 DROP / TRUNCATE

---

## 8. Redis 使用规则（如引入）

必须明确用途之一：

- 缓存（必须 TTL）
- 分布式锁
- 队列 / 状态标记

禁止：

- 当数据库使用
- 永久数据存储

---

## 9. Docker / Compose 规则

- dev 与 prod compose 分离
- Dockerfile 中：
  - 不写密钥
  - 不写环境差异逻辑
- 服务必须：
  - 可单独启动
  - 可被 Nginx 代理

---

## 10. Nginx 规则

- 仅承担：
  - 反向代理
  - TLS / Header
- upstream 明确指向容器服务名
- 不做业务判断

---

## 11. Frontend（Vue3）对齐规则

- 所有 API：
  - 必须在 `src/api/` 统一封装
  - 必须有 TypeScript 类型
- 不在组件中直接拼 URL
- 不处理后端异常细节

---

## 12. 安全与变更控制

以下操作必须 显式二次确认：

- 覆盖 nginx 配置
- 覆盖 docker-compose.prod.yml
- 数据库结构修改
- 生产环境部署

---

## 13. 输出要求（Agent 必须给出）

每次执行结束，必须输出：

- 本次修改清单（文件级）
- 是否破坏已有接口（Yes / No）
- 新增 / 修改接口示例
- 是否需要手动操作（如 migration / reload）

---

## 14. 调用方式（对 Agent）

在对话中直接使用：

> 请严格遵循 `skill.md`，执行以下任务：
> （任务描述）

---

## 15. 演进规则

- 新项目 → 复用本 Skill
- 新坑 → 只允许追加规则
- 不允许为了方便删规则

---

**本 Skill 是工程约束，不是建议。**
