# Skill — MCP — 连接方式 完整详情表

## 一、MCP Server 连接信息

| MCP Server | 传输协议 | 本地启动 | 远程启动 | 端口 | 端点 | 所需环境变量 |
|-----------|---------|---------|---------|------|------|------------|
| Coding | stdio / streamable-http | `make run-coding` | `make run-coding-remote` | 8001 | `/mcp` | `CODING_TOKEN`, `CODING_TEAM` |
| Jenkins | stdio / streamable-http | `make run-jenkins` | `make run-jenkins-remote` | 8002 | `/mcp` | `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN` |
| GitLab | stdio / streamable-http | `make run-gitlab` | `make run-gitlab-remote` | 8003 | `/mcp` | `GITLAB_URL`, `GITLAB_TOKEN` |
| TKE | stdio / streamable-http | `make run-tke` | `make run-tke-remote` | 8004 | `/mcp` | `TKE_SECRET_ID`, `TKE_SECRET_KEY`, `TKE_REGION` |

---

## 二、全量 Skill → MCP Tool 详情表

> 共 7 个 Skill，调用 56 个 MCP Tool（Coding 40 + Jenkins 9 + GitLab 3 + TKE 4）

### Skill ① repo-linker — 代码仓库关联

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `list_depots` | `project_id, page_number?, page_size?` | Coding API | 列出项目下代码仓库，获取仓库 URL |
| Coding :8001 | `link_repository` | `project_name, job_name, repo_url, credential_id?, default_branch?, auth_type?, branch_strategy?, branch_pattern?` | 本地 YAML | 将仓库关联到流水线 |
| Coding :8001 | `list_linked_repos` | `project_name, job_name` | 本地 YAML | 查询已关联的仓库列表 |
| Coding :8001 | `unlink_repository` | `project_name, job_name, repo_url` | 本地 YAML | 取消仓库关联 |
| Coding :8001 | `configure_webhook` | `project_name, job_name, repo_url, events[]` | 本地 YAML | 配置 Webhook 触发事件（push/merge_request/tag_push） |
| GitLab :8003 | `list_projects` | `search?` | GitLab API | 搜索 GitLab 项目，获取仓库 clone URL |
| GitLab :8003 | `get_project` | `project_id` | GitLab API | 获取 GitLab 项目详情 |
| GitLab :8003 | `list_branches` | `project_id, search?` | GitLab API | 列出分支，用于选择默认分支 |

**存储路径：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.repos[]`
**需要外部连接：** 是（Coding API + GitLab API）

---

### Skill ② pipeline-param-designer — 流水线参数定义

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `define_pipeline_params` | `project_name, job_name, params[]` | 本地 YAML | 定义参数列表，每项含 name/type/default/choices/required/description |
| Coding :8001 | `list_pipeline_params` | `project_name, job_name` | 本地 YAML | 查询已定义的参数列表 |
| Coding :8001 | `update_pipeline_param` | `project_name, job_name, param_name, updates{}` | 本地 YAML | 修改单个参数的属性 |
| Coding :8001 | `delete_pipeline_param` | `project_name, job_name, param_name` | 本地 YAML | 删除一个参数定义 |

**存储路径：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.params[]`
**需要外部连接：** 否（纯本地 YAML 读写）

**参数类型对照：**

| 类型 | Jenkins 对应 | Coding envs 对应 | 示例 |
|------|-------------|-----------------|------|
| `string` | `string(name:..., defaultValue:...)` | `Sensitive: 0` | BRANCH=master |
| `choice` | `choice(name:..., choices:[...])` | `Sensitive: 0` | ENV=[dev,prod] |
| `boolean` | `booleanParam(name:..., defaultValue:...)` | `Sensitive: 0` | SKIP_TESTS=false |
| `password` | `password(name:...)` | `Sensitive: 1` | DB_PASSWORD |
| `text` | `text(name:..., defaultValue:...)` | `Sensitive: 0` | DEPLOY_NOTES |

---

