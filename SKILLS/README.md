# SKILLS

本目录已重构为可触发的 Codex skills。

## 目录约定

- 可触发 skills：`SKILLS/skills/<skill-name>/SKILL.md`
- 每个 skill 可包含：
- `references/` 领域参考
- `agents/openai.yaml` UI 元数据

## 使用方式

1. 先在 `SKILLS/catalog/*.yaml` 选择主题与 skill。
2. 通过 skill 名称触发，例如：`$add-api-endpoint`。
3. 按 skill 内工作流执行，按需读取其 `references/`。

## 维护规则

- 每次新增能力优先新增独立 skill，而不是堆叠在通用文档。
- 变更时优先更新对应 skill 的 `SKILL.md` 与 `references/`。
- 保持 frontmatter 的 `name` 与目录名一致。
