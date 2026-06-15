.PHONY: install dev run-jenkins run-tke run-coding run-gitlab lint test

install:
	uv sync

dev:
	uv sync --extra dev

run-jenkins:
	uv run python -m mcp_servers.jenkins.server

run-tke:
	uv run python -m mcp_servers.tke.server

run-coding:
	uv run python -m mcp_servers.coding.server

run-gitlab:
	uv run python -m mcp_servers.gitlab.server

dev-coding:
	uv run fastmcp dev mcp_servers/coding/server.py

dev-gitlab:
	uv run fastmcp dev mcp_servers/gitlab/server.py

dev-jenkins:
	uv run fastmcp dev mcp_servers/jenkins/server.py

lint:
	uv run ruff check src/ mcp_servers/

test:
	uv run pytest

# 将项目内 skill 链接到 ~/.kiro/skills（首次设置时运行）
link-skills:
	@for skill in skills/*/; do \
		name=$$(basename $$skill); \
		rm -rf ~/.kiro/skills/$$name; \
		ln -s $$(pwd)/$$skill ~/.kiro/skills/$$name; \
		echo "Linked: $$name"; \
	done
