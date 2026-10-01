"""Bounded GitHub clients; credentials never enter arguments or evidence."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .contracts import ContractError, Json, array_value

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


def check_path(path: str) -> None:
    if not path.startswith("/repos/") and path != "/graphql" and path != "/user":
        raise ContractError("API path is outside the demo's GitHub endpoints")
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
        check_path(path)
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
        check_path(path)
        arguments = [
            "api", "--hostname", "github.com", "--method", method,
            "-H", "Accept: application/vnd.github+json",
            "-H", f"X-GitHub-Api-Version: {API_VERSION}", path,
        ]
        if body is not None:
            arguments.extend(["--input", "-"])
        return gh_json(arguments, body)


def paginated(api: Api, path: str) -> list[Json]:
    result: list[Json] = []
    separator = "&" if "?" in path else "?"
    for page in range(1, 11):
        items = array_value(api.request("GET", f"{path}{separator}per_page=100&page={page}"), path)
        result.extend(items)
        if len(items) < 100:
            return result
    raise ContractError("Pagination limit reached; refusing to act on an incomplete issue ledger")
