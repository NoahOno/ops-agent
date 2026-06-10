# MCP Servers

各 MCP server 基于 FastMCP 框架，为 ops-agent 提供与外部平台交互的能力。

| Server | 说明 | 启动命令 |
|--------|------|----------|
| jenkins | 内部 Jenkins CI/CD | `make run-jenkins` |
| tke | 腾讯 TKE (K8s) | `make run-tke` |
| coding | 腾讯 Coding DevOps | `make run-coding` |
| gitlab | 内网 GitLab | `make run-gitlab` |
