# Contributing to ChemClaw

感谢你为 ChemClaw 贡献。ChemClaw 是面向化学工作流的 skills 仓库。

安装方式：

```bash
npx skills add AI4Chem/ChemClaw
```

## Contribution Guide

- 1) Fork + Clone + Branch（先准备开发环境）
  - Fork 仓库到个人账号
  - 克隆 fork 并设置上游：

```bash
git clone https://github.com/<your-username>/ChemClaw
cd ChemClaw
git remote add upstream https://github.com/AI4Chem/ChemClaw
```

  - 同步主分支并创建功能分支：

```bash
git checkout main
git pull upstream main
git checkout -b feat/<category>-<skill-name>
```

- 2) 创建或修改 Skill（在分支上开发）
  - 目录位置：`skills/<skill-name>/`
  - 最少文件：`SKILL.md`
  - 可选文件：`scripts/`、`requirements.txt`、`assets/`、`examples/`、`references/`、`tests/`
  - 何时使用可选目录
    - `scripts/`：需要可复用脚本时（如解析、预测、转换）
    - `examples/`：需要提供标准输入输出样例时
    - `references/`：需要放算法说明、外部规范、术语解释时
    - `tests/`：有脚本且可自动验证时

- `SKILL.md` 必填规范
  - frontmatter 必须包含：`name`、`description`
  - `name` 规则
    - 使用小写 kebab-case（如 `mol-image-to-smiles`）
    - 与文件夹名保持一致
  - `description` 规则
    - 一句话写清能力
    - 一句话写清触发场景（建议以 `Use when ...` 开头）
    - 避免空泛描述，尽量包含输入/输出关键词

- `SKILL.md` 建议正文大纲
  - 目标与适用场景
  - 输入格式与约束（字段、单位、允许格式）
  - 核心流程（编号步骤）
  - 输出格式约定（文本、JSON、表格、文件）
  - 错误处理与边界条件
  - 最少一个正向示例；如有歧义场景，补一个反例

- `SKILL.md` Recommended Outline

```md
---
name: your-skill-name
description: What this skill does. Use when users need this capability.
---

# Skill Title

## Overview
(Detailed introduction of the skill, including use cases and technical context.)

## Prerequisites
(Required environment setup, dependencies, and assumptions.)

## Workflow
(Step-by-step instructions for how the agent should execute the task.)

## Best Practices
(Practical tips, caveats, and common pitfalls.)

## Examples
(Concrete usage examples to guide behavior.)

## Troubleshooting
(Common issues and how to resolve them.)
```

- 测试建议
  - 覆盖一个正常输入（happy path）
  - 覆盖一个边界或噪声输入（edge case）
  - 若 skill 依赖脚本，补充脚本运行命令和依赖安装方式

- 3) 提交与 PR

```bash
git add .
git commit -m "feat(<skill>): add <skill-name>"
git push origin feat/<category>-<skill-name>
```

- 在 GitHub 发起 PR，并在描述中写清
  - 变更内容（新增/修改哪些文件）
  - 为什么这样设计
  - 如何验证（命令、样例、截图）
  - 影响范围（是否影响已有 skill）

- Review 迭代
  - 根据 review 评论在同一分支继续提交
  - 不需要新开 PR，push 后会自动更新当前 PR

- PR 质量要求
  - 一个 PR 聚焦一件事（一个 skill 或一个明确修复）
  - 不提交无关文件和大体积无用资源
  - 有脚本就写最小可运行说明（依赖 + 命令）
  - 文档与实现保持一致（`name`、目录名、README/示例同步）
