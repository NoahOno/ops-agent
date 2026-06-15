import os


def run_server(mcp):
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    stateless = os.environ.get("MCP_STATELESS", "false").lower() == "true"

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            stateless_http=stateless,
        )
