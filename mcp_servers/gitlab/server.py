import json

from fastmcp import FastMCP

from .api import GitLabClient, GitLabConfig

mcp = FastMCP("gitlab")
_client: GitLabClient | None = None


def _get_client() -> GitLabClient:
    global _client
    if _client is None:
        _client = GitLabClient(GitLabConfig())
    return _client


@mcp.tool()
async def list_projects(search: str = "") -> str:
    """搜索内网 GitLab 项目，返回仓库 ID、名称、Clone URL。search 为关键字模糊匹配"""
    client = _get_client()
    projects = await client.list_projects(search=search)
    if not projects:
        return "未找到匹配的项目"
    lines = []
    for p in projects:
        lines.append(
            f"- **{p.get('path_with_namespace', '')}** (ID: {p.get('id', 'N/A')})"
            f"\n  HTTP: {p.get('http_url_to_repo', '')}"
            f"\n  SSH: {p.get('ssh_url_to_repo', '')}"
            f"\n  默认分支: {p.get('default_branch', 'main')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_project(project_id: int) -> str:
    """获取 GitLab 项目详情，包含仓库 ID、Clone URL、默认分支等信息"""
    client = _get_client()
    p = await client.get_project(project_id)
    if not p:
        return f"未找到项目 ID: {project_id}"
    return json.dumps(
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "path_with_namespace": p.get("path_with_namespace"),
            "default_branch": p.get("default_branch"),
            "http_url_to_repo": p.get("http_url_to_repo"),
            "ssh_url_to_repo": p.get("ssh_url_to_repo"),
            "description": p.get("description"),
            "web_url": p.get("web_url"),
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def list_branches(project_id: int, search: str = "") -> str:
    """列出 GitLab 项目的分支列表，支持按名称搜索"""
    client = _get_client()
    branches = await client.list_branches(project_id, search=search)
    if not branches:
        return "未找到分支"
    lines = []
    for b in branches:
        commit = b.get("commit", {})
        lines.append(
            f"- **{b.get('name', '')}**"
            f"\n  最新提交: {commit.get('short_id', '')} {commit.get('title', '')}"
            f"\n  作者: {commit.get('author_name', '')}  时间: {commit.get('created_at', '')}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
