---
name: pipeline-composer
description: >
  编排构建步骤，生成完整的 Jenkinsfile/Pipeline 脚本。
  当用户需要创建或修改流水线的构建流程时使用此 skill。
  从预定义的 Stage 模板中选择组合，输出完整的 Pipeline 脚本
  （Stage列表/步骤定义/并行配置/后置处理）。
---

# Pipeline Composer

## 适用场景

- 用户说"编排构建步骤"、"创建 Pipeline"、"生成 Jenkinsfile"
- 需要组合多个构建阶段（编译→测试→打包→推送→部署）
- 修改已有流水线的构建步骤

## 执行流程

```
Step 1  了解构建需求
  询问:
    - 项目技术栈（Java/Node/Go/Python/通用）
    - 构建目标（仅编译 / 编译+测试 / 编译+推镜像 / 编译+推镜像+部署）
    - 是否需要并行构建

Step 2  展示可用模板
  调用 list_stage_templates() 列出所有可用阶段模板
  根据技术栈推荐组合:

    Java 标准流程:  maven-build → maven-test → docker-build-push
    Node 标准流程:  npm-build → npm-test → docker-build-push
    Go 标准流程:    go-build → go-test → docker-build-push
    完整部署流程:   *-build → *-test → docker-build-push → helm-deploy

Step 3  选择并排列阶段
  用户确认:
    - 选用哪些 Stage 模板
    - 执行顺序
    - 是否需要并行组（如同时跑 lint 和 test）
    - 是否需要自定义步骤（模板不覆盖的场景）

Step 4  配置参数和环境变量
  检查是否需要:
    - parameters 块（调用 list_pipeline_params 获取已定义参数）
    - environment 块（镜像地址、凭据 ID 等）
    - post 块（清理、通知）

Step 5  生成 Jenkinsfile
  调用 compose_pipeline(stages, params_block, env_block, post_block)
  展示生成的 Jenkinsfile 供用户确认

Step 6  创建/更新构建计划
  用户确认后:
    - Coding CI: create_ci_job 或 get_or_create_ci_job
    - Jenkins: jenkins.create_job
```

## 可用 Stage 模板

| 模板 | 语言 | 说明 |
|------|------|------|
| `maven-build` | Java | mvn clean package -DskipTests |
| `maven-test` | Java | mvn test + junit 报告 |
| `gradle-build` | Java | ./gradlew build -x test |
| `npm-build` | Node.js | npm ci + npm run build |
| `npm-test` | Node.js | npm test |
| `go-build` | Go | go mod download + go build |
| `go-test` | Go | go test ./... -v |
| `docker-build-push` | 通用 | docker build + login + push |
| `sonar-scan` | 通用 | SonarQube 代码扫描 |
| `helm-deploy` | 通用 | Helm upgrade --install |
| `artifact-archive` | 通用 | 制品归档 |

## 推荐组合

### Java 微服务（仅 CI）
```
maven-build → maven-test → docker-build-push
```

### Java 微服务（CI + CD）
```
maven-build → maven-test → docker-build-push → helm-deploy
```

### Node.js 前端
```
npm-build → npm-test → docker-build-push
```

### Go 服务 + 代码扫描
```
go-build → go-test → sonar-scan → docker-build-push
```

### 并行构建示例
```
Stage 1: checkout（串行）
Stage 2: parallel { maven-test, sonar-scan }
Stage 3: docker-build-push（串行）
```

## Post 块模板

### 标准清理
```groovy
post {
    always {
        cleanWs()
    }
    success {
        echo 'Build succeeded'
    }
    failure {
        echo 'Build failed'
    }
}
```

### 清理 + 通知
```groovy
post {
    always {
        cleanWs()
    }
    failure {
        dingtalk(
            robot: 'my-robot',
            type: 'MARKDOWN',
            title: '构建失败',
            text: ["- 项目: ${env.JOB_NAME}", "- 构建: #${env.BUILD_NUMBER}"]
        )
    }
}
```

## MCP 工具调用

| 步骤 | 工具 |
|------|------|
| 查看可用模板 | `list_stage_templates()` |
| 获取模板详情 | `get_stage_template(name)` |
| 组合生成 Jenkinsfile | `compose_pipeline(stages, params_block, env_block, post_block)` |
| 创建 Coding CI 计划 | `create_ci_job(...)` / `get_or_create_ci_job(...)` |
| 创建 Jenkins Job | `jenkins.create_job(name, jenkinsfile, git_url, branch)` |
| 查看已有参数 | `list_pipeline_params(project_name, job_name)` |
