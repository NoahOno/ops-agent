# Skill — MCP — 连接方式 速查表

## MCP Server 连接方式

| Server | 本地 (stdio) | 远程 (streamable-http) | 端口 | 所需凭据 |
|--------|-------------|----------------------|------|---------|
| **Coding** | `make run-coding` | `make run-coding-remote` | 8001 | `CODING_TOKEN` `CODING_TEAM` |
| **Jenkins** | `make run-jenkins` | `make run-jenkins-remote` | 8002 | `JENKINS_URL` `JENKINS_USER` `JENKINS_TOKEN` |
| **GitLab** | `make run-gitlab` | `make run-gitlab-remote` | 8003 | `GITLAB_URL` `GITLAB_TOKEN` |
| **TKE** | `make run-tke` | `make run-tke-remote` | 8004 | `TKE_SECRET_ID` `TKE_SECRET_KEY` |

客户端远程连接配置：
```json
{
  "mcpServers": {
    "coding":  { "url": "http://<server>:8001/mcp", "transport": "streamable-http" },
    "jenkins": { "url": "http://<server>:8002/mcp", "transport": "streamable-http" },
    "gitlab":  { "url": "http://<server>:8003/mcp", "transport": "streamable-http" },
    "tke":     { "url": "http://<server>:8004/mcp", "transport": "streamable-http" }
  }
}
```

---

## Skill ① repo-linker — 代码仓库关联

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 搜索 Coding 仓库 | Coding | `list_depots(project_id)` | Coding :8001 | 列出项目下仓库 |
| 搜索 GitLab 仓库 | GitLab | `list_projects(search)` | GitLab :8003 | 模糊搜索项目 |
| 查看 GitLab 分支 | GitLab | `list_branches(project_id)` | GitLab :8003 | 选择默认分支 |
| 关联仓库 | Coding | `link_repository(...)` | Coding :8001 | 写入本地 YAML |
| 查看已关联 | Coding | `list_linked_repos(...)` | Coding :8001 | 读取本地 YAML |
| 取消关联 | Coding | `unlink_repository(...)` | Coding :8001 | 修改本地 YAML |
| 配置 Webhook | Coding | `configure_webhook(...)` | Coding :8001 | 写入本地 YAML |

**存储：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.repos[]`

---

## Skill ② pipeline-param-designer — 流水线参数定义

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 查看已有参数 | Coding | `list_pipeline_params(project, job)` | Coding :8001 | 读取本地 YAML |
| 保存参数定义 | Coding | `define_pipeline_params(project, job, params[])` | Coding :8001 | 写入本地 YAML |
| 修改单个参数 | Coding | `update_pipeline_param(project, job, name, updates)` | Coding :8001 | 修改本地 YAML |
| 删除参数 | Coding | `delete_pipeline_param(project, job, name)` | Coding :8001 | 修改本地 YAML |

**存储：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.params[]`

---

## Skill ③ pipeline-composer — 构建步骤编排

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 列出可用模板 | Coding | `list_stage_templates()` | Coding :8001 | 返回 11 个预定义模板 |
| 获取模板详情 | Coding | `get_stage_template(name)` | Coding :8001 | 含 Jenkinsfile 片段 |
| 组合生成 Jenkinsfile | Coding | `compose_pipeline(stages[], params, env, post)` | Coding :8001 | 本地拼接 |
| 创建 Coding CI 计划 | Coding | `create_ci_job(...)` | Coding :8001 | 调 Coding API |
| 幂等创建 Coding CI | Coding | `get_or_create_ci_job(...)` | Coding :8001 | 调 Coding API |
| 创建 Jenkins Job | Jenkins | `create_job(name, jenkinsfile, git_url)` | Jenkins :8002 | 调 Jenkins API |

---

## Skill ④ trigger-configurator — 触发条件配置

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 查看已有规则 | Coding | `list_triggers(project, job)` | Coding :8001 | 读取本地 YAML |
| 保存触发规则 | Coding | `configure_trigger(project, job, type, ...)` | Coding :8001 | 写入本地 YAML |
| 删除触发规则 | Coding | `delete_trigger(project, job, type)` | Coding :8001 | 修改本地 YAML |
| 校验 cron | Coding | `validate_cron_expression(expr)` | Coding :8001 | 本地校验 |

**存储：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.triggers[]`

---

## Skill ⑤ notification-setup — 通知与归档配置

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 查看通知配置 | Coding | `list_notifications(project, job)` | Coding :8001 | 读取本地 YAML |
| 配置通知 | Coding | `configure_notification(project, job, channel, ...)` | Coding :8001 | 写入本地 YAML |
| 删除通知 | Coding | `delete_notification(project, job, channel)` | Coding :8001 | 修改本地 YAML |
| 查看归档配置 | Coding | `list_artifacts_config(project, job)` | Coding :8001 | 读取本地 YAML |
| 配置归档 | Coding | `configure_artifact(project, job, ...)` | Coding :8001 | 写入本地 YAML |
| 查看制品列表 | Coding | `list_ci_artifacts(job_id)` | Coding :8001 | 调 Coding API |

**存储：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.notifications[]` / `.artifacts[]`

