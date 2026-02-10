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

## 系统组件

- 前端：Vue 3 + Vant（移动端友好）
- 后端：FastAPI + SQLAlchemy（异步）
- 模型：vLLM（OpenAI 兼容接口）
- 存储：PostgreSQL（业务数据）、MinIO（对象存储）
- 代理：Nginx（HTTPS 与 SSE 反代）

## 核心流程

登录 → 病例列表 → 创建会话 → 流式问诊 → 申请检查 → 提交诊断 → 查看评分 → 历史会话

## 关键接口

- 认证：`POST /api/auth/login`、`GET /api/auth/me`
- 病例：`GET /api/cases`、`GET /api/cases/{case_id}`、`GET /api/cases/{case_id}/available-tests`
- 会话：`POST /api/sessions`、`GET /api/sessions`、`GET /api/sessions/{session_id}`
- 对话：`POST /api/chat`（SSE）
- 检查：`POST /api/sessions/{session_id}/tests`、`GET /api/sessions/{session_id}/tests`
- 评分：`POST /api/sessions/{session_id}/submit`、`GET /api/sessions/{session_id}/score`

## 开发与部署

- 开发环境与命令：见 [AGENTS.md](AGENTS.md)
- 执行流程（SKILL触发）：见 [SKILLS/README.md](SKILLS/README.md)
- 架构详解：见 [src/docs/ARCHITECTURE.md](src/docs/ARCHITECTURE.md)

## 测试

```bash
pytest                                              # 运行全部测试
pytest --cov=src/apps/api --cov-report=term-missing  # 覆盖率
```

## 可审计数据

- messages（对话内容、token、延迟）
- sessions（状态、诊断提交、时间）
- scores（维度分与评分依据）
- audit_logs（用户行为）
