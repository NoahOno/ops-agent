"""Jenkinsfile 模板生成"""


def build_and_push_image(
    image_registry: str,
    image_repo: str,
    image_tag: str = "${GIT_COMMIT[0..7]}",
    dockerfile: str = "Dockerfile",
    build_context: str = ".",
    registry_credential_id: str = "REGISTRY_CREDENTIAL",
) -> str:
    """生成构建+推送镜像的声明式 Jenkinsfile。

    参数均可在 Coding CI 环境变量中覆盖，模板仅提供默认值。
    """
    return f"""\
pipeline {{
    agent any

    environment {{
        IMAGE_REGISTRY   = "{image_registry}"
        IMAGE_REPO       = "{image_repo}"
        IMAGE_TAG        = "{image_tag}"
        DOCKERFILE       = "{dockerfile}"
        BUILD_CONTEXT    = "{build_context}"
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}

        stage('Build Image') {{
            steps {{
                sh '''
                    docker build \\
                        -f $DOCKERFILE \\
                        -t $IMAGE_REGISTRY/$IMAGE_REPO:$IMAGE_TAG \\
                        $BUILD_CONTEXT
                '''
            }}
        }}

        stage('Push Image') {{
            steps {{
                withCredentials([usernamePassword(
                    credentialsId: '{registry_credential_id}',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {{
                    sh '''
                        echo "$REGISTRY_PASS" | docker login $IMAGE_REGISTRY -u "$REGISTRY_USER" --password-stdin
                        docker push $IMAGE_REGISTRY/$IMAGE_REPO:$IMAGE_TAG
                    '''
                }}
            }}
        }}
    }}

    post {{
        always {{
            sh 'docker rmi $IMAGE_REGISTRY/$IMAGE_REPO:$IMAGE_TAG || true'
        }}
    }}
}}
"""
