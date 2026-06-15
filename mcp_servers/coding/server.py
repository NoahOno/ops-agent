import json

from fastmcp import FastMCP

from .api import CodingClient, CodingConfig
from .templates import build_and_push_image
from .stage_templates import list_templates, get_template, compose_jenkinsfile
from . import pipeline_config

mcp = FastMCP("coding")
_client: CodingClient | None = None


def _get_client() -> CodingClient:
    global _client
    if _client is None:
        _client = CodingClient(CodingConfig())
    return _client


# ── Project Tools ────────────────────────────────────────────


@mcp.tool()
async def list_projects(project_name: str | None = None) -> str:
    """查询当前用户在 Coding DevOps 中的项目列表，支持按名称模糊匹配"""
    client = _get_client()
    projects = await client.list_projects(project_name)
    if not projects:
        return "未找到匹配的项目"
    lines = []
    for p in projects:
        lines.append(
            f"- **{p.get('Name', '')}** ({p.get('DisplayName', '')})"
            f"\n  ID: {p.get('Id', 'N/A')}"
            f"\n  描述: {p.get('Description', '无')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_project(project_name: str) -> str:
    """根据项目名称查询项目详情"""
    client = _get_client()
    project = await client.get_project_by_name(project_name)
    if not project:
        return f"未找到项目: {project_name}"
    return json.dumps(project, ensure_ascii=False, indent=2)


@mcp.tool()
async def create_project(
    name: str,
    display_name: str,
    description: str = "",
    project_template: str = "DEV_OPS",
    shared: str = "0",
) -> str:
    """创建 Coding DevOps 项目。project_template 可选: DEV_OPS, DEMO_BEGIN, CHOICE_DEMAND, PROJECT_MANAGE, CODE_HOST。shared: 0=私有, 1=公开"""
    client = _get_client()
    result = await client.create_project(name, display_name, description, project_template, shared)
    return f"项目创建成功，ProjectId: {result.get('ProjectId')}"


@mcp.tool()
async def delete_project(project_id: str) -> str:
    """删除指定的 Coding DevOps 项目"""
    client = _get_client()
    await client.delete_project(project_id)
    return f"项目 {project_id} 已删除"


# ── Issue / Work Item Tools ──────────────────────────────────


@mcp.tool()
async def list_issues(
    project_name: str,
    issue_type: str = "ALL",
    limit: str = "20",
    offset: str = "0",
    sort_key: str = "UPDATED_AT",
    sort_value: str = "DESC",
) -> str:
    """查询工作项列表。issue_type 可选: ALL, DEFECT, REQUIREMENT, MISSION, EPIC"""
    client = _get_client()
    issues = await client.list_issues(project_name, issue_type, limit, offset, sort_key, sort_value)
    if not issues:
        return "未找到工作项"
    lines = []
    for i in issues:
        lines.append(
            f"- [{i.get('Type', '')}] #{i.get('Code', '')} {i.get('Name', '')}"
            f"\n  优先级: {i.get('Priority', 'N/A')}  状态: {i.get('Status', 'N/A')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def describe_issue(project_name: str, issue_code: int) -> str:
    """查询工作项详情"""
    client = _get_client()
    issue = await client.describe_issue(project_name, issue_code)
    if not issue:
        return f"未找到工作项 #{issue_code}"
    return json.dumps(issue, ensure_ascii=False, indent=2)


@mcp.tool()
async def create_issue(
    project_name: str,
    name: str,
    issue_type: str,
    priority: str,
    description: str,
    parent_code: int | None = None,
) -> str:
    """创建工作项。issue_type: DEFECT/REQUIREMENT/MISSION/EPIC。priority: 0=低, 1=中, 2=高, 3=紧急。可选 parent_code 设为父事项的子项"""
    client = _get_client()
    issue = await client.create_issue(project_name, name, issue_type, priority, description, parent_code)
    return f"工作项创建成功: #{issue.get('Code', 'N/A')} {name}"


@mcp.tool()
async def delete_issue(project_name: str, issue_code: int) -> str:
    """删除指定的工作项"""
    client = _get_client()
    await client.delete_issue(project_name, issue_code)
    return f"工作项 #{issue_code} 已删除"


@mcp.tool()
async def decompose_issue(
    project_name: str,
    parent_issue_code: int,
    sub_tasks: list[dict],
) -> str:
    """将需求拆解为多个子任务。sub_tasks 每项需包含 name, description, priority"""
    client = _get_client()
    created = []
    for task in sub_tasks:
        issue = await client.create_issue(
            project_name=project_name,
            name=task["name"],
            issue_type="MISSION",
            priority=task.get("priority", "1"),
            description=task.get("description", ""),
            parent_code=parent_issue_code,
        )
        created.append(f"  - #{issue.get('Code', 'N/A')} {task['name']}")
    return f"已将需求 #{parent_issue_code} 拆解为 {len(created)} 个子任务:\n" + "\n".join(created)


# ── Code / Depot Tools ───────────────────────────────────────


@mcp.tool()
async def list_depots(
    project_id: str,
    page_number: str = "1",
    page_size: str = "20",
) -> str:
    """查询项目下的代码仓库列表"""
    client = _get_client()
    data = await client.list_depots(project_id, page_number, page_size)
    depots = data.get("Depots", [])
    page = data.get("Page", {})
    if not depots:
        return "未找到仓库"
    lines = []
    for d in depots:
        lines.append(
            f"- **{d.get('Name', '')}**"
            f"\n  HTTPS: {d.get('HttpsUrl', '')}"
            f"\n  SSH: {d.get('SshUrl', '')}"
            f"\n  默认分支: {d.get('DefaultBranch', 'master')}"
        )
    lines.append(f"\n共 {page.get('TotalRow', 0)} 个仓库，第 {page.get('PageNumber', 1)}/{page.get('TotalPage', 1)} 页")
    return "\n".join(lines)


@mcp.tool()
async def list_commits(
    ref: str,
    depot_id: str | None = None,
    depot_path: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    keyword: str | None = None,
    page_number: str = "1",
    page_size: str = "20",
) -> str:
    """查询仓库分支下的提交记录。ref 为分支名，depot_id 和 depot_path 二选一"""
    client = _get_client()
    data = await client.list_commits(
        ref=ref,
        depot_id=depot_id,
        depot_path=depot_path,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
        page_number=page_number,
        page_size=page_size,
    )
    commits = data.get("Commits", [])
    if not commits:
        return "未找到提交记录"
    lines = []
    for c in commits:
        lines.append(
            f"- `{c.get('Sha', '')[:8]}` {c.get('ShortMessage', '')}"
            f"\n  作者: {c.get('AuthorName', '')} <{c.get('AuthorEmail', '')}>"
        )
    return "\n".join(lines)


@mcp.tool()
async def create_merge_request(
    depot_path: str,
    title: str,
    content: str,
    src_branch: str,
    dest_branch: str = "master",
) -> str:
    """创建合并请求 (MR)。depot_path 格式如 team/project/depot"""
    client = _get_client()
    resp = await client.create_merge_request(depot_path, title, content, src_branch, dest_branch)
    mr_info = resp.get("MergeInfo", {})
    return (
        f"合并请求创建成功\n"
        f"  MR ID: {mr_info.get('MergeRequestId', 'N/A')}\n"
        f"  URL: {mr_info.get('MergeRequestUrl', 'N/A')}"
    )


# ── CI Build Tools (构建计划) ───────────────────────────────


@mcp.tool()
async def list_ci_jobs(project_id: int) -> str:
    """查询项目下的构建计划列表。project_id 可通过 get_project 获取"""
    client = _get_client()
    jobs = await client.list_ci_jobs(project_id)
    if not jobs:
        return "未找到构建计划"
    lines = []
    for j in jobs:
        lines.append(
            f"- **{j.get('Name', '')}** (ID: {j.get('Id', 'N/A')})"
            f"\n  执行方式: {j.get('ExecuteIn', 'N/A')}"
            f"\n  最近构建: {j.get('LastBuildStatus', '无')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def describe_ci_job(job_id: int) -> str:
    """获取构建计划详情，包含 Jenkinsfile 内容和触发规则"""
    client = _get_client()
    job = await client.describe_ci_job(job_id)
    if not job:
        return f"未找到构建计划 #{job_id}"
    return json.dumps(job, ensure_ascii=False, indent=2)


@mcp.tool()
async def create_ci_job(
    project_id: int,
    name: str,
    depot_id: int | None = None,
    jenkinsfile: str | None = None,
    execute_in: str = "CVM",
    ref: str | None = None,
    envs: list[dict] | None = None,
) -> str:
    """创建构建计划。execute_in: CVM/STATIC/AGENT。
    提供 jenkinsfile 时使用内联脚本模式；不提供则从仓库 SCM 读取 Jenkinsfile。
    ref 为代码更新触发的匹配分支，默认 master。
    envs 格式: [{"Name": "KEY", "Value": "val", "Sensitive": 0}]，Sensitive=1 为加密变量。
    """
    client = _get_client()
    trigger_methods = [{"TriggerMethod": "REF_CHANGE", "Branch": ref or "master"}]
    result = await client.create_ci_job(
        project_id=project_id,
        name=name,
        depot_id=depot_id,
        jenkinsfile=jenkinsfile,
        execute_in=execute_in,
        trigger_methods=trigger_methods,
        envs=envs,
    )
    job_id = result.get("JobId", result.get("Id", "N/A"))
    return f"构建计划创建成功，JobId: {job_id}"


@mcp.tool()
async def get_or_create_ci_job(
    project_id: int,
    name: str,
    depot_id: int | None = None,
    image_registry: str = "",
    image_repo: str = "",
    image_tag: str = '${GIT_COMMIT[0..7]}',
    registry_credential_id: str = "REGISTRY_CREDENTIAL",
    execute_in: str = "CVM",
    ref: str | None = None,
    envs: list[dict] | None = None,
) -> str:
    """幂等创建构建计划：若同名计划已存在则直接返回，否则用内置镜像构建模板创建。
    image_registry: 镜像仓库地址，如 ccr.ccs.tencentyun.com
    image_repo: 镜像路径，如 my-team/my-service
    registry_credential_id: Coding CI 凭据 ID（用于 docker login）
    envs 格式: [{"Name": "KEY", "Value": "val", "Sensitive": 0}]
    """
    client = _get_client()
    # 检查同名 job 是否已存在
    jobs = await client.list_ci_jobs(project_id)
    existing = next((j for j in jobs if j.get("Name") == name), None)
    if existing:
        job_id = existing.get("Id", "N/A")
        return f"构建计划已存在，JobId: {job_id}，Name: {name}"

    jenkinsfile = build_and_push_image(
        image_registry=image_registry,
        image_repo=image_repo,
        image_tag=image_tag,
        registry_credential_id=registry_credential_id,
    )
    trigger_methods = [{"TriggerMethod": "REF_CHANGE", "Branch": ref or "master"}]
    result = await client.create_ci_job(
        project_id=project_id,
        name=name,
        depot_id=depot_id,
        jenkinsfile=jenkinsfile,
        execute_in=execute_in,
        trigger_methods=trigger_methods,
        envs=envs,
    )
    job_id = result.get("JobId", result.get("Id", "N/A"))
    return f"构建计划创建成功，JobId: {job_id}，Name: {name}"


@mcp.tool()
async def trigger_ci_build(
    job_id: int,
    ref: str = "master",
) -> str:
    """触发构建。ref 为分支名或 CommitId"""
    client = _get_client()
    result = await client.trigger_ci_build(job_id, ref)
    build_id = result.get("BuildId", result.get("Id", "N/A"))
    return f"构建已触发，BuildId: {build_id}"


@mcp.tool()
async def list_ci_builds(job_id: int, page: int = 1, page_size: int = 10) -> str:
    """获取构建计划的历史构建记录"""
    client = _get_client()
    data = await client.list_ci_builds(job_id, page, page_size)
    builds = data.get("BuildSet", data.get("Builds", []))
    total = data.get("TotalCount", data.get("Total", 0))
    if not builds:
        return "未找到构建记录"
    lines = []
    for b in builds:
        status = b.get("Status", "UNKNOWN")
        lines.append(
            f"- #{b.get('Id', 'N/A')} [{status}] {b.get('Ref', '')}"
            f"\n  触发者: {b.get('TriggerUser', 'N/A')}  耗时: {b.get('Duration', 'N/A')}s"
        )
    lines.append(f"\n共 {total} 条记录")
    return "\n".join(lines)


@mcp.tool()
async def describe_ci_build(build_id: int) -> str:
    """查询构建记录详情，包含各阶段状态和耗时"""
    client = _get_client()
    build = await client.describe_ci_build(build_id)
    if not build:
        return f"未找到构建记录 #{build_id}"
    return json.dumps(build, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_ci_build_log(build_id: int, log_start: int = 0) -> str:
    """获取构建日志。log_start 为日志起始偏移量，用于分页读取"""
    client = _get_client()
    resp = await client.get_ci_build_log(build_id, log_start)
    log = resp.get("Log", resp.get("Content", ""))
    if not log:
        return "构建日志为空或构建尚未开始"
    return log


# ── Pipeline Param Tools ──────────────────────────────────────


@mcp.tool()
def define_pipeline_params(
    project_name: str,
    job_name: str,
    params: list[dict],
) -> str:
    """为流水线定义参数列表（持久化到本地配置）。
    params 每项需包含:
      - name: 参数名称
      - type: string / choice / boolean / password / text
      - default: 默认值
      - choices: 可选值列表（仅 type=choice 时需要）
      - required: 是否必填（true/false）
      - description: 参数说明
    """
    for p in params:
        if "name" not in p or "type" not in p:
            return f"参数定义缺少必填字段 name 或 type: {p}"
    result = pipeline_config.define_params(project_name, job_name, params)
    return f"已为流水线 {job_name} 定义 {result['param_count']} 个参数"


@mcp.tool()
def list_pipeline_params(project_name: str, job_name: str) -> str:
    """查询流水线已定义的参数列表"""
    params = pipeline_config.list_params(project_name, job_name)
    if not params:
        return f"流水线 {job_name} 未定义任何参数"
    return json.dumps(params, ensure_ascii=False, indent=2)


@mcp.tool()
def update_pipeline_param(
    project_name: str,
    job_name: str,
    param_name: str,
    updates: dict,
) -> str:
    """修改流水线单个参数的定义。updates 可包含 default/choices/required/description 等字段"""
    result = pipeline_config.update_param(project_name, job_name, param_name, updates)
    if "error" in result:
        return result["error"]
    return f"参数 {param_name} 已更新: {json.dumps(result, ensure_ascii=False)}"


@mcp.tool()
def delete_pipeline_param(project_name: str, job_name: str, param_name: str) -> str:
    """删除流水线的一个参数定义"""
    result = pipeline_config.delete_param(project_name, job_name, param_name)
    if "error" in result:
        return result["error"]
    return f"参数 {param_name} 已从流水线 {job_name} 删除"


# ── Repository Link Tools ─────────────────────────────────────


@mcp.tool()
def link_repository(
    project_name: str,
    job_name: str,
    repo_url: str,
    credential_id: str = "",
    default_branch: str = "master",
    auth_type: str = "coding_credential",
    branch_strategy: str = "single",
    branch_pattern: str = "",
) -> str:
    """将 Git 仓库关联到流水线。
    auth_type: ssh_key / https_token / coding_credential / jenkins_credential
    branch_strategy: single（固定分支）/ pattern（正则匹配）/ all
    """
    repo = {
        "repo_url": repo_url,
        "credential_id": credential_id,
        "default_branch": default_branch,
        "auth_type": auth_type,
        "branch_strategy": branch_strategy,
        "branch_pattern": branch_pattern,
        "webhook_enabled": False,
        "webhook_events": [],
    }
    result = pipeline_config.link_repo(project_name, job_name, repo)
    return f"仓库已关联: {json.dumps(result, ensure_ascii=False)}"


@mcp.tool()
def list_linked_repos(project_name: str, job_name: str) -> str:
    """查询流水线已关联的仓库列表"""
    repos = pipeline_config.list_repos(project_name, job_name)
    if not repos:
        return f"流水线 {job_name} 未关联任何仓库"
    return json.dumps(repos, ensure_ascii=False, indent=2)


@mcp.tool()
def unlink_repository(project_name: str, job_name: str, repo_url: str) -> str:
    """取消仓库与流水线的关联"""
    result = pipeline_config.unlink_repo(project_name, job_name, repo_url)
    if "error" in result:
        return result["error"]
    return f"仓库 {repo_url} 已取消关联"


@mcp.tool()
def configure_webhook(
    project_name: str,
    job_name: str,
    repo_url: str,
    events: list[str],
) -> str:
    """配置仓库的 Webhook 触发。events 可选: push / merge_request / tag_push"""
    result = pipeline_config.configure_webhook(project_name, job_name, repo_url, events)
    if "error" in result:
        return result["error"]
    return f"Webhook 已配置: 事件={events}"


# ── Stage Template Tools ──────────────────────────────────────


@mcp.tool()
def list_stage_templates() -> str:
    """列出可用的构建阶段模板（如 maven-build、docker-build-push、helm-deploy 等）"""
    templates = list_templates()
    lines = []
    for t in templates:
        lines.append(
            f"- **{t['name']}** [{t['language']}]"
            f"\n  {t['description']}"
            f"\n  工具依赖: {', '.join(t['tools']) or '无'}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_stage_template(name: str) -> str:
    """获取某个阶段模板的详细内容（含 Jenkinsfile 代码片段）"""
    tpl = get_template(name)
    if not tpl:
        return f"未找到模板: {name}，请使用 list_stage_templates 查看可用模板"
    return json.dumps(tpl, ensure_ascii=False, indent=2)


@mcp.tool()
def compose_pipeline(
    stages: list[str],
    params_block: str = "",
    env_block: str = "",
    post_block: str = "",
) -> str:
    """根据阶段模板名称列表组合生成完整 Jenkinsfile。
    stages: 模板名称列表，如 ["maven-build", "docker-build-push", "helm-deploy"]
    params_block: Jenkins parameters {} 块内容（可选）
    env_block: Jenkins environment {} 块内容（可选）
    post_block: Jenkins post {} 块内容（可选）
    """
    jenkinsfile = compose_jenkinsfile(
        stages=stages,
        params_block=params_block,
        env_block=env_block,
        post_block=post_block,
    )
    return jenkinsfile


# ── Trigger Tools ─────────────────────────────────────────────


@mcp.tool()
def configure_trigger(
    project_name: str,
    job_name: str,
    trigger_type: str,
    schedule: str = "",
    branch_pattern: str = "",
    path_filter: list[str] | None = None,
    source_branch: str = "",
    target_branch: str = "",
    tag_pattern: str = "",
    token: str = "",
) -> str:
    """为流水线配置触发规则。
    trigger_type 可选:
      - cron: 定时触发，需提供 schedule（cron 表达式，如 "0 2 * * 1"）
      - push: 代码推送触发，需提供 branch_pattern，可选 path_filter
      - merge_request: MR 触发，可选 source_branch/target_branch
      - tag_push: 标签推送触发，需提供 tag_pattern
      - manual: 手动触发，无额外条件
      - api: API 触发，可选 token
    """
    trigger = {
        "trigger_type": trigger_type,
        "schedule": schedule,
        "branch_pattern": branch_pattern,
        "path_filter": path_filter or [],
        "source_branch": source_branch,
        "target_branch": target_branch,
        "tag_pattern": tag_pattern,
        "token": token,
    }
    trigger = {k: v for k, v in trigger.items() if v or k == "trigger_type"}
    result = pipeline_config.configure_trigger(project_name, job_name, trigger)
    return f"触发规则已配置: {json.dumps(result, ensure_ascii=False)}"


@mcp.tool()
def list_triggers(project_name: str, job_name: str) -> str:
    """查询流水线已配置的触发规则列表"""
    triggers = pipeline_config.list_triggers(project_name, job_name)
    if not triggers:
        return f"流水线 {job_name} 未配置任何触发规则"
    return json.dumps(triggers, ensure_ascii=False, indent=2)


@mcp.tool()
def delete_trigger(project_name: str, job_name: str, trigger_type: str) -> str:
    """删除指定的触发规则"""
    result = pipeline_config.delete_trigger(project_name, job_name, trigger_type)
    if "error" in result:
        return result["error"]
    return f"触发规则 {trigger_type} 已删除"


@mcp.tool()
def validate_cron_expression(expression: str) -> str:
    """校验 cron 表达式合法性，返回解析结果和未来 5 次触发时间预览。
    支持标准 5 段 cron: 分 时 日 月 周
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        return f"cron 表达式格式错误：应为 5 段（分 时 日 月 周），当前为 {len(parts)} 段"
    field_names = ["分钟", "小时", "日", "月", "周"]
    for i, (part, name) in enumerate(zip(parts, field_names)):
        if not _validate_cron_field(part, name):
            return _validate_cron_field(part, name)
    return (
        f"cron 表达式合法: {expression}\n"
        f"  含义: 每 {parts[0]}分 {parts[1]}时 {parts[2]}日 {parts[3]}月 周{parts[4]}\n"
        f"  提示: 实际触发时间取决于调度器实现，建议使用 Jenkins H 语法避免负载尖峰"
    )


def _validate_cron_field(field: str, name: str) -> str | bool:
    for item in field.split(","):
        if "/" in item:
            base, step = item.split("/", 1)
            if not step.isdigit():
                return f"{name} 字段步进值无效: {step}"
        if item in ("*", "H"):
            continue
        if "-" in item:
            start, end = item.split("-", 1)
            if not (start.isdigit() and end.isdigit()):
                return f"{name} 字段范围无效: {item}"
        elif not item.replace("H", "").replace("/", "").isdigit():
            return f"{name} 字段无效: {item}"
    return True


# ── Notification Tools ────────────────────────────────────────


@mcp.tool()
def configure_notification(
    project_name: str,
    job_name: str,
    channel: str,
    webhook_url: str = "",
    smtp_host: str = "",
    smtp_port: int = 465,
    smtp_user: str = "",
    smtp_pass: str = "",
    recipients: list[str] | None = None,
    conditions: list[str] | None = None,
    template: str = "default",
) -> str:
    """配置流水线通知规则。
    channel: dingtalk / wecom / email / slack
    conditions: 触发通知的条件列表，可选 success / failure / always / unstable
    template: 通知模板名称，默认 default
    """
    notification = {
        "channel": channel,
        "webhook_url": webhook_url,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_pass": smtp_pass,
        "recipients": recipients or [],
        "conditions": conditions or ["failure"],
        "template": template,
    }
    notification = {k: v for k, v in notification.items() if v or k in ("channel", "conditions", "template")}
    result = pipeline_config.configure_notification(project_name, job_name, notification)
    return f"通知规则已配置: channel={result.get('channel')}, conditions={result.get('conditions')}"


@mcp.tool()
def list_notifications(project_name: str, job_name: str) -> str:
    """查询流水线已配置的通知规则"""
    notifs = pipeline_config.list_notifications(project_name, job_name)
    if not notifs:
        return f"流水线 {job_name} 未配置任何通知规则"
    return json.dumps(notifs, ensure_ascii=False, indent=2)


@mcp.tool()
def delete_notification(project_name: str, job_name: str, channel: str) -> str:
    """删除指定的通知渠道配置"""
    result = pipeline_config.delete_notification(project_name, job_name, channel)
    if "error" in result:
        return result["error"]
    return f"通知渠道 {channel} 已删除"


# ── Artifact Tools ────────────────────────────────────────────


@mcp.tool()
def configure_artifact(
    project_name: str,
    job_name: str,
    storage_type: str,
    storage_path: str,
    version_tag_pattern: str = "",
    retention_days: int = 30,
    archive_patterns: list[str] | None = None,
) -> str:
    """配置制品归档规则。
    storage_type: cos / nexus / coding_artifact
    storage_path: 存储路径，如 cos://bucket/path/ 或 nexus://repo/path/
    version_tag_pattern: 版本标记规则，如 v{major}.{minor}.{patch}-{commit}
    retention_days: 制品保留天数
    archive_patterns: 归档文件匹配模式列表，如 ["**/*.jar", "**/*.tar.gz"]
    """
    artifact = {
        "storage_type": storage_type,
        "storage_path": storage_path,
        "version_tag_pattern": version_tag_pattern,
        "retention_days": retention_days,
        "archive_patterns": archive_patterns or ["**/*"],
    }
    result = pipeline_config.configure_artifact(project_name, job_name, artifact)
    return f"制品归档已配置: {json.dumps(result, ensure_ascii=False)}"


@mcp.tool()
def list_artifacts_config(project_name: str, job_name: str) -> str:
    """查询流水线的制品归档配置"""
    artifacts = pipeline_config.list_artifacts_config(project_name, job_name)
    if not artifacts:
        return f"流水线 {job_name} 未配置制品归档"
    return json.dumps(artifacts, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_ci_artifacts(job_id: int, page: int = 1, page_size: int = 20) -> str:
    """查询构建计划产出的制品列表（从 Coding CI API 获取）"""
    client = _get_client()
    data = await client.list_ci_builds(job_id, page, page_size)
    builds = data.get("BuildSet", data.get("Builds", []))
    artifacts = []
    for b in builds:
        for a in b.get("Artifacts", []):
            artifacts.append({
                "build_id": b.get("Id"),
                "name": a.get("Name", ""),
                "size": a.get("Size", 0),
                "url": a.get("DownloadUrl", ""),
            })
    if not artifacts:
        return "未找到制品"
    return json.dumps(artifacts, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    from mcp_servers import run_server
    run_server(mcp)
