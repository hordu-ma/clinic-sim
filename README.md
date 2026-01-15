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
