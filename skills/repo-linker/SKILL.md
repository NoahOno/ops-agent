---
name: repo-linker
description: >
  引导用户将代码仓库关联到流水线，配置认证信息、分支策略和 Webhook。
  当用户需要为流水线配置源码仓库、设置 Git 拉取策略时使用此 skill。
  输出结构化仓库配置（仓库URL/认证方式/凭据ID/默认分支/Webhook触发配置）。
---

# Repo Linker

## 适用场景

- 用户说"关联仓库"、"配置 Git 地址"、"设置源码拉取"
- 创建流水线时选择代码来源
- 修改已有流水线的仓库配置

## 执行流程

```
Step 1  确认目标流水线
  询问: project_name 和 job_name
  调用 list_linked_repos(project_name, job_name) 查看已有关联

Step 2  选择仓库来源
  向用户展示选项:
    a) Coding 仓库 → list_depots(project_id) 列出可选仓库
    b) GitLab 仓库 → gitlab.list_projects(search) 搜索仓库
    c) 外部 Git 仓库 → 用户手动输入 URL

Step 3  配置认证信息
  根据仓库来源引导:
    - Coding: 自动使用 Coding 凭据，无需额外配置
    - GitLab: 询问凭据类型（ssh_key/https_token）和凭据 ID
    - 外部: 询问认证方式和凭据 ID

Step 4  配置分支策略
  引导用户选择:
    - single: 固定分支（如 master/main/release）
    - pattern: 正则匹配（如 release/*, hotfix/*）
    - all: 所有分支

Step 5  配置 Webhook（可选）
  询问是否启用 Webhook 自动触发:
    - 是 → 选择事件类型（push/merge_request/tag_push）
    - 否 → 跳过

Step 6  保存配置
  调用 link_repository 保存
  如配置了 Webhook → 调用 configure_webhook
```

## 认证方式对照

| 仓库来源 | 推荐认证方式 | 凭据来源 |
|---------|------------|---------|
| Coding 仓库 | `coding_credential` | Coding 内置，自动关联 |
| GitLab SSH | `ssh_key` | Jenkins/Coding 凭据管理 |
| GitLab HTTPS | `https_token` | Jenkins/Coding 凭据管理 |
| GitHub | `https_token` | Personal Access Token |
| 自建 GitLab | `ssh_key` 或 `https_token` | 手动配置 |

## 分支策略说明

| 策略 | 适用场景 | 示例 |
|------|---------|------|
| `single` | 固定分支构建 | `master`, `main`, `release-1.0` |
| `pattern` | 多分支构建 | `release/*`, `feature/**`, `hotfix/*` |
| `all` | 任意分支触发 | 配合 MR 事件使用 |

## Webhook 事件类型

| 事件 | 说明 | 典型用途 |
|------|------|---------|
| `push` | 代码推送 | 推送后自动构建 |
| `merge_request` | MR/PR 创建或更新 | MR 检查构建 |
| `tag_push` | 标签推送 | 版本发布构建 |

## 输出格式

```json
{
  "repo_url": "https://coding.example.com/team/project.git",
  "credential_id": "coding-deploy-key",
  "default_branch": "master",
  "auth_type": "coding_credential",
  "branch_strategy": "single",
  "branch_pattern": "",
  "webhook_enabled": true,
  "webhook_events": ["push", "merge_request"]
}
```

## MCP 工具调用

| 步骤 | 工具 |
|------|------|
| 搜索 Coding 仓库 | `list_depots(project_id)` |
| 搜索 GitLab 仓库 | `gitlab.list_projects(search)` |
| 查看 GitLab 分支 | `gitlab.list_branches(project_id)` |
| 关联仓库 | `link_repository(project_name, job_name, ...)` |
| 查看已关联 | `list_linked_repos(project_name, job_name)` |
| 取消关联 | `unlink_repository(project_name, job_name, repo_url)` |
| 配置 Webhook | `configure_webhook(project_name, job_name, repo_url, events)` |
