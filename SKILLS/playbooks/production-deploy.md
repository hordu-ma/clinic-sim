# Playbook: Production Deploy

目标：稳定、安全地部署生产环境。

步骤：

1. 确认环境变量完整。
2. 分别部署 A/B 服务器编排。
3. 校验 Nginx 与 SSE 配置。
4. 禁用生产 Swagger。
5. 验证接口与前端访问。

校验点：

- JWT 密钥未硬编码
- 仅开放必要端口
- A/B 分层清晰
