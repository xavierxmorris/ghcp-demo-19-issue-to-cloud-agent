"""Preview offline, raise one unassigned issue, or process its opened event."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from .contracts import (
    BOT_LOGINS, ContractError, Json, assigned_to_copilot, commit_sha,
    object_value, parse_body, positive_integer, repository_name, string_value,
)
from .evidence import reserve_output, write_bundle
from .github_api import ApiError, GhApi, RestApi, gh_json, paginated, redact
from .service import Evidence, read_issue, root, safe_run_url, start_from_event, submit_request

ROOT = Path(__file__).resolve().parents[1]


def git_output(*arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *arguments],
            capture_output=True, text=True, encoding="utf-8", timeout=20, check=False,
        )
    except FileNotFoundError:
        raise ContractError("Git is required for the live issue-creation command") from None
    except subprocess.TimeoutExpired:
        raise ContractError("Git timed out before issue creation") from None
    if result.returncode:
        raise ContractError(f"Git failed ({result.returncode}): {redact(result.stderr.strip())}")
    return result.stdout.strip()


def local_live_commit(repository: str) -> str:
    if git_output("status", "--porcelain"):
        raise ContractError("Live intake requires a clean checkout; preserve and commit intended changes first")
    origin = git_output("remote", "get-url", "origin")
    permitted = {
        f"https://github.com/{repository}", f"https://github.com/{repository}.git",
        f"git@github.com:{repository}.git",
    }
    if origin not in permitted:
        raise ContractError("The explicit repository must match this clone's credential-free github.com origin")
    return commit_sha(git_output("rev-parse", "HEAD"))


def observe(repository: str, number: int, evidence: Evidence) -> None:
    api = GhApi()
    issue = read_issue(api, repository, number)
    evidence.issue_number = number
    evidence.issue_url = f"https://github.com/{repository}/issues/{number}"
    evidence.source_commit = parse_body(string_value(issue.get("body"), "issue.body"))
    evidence.assignment_verified = assigned_to_copilot(issue)
    evidence.state = "assigned-not-yet-observed" if evidence.assignment_verified else "not-assigned"
    seen: set[int] = set()
    for item in paginated(api, f"{root(repository)}/issues/{number}/timeline"):
        event = object_value(item, "timeline event")
        if event.get("event") != "cross-referenced":
            continue
        source = object_value(event.get("source"), "cross-reference.source")
        linked = object_value(source.get("issue"), "cross-reference.issue")
        if "pull_request" not in linked or linked.get("repository_url") != "https://api.github.com" + root(repository):
            continue
        author = object_value(linked.get("user"), "linked issue.user")
        if author.get("login") not in BOT_LOGINS:
            continue
        pr_number = positive_integer(linked.get("number"), "linked PR number")
        if pr_number in seen:
            continue
        seen.add(pr_number)
        pr = object_value(api.request("GET", f"{root(repository)}/pulls/{pr_number}"), "pull request")
        session = object_value(gh_json([
            "agent-task", "view", "--repo", repository, str(pr_number),
            "--json", "id,state,createdAt,updatedAt,completedAt,pullRequestUrl",
        ]), "agent session")
        expected_url = f"https://github.com/{repository}/pull/{pr_number}"
        if pr.get("html_url") != expected_url or session.get("pullRequestUrl") != expected_url:
            raise ContractError("Agent session and linked pull request identities disagree")
        state = string_value(session.get("state"), "session.state")
        session_id = string_value(session.get("id"), "session.id")
        if not session_id:
            raise ContractError("Agent session identifier is empty")
        evidence.pull_requests.append({
            "url": expected_url,
            "draft": pr.get("draft"),
            "merged": pr.get("merged"),
            "head_commit": object_value(pr.get("head"), "PR head").get("sha"),
            "session_id": session_id,
            "session_state": state,
            "session_created_at": session.get("createdAt"),
            "session_completed_at": session.get("completedAt"),
        })
        evidence.agent_execution_observed |= state.lower() in {
            "in_progress", "completed", "idle", "waiting_for_user",
        }
    if evidence.pull_requests:
        evidence.state = "agent-execution-observed" if evidence.agent_execution_observed else "linked-pr-observed"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("preview", "raise", "observe", "trigger"):
        command = commands.add_parser(name)
        command.add_argument("--out", type=Path, default=Path("out") / f"{name}-{uuid.uuid4().hex[:12]}")
        if name != "trigger":
            command.add_argument("--repository", required=name != "preview", default="demo-owner/hello-world")
        if name == "preview":
            command.add_argument("--source-commit", default="0" * 40)
        if name == "raise":
            command.add_argument("--accept-live-run", action="store_true")
        if name == "observe":
            command.add_argument("--issue", type=int, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    bundle: Path | None = None
    evidence: Evidence | None = None
    try:
        repository = repository_name(
            os.environ.get("GITHUB_REPOSITORY", "") if args.command == "trigger" else args.repository,
        )
        if args.command == "raise" and not args.accept_live_run:
            raise ContractError("Raising an issue starts paid cloud work: --accept-live-run is required")
        evidence = Evidence(mode=args.command, repository=repository)
        bundle = reserve_output(ROOT, args.out)
        if args.command == "preview":
            evidence.source_commit = commit_sha(args.source_commit)
            evidence.source_commit_is_fixture = args.source_commit == "0" * 40
            evidence.state = "offline-preview-no-mutations"
        elif args.command == "raise":
            source_commit = local_live_commit(repository)
            submit_request(GhApi(), repository, source_commit, evidence)
        elif args.command == "observe":
            positive_integer(args.issue, "issue number")
            observe(repository, args.issue, evidence)
        else:
            event_path = Path(os.environ.get("GITHUB_EVENT_PATH", ""))
            if not event_path.is_file() or event_path.stat().st_size > 1024 * 1024:
                raise ContractError("GITHUB_EVENT_PATH must be a regular JSON event file no larger than 1 MiB")
            event = object_value(json.loads(event_path.read_text(encoding="utf-8")), "event")
            evidence.workflow_run_url = safe_run_url(repository, os.environ.get("GITHUB_RUN_ID", ""))
            start_from_event(
                event, repository,
                RestApi(os.environ.get("GITHUB_TOKEN", "")),
                RestApi(os.environ.get("COPILOT_USER_TOKEN", "")),
                evidence,
                enabled=os.environ.get("ISSUE_AGENT_ENABLED") == "true",
                event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
                workflow_ref=os.environ.get("GITHUB_REF", ""),
                workflow_commit=os.environ.get("GITHUB_SHA", ""),
            )
        write_bundle(bundle, evidence)
        print(json.dumps({
            "state": evidence.state, "issue_url": evidence.issue_url,
            "evidence": str(bundle), "agent_execution_observed": evidence.agent_execution_observed,
        }))
        return 0
    except (ContractError, ApiError, OSError, json.JSONDecodeError) as error:
        message = redact(
            str(error), os.environ.get("GITHUB_TOKEN", ""), os.environ.get("COPILOT_USER_TOKEN", ""),
        )
        if evidence is not None:
            evidence.error = message
            if evidence.state not in {"assignment-uncertain", "assignment-verified", "issue-creation-uncertain"}:
                evidence.state = "blocked"
            if bundle is not None and not (bundle / "report.json").exists():
                write_bundle(bundle, evidence)
        print(f"ERROR: {message}", file=sys.stderr)
        return 2
