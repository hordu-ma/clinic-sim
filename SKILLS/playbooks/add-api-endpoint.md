# Playbook: Add API Endpoint

目标：新增一个可用、可测试、可维护的 API。

步骤：

1. 在 schemas 中定义请求与响应模型。
2. 在 routes 中新增路由函数，仅做参数校验与依赖注入。
3. 在 services 中新增业务逻辑函数。
4. 如需数据访问，使用 models 与异步会话。
5. 在 tests 中新增对应测试用例。
6. 通过本地运行验证接口返回与错误处理。

校验点：

- route 层不写业务逻辑
- service 层不硬编码配置
- 返回结构与 schema 一致
