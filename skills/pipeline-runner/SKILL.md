---
name: pipeline-runner
description: >
  执行流水线并跟踪构建全过程，输出实时状态和结果。
  当用户需要触发一次构建并查看执行结果时使用此 skill。
  输出执行结果（构建号/执行状态/各阶段耗时/日志URL/制品地址/部署结果）。
---

# Pipeline Runner

## 适用场景

- 用户说"执行流水线"、"触发构建"、"跑一次 CI"
- 用户说"查看构建状态"、"构建进度"、"构建日志"
- 用户说"重跑失败的构建"、"取消构建"

## 执行流程

### 触发构建

```
Step 1  确认目标流水线
  询问: 使用 Coding CI 还是 Jenkins？

  Coding CI:
    → 需要 project_name + job_name
    → list_projects → get_project → project_id
    → list_ci_jobs(project_id) → job_id

  Jenkins:
    → 需要 job_name
    → jenkins.list_jobs() 确认 Job 存在

Step 2  确认构建参数
  调用 list_pipeline_params(project_name, job_name) 获取参数定义
  如果有参数:
    → 展示参数列表（名称/类型/默认值）
    → 让用户确认或修改每个参数值
    → 校验必填参数是否已提供
  如果无参数:
    → 仅需确认分支 (ref)

Step 3  触发构建
  Coding CI:
    → trigger_ci_build(job_id, ref)
    → 记录 BuildId

  Jenkins:
    → trigger_build(job_name, params={...})
    → get_last_build_number(job_name) → 获取构建号

Step 4  轮询构建状态
  每 10-15 秒检查一次:

  Coding CI:
    → describe_ci_build(build_id) → status
    → 状态流转: PENDING → BUILDING → SUCCESS/FAILURE/CANCELLED

  Jenkins:
    → get_build_status(job_name, build_number) → result
    → 状态流转: null(building) → SUCCESS/FAILURE/UNSTABLE/ABORTED

Step 5  构建完成后输出汇总
  - 构建号
  - 最终状态
  - 总耗时
  - 各阶段耗时（如可用）
  - 日志关键片段（最后 20 行或失败阶段日志）
  - 制品地址（如有）
```

### 查看构建状态

```
Step 1  获取状态
  Coding CI:
    → describe_ci_build(build_id) → 各阶段状态和耗时

  Jenkins:
    → get_build_status(job_name, build_number) → 构建状态
    → get_build_stages(job_name, build_number) → 各 Stage 耗时（需 Blue Ocean）

Step 2  输出结果表格
  | Stage | 状态 | 耗时 |
  |-------|------|------|
  | 检出  | SUCCESS | 5s |
  | 构建  | FAILURE | 1m 32s |
  | 推送  | SKIPPED | - |
```

### 查看构建日志

```
Step 1  获取日志
  Coding CI:
    → get_ci_build_log(build_id, log_start) 支持分页

  Jenkins:
    → get_build_log(job_name, build_number) 全文

Step 2  分析日志
  如果构建失败:
    → 定位错误信息（ERROR / FAILED / Exception）
    → 提取关键错误上下文（前后各 5 行）
    → 给出可能的修复建议
```

### 重跑/取消构建

```
重跑:
  Jenkins → replay_build(job_name, build_number)
  Coding  → trigger_ci_build(job_id, ref) 重新触发

取消:
  Jenkins → cancel_build(job_name, build_number)
  Coding  → 暂不支持（需手动取消）
```

## 构建状态枚举

| 状态 | 说明 |
|------|------|
| `QUEUED` / `PENDING` | 排队等待 |
| `BUILDING` / `RUNNING` | 正在构建 |
| `SUCCESS` | 构建成功 |
| `FAILURE` | 构建失败 |
| `UNSTABLE` | 不稳定（测试失败但编译通过） |
| `ABORTED` / `CANCELLED` | 已取消 |

## 日志分析策略

### 常见错误模式

| 错误关键词 | 可能原因 | 建议 |
|-----------|---------|------|
| `docker: command not found` | 构建环境缺少 Docker | 检查执行环境配置 |
| `mvn: command not found` | 构建环境缺少 Maven | 安装 Maven 或使用 Docker 容器 |
| `npm ERR!` | npm 依赖安装失败 | 检查 package.json 和 registry |
| `permission denied` | 权限不足 | 检查凭据配置和 SSH key |
| `Connection refused` | 网络问题 | 检查代理和网络策略 |
| `OutOfMemoryError` | 内存不足 | 增加构建环境资源限制 |
| `COPY failed` | Dockerfile 文件路径错误 | 检查 COPY 指令和构建上下文 |

## 输出格式

```
构建结果:
  流水线: my-service-ci
  构建号: #42
  状态:   FAILURE
  耗时:   3m 25s
  触发者: zhangsan
  分支:   release/1.0

  阶段耗时:
    检出    [SUCCESS]  5s
    构建    [FAILURE]  1m 32s  ← 失败点
    推镜像  [SKIPPED]  -

  错误摘要:
    [ERROR] Failed to execute goal org.apache.maven...
    Compilation failure: cannot find symbol...

  日志: https://coding.example.com/ci/builds/42/log
```

## MCP 工具调用

| 步骤 | 工具 |
|------|------|
| 查询构建计划 | `list_ci_jobs(project_id)` |
| 获取参数定义 | `list_pipeline_params(project_name, job_name)` |
| 触发 Coding 构建 | `trigger_ci_build(job_id, ref)` |
| 触发 Jenkins 构建 | `jenkins.trigger_build(job_name, params)` |
| Coding 构建状态 | `describe_ci_build(build_id)` |
| Jenkins 构建状态 | `jenkins.get_build_status(job_name, build_number)` |
| Jenkins Stage 详情 | `jenkins.get_build_stages(job_name, build_number)` |
| Coding 构建日志 | `get_ci_build_log(build_id, log_start)` |
| Jenkins 构建日志 | `jenkins.get_build_log(job_name, build_number)` |
| 取消 Jenkins 构建 | `jenkins.cancel_build(job_name, build_number)` |
| 重跑 Jenkins 构建 | `jenkins.replay_build(job_name, build_number)` |
| Jenkins 最新构建号 | `jenkins.get_last_build_number(job_name)` |
