from fastmcp import FastMCP

mcp = FastMCP("gitlab")


@mcp.tool()
def list_projects(search: str = "") -> str:
    """搜索内网 GitLab 项目"""
    return f"TODO: search projects with '{search}'"


@mcp.tool()
def get_project(project_id: int) -> str:
    """获取项目详情"""
    return f"TODO: get project {project_id}"


@mcp.tool()
def list_branches(project_id: int) -> str:
    """列出项目的分支"""
    return f"TODO: list branches for project {project_id}"


@mcp.tool()
def list_merge_requests(project_id: int, state: str = "opened") -> str:
    """列出项目的 Merge Request"""
    return f"TODO: list MRs for project {project_id} (state={state})"


if __name__ == "__main__":
    mcp.run()
