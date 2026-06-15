---
name: notification-setup
description: >
  引导用户配置流水线发布结果通知（钉钉/企微/邮件/Slack）及制品归档。
  当用户需要设置构建结果通知或配置制品归档策略时使用此 skill。
  输出通知/归档配置（通知渠道/通知模板/通知条件/制品存储路径/版本标记）。
---

# Notification Setup

## 适用场景

- 用户说"配置通知"、"构建失败发钉钉"、"设置邮件通知"
- 用户说"配置制品归档"、"设置镜像版本规则"
- 流水线创建后配置通知和归档策略

## 执行流程

### 通知配置

```
Step 1  确认目标流水线
  询问: project_name 和 job_name
  调用 list_notifications(project_name, job_name) 查看已有配置

Step 2  选择通知渠道
  向用户展示选项:
    a) 钉钉机器人 (dingtalk)
    b) 企业微信机器人 (wecom)
    c) 邮件 (email)
    d) Slack (slack)

Step 3  根据渠道收集信息

  钉钉/企微/Slack:
    → Webhook URL（从对应平台获取）
    → 引导用户: "请在钉钉群 → 群设置 → 智能群助手 → 添加机器人 → 获取 Webhook URL"

  邮件:
    → SMTP 配置（host/port/user/pass）
    → 收件人列表
    → 引导用户: "请提供 SMTP 服务器地址和端口"

Step 4  配置通知条件
  询问何时发送通知:
    - success: 仅构建成功时
    - failure: 仅构建失败时
    - always: 构建完成就通知
    - unstable: 构建不稳定时（测试失败但编译通过）

Step 5  选择通知模板
  default: 标准模板（包含项目名/构建号/状态/耗时/日志链接）
  用户也可自定义模板

Step 6  保存
  调用 configure_notification(project_name, job_name, channel, ...)
```

### 制品归档配置

```
Step 7  配置制品存储
  询问存储类型:
    a) cos: 腾讯云对象存储
    b) nexus: Nexus 制品仓库
    c) coding_artifact: Coding 制品库

  收集:
    → 存储路径（如 cos://my-bucket/artifacts/）
    → 版本标记规则（如 v{major}.{minor}.{patch}-{commit}）
    → 保留天数（默认 30 天）
    → 归档文件匹配模式（如 **/*.jar, **/*.tar.gz）

Step 8  保存
  调用 configure_artifact(project_name, job_name, ...)
```

## 通知渠道 Webhook 格式

### 钉钉
```
URL: https://oapi.dingtalk.com/robot/send?access_token=xxxx
获取: 钉钉群 → 群设置 → 智能群助手 → 添加机器人 → 自定义 → 复制 Webhook
安全设置: 建议选择"加签"模式
```

### 企业微信
```
URL: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx
获取: 企微群 → 群机器人 → 添加群机器人 → 复制 Webhook
```

### Slack
```
URL: https://hooks.slack.com/services/T00/B00/xxxx
获取: Slack → Apps → Incoming WebHooks → Add to Slack → 复制 URL
```

### 邮件 SMTP
```
常用配置:
  - 腾讯企业邮: smtp.exmail.qq.com:465
  - QQ 邮箱: smtp.qq.com:465
  - 163 邮箱: smtp.163.com:465
  - Gmail: smtp.gmail.com:587
```

## 默认通知模板变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `${job_name}` | 流水线名称 | my-service-ci |
| `${build_number}` | 构建号 | #42 |
| `${status}` | 构建状态 | SUCCESS / FAILURE |
| `${duration}` | 耗时 | 3m 25s |
| `${trigger_user}` | 触发者 | zhangsan |
| `${git_branch}` | 构建分支 | release/1.0 |
| `${git_commit}` | 提交 SHA（短） | a1b2c3d |
| `${log_url}` | 日志链接 | https://... |

## 版本标记规范

| 规则 | 示例 | 适用场景 |
|------|------|---------|
| `v{major}.{minor}.{patch}` | v1.2.3 | 正式版本 |
| `v{major}.{minor}.{patch}-{commit}` | v1.2.3-a1b2c3d | 可追溯版本 |
| `{branch}-{timestamp}` | release-20240115 | 分支快照 |
| `{branch}-{build_number}` | master-42 | CI 构建 |
| `latest` | latest | 开发环境 |

## MCP 工具调用

| 步骤 | 工具 |
|------|------|
| 查看已有通知 | `list_notifications(project_name, job_name)` |
| 配置通知 | `configure_notification(project_name, job_name, channel, ...)` |
| 删除通知 | `delete_notification(project_name, job_name, channel)` |
| 查看归档配置 | `list_artifacts_config(project_name, job_name)` |
| 配置归档 | `configure_artifact(project_name, job_name, ...)` |
| 查看制品列表 | `list_ci_artifacts(job_id)` |
