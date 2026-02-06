# Playbook: Change DB Model

目标：安全修改数据库模型并完成迁移。

步骤：

1. 修改 models 中的字段定义。
2. 在 migrations 生成迁移脚本。
3. 本地升级数据库并验证表结构。
4. 更新相关 schema 与服务逻辑。
5. 更新测试与必要数据脚本。

校验点：

- 迁移脚本可重复执行
- 不在生产自动 migration
- 更新后所有 API 与测试通过
