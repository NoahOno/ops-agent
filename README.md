# ops-agent

运维自动化 agent —— 接收业务上线需求，自动完成部署上线、CI/CD 流水线配置、网络配置。

## 集成平台

- 腾讯 Coding DevOps
- 内部 Jenkins
- 腾讯 TKE (Kubernetes)
- 腾讯 EO
- 内网 GitLab
- SVN

## 项目结构

```
src/ops_agent/      # agent 主逻辑
mcp_servers/        # FastMCP server 集合
  jenkins/          # Jenkins MCP server
  tke/              # TKE (K8s) MCP server
  coding/           # Coding DevOps MCP server
  gitlab/           # 内网 GitLab MCP server
skills/             # Qoder skill 定义
prompts/            # agent prompt 模板
configs/            # 配置模板
tests/              # 测试
docs/               # 设计文档
```

## 快速开始

```bash
# 安装依赖
make install

# 运行 MCP server
make run-jenkins
make run-tke
make run-coding
make run-gitlab
```
