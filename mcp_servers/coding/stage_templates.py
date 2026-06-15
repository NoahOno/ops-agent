STAGE_TEMPLATES: dict[str, dict] = {
    "maven-build": {
        "name": "maven-build",
        "description": "Java Maven 构建：编译 + 打包（跳过测试）",
        "language": "java",
        "tools": ["maven"],
        "steps": [
            "sh 'mvn clean package -DskipTests'",
        ],
        "jenkinsfile_snippet": """\
        stage('Maven Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }""",
    },
    "maven-test": {
        "name": "maven-test",
        "description": "Java Maven 单元测试",
        "language": "java",
        "tools": ["maven"],
        "steps": [
            "sh 'mvn test'",
        ],
        "jenkinsfile_snippet": """\
        stage('Maven Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit '**/target/surefire-reports/*.xml'
                }
            }
        }""",
    },
    "gradle-build": {
        "name": "gradle-build",
        "description": "Java Gradle 构建",
        "language": "java",
        "tools": ["gradle"],
        "steps": [
            "sh './gradlew build -x test'",
        ],
        "jenkinsfile_snippet": """\
        stage('Gradle Build') {
            steps {
                sh './gradlew build -x test'
            }
        }""",
    },
    "npm-build": {
        "name": "npm-build",
        "description": "Node.js npm 安装依赖 + 构建",
        "language": "nodejs",
        "tools": ["node", "npm"],
        "steps": [
            "sh 'npm ci'",
            "sh 'npm run build'",
        ],
        "jenkinsfile_snippet": """\
        stage('NPM Build') {
            steps {
                sh 'npm ci'
                sh 'npm run build'
            }
        }""",
    },
    "npm-test": {
        "name": "npm-test",
        "description": "Node.js 单元测试",
        "language": "nodejs",
        "tools": ["node", "npm"],
        "steps": [
            "sh 'npm test'",
        ],
        "jenkinsfile_snippet": """\
        stage('NPM Test') {
            steps {
                sh 'npm test'
            }
        }""",
    },
    "go-build": {
        "name": "go-build",
        "description": "Go 编译构建",
        "language": "go",
        "tools": ["go"],
        "steps": [
            "sh 'go mod download'",
            "sh 'go build -o output/app ./...'",
        ],
        "jenkinsfile_snippet": """\
        stage('Go Build') {
            steps {
                sh 'go mod download'
                sh 'go build -o output/app ./...'
            }
        }""",
    },
    "go-test": {
        "name": "go-test",
        "description": "Go 单元测试",
        "language": "go",
        "tools": ["go"],
        "steps": [
            "sh 'go test ./... -v'",
        ],
        "jenkinsfile_snippet": """\
        stage('Go Test') {
            steps {
                sh 'go test ./... -v'
            }
        }""",
    },
    "docker-build-push": {
        "name": "docker-build-push",
        "description": "Docker 镜像构建 + 推送",
        "language": "any",
        "tools": ["docker"],
        "params": ["IMAGE_REGISTRY", "IMAGE_REPO", "IMAGE_TAG", "REGISTRY_CREDENTIAL_ID"],
        "steps": [
            "docker build",
            "docker login",
            "docker push",
        ],
        "jenkinsfile_snippet": """\
        stage('Docker Build & Push') {
            steps {
                script {
                    docker.withRegistry("https://${IMAGE_REGISTRY}", "${REGISTRY_CREDENTIAL_ID}") {
                        def img = docker.build("${IMAGE_REPO}:${IMAGE_TAG}", "-f ${DOCKERFILE} ${BUILD_CONTEXT}")
                        img.push()
                    }
                }
            }
        }""",
    },
    "sonar-scan": {
        "name": "sonar-scan",
        "description": "SonarQube 代码质量扫描",
        "language": "any",
        "tools": ["sonar-scanner"],
        "steps": [
            "sh 'sonar-scanner -Dsonar.projectKey=${PROJECT_KEY} -Dsonar.host.url=${SONAR_HOST}'",
        ],
        "jenkinsfile_snippet": """\
        stage('SonarQube Scan') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner -Dsonar.projectKey=${PROJECT_KEY} -Dsonar.host.url=${SONAR_HOST}'
                }
            }
        }""",
    },
    "helm-deploy": {
        "name": "helm-deploy",
        "description": "Helm 部署到 Kubernetes 集群",
        "language": "any",
        "tools": ["helm", "kubectl"],
        "params": ["HELM_RELEASE", "HELM_CHART", "NAMESPACE", "IMAGE_TAG"],
        "steps": [
            "sh 'helm upgrade --install ${HELM_RELEASE} ${HELM_CHART} --namespace ${NAMESPACE} --set image.tag=${IMAGE_TAG}'",
        ],
        "jenkinsfile_snippet": """\
        stage('Helm Deploy') {
            steps {
                sh 'helm upgrade --install ${HELM_RELEASE} ${HELM_CHART} --namespace ${NAMESPACE} --set image.tag=${IMAGE_TAG}'
            }
        }""",
    },
    "artifact-archive": {
        "name": "artifact-archive",
        "description": "制品归档",
        "language": "any",
        "tools": [],
        "params": ["ARCHIVE_PATTERN"],
        "steps": [
            "archiveArtifacts artifacts: '${ARCHIVE_PATTERN}', fingerprint: true",
        ],
        "jenkinsfile_snippet": """\
        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: "${ARCHIVE_PATTERN}", fingerprint: true
            }
        }""",
    },
}


def get_template(name: str) -> dict | None:
    return STAGE_TEMPLATES.get(name)


def list_templates() -> list[dict]:
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "language": t["language"],
            "tools": t["tools"],
        }
        for t in STAGE_TEMPLATES.values()
    ]


def compose_jenkinsfile(
    stages: list[str],
    params_block: str = "",
    env_block: str = "",
    post_block: str = "",
    parallel_groups: dict[str, list[str]] | None = None,
) -> str:
    parts = ["pipeline {", "    agent any", ""]

    if params_block:
        parts.append(f"    parameters {{")
        parts.append(f"        {params_block}")
        parts.append(f"    }}")
        parts.append("")

    if env_block:
        parts.append(f"    environment {{")
        parts.append(f"        {env_block}")
        parts.append(f"    }}")
        parts.append("")

    parts.append("    stages {")
    for stage_name in stages:
        tpl = STAGE_TEMPLATES.get(stage_name)
        if tpl:
            parts.append(f"        {tpl['jenkinsfile_snippet']}")
        else:
            parts.append(f"""        stage('{stage_name}') {{
            steps {{
                echo 'TODO: implement {stage_name}'
            }}
        }}""")

    if parallel_groups:
        parts.append("        stage('Parallel') {")
        parts.append("            parallel {")
        for group_name, group_stages in parallel_groups.items():
            for s in group_stages:
                tpl = STAGE_TEMPLATES.get(s)
                snippet = tpl["jenkinsfile_snippet"] if tpl else f"echo 'TODO: {s}'"
                parts.append(f"                {snippet}")
        parts.append("            }")
        parts.append("        }")

    parts.append("    }")

    if post_block:
        parts.append("")
        parts.append(f"    post {{")
        parts.append(f"        {post_block}")
        parts.append(f"    }}")

    parts.append("}")
    return "\n".join(parts)