### Skill ③ pipeline-composer — 构建步骤编排

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `list_stage_templates` | 无 | 本地内存 | 列出 11 个预定义 Stage 模板 |
| Coding :8001 | `get_stage_template` | `name` | 本地内存 | 获取模板详情（含 Jenkinsfile 代码片段） |
| Coding :8001 | `compose_pipeline` | `stages[], params_block?, env_block?, post_block?` | 本地拼接 | 根据模板名称列表组合生成完整 Jenkinsfile |
| Coding :8001 | `create_ci_job` | `project_id, name, depot_id?, jenkinsfile?, execute_in?, ref?, envs?` | Coding API | 创建 Coding CI 构建计划 |
| Coding :8001 | `get_or_create_ci_job` | `project_id, name, depot_id?, image_registry?, image_repo?, image_tag?, ...` | Coding API | 幂等创建（同名已存在则直接返回） |
| Jenkins :8002 | `create_job` | `name, jenkinsfile, git_url, branch?, credentials_id?` | Jenkins API | 创建 Jenkins Pipeline Job |

**可用 Stage 模板：**

| 模板名 | 语言 | 工具依赖 | 说明 |
|--------|------|---------|------|
| `maven-build` | Java | maven | mvn clean package -DskipTests |
| `maven-test` | Java | maven | mvn test + junit 报告 |
| `gradle-build` | Java | gradle | ./gradlew build -x test |
| `npm-build` | Node.js | node, npm | npm ci + npm run build |
| `npm-test` | Node.js | node, npm | npm test |
| `go-build` | Go | go | go mod download + go build |
| `go-test` | Go | go | go test ./... -v |
| `docker-build-push` | 通用 | docker | docker build + login + push |
| `sonar-scan` | 通用 | sonar-scanner | SonarQube 代码质量扫描 |
| `helm-deploy` | 通用 | helm, kubectl | helm upgrade --install |
| `artifact-archive` | 通用 | 无 | archiveArtifacts 归档 |

**需要外部连接：** 创建 Job 时需要（Coding API 或 Jenkins API）

---

### Skill ④ trigger-configurator — 触发条件配置

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `configure_trigger` | `project_name, job_name, trigger_type, schedule?, branch_pattern?, path_filter?, source_branch?, target_branch?, tag_pattern?, token?` | 本地 YAML | 配置触发规则 |
| Coding :8001 | `list_triggers` | `project_name, job_name` | 本地 YAML | 查询已配置的触发规则 |
| Coding :8001 | `delete_trigger` | `project_name, job_name, trigger_type` | 本地 YAML | 删除指定类型的触发规则 |
| Coding :8001 | `validate_cron_expression` | `expression` | 本地校验 | 校验 cron 表达式合法性（5 段格式） |

**存储路径：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.triggers[]`
**需要外部连接：** 否（纯本地 YAML 读写 + 本地校验）

**触发类型对照：**

| trigger_type | 条件字段 | 示例值 |
|-------------|---------|--------|
| `cron` | `schedule` | `"0 2 * * 1"` 每周一凌晨 2 点 |
| `push` | `branch_pattern`, `path_filter[]` | `"release/*"`, `["src/**", "!docs/**"]` |
| `merge_request` | `source_branch`, `target_branch` | `"feature/*"` → `"main"` |
| `tag_push` | `tag_pattern` | `"v[0-9]+.*"` |
| `manual` | 无 | 用户在 UI 手动点击 |
| `api` | `token` | Webhook token |

---

### Skill ⑤ notification-setup — 通知与归档配置

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `configure_notification` | `project_name, job_name, channel, webhook_url?, smtp_host?, smtp_port?, recipients?, conditions?, template?` | 本地 YAML | 配置通知规则 |
| Coding :8001 | `list_notifications` | `project_name, job_name` | 本地 YAML | 查询通知规则列表 |
| Coding :8001 | `delete_notification` | `project_name, job_name, channel` | 本地 YAML | 删除指定渠道的通知 |
| Coding :8001 | `configure_artifact` | `project_name, job_name, storage_type, storage_path, version_tag_pattern?, retention_days?, archive_patterns?` | 本地 YAML | 配置制品归档规则 |
| Coding :8001 | `list_artifacts_config` | `project_name, job_name` | 本地 YAML | 查询归档配置 |
| Coding :8001 | `list_ci_artifacts` | `job_id, page?, page_size?` | Coding API | 查询构建产出的制品列表 |

**存储路径：** `configs/pipelines/{project_name}.yaml` → `jobs.{job_name}.notifications[]` / `.artifacts[]`
**需要外部连接：** 查制品列表时需要（Coding API），配置读写为本地

**通知渠道对照：**

| channel | 配置方式 | Webhook URL 格式 |
|---------|---------|-----------------|
| `dingtalk` | Webhook URL | `https://oapi.dingtalk.com/robot/send?access_token=xxx` |
| `wecom` | Webhook URL | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx` |
| `email` | SMTP (host/port/user/pass) | 无 Webhook，使用 recipients[] |
| `slack` | Incoming Webhook | `https://hooks.slack.com/services/xxx` |

