# 运维平台（renwupingtai / pinkongzidonghua / AIOpsEngineer）业务规范

## 业务特征

- Coding 项目：`renwupingtai`、`pinkongzidonghua`、`AIOpsEngineer`
- Dockerfile 在代码根目录，直接使用通用版模板

## 环境变量规范

```json
[
  {"Name": "DOCKER_IMAGE_NAME",      "Value": "cyouops/{service-name}-{env}"},
  {"Name": "CODING_DOCKER_REG_HOST", "Value": "tkeprod.tencentcloudcr.com"},
  {"Name": "TCR_PUSH_CREDENTIAL_ID", "Value": "<凭据UUID，从同项目已有计划获取>"},
  {"Name": "DOCKER_IMAGE_TAG",       "Value": "${GIT_BUILD_REF}"}
]
```

## 环境对应关系

| 环境 | 计划名后缀 | 镜像名后缀 |
|------|----------|---------|
| 测试 | `-test` | `-test` |
| 正式 | `-prod` | `-prod` |

test 和 prod 的 `TCR_PUSH_CREDENTIAL_ID` 可能不同，分别从对应环境的已有计划中获取。

## 命名示例

- `op-auto-manager-test` → 镜像 `cyouops/op-auto-manager-test`
- `cmdb-v2-prod` → 镜像 `cyouops/cmdb-v2-prod`
