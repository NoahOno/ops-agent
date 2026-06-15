---
name: pipeline-param-designer
description: >
  引导用户定义流水线构建参数（分支/版本号/环境/配置项）。
  当用户需要为流水线配置参数化构建时使用此 skill。
  输出结构化的参数定义（参数名称/类型/默认值/可选值/是否必填/参数说明），
  并通过 define_pipeline_params 持久化到本地配置。
---

# Pipeline Param Designer

## 适用场景

- 用户说"给流水线加参数"、"配置构建参数"、"这个流水线需要传什么参数"
- 创建参数化的 Jenkinsfile 之前，先定义参数
- 修改已有流水线的参数定义

## 执行流程

```
Step 1  确认目标流水线
  询问用户: project_name 和 job_name
  调用 list_pipeline_params(project_name, job_name) 查看是否已有参数

Step 2  收集参数定义
  逐个引导用户定义参数，每个参数需确认:
    - name:        参数名称（英文，如 BRANCH, VERSION, ENV）
    - type:        类型（string / choice / boolean / password / text）
    - default:     默认值
    - choices:     可选值列表（仅 type=choice）
    - required:    是否必填
    - description: 参数说明（中文）

Step 3  生成参数定义并确认
  汇总所有参数，以表格形式展示给用户确认
  用户确认后调用 define_pipeline_params 持久化

Step 4  （可选）生成 Jenkins parameters 块
  根据参数定义自动生成 Jenkinsfile parameters {} 块内容
  输出可直接用于 compose_pipeline 的 params_block
```

## 参数类型规范

| 类型 | Jenkins 对应 | 说明 | 示例 |
|------|-------------|------|------|
| `string` | `string(name:..., defaultValue:...)` | 普通字符串 | BRANCH=master |
| `choice` | `choice(name:..., choices:[...])` | 下拉选择 | ENV=[dev,staging,prod] |
| `boolean` | `booleanParam(name:..., defaultValue:...)` | 布尔开关 | SKIP_TESTS=false |
| `password` | `password(name:...)` | 敏感信息 | DB_PASSWORD |
| `text` | `text(name:..., defaultValue:...)` | 多行文本 | DEPLOY_NOTES |

## 参数到 Jenkins parameters 块的映射

```groovy
parameters {
    string(name: 'BRANCH', defaultValue: 'master', description: '构建分支')
    choice(name: 'ENV', choices: ['dev', 'staging', 'prod'], description: '部署环境')
    booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: '是否跳过测试')
    password(name: 'DB_PASSWORD', description: '数据库密码')
}
```

## 参数到 Coding CI envs 的映射

```json
[
  {"Name": "BRANCH", "Value": "master", "Sensitive": 0},
  {"Name": "ENV", "Value": "dev", "Sensitive": 0},
  {"Name": "DB_PASSWORD", "Value": "", "Sensitive": 1}
]
```

`Sensitive=1` 对应 `password` 类型，值在 Coding 控制台中加密存储。

## 常用参数模板

### 标准发布参数
```yaml
- name: BRANCH          type: string   default: master     required: true   description: 构建分支
- name: VERSION         type: string   default: ""         required: true   description: 版本号
- name: ENV             type: choice   choices: [dev, staging, prod]  required: true   description: 部署环境
- name: SKIP_TESTS      type: boolean  default: false      required: false  description: 是否跳过测试
```

### 镜像构建参数
```yaml
- name: IMAGE_TAG       type: string   default: ${GIT_COMMIT[0..7]}  required: false  description: 镜像标签
- name: DOCKERFILE      type: string   default: Dockerfile           required: false  description: Dockerfile路径
- name: BUILD_CONTEXT    type: string   default: "."                  required: false  description: 构建上下文
```

## MCP 工具调用

| 步骤 | 工具 |
|------|------|
| 查看已有参数 | `list_pipeline_params(project_name, job_name)` |
| 保存参数定义 | `define_pipeline_params(project_name, job_name, params)` |
| 修改单个参数 | `update_pipeline_param(project_name, job_name, param_name, updates)` |
| 删除参数 | `delete_pipeline_param(project_name, job_name, param_name)` |
| 生成 Jenkinsfile 参数块 | 本地生成，无需 MCP |
