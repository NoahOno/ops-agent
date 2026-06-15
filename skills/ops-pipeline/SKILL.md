---
name: ops-pipeline
description: >
  用于在腾讯 Coding DevOps 平台上创建、管理和触发 CI 构建计划（构建+推镜像）。
  当用户需要为某个服务创建或更新 CI 流水线、触发构建、查看构建结果时使用此 skill。
  涵盖：生成 Jenkinsfile、注入环境变量、幂等创建构建计划、构建触发与结果观察的完整链路。
---

# Coding Pipeline Builder

## 概述

当前阶段只做 CI（构建+推镜像），不包含部署。

分两层：
- **通用层**（本文件）：MCP 工具调用流程、标准 Pipeline 模板、通用规范
- **业务层**（`references/` 目录）：各业务线的差异化配置

---

## CI 平台选择

根据代码仓库所在平台决定使用哪套 CI 工具：

| 代码仓库 | CI 执行平台 | 流程入口 |
|---------|-----------|---------|
| Coding 仓库 | Coding CI | 流程 A |
| 内网 GitLab 仓库 | Jenkins | 流程 B（⚠️ 暂未完善） |

---

## 流程 A：Coding 标准流程

```
Step 1  确认项目和仓库
  list_projects → get_project → project_id
  list_depots(project_id) → depot_id

Step 2  获取凭据 ID（必须从已有计划获取，不能猜测）
  list_ci_jobs(project_id) → 找同类已有计划
  describe_ci_job(job_id) → 从中提取 TCR_PUSH_CREDENTIAL_ID

  ⚠️ 若同项目无已有计划（或已有计划无法获取凭据）：
  → 向用户说明当前缺少哪些信息，列出需要手动提供的参数：
    - TCR_PUSH_CREDENTIAL_ID：Coding 凭据管理中的 TCR 推送凭据 UUID
    - CODING_DOCKER_REG_HOST：镜像仓库域名（通常为 tkeprod.tencentcloudcr.com）
    - DOCKER_IMAGE_NAME：镜像路径（如 cyouops/my-service）
  → 等用户提供后继续；或用户明确表示跳过推镜像，则生成纯构建计划（只做检出+构建，不推镜像）

Step 3  生成 Jenkinsfile + env_vars
  参考业务规范文件确认差异配置（Dockerfile 位置、镜像命名）

Step 4  幂等创建构建计划
  get_or_create_ci_job(...)   ← 推荐，自动去重
  create_ci_job(jenkinsfile=..., envs=...)  ← 需要自定义时

Step 5  触发 + 观察
  trigger_ci_build(job_id, ref)
  list_ci_builds → describe_ci_build → get_ci_build_log
```

---

## 流程 B：GitLab + Jenkins 流程

> ⚠️ 此流程暂未完善，GitLab MCP 和 Jenkins MCP 工具实现尚在开发中。
> 遇到此场景时，告知用户该能力尚未就绪，并记录需求等待后续实现。

```
Step 1  确认 GitLab 项目和目标分支
  gitlab.list_projects(search=...) → project_id, clone_url
  gitlab.list_branches(project_id) → 呈现分支列表，让用户确认目标分支

Step 2  确认 Jenkins Job 是否已存在
  jenkins.list_jobs() → 查找同名 Job

Step 3  创建 Jenkins Job（⚠️ create_job 待实现）
  jenkins.create_job(name, jenkinsfile, git_url, branch)

Step 4  触发构建（⚠️ 待实现真实调用）
  jenkins.trigger_build(job_name, params={branch: ...})

Step 5  观察结果（⚠️ get_build_log 待实现）
  jenkins.get_build_status(job_name, build_number)
  jenkins.get_build_log(job_name, build_number)
```

---

## 标准 CI Pipeline 模板

### 通用版（Dockerfile 在代码根目录，含推镜像）

适用于大多数内部服务。

```groovy
pipeline {
  agent any
  stages {
    stage('检出') {
      steps {
        checkout([$class: 'GitSCM',
          branches: [[name: GIT_BUILD_REF]],
          userRemoteConfigs: [[url: GIT_REPO_URL, credentialsId: CREDENTIALS_ID]]])
      }
    }
    stage('构建镜像') {
      steps {
        script {
          docker.withRegistry("https://${env.CODING_DOCKER_REG_HOST}", "${env.TCR_PUSH_CREDENTIAL_ID}") {
            docker.build("${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}")
          }
        }
      }
    }
    stage('推送镜像') {
      steps {
        script {
          docker.withRegistry("https://${env.CODING_DOCKER_REG_HOST}", "${env.TCR_PUSH_CREDENTIAL_ID}") {
            docker.image("${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}").push()
          }
        }
      }
    }
  }
}
```

### 差异化版（Dockerfile 在子目录）

部分业务的 Dockerfile 不在根目录，需在构建前 copy 出来。
差异仅在 `构建镜像` stage，检出和推送与通用版相同：

```groovy
stage('构建镜像') {
  steps {
    script {
      sh 'cp -rp dockerfile/* .'   // dockerfile 子目录路径见业务规范
      docker.withRegistry("https://${env.CODING_DOCKER_REG_HOST}", "${env.TCR_PUSH_CREDENTIAL_ID}") {
        docker.build("${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}")
      }
    }
  }
}
```

---

## 通用环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `DOCKER_IMAGE_NAME` | 镜像路径（不含 registry host） | `cyouops/my-service-test` |
| `CODING_DOCKER_REG_HOST` | TCR 域名 | `tkeprod.tencentcloudcr.com` |
| `TCR_PUSH_CREDENTIAL_ID` | TCR 推送凭据 UUID（从已有计划获取） | `911589f5-...` |
| `DOCKER_IMAGE_TAG` | 镜像 tag | `${CI_BUILD_NUMBER}` 或 `${GIT_BUILD_REF}` |

### 镜像 Tag 选择

| 场景 | 推荐 |
|------|------|
| 活动类（每次唯一） | `${CI_BUILD_NUMBER}` |
| 内部服务（可追溯分支） | `${GIT_BUILD_REF}` |

---

### 保底版（无镜像凭据时，仅构建验证）

当无法获取 TCR 凭据且用户未提供时，使用此模板。根据技术栈选择构建命令：

```groovy
pipeline {
  agent any
  stages {
    stage('检出') {
      steps {
        checkout([$class: 'GitSCM',
          branches: [[name: GIT_BUILD_REF]],
          userRemoteConfigs: [[url: GIT_REPO_URL, credentialsId: CREDENTIALS_ID]]])
      }
    }
    stage('构建') {
      steps {
        // Java/Maven：
        sh 'mvn package -DskipTests'
        // Java/Gradle：sh './gradlew build'
        // Node.js：sh 'npm ci && npm run build'
        // Python：sh 'pip install -r requirements.txt'
        // Go：sh 'go build ./...'
      }
    }
  }
}
```

保底版**不需要任何 env_vars**，只依赖 Coding CI 内置变量（`GIT_BUILD_REF`、`GIT_REPO_URL`、`CREDENTIALS_ID`）。
创建时使用 `create_ci_job(project_id, name, depot_id, jenkinsfile=...)`，不传 `envs`。

---

## 业务规范文件

| 业务线 | 文件 | 主要差异 |
|--------|------|---------|
| 外包活动 | `references/waibaohuodong.md` | Dockerfile 在 `code/dockerfile/`，镜像命名规则 |
| 运维平台 | `references/renwupingtai.md` | 镜像命名、test/prod 双环境规范 |
| 新业务 | `references/new-business.md` | 接入决策和信息收集 |
