"""Bounded GitHub clients; credentials never enter arguments or evidence."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .contracts import (
    ContractError, Json, array_value, object_value, positive_integer,
    repository_name, string_value,
)

API_VERSION = "2026-03-10"
MAX_RESPONSE = 2 * 1024 * 1024


def redact(value: str, *tokens: str) -> str:
    for token in tokens:
        if token:
            value = value.replace(token, "[REDACTED]")
    return re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b", "[REDACTED]", value)


class ApiError(RuntimeError):
    """A bounded, credential-redacted API diagnostic."""


class Api(Protocol):
    def request(self, method: str, path: str, body: dict[str, Json] | None = None) -> Json: ...


def check_path(path: str, method: str = "GET") -> None:
    agent_path = path.startswith("/agents/repos/")
    if not path.startswith("/repos/") and not agent_path and path not in {"/graphql", "/user"}:
        raise ContractError("API path is outside the demo's GitHub endpoints")
    if agent_path and method != "GET":
        raise ContractError("Agent Tasks endpoints are read-only; this demo starts work only by issue assignment")
    if any(char in path for char in ("\r", "\n", "#", "\\")) or ".." in path.split("/"):
        raise ContractError("Unsafe API path")


def decode_json(raw: bytes) -> Json:
    if len(raw) > MAX_RESPONSE:
        raise ApiError("GitHub response exceeds the 2 MiB limit; refusing incomplete evidence")
    try:
        return json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApiError("GitHub returned an invalid JSON response") from error


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ApiError("GitHub API redirect refused; verify repository identity before retrying")


@dataclass(frozen=True)
class RestApi:
    token: str = field(repr=False)

    def request(self, method: str, path: str, body: dict[str, Json] | None = None) -> Json:
        check_path(path, method)
        if not self.token or self.token.strip() != self.token or any(c.isspace() for c in self.token):
            raise ApiError("Required GitHub token is missing or malformed")
        request = Request(
            "https://api.github.com" + path,
            method=method,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self.token,
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "ghcp-demo-19-issue-to-cloud-agent",
            },
        )
        try:
            with build_opener(NoRedirect()).open(request, timeout=30) as response:
                return decode_json(response.read(MAX_RESPONSE + 1))
        except HTTPError as error:
            with error:
                detail = redact(error.read(4096).decode("utf-8", errors="replace"), self.token)
                request_id = error.headers.get("X-GitHub-Request-Id", "unavailable")
            raise ApiError(
                f"{method} {path}: HTTP {error.code}; request {request_id}; {detail}"
            ) from None
        except (URLError, TimeoutError) as error:
            raise ApiError(f"{method} {path}: transport failure: {redact(str(error), self.token)}") from None


def gh_json(arguments: list[str], body: dict[str, Json] | None = None) -> Json:
    try:
        result = subprocess.run(
            ["gh", *arguments],
            input=None if body is None else json.dumps(body),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
    except FileNotFoundError:
        raise ApiError("GitHub CLI (gh) is required for this live command") from None
    except subprocess.TimeoutExpired:
        raise ApiError("GitHub CLI timed out; a mutation may have succeeded. Inspect before retrying.") from None
    if result.returncode:
        raise ApiError(f"GitHub CLI failed ({result.returncode}): {redact(result.stderr.strip())}")
    return decode_json(result.stdout.encode("utf-8"))


class GhApi:
    def request(self, method: str, path: str, body: dict[str, Json] | None = None) -> Json:
        check_path(path, method)
        arguments = [
            "api", "--hostname", "github.com", "--method", method,
            "-H", "Accept: application/vnd.github+json",
            "-H", f"X-GitHub-Api-Version: {API_VERSION}", path,
        ]
        if body is not None:
            arguments.extend(["--input", "-"])
        return gh_json(arguments, body)


def paginated(api: Api, path: str, collection_key: str | None = None) -> list[Json]:
    result: list[Json] = []
    separator = "&" if "?" in path else "?"
    for page in range(1, 11):
        raw = api.request("GET", f"{path}{separator}per_page=100&page={page}")
        if collection_key is not None:
            raw = object_value(raw, path).get(collection_key)
        items = array_value(raw, path)
        result.extend(items)
        if len(items) < 100:
            return result
    raise ContractError("Pagination limit reached; refusing incomplete GitHub evidence")


def task_has_pull(task: dict[str, Json], pull_id: int) -> bool:
    for item in array_value(task.get("artifacts"), "task.artifacts"):
        artifact = object_value(item, "task artifact")
        if artifact.get("provider") == "github" and artifact.get("type") == "pull":
            data = object_value(artifact.get("data"), "pull artifact data")
            if positive_integer(data.get("id"), "pull artifact id") == pull_id:
                return True
    return False


def session_created_at(session: dict[str, Json]) -> datetime:
    value = string_value(session.get("created_at"), "session.created_at")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ContractError("Session creation time is not a valid ISO timestamp") from None
    if timestamp.tzinfo is None:
        raise ContractError("Session creation time must include a timezone")
    return timestamp


def task_session_for_pull(
    api: Api, repository: str, pull_id: int,
) -> tuple[dict[str, Json], dict[str, Json] | None]:
    prefix = f"/agents/repos/{repository_name(repository)}/tasks"
    positive_integer(pull_id, "pull request database id")
    matches: dict[str, dict[str, Json]] = {}
    for archived in ("false", "true"):
        tasks = paginated(
            api, f"{prefix}?is_archived={archived}&sort=created_at&direction=asc", "tasks",
        )
        for item in tasks:
            task = object_value(item, "agent task")
            if task_has_pull(task, pull_id):
                task_id = string_value(task.get("id"), "task.id")
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", task_id):
                    raise ContractError("Agent task identifier is not a safe opaque identifier")
                matches[task_id] = task
    if len(matches) != 1:
        raise ContractError(
            f"Expected one task linked to this PR, observed {len(matches)}; "
            "inspect the task ledger or repeat read-only observation later"
        )
    task_id = next(iter(matches))
    task = object_value(api.request("GET", f"{prefix}/{task_id}"), "agent task detail")
    if task.get("id") != task_id or not task_has_pull(task, pull_id):
        raise ContractError("Task detail and pull request identities disagree")
    sessions = [
        object_value(item, "agent session")
        for item in array_value(task.get("sessions"), "task.sessions")
    ]
    count = task.get("session_count")
    if type(count) is not int or count != len(sessions):
        raise ContractError("Task response does not contain its complete session evidence")
    for session in sessions:
        if session.get("task_id") != task_id:
            raise ContractError("Session belongs to a different task")
        if not string_value(session.get("id"), "session.id"):
            raise ContractError("Agent session identifier is empty")
    return task, max(sessions, key=session_created_at) if sessions else None
