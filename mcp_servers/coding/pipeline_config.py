import os
from pathlib import Path

import yaml

_CONFIG_DIR = Path(os.environ.get("PIPELINE_CONFIG_DIR", "configs/pipelines"))


def _project_path(project_name: str) -> Path:
    path = _CONFIG_DIR / f"{project_name}.yaml"
    return path


def _load(project_name: str) -> dict:
    path = _project_path(project_name)
    if not path.exists():
        return {
            "project_name": project_name,
            "params": [],
            "repos": [],
            "triggers": [],
            "notifications": [],
            "artifacts": [],
        }
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save(project_name: str, data: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = _project_path(project_name)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ── Params ─────────────────────────────────────────────────────

def define_params(project_name: str, job_name: str, params: list[dict]) -> dict:
    data = _load(project_name)
    job = _ensure_job(data, job_name)
    job["params"] = params
    _save(project_name, data)
    return {"job_name": job_name, "param_count": len(params)}


def list_params(project_name: str, job_name: str) -> list[dict]:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return []
    return job.get("params", [])


def update_param(project_name: str, job_name: str, param_name: str, updates: dict) -> dict:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return {"error": f"流水线 {job_name} 未找到"}
    for p in job.get("params", []):
        if p["name"] == param_name:
            p.update(updates)
            _save(project_name, data)
            return p
    return {"error": f"参数 {param_name} 未找到"}


def delete_param(project_name: str, job_name: str, param_name: str) -> dict:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return {"error": f"流水线 {job_name} 未找到"}
    before = len(job.get("params", []))
    job["params"] = [p for p in job.get("params", []) if p["name"] != param_name]
    after = len(job["params"])
    if before == after:
        return {"error": f"参数 {param_name} 未找到"}
    _save(project_name, data)
    return {"deleted": param_name}


# ── Repos ──────────────────────────────────────────────────────

def link_repo(project_name: str, job_name: str, repo: dict) -> dict:
    data = _load(project_name)
    job = _ensure_job(data, job_name)
    existing = [r for r in job.get("repos", []) if r.get("repo_url") == repo.get("repo_url")]
    if existing:
        existing[0].update(repo)
    else:
        job.setdefault("repos", []).append(repo)
    _save(project_name, data)
    return repo


def list_repos(project_name: str, job_name: str) -> list[dict]:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return []
    return job.get("repos", [])


def unlink_repo(project_name: str, job_name: str, repo_url: str) -> dict:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return {"error": f"流水线 {job_name} 未找到"}
    before = len(job.get("repos", []))
    job["repos"] = [r for r in job.get("repos", []) if r.get("repo_url") != repo_url]
    if len(job["repos"]) == before:
        return {"error": f"仓库 {repo_url} 未关联"}
    _save(project_name, data)
    return {"unlinked": repo_url}


def configure_webhook(project_name: str, job_name: str, repo_url: str, events: list[str]) -> dict:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return {"error": f"流水线 {job_name} 未找到"}
    for r in job.get("repos", []):
        if r.get("repo_url") == repo_url:
            r["webhook_enabled"] = True
            r["webhook_events"] = events
            _save(project_name, data)
            return {"repo_url": repo_url, "events": events, "webhook_enabled": True}
    return {"error": f"仓库 {repo_url} 未关联，请先 link_repository"}


# ── Triggers ───────────────────────────────────────────────────

def configure_trigger(project_name: str, job_name: str, trigger: dict) -> dict:
    data = _load(project_name)
    job = _ensure_job(data, job_name)
    triggers = job.setdefault("triggers", [])
    existing = [t for t in triggers if t.get("trigger_type") == trigger.get("trigger_type")]
    if existing:
        existing[0].update(trigger)
        result = existing[0]
    else:
        triggers.append(trigger)
        result = trigger
    _save(project_name, data)
    return result


def list_triggers(project_name: str, job_name: str) -> list[dict]:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return []
    return job.get("triggers", [])


def delete_trigger(project_name: str, job_name: str, trigger_type: str) -> dict:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return {"error": f"流水线 {job_name} 未找到"}
    before = len(job.get("triggers", []))
    job["triggers"] = [t for t in job.get("triggers", []) if t.get("trigger_type") != trigger_type]
    if len(job["triggers"]) == before:
        return {"error": f"触发类型 {trigger_type} 未找到"}
    _save(project_name, data)
    return {"deleted": trigger_type}


# ── Notifications ──────────────────────────────────────────────

def configure_notification(project_name: str, job_name: str, notification: dict) -> dict:
    data = _load(project_name)
    job = _ensure_job(data, job_name)
    notifs = job.setdefault("notifications", [])
    channel = notification.get("channel")
    existing = [n for n in notifs if n.get("channel") == channel]
    if existing:
        existing[0].update(notification)
        result = existing[0]
    else:
        notifs.append(notification)
        result = notification
    _save(project_name, data)
    return result


def list_notifications(project_name: str, job_name: str) -> list[dict]:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return []
    return job.get("notifications", [])


def delete_notification(project_name: str, job_name: str, channel: str) -> dict:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return {"error": f"流水线 {job_name} 未找到"}
    before = len(job.get("notifications", []))
    job["notifications"] = [n for n in job.get("notifications", []) if n.get("channel") != channel]
    if len(job["notifications"]) == before:
        return {"error": f"通知渠道 {channel} 未找到"}
    _save(project_name, data)
    return {"deleted": channel}


# ── Artifacts ──────────────────────────────────────────────────

def configure_artifact(project_name: str, job_name: str, artifact: dict) -> dict:
    data = _load(project_name)
    job = _ensure_job(data, job_name)
    job["artifacts"] = [artifact]
    _save(project_name, data)
    return artifact


def list_artifacts_config(project_name: str, job_name: str) -> list[dict]:
    data = _load(project_name)
    job = _find_job(data, job_name)
    if not job:
        return []
    return job.get("artifacts", [])


# ── Helpers ────────────────────────────────────────────────────

def _ensure_job(data: dict, job_name: str) -> dict:
    jobs = data.setdefault("jobs", {})
    if job_name not in jobs:
        jobs[job_name] = {
            "params": [],
            "repos": [],
            "triggers": [],
            "notifications": [],
            "artifacts": [],
        }
    return jobs[job_name]


def _find_job(data: dict, job_name: str) -> dict | None:
    return data.get("jobs", {}).get(job_name)
