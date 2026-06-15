FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir "fastmcp>=3.0.0" "httpx>=0.27.0" "pydantic>=2.0.0" "pydantic-settings>=2.0.0" "pyyaml>=6.0"

COPY mcp_servers/ ./mcp_servers/
COPY configs/ ./configs/

ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_STATELESS=true

EXPOSE 8001 8002 8003 8004

CMD ["python", "-m", "mcp_servers.coding.server"]