**归档存储类型：**

| storage_type | 路径格式 | 说明 |
|-------------|---------|------|
| `cos` | `cos://bucket/path/` | 腾讯云对象存储 |
| `nexus` | `nexus://repo/path/` | Nexus 制品仓库 |
| `coding_artifact` | `coding://project/depot/` | Coding 制品库 |

---

### Skill ⑥ ops-pipeline — CI 构建全流程

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `list_projects` | `project_name?` | Coding API | 搜索项目列表 |
| Coding :8001 | `get_project` | `project_name` | Coding API | 获取项目详情 → 拿到 `project_id` |
| Coding :8001 | `list_depots` | `project_id, page_number?, page_size?` | Coding API | 查仓库 → 拿到 `depot_id` |
| Coding :8001 | `list_ci_jobs` | `project_id` | Coding API | 查已有构建计划 → 找同类计划获取凭据 |
| Coding :8001 | `describe_ci_job` | `job_id` | Coding API | 查详情 → 提取 `TCR_PUSH_CREDENTIAL_ID` |
| Coding :8001 | `get_or_create_ci_job` | `project_id, name, depot_id?, image_registry?, image_repo?, ...` | Coding API | 幂等创建构建计划 |
| Coding :8001 | `create_ci_job` | `project_id, name, depot_id?, jenkinsfile?, execute_in?, ref?, envs?` | Coding API | 自定义创建（需手写 Jenkinsfile） |
| Coding :8001 | `trigger_ci_build` | `job_id, ref` | Coding API | 触发构建 |
| GitLab :8003 | `list_projects` | `search?` | GitLab API | 流程 B：搜索 GitLab 项目 |
| GitLab :8003 | `list_branches` | `project_id, search?` | GitLab API | 流程 B：确认目标分支 |
| Jenkins :8002 | `list_jobs` | 无 | Jenkins API | 流程 B：确认 Job 是否已存在 |
| Jenkins :8002 | `create_job` | `name, jenkinsfile, git_url, branch?, credentials_id?` | Jenkins API | 流程 B：创建 Jenkins Job |
| Jenkins :8002 | `trigger_build` | `job_name, params?` | Jenkins API | 流程 B：触发 Jenkins 构建 |

**两条流程：**

| | 流程 A（Coding 仓库 → Coding CI） | 流程 B（GitLab 仓库 → Jenkins） |
|---|---|---|
| 调用链 | `list_projects` → `get_project` → `list_depots` → `list_ci_jobs` → `describe_ci_job` → `get_or_create_ci_job` → `trigger_ci_build` | `gitlab.list_projects` → `gitlab.list_branches` → `jenkins.list_jobs` → `jenkins.create_job` → `jenkins.trigger_build` |
| 凭据来源 | 从同类已有计划自动提取 | 用户手动提供 credentials_id |
| 降级策略 | 无凭据 → 保底版（仅编译，不推镜像） | - |

**需要外部连接：** 是（全流程调 Coding API，流程 B 还调 GitLab + Jenkins API）

---

### Skill ⑦ pipeline-runner — 流水线执行与日志

