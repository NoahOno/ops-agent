import os
from dataclasses import dataclass

import httpx


@dataclass
class GitLabConfig:
    url: str = ""
    token: str = ""

    def __post_init__(self):
        if not self.url:
            self.url = os.environ.get("GITLAB_URL", "")
        if not self.token:
            self.token = os.environ.get("GITLAB_TOKEN", "")
        if not self.url:
            raise ValueError("GITLAB_URL is required (env var or constructor arg)")
        if not self.token:
            raise ValueError("GITLAB_TOKEN is required (env var or constructor arg)")
        self.url = self.url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "PRIVATE-TOKEN": self.token,
            "Accept": "application/json",
        }


class GitLabClient:
    def __init__(self, config: GitLabConfig | None = None):
        self.config = config or GitLabConfig()
        proxy = (
            os.environ.get("HTTPS_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("http_proxy")
        )
        self._http = httpx.AsyncClient(
            base_url=self.config.url,
            headers=self.config.headers,
            timeout=30,
            proxy=proxy or None,
        )

    async def _get(self, path: str, **params) -> dict | list:
        resp = await self._http.get(f"/api/v4{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._http.aclose()

    async def list_projects(
        self,
        search: str = "",
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        """搜索项目，返回匹配列表"""
        params: dict = {"page": page, "per_page": per_page, "order_by": "last_activity_at", "sort": "desc"}
        if search:
            params["search"] = search
        return await self._get("/projects", **params)

    async def get_project(self, project_id: int) -> dict:
        """获取项目详情"""
        return await self._get(f"/projects/{project_id}")

    async def list_branches(
        self,
        project_id: int,
        search: str = "",
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict]:
        """列出项目分支"""
        params: dict = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        return await self._get(f"/projects/{project_id}/repository/branches", **params)
