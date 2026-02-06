# Playbook: Extend Scoring

目标：扩展或优化评分逻辑，确保可追溯。

步骤：

1. 明确新增维度或规则，更新评分权重。
2. 在 scoring service 中实现规则。
3. 更新评分输出结构与 schema。
4. 增加测试覆盖关键分支。
5. 记录规则版本变更。

校验点：

- scoring_details 能解释分数来源
- 规则版本可追溯
- 无破坏历史评分记录