| MCP Server | MCP Tool | 参数 | 数据源 | 说明 |
|-----------|----------|------|--------|------|
| Coding :8001 | `list_ci_jobs` | `project_id` | Coding API | 查构建计划 → 拿 job_id |
| Coding :8001 | `list_pipeline_params` | `project_name, job_name` | 本地 YAML | 查参数定义 → 提示用户填参 |
| Coding :8001 | `trigger_ci_build` | `job_id, ref` | Coding API | 触发 Coding CI 构建 |
| Coding :8001 | `describe_ci_build` | `build_id` | Coding API | 查询构建状态（轮询直到完成） |
| Coding :8001 | `get_ci_build_log` | `build_id, log_start?` | Coding API | 获取构建日志（分页） |
| Jenkins :8002 | `trigger_build` | `job_name, params?` | Jenkins API | 触发 Jenkins 构建 |
| Jenkins :8002 | `get_build_status` | `job_name, build_number` | Jenkins API | 获取构建状态（轮询） |
| Jenkins :8002 | `get_build_stages` | `job_name, build_number` | Jenkins API | 各 Stage 状态和耗时（Blue Ocean） |
| Jenkins :8002 | `get_build_log` | `job_name, build_number` | Jenkins API | 获取构建控制台日志全文 |
| Jenkins :8002 | `get_last_build_number` | `job_name` | Jenkins API | 获取最新构建编号 |
| Jenkins :8002 | `cancel_build` | `job_name, build_number` | Jenkins API | 中止正在运行的构建 |
| Jenkins :8002 | `replay_build` | `job_name, build_number` | Jenkins API | 以相同参数重跑构建 |

**需要外部连接：** 是（全流程调 Coding API + Jenkins API）

---

## 三、按 MCP Server 视角汇总

### Coding MCP — 40 tools

| Tool 类别 | Tool 数量 | 被哪些 Skill 使用 | 数据源 |
|----------|----------|------------------|--------|
| 项目管理 | 4 | ⑥ | Coding API |
| 工作项 | 5 | （独立使用） | Coding API |
| 代码仓库 | 3 | ① ⑥ | Coding API |
| CI 构建 | 8 | ③ ⑥ ⑦ | Coding API |
| 流水线参数 | 4 | ② | 本地 YAML |
| 仓库关联 | 4 | ① | 本地 YAML |
| 构建模板 | 3 | ③ | 本地内存 |
| 触发条件 | 4 | ④ | 本地 YAML |
| 通知归档 | 6 | ⑤ | 本地 YAML + Coding API |

### Jenkins MCP — 9 tools

| Tool 类别 | Tool 数量 | 被哪些 Skill 使用 | 数据源 |
|----------|----------|------------------|--------|
| Job 管理 | 2 | ③ ⑥ | Jenkins API |
| 构建触发 | 3 | ⑥ ⑦ | Jenkins API |
| 状态日志 | 4 | ⑦ | Jenkins API |

### GitLab MCP — 3 tools

| Tool 类别 | Tool 数量 | 被哪些 Skill 使用 | 数据源 |
|----------|----------|------------------|--------|
| 项目搜索 | 2 | ① ⑥ | GitLab API |
| 分支管理 | 1 | ① | GitLab API |

### TKE MCP — 4 tools (TODO)

| Tool 类别 | Tool 数量 | 被哪些 Skill 使用 | 数据源 |
|----------|----------|------------------|--------|
| 集群管理 | 4 | （预留，暂未绑定） | TKE API |

---

## 四、测试依赖矩阵

| Skill | Coding API | Jenkins API | GitLab API | 本地 YAML | 可离线测试 |
|-------|:---------:|:----------:|:---------:|:--------:|:---------:|
| ① repo-linker | 需要 | - | 需要 | 读写 | 否 |
| ② pipeline-param-designer | - | - | - | 读写 | **是** |
| ③ pipeline-composer | 创建时需要 | 创建时需要 | - | 读取 | 部分（生成可离线，创建需连接） |
| ④ trigger-configurator | - | - | - | 读写 | **是** |
| ⑤ notification-setup | 查制品时需要 | - | - | 读写 | 部分（配置可离线，查制品需连接） |
| ⑥ ops-pipeline | 需要 | 流程B需要 | 流程B需要 | - | 否 |
| ⑦ pipeline-runner | 需要 | 需要 | - | 读取 | 否 |
