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

lint:
	uv run ruff check src/ mcp_servers/

test:
	uv run pytest
