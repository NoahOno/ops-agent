import json

from fastmcp import FastMCP

from .api import JenkinsClient, JenkinsConfig

mcp = FastMCP("jenkins")
_client: JenkinsClient | None = None


def _get_client() -> JenkinsClient:
    global _client
    if _client is None:
        _client = JenkinsClient(JenkinsConfig())
    return _client


@mcp.tool()
async def list_jobs() -> str:
    """列出 Jenkins 上的所有构建计划（job），返回名称、状态、最近构建信息"""
    client = _get_client()
    jobs = await client.list_jobs()
    if not jobs:
        return "未找到任何 Job"
    lines = []
    for j in jobs:
        last = j.get("lastBuild") or {}
        lines.append(
            f"- **{j.get('name', '')}** [{j.get('color', 'N/A')}]"
            f"\n  URL: {j.get('url', '')}"
            f"\n  最近构建: #{last.get('number', 'N/A')} {last.get('result', '未运行')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def create_job(
    name: str,
    jenkinsfile: str,
    git_url: str,
    branch: str = "master",
    credentials_id: str = "",
) -> str:
    """创建 Jenkins Pipeline Job（内联 Jenkinsfile + Git SCM）。
    name: Job 名称
    jenkinsfile: Pipeline 脚本内容（Groovy）
    git_url: Git 仓库地址
    branch: 分支名，默认 master
    credentials_id: Jenkins 中配置的 Git 凭据 ID（可选）
    """
    client = _get_client()
    await client.create_job(name, jenkinsfile, git_url, branch, credentials_id)
    return f"Job 创建成功: {name}"


@mcp.tool()
async def trigger_build(job_name: str, params: dict | None = None) -> str:
    """触发 Jenkins 构建。params 为构建参数（可选），如 {"BRANCH": "main"}"""
    client = _get_client()
    await client.trigger_build(job_name, params)
    if params:
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"构建已触发: {job_name} (参数: {param_str})"
    return f"构建已触发: {job_name}"


@mcp.tool()
async def get_build_status(job_name: str, build_number: int) -> str:
    """获取指定构建的状态，包含结果、耗时、是否仍在构建中"""
    client = _get_client()
    data = await client.get_build_status(job_name, build_number)
    return json.dumps(
        {
            "job": job_name,
            "number": data.get("number"),
            "result": data.get("result") or ("BUILDING" if data.get("building") else "UNKNOWN"),
            "duration_ms": data.get("duration"),
            "timestamp": data.get("timestamp"),
            "url": data.get("url"),
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def get_last_build_number(job_name: str) -> str:
    """获取 Job 的最新构建编号。若从未构建过则返回提示"""
    client = _get_client()
    number = await client.get_last_build_number(job_name)
    if number is None:
        return f"Job {job_name} 尚未有任何构建记录"
    return f"Job {job_name} 最新构建编号: #{number}"


@mcp.tool()
async def get_build_log(job_name: str, build_number: int) -> str:
    """获取构建的控制台日志全文"""
    client = _get_client()
    log = await client.get_build_log(job_name, build_number)
    if not log:
        return "构建日志为空或构建尚未开始"
    return log


@mcp.tool()
async def cancel_build(job_name: str, build_number: int) -> str:
    """中止正在运行的 Jenkins 构建"""
    client = _get_client()
    await client.cancel_build(job_name, build_number)
    return f"构建已中止: {job_name} #{build_number}"


@mcp.tool()
async def replay_build(job_name: str, build_number: int) -> str:
    """以相同参数重新触发构建（重跑失败的流水线）"""
    client = _get_client()
    await client.replay_build(job_name, build_number)
    return f"构建已重新触发: {job_name} #{build_number}"


@mcp.tool()
async def get_build_stages(job_name: str, build_number: int) -> str:
    """获取构建的各 Stage 状态和耗时（依赖 Blue Ocean 插件）"""
    client = _get_client()
    stages = await client.get_build_stages(job_name, build_number)
    if not stages:
        return "未获取到 Stage 信息（可能 Blue Ocean 插件未安装）"
    lines = []
    total_ms = 0
    for s in stages:
        duration = s.get("duration_ms", 0)
        total_ms += duration
        lines.append(
            f"- **{s.get('name', '')}** [{s.get('status', 'UNKNOWN')}]"
            f"\n  状态: {s.get('state', '')}  耗时: {duration / 1000:.1f}s"
        )
    lines.append(f"\n总耗时: {total_ms / 1000:.1f}s")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
