# 外包活动（waibaohuodong）业务规范

## 业务特征

- Coding 项目：`waibaohuodong`
- 服务类型：游戏活动 H5（天龙归来、天龙经典、刀剑、水浒Q传等）
- 每个活动通常包含：前端（frontend）、后端（backend），部分有管理端（admin-frontend / admin-backend）

## 与通用模板的差异

Dockerfile **不在代码根目录**，位于 `code/dockerfile/` 子目录（构建前需 copy）。

使用差异化版模板，`构建镜像` stage：

```groovy
stage('构建镜像') {
  steps {
    script {
      sh 'cp -rp code/dockerfile/* .'
      docker.withRegistry("https://${env.CODING_DOCKER_REG_HOST}", "${env.TCR_PUSH_CREDENTIAL_ID}") {
        docker.build("${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}")
      }
    }
  }
}
```

## 环境变量规范

```json
[
  {"Name": "DOCKER_IMAGE_NAME",      "Value": "web-wbhd/{项目}-{服务类型}-prod"},
  {"Name": "CODING_DOCKER_REG_HOST", "Value": "tkeprod.tencentcloudcr.com"},
  {"Name": "TCR_PUSH_CREDENTIAL_ID", "Value": "<凭据UUID，从同项目已有计划获取>"},
  {"Name": "DOCKER_IMAGE_TAG",       "Value": "${CI_BUILD_NUMBER}"}
]
```

## 凭据 ID

同 `waibaohuodong` 项目内所有计划共用同一套凭据，从任意一个已有计划 `describe_ci_job` 获取复用。

## 命名规范

| 活动简称 | 后端计划名 | 前端计划名 |
|---------|-----------|-----------|
| `tlgl-ghzbv8` | `tlgl-ghzbv8-backend-prod-build` | `tlgl-ghzbv8-frontend-prod-build` |
| `tljd-5ybfhf` | `tljd-5ybfhf-backend-prod-build` | `tljd-5ybfhf-frontend-prod-build` |
| `dj-q2ns` | `dj-q2ns-backend-prod-build` | `dj-q2ns-frontend-prod-build` |
