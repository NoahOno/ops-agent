import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx


@dataclass
class JenkinsConfig:
    url: str = ""
    user: str = ""
    token: str = ""

    def __post_init__(self):
        if not self.url:
            self.url = os.environ.get("JENKINS_URL", "")
        if not self.user:
            self.user = os.environ.get("JENKINS_USER", "")
        if not self.token:
            self.token = os.environ.get("JENKINS_TOKEN", "")
        if not self.url:
            raise ValueError("JENKINS_URL is required (env var or constructor arg)")
        if not self.user:
            raise ValueError("JENKINS_USER is required (env var or constructor arg)")
        if not self.token:
            raise ValueError("JENKINS_TOKEN is required (env var or constructor arg)")
        self.url = self.url.rstrip("/")


def _encode_job(name: str) -> str:
    return quote(name, safe="")


class JenkinsClient:
    def __init__(self, config: JenkinsConfig | None = None):
        self.config = config or JenkinsConfig()
        proxy = (
            os.environ.get("HTTPS_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("http_proxy")
        )
        self._http = httpx.AsyncClient(
            base_url=self.config.url,
            auth=(self.config.user, self.config.token),
            timeout=60,
            proxy=proxy or None,
        )
        self._crumb: dict[str, str] | None = None

    async def _get_crumb(self) -> dict[str, str]:
        if self._crumb is not None:
            return self._crumb
        try:
            resp = await self._http.get("/crumbIssuer/api/json")
            resp.raise_for_status()
            data = resp.json()
            self._crumb = {data["crumbRequestField"]: data["crumb"]}
        except httpx.HTTPStatusError:
            self._crumb = {}
        return self._crumb

    async def _post(self, path: str, **kwargs) -> httpx.Response:
        crumb = await self._get_crumb()
        headers = kwargs.pop("headers", {})
        headers.update(crumb)
        resp = await self._http.post(path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    async def _get_json(self, path: str) -> dict:
        resp = await self._http.get(path)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._http.aclose()

    async def list_jobs(self) -> list[dict]:
        """列出所有顶层 job"""
        data = await self._get_json("/api/json?tree=jobs[name,color,url,buildable,lastBuild[number,result,timestamp]]")
        return data.get("jobs", [])

    async def create_job(
        self,
        name: str,
        jenkinsfile: str,
        git_url: str = "",
        branch: str = "master",
        credentials_id: str = "",
    ) -> None:
        """创建 Pipeline job，使用内联 Jenkinsfile。git_url/branch/credentials_id 供 Jenkinsfile 脚本内部使用"""
        xml_config = self._build_pipeline_xml(jenkinsfile)
        await self._post(
            f"/createItem?name={_encode_job(name)}",
            content=xml_config.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

    async def trigger_build(self, job_name: str, params: dict | None = None) -> None:
        """触发构建。有参数时使用 buildWithParameters"""
        encoded = _encode_job(job_name)
        if params:
            await self._post(f"/job/{encoded}/buildWithParameters", params=params)
        else:
            await self._post(f"/job/{encoded}/build")

    async def get_build_status(self, job_name: str, build_number: int) -> dict:
        """获取构建状态"""
        encoded = _encode_job(job_name)
        return await self._get_json(
            f"/job/{encoded}/{build_number}/api/json"
            "?tree=number,result,building,timestamp,duration,displayName,fullDisplayName,url"
        )

    async def get_last_build_number(self, job_name: str) -> int | None:
        """获取最新构建编号，无构建时返回 None"""
        encoded = _encode_job(job_name)
        data = await self._get_json(f"/job/{encoded}/api/json?tree=lastBuild[number]")
        last = data.get("lastBuild")
        return last["number"] if last else None

    async def get_build_log(self, job_name: str, build_number: int) -> str:
        """获取构建控制台日志"""
        encoded = _encode_job(job_name)
        resp = await self._http.get(f"/job/{encoded}/{build_number}/consoleText")
        resp.raise_for_status()
        return resp.text

    async def cancel_build(self, job_name: str, build_number: int) -> None:
        """中止正在运行的构建"""
        encoded = _encode_job(job_name)
        await self._post(f"/job/{encoded}/{build_number}/stop")

    async def replay_build(self, job_name: str, build_number: int) -> None:
        """以相同参数重新触发构建"""
        encoded = _encode_job(job_name)
        await self._post(f"/job/{encoded}/{build_number}/replay/replay")

    async def get_build_stages(self, job_name: str, build_number: int) -> list[dict]:
        """获取构建的各 Stage 状态和耗时（Blue Ocean API）"""
        encoded = _encode_job(job_name)
        data = await self._get_json(
            f"/blue/rest/organizations/jenkins/pipelines/{encoded}/runs/{build_number}/nodes"
        )
        stages = []
        for node in data:
            stages.append({
                "name": node.get("displayName", ""),
                "status": node.get("result", "UNKNOWN"),
                "state": node.get("state", ""),
                "duration_ms": node.get("durationInMillis", 0),
                "start_time": node.get("startTime", ""),
            })
        return stages

    @staticmethod
    def _build_pipeline_xml(jenkinsfile: str) -> str:
        """生成 Pipeline 内联脚本的 Jenkins config.xml"""
        return f"""\
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[{jenkinsfile}]]></script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
</flow-definition>"""
