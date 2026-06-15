---
name: trigger-configurator
description: >
  引导用户配置流水线的触发条件（定时/代码推送/MR/手动/API）。
  当用户需要设置流水线自动触发规则时使用此 skill。
  输出结构化触发规则（触发类型/触发条件/触发时间/触发过滤规则）。
---

# Trigger Configurator

## 适用场景

- 用户说"配置触发条件"、"设置定时构建"、"推送代码自动构建"
- 创建流水线时设置触发方式
- 修改已有触发规则

## 执行流程

```
Step 1  确认目标流水线
  询问: project_name 和 job_name
  调用 list_triggers(project_name, job_name) 查看已有触发规则

Step 2  选择触发类型
  向用户展示可选类型并引导选择:

    ┌─────────────────────────────────────────────────┐
    │  触发类型    │ 说明               │ 需要提供     │
    ├─────────────────────────────────────────────────┤
    │  cron        │ 定时触发           │ cron 表达式   │
    │  push        │ 代码推送触发       │ 分支+路径过滤 │
    │  merge_request│ MR 触发          │ 源/目标分支   │
    │  tag_push    │ 标签推送触发       │ 标签模式     │
    │  manual      │ 手动触发           │ 无           │
    │  api         │ API/Webhook 触发   │ Token        │
    └─────────────────────────────────────────────────┘

Step 3  根据类型收集条件

  cron:
    → 引导输入 cron 表达式
    → 调用 validate_cron_expression 校验合法性
    → 展示含义确认

  push:
    → 询问分支匹配模式（如 master, release/*, *）
    → 可选: 路径过滤（include/exclude glob）
    → 示例: branch_pattern="release/*", path_filter=["src/**", "!docs/**"]

  merge_request:
    → 可选: 源分支匹配（如 feature/*）
    → 可选: 目标分支匹配（如 main, master）

  tag_push:
    → 询问标签匹配模式（如 v[0-9]+.*, release-*）

  manual / api:
    → 无额外条件，api 可选 token

Step 4  保存触发规则
  调用 configure_trigger(project_name, job_name, trigger_type, ...)

Step 5  （可选）配置多个触发规则
  询问是否需要添加更多触发规则（如同时配置 cron + push）
```

## Cron 表达式参考

### 标准 5 段格式
```
┌───────────── 分钟 (0-59)
│ ┌───────────── 小时 (0-23)
│ │ ┌───────────── 日 (1-31)
│ │ │ ┌───────────── 月 (1-12)
│ │ │ │ ┌───────────── 周几 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * *
```

### 常用表达式

| 表达式 | 含义 |
|--------|------|
| `0 2 * * *` | 每天凌晨 2:00 |
| `0 2 * * 1` | 每周一凌晨 2:00 |
| `30 8 * * 1-5` | 工作日每天 8:30 |
| `0 */6 * * *` | 每 6 小时 |
| `0 0 1 * *` | 每月 1 号 0:00 |
| `H 2 * * *` | 每天凌晨 2:xx（Jenkins 散列，避免同时触发） |

### Jenkins 特殊语法
- `H` = 散列值（0-59），每个 Job 固定但不同 Job 不同，用于打散负载
- `H/15` = 每 15 分钟，起始点散列
- `H(0-30)` = 0-30 范围内散列

## 路径过滤规则

```yaml
# 仅 src 目录变更时触发
path_filter:
  - "src/**"

# src 变更但 docs 变更不触发
path_filter:
  - "src/**"
  - "!docs/**"

# 多目录
path_filter:
  - "src/**"
  - "lib/**"
  - "pom.xml"
```

## 标签匹配模式

| 模式 | 匹配示例 |
|------|---------|
| `v*` | v1.0, v2.3.1 |
| `v[0-9]+.*` | v1.0, v10.2.3 |
| `release-*` | release-2024, release-1.0 |
| `*` | 所有标签 |

## MCP 工具调用

| 步骤 | 工具 |
|------|------|
| 查看已有规则 | `list_triggers(project_name, job_name)` |
| 校验 cron | `validate_cron_expression(expression)` |
| 保存规则 | `configure_trigger(project_name, job_name, trigger_type, ...)` |
| 删除规则 | `delete_trigger(project_name, job_name, trigger_type)` |
