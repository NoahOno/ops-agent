from fastmcp import FastMCP

mcp = FastMCP("coding")


@mcp.tool()
def list_projects() -> str:
    """列出 Coding DevOps 项目"""
    return "TODO: implement list_projects"


@mcp.tool()
def list_repos(project_name: str) -> str:
    """列出项目下的代码仓库"""
    return f"TODO: list repos for {project_name}"


@mcp.tool()
def list_pipelines(project_name: str) -> str:
    """列出项目下的 CI/CD 流水线"""
    return f"TODO: list pipelines for {project_name}"


@mcp.tool()
def trigger_pipeline(project_name: str, pipeline_id: str) -> str:
    """触发指定流水线"""
    return f"TODO: trigger pipeline {pipeline_id} in {project_name}"


if __name__ == "__main__":
    mcp.run()
