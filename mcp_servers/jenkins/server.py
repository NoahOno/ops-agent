from fastmcp import FastMCP

mcp = FastMCP("jenkins")


@mcp.tool()
def list_jobs() -> str:
    """列出 Jenkins 上的所有 job"""
    return "TODO: implement list_jobs"


@mcp.tool()
def trigger_build(job_name: str) -> str:
    """触发指定 job 的构建"""
    return f"TODO: trigger build for {job_name}"


@mcp.tool()
def get_build_status(job_name: str, build_number: int) -> str:
    """获取指定构建的状态"""
    return f"TODO: get status for {job_name}#{build_number}"


if __name__ == "__main__":
    mcp.run()
