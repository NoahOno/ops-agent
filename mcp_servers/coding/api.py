import os
from dataclasses import dataclass, field

import httpx


@dataclass
class CodingConfig:
    token: str = ""
    team: str = ""
    api_url: str = ""

    def __post_init__(self):
        if not self.token:
            self.token = os.environ.get("CODING_TOKEN", "")
        if not self.token:
            raise ValueError("CODING_TOKEN is required (env var or constructor arg)")
        if not self.team:
            self.team = os.environ.get("CODING_TEAM", "")
        if not self.api_url:
            if self.team:
                self.api_url = f"https://{self.team}.coding.net/open-api"
            else:
                self.api_url = "https://e.coding.net/open-api"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


class CodingClient:
    def __init__(self, config: CodingConfig | None = None):
        self.config = config or CodingConfig()
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        self._http = httpx.AsyncClient(
            headers=self.config.headers,
            timeout=30,
            proxy=proxy or None,
        )

    async def _call(self, action: str, **params) -> dict:
        body = {"Action": action, **params}
        resp = await self._http.post(self.config.api_url, json=body)
        resp.raise_for_status()
        data = resp.json()
        if "Response" in data and "Error" in data["Response"]:
            err = data["Response"]["Error"]
            raise RuntimeError(f"Coding API error: {err.get('Code')} - {err.get('Message')}")
        return data.get("Response", data)

    async def close(self):
        await self._http.aclose()

    # ── Project ──────────────────────────────────────────────

    async def describe_current_user(self) -> dict:
        resp = await self._call("DescribeCodingCurrentUser")
        return resp["User"]

    async def list_projects(self, project_name: str | None = None) -> list[dict]:
        user = await self.describe_current_user()
        params: dict = {"UserId": user["Id"]}
        if project_name:
            params["ProjectName"] = project_name
        resp = await self._call("DescribeUserProjects", **params)
        return resp.get("ProjectList", [])

    async def get_project_by_name(self, project_name: str) -> dict:
        resp = await self._call("DescribeProjectByName", ProjectName=project_name)
        return resp.get("Project", {})

    async def create_project(
        self,
        name: str,
        display_name: str,
        description: str = "",
        project_template: str = "DEV_OPS",
        shared: str = "0",
    ) -> dict:
        resp = await self._call(
            "CreateCodingProject",
            Name=name,
            DisplayName=display_name,
            Description=description,
            ProjectTemplate=project_template,
            Shared=shared,
        )
        return {"ProjectId": resp.get("ProjectId")}

    async def delete_project(self, project_id: str) -> None:
        await self._call("DeleteOneProject", ProjectId=project_id)

    # ── Issue / Work Item ────────────────────────────────────

    async def list_issues(
        self,
        project_name: str,
        issue_type: str = "ALL",
        limit: str = "20",
        offset: str = "0",
        sort_key: str = "UPDATED_AT",
        sort_value: str = "DESC",
    ) -> list[dict]:
        resp = await self._call(
            "DescribeIssueList",
            ProjectName=project_name,
            IssueType=issue_type,
            Limit=limit,
            Offset=offset,
            SortKey=sort_key,
            SortValue=sort_value,
        )
        return resp.get("IssueList", [])

    async def describe_issue(self, project_name: str, issue_code: int) -> dict:
        resp = await self._call(
            "DescribeIssue",
            ProjectName=project_name,
            IssueCode=issue_code,
        )
        return resp.get("Issue", {})

    async def create_issue(
        self,
        project_name: str,
        name: str,
        issue_type: str,
        priority: str,
        description: str,
        parent_code: int | None = None,
    ) -> dict:
        params: dict = {
            "ProjectName": project_name,
            "Name": name,
            "Type": issue_type,
            "Priority": priority,
            "Description": description,
        }
        if parent_code is not None:
            params["ParentCode"] = parent_code
        resp = await self._call("CreateIssue", **params)
        return resp.get("Issue", {})

    async def delete_issue(self, project_name: str, issue_code: int) -> None:
        await self._call(
            "DeleteIssue",
            ProjectName=project_name,
            IssueCode=issue_code,
        )

    # ── Code / Depot ─────────────────────────────────────────

    async def list_depots(
        self,
        project_id: str,
        page_number: str = "1",
        page_size: str = "20",
    ) -> dict:
        resp = await self._call(
            "DescribeProjectDepotInfoList",
            ProjectId=project_id,
            PageNumber=page_number,
            PageSize=page_size,
        )
        return resp.get("DepotData", {})

    async def list_commits(
        self,
        ref: str,
        depot_id: str | None = None,
        depot_path: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        keyword: str | None = None,
        page_number: str = "1",
        page_size: str = "20",
        path: str | None = None,
    ) -> dict:
        params: dict = {
            "Ref": ref,
            "PageNumber": page_number,
            "PageSize": page_size,
        }
        if depot_id:
            params["DepotId"] = depot_id
        if depot_path:
            params["DepotPath"] = depot_path
        if start_date:
            params["StartDate"] = start_date
        if end_date:
            params["EndDate"] = end_date
        if keyword:
            params["KeyWord"] = keyword
        if path:
            params["Path"] = path
        resp = await self._call("DescribeGitCommitsInPage", **params)
        return resp.get("Data", {})

    async def create_merge_request(
        self,
        depot_path: str,
        title: str,
        content: str,
        src_branch: str,
        dest_branch: str,
    ) -> dict:
        resp = await self._call(
            "CreateGitMergeReq",
            DepotPath=depot_path,
            Title=title,
            Content=content,
            SrcBranch=src_branch,
            DestBranch=dest_branch,
        )
        return resp

    # ── CI Build (构建计划) ──────────────────────────────────

    async def list_ci_jobs(self, project_id: int) -> list[dict]:
        """查询项目下的构建计划列表"""
        resp = await self._call(
            "DescribeCodingCIJobs",
            ProjectId=project_id,
        )
        return resp.get("JobList", resp.get("JobSet", []))

    async def describe_ci_job(self, job_id: int) -> dict:
        """获取构建计划详情"""
        resp = await self._call(
            "DescribeCodingCIJob",
            Id=job_id,
        )
        return resp.get("Job", {})

    async def create_ci_job(
        self,
        project_id: int,
        name: str,
        depot_id: int | None = None,
        jenkinsfile: str | None = None,
        execute_in: str = "CVM",
        trigger_methods: list[dict] | None = None,
        envs: list[dict] | None = None,
    ) -> dict:
        """创建构建计划。execute_in 可选: CVM, STATIC, AGENT。
        提供 jenkinsfile 时使用 STATIC 模式 (JenkinsFileFromType=STATIC)。
        trigger_methods 每项需包含 triggerMethod 字段: REF_CHANGE / CRON / MR_CHANGE。
        """
        params: dict = {
            "ProjectId": project_id,
            "Name": name,
            "ExecuteIn": execute_in,
            "JobFromType": "CODING",
            "HookType": "DEFAULT",
            "AutoCancelSameRevision": False,
            "AutoCancelSameMergeRequest": False,
            "DepotType": "CODING",
        }
        if depot_id is not None:
            params["DepotId"] = depot_id
        if jenkinsfile is not None:
            params["JenkinsFileFromType"] = "STATIC"
            params["JenkinsFileStaticContent"] = jenkinsfile
        else:
            params["JenkinsFileFromType"] = "SCM"
            params["JenkinsFilePath"] = "Jenkinsfile"
        if trigger_methods:
            params["TriggerMethodList"] = [m.get("TriggerMethod", m) if isinstance(m, dict) else m for m in trigger_methods]
        if envs:
            params["EnvList"] = envs
        resp = await self._call("CreateCodingCIJob", **params)
        return resp

    async def trigger_ci_build(
        self,
        job_id: int,
        ref: str = "master",
        envs: list[dict] | None = None,
    ) -> dict:
        """触发构建。ref 为分支名或 CommitId"""
        params: dict = {
            "JobId": job_id,
            "Ref": ref,
        }
        if envs:
            params["Envs"] = envs
        resp = await self._call("TriggerCodingCIBuild", **params)
        return resp

    async def list_ci_builds(
        self,
        job_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取构建计划的构建记录列表"""
        resp = await self._call(
            "DescribeCodingCIBuilds",
            JobId=job_id,
            Page=page,
            PageSize=page_size,
        )
        return resp

    async def describe_ci_build(self, build_id: int) -> dict:
        """查询构建记录详情"""
        resp = await self._call(
            "DescribeCodingCIBuild",
            Id=build_id,
        )
        return resp.get("Build", resp)

    async def get_ci_build_log(self, build_id: int, log_start: int = 0) -> dict:
        """获取构建日志"""
        resp = await self._call(
            "DescribeCodingCIBuildLog",
            Id=build_id,
            LogStart=log_start,
        )
        return resp