---

## Skill ⑥ ops-pipeline — CI 构建全流程

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 查项目列表 | Coding | `list_projects(name?)` | Coding :8001 | 调 Coding API |
| 查项目详情 | Coding | `get_project(name)` | Coding :8001 | 调 Coding API → 拿 project_id |
| 查代码仓库 | Coding | `list_depots(project_id)` | Coding :8001 | 调 Coding API → 拿 depot_id |
| 查已有构建计划 | Coding | `list_ci_jobs(project_id)` | Coding :8001 | 找同类计划获取凭据 |
| 查构建计划详情 | Coding | `describe_ci_job(job_id)` | Coding :8001 | 提取 CREDENTIAL_ID |
| 幂等创建计划 | Coding | `get_or_create_ci_job(...)` | Coding :8001 | 调 Coding API 创建 |
| 自定义创建 | Coding | `create_ci_job(...)` | Coding :8001 | 调 Coding API 创建 |
| 触发构建 | Coding | `trigger_ci_build(job_id, ref)` | Coding :8001 | 调 Coding API 触发 |

**流程 A（Coding）：** `list_projects` → `get_project` → `list_depots` → `list_ci_jobs` → `describe_ci_job` → `get_or_create_ci_job` → `trigger_ci_build`

**流程 B（Jenkins）：** `gitlab.list_projects` → `gitlab.list_branches` → `jenkins.list_jobs` → `jenkins.create_job` → `jenkins.trigger_build`

---

## Skill ⑦ pipeline-runner — 流水线执行与日志

| 步骤 | MCP Server | MCP Tool | 连接方式 | 说明 |
|------|-----------|----------|---------|------|
| 查构建计划 | Coding | `list_ci_jobs(project_id)` | Coding :8001 | 找 job_id |
| 查参数定义 | Coding | `list_pipeline_params(project, job)` | Coding :8001 | 读取本地 YAML |
| 触发 Coding 构建 | Coding | `trigger_ci_build(job_id, ref)` | Coding :8001 | 调 Coding API |
| Coding 构建状态 | Coding | `describe_ci_build(build_id)` | Coding :8001 | 轮询直到完成 |
| Coding 构建日志 | Coding | `get_ci_build_log(build_id)` | Coding :8001 | 分页读取 |
| 触发 Jenkins 构建 | Jenkins | `trigger_build(job_name, params)` | Jenkins :8002 | 调 Jenkins API |
| Jenkins 构建状态 | Jenkins | `get_build_status(job, number)` | Jenkins :8002 | 轮询 |
| Jenkins Stage 详情 | Jenkins | `get_build_stages(job, number)` | Jenkins :8002 | Blue Ocean API |
| Jenkins 构建日志 | Jenkins | `get_build_log(job, number)` | Jenkins :8002 | 全文 |
| 获取最新构建号 | Jenkins | `get_last_build_number(job_name)` | Jenkins :8002 | 定位构建号 |
| 取消构建 | Jenkins | `cancel_build(job, number)` | Jenkins :8002 | 中止运行 |
| 重跑构建 | Jenkins | `replay_build(job, number)` | Jenkins :8002 | 重跑失败 |

---

## 按 MCP Server 汇总 — 各 Skill 调用分布

### Coding MCP (40 tools) — 被 7 个 Skill 全部使用

```
项目管理 (4)    ← ⑥ ops-pipeline
工作项 (5)      ← （暂未绑定 Skill，独立使用）
代码仓库 (3)    ← ① repo-linker, ⑥ ops-pipeline
CI 构建 (8)     ← ③ pipeline-composer, ⑥ ops-pipeline, ⑦ pipeline-runner
流水线参数 (4)  ← ② pipeline-param-designer
仓库关联 (4)    ← ① repo-linker
构建模板 (3)    ← ③ pipeline-composer
触发条件 (4)    ← ④ trigger-configurator
通知归档 (6)    ← ⑤ notification-setup
```

### Jenkins MCP (9 tools) — 被 2 个 Skill 使用

```
Job 管理 (2)    ← ③ pipeline-composer, ⑥ ops-pipeline (流程B)
构建触发 (3)    ← ⑥ ops-pipeline, ⑦ pipeline-runner
状态日志 (4)    ← ⑦ pipeline-runner
```

### GitLab MCP (3 tools) — 被 2 个 Skill 使用

```
项目搜索 (2)    ← ① repo-linker, ⑥ ops-pipeline (流程B)
分支管理 (1)    ← ① repo-linker
```

### TKE MCP (4 tools, TODO)

```
暂未绑定 Skill，预留用于未来部署流程
```
