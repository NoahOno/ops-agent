.PHONY: install dev run-jenkins run-tke run-coding run-gitlab lint test \
       run-coding-remote run-jenkins-remote run-gitlab-remote run-tke-remote \
       docker-build docker-up docker-down

install:
	uv sync

dev:
	uv sync --extra dev

# ── Local stdio mode (default) ──────────────────────────────────

run-jenkins:
	uv run python -m mcp_servers.jenkins.server

run-tke:
	uv run python -m mcp_servers.tke.server

run-coding:
	uv run python -m mcp_servers.coding.server

run-gitlab:
	uv run python -m mcp_servers.gitlab.server

# ── Remote streamable-http mode ─────────────────────────────────

run-coding-remote:
	MCP_TRANSPORT=streamable-http MCP_PORT=8001 uv run python -m mcp_servers.coding.server

run-jenkins-remote:
	MCP_TRANSPORT=streamable-http MCP_PORT=8002 uv run python -m mcp_servers.jenkins.server

run-gitlab-remote:
	MCP_TRANSPORT=streamable-http MCP_PORT=8003 uv run python -m mcp_servers.gitlab.server

run-tke-remote:
	MCP_TRANSPORT=streamable-http MCP_PORT=8004 uv run python -m mcp_servers.tke.server

# ── FastMCP Inspector (dev) ─────────────────────────────────────

dev-coding:
	uv run fastmcp dev mcp_servers/coding/server.py

dev-gitlab:
	uv run fastmcp dev mcp_servers/gitlab/server.py

dev-jenkins:
	uv run fastmcp dev mcp_servers/jenkins/server.py

# ── Docker ──────────────────────────────────────────────────────

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

# ── Quality ─────────────────────────────────────────────────────

lint:
	uv run ruff check src/ mcp_servers/

test:
	uv run pytest

# ── Skills ──────────────────────────────────────────────────────

# 将项目内 skill 链接到 ~/.kiro/skills（首次设置时运行）
link-skills:
	@for skill in skills/*/; do \
		name=$$(basename $$skill); \
		rm -rf ~/.kiro/skills/$$name; \
		ln -s $$(pwd)/$$skill ~/.kiro/skills/$$name; \
		echo "Linked: $$name"; \
	done
