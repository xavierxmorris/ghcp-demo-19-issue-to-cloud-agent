"""Owner-approved issue intake, identity separation, and at-most-once attempts."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import asdict, dataclass, field

from .contracts import (
    ASSIGNED_LABEL, BOT_LOGINS, HARNESS_WORKFLOWS, QUEUE_LABEL, SOURCE_SHA256,
    START_LABEL, TITLE, ContractError, Json, array_value, assigned_to_copilot,
    assignment_payload, check_source, commit_sha, issue_payload, labels, normalize_body,
    object_value, parse_body, positive_integer, repository_name, string_value,
)
from .github_api import Api, ApiError, paginated


@dataclass
class Evidence:
    mode: str
    repository: str
    state: str = "not-started"
    source_commit: str | None = None
    source_commit_is_fixture: bool = False
    controller_commit: str | None = None
    source_sha256: str = SOURCE_SHA256
    issue_number: int | None = None
    issue_url: str | None = None
    workflow_run_url: str | None = None
    assignment_attempted: bool = False
    assignment_verified: bool = False
    agent_execution_observed: bool = False
    selected_pipeline_definitions: int = 1
    migrated_pipeline_definitions: int = 0
    mutations: list[str] = field(default_factory=list)
    pull_requests: list[dict[str, Json]] = field(default_factory=list)
    error: str | None = None

    def json(self) -> dict[str, Json]:
        return asdict(self)


def root(repository: str) -> str:
    return f"/repos/{repository_name(repository)}"


def read_issue(api: Api, repository: str, number: int) -> dict[str, Json]:
    positive_integer(number, "issue number")
    issue = object_value(api.request("GET", f"{root(repository)}/issues/{number}"), "issue")
    if issue.get("number") != number or issue.get("repository_url") != "https://api.github.com" + root(repository):
        raise ContractError("Issue identity does not match the requested repository and number")
    return issue


def validate_issue(issue: dict[str, Json], repository: str) -> str:
    if "pull_request" in issue:
        raise ContractError("A pull request cannot be used as an intake issue")
    author = object_value(issue.get("user"), "issue.user")
    if author.get("login") != repository.split("/")[0] or author.get("type") != "User":
        raise ContractError("This personal-repository proof accepts only requests from the repository owner")
    if issue.get("state") != "open":
        raise ContractError("Issue is not open")
    if issue.get("title") != TITLE:
        raise ContractError("Issue title does not match the synthetic request")
    if QUEUE_LABEL not in labels(issue):
        raise ContractError("The cloud-agent-request label is required")
    return parse_body(string_value(issue.get("body"), "issue.body"))


def source_preflight(api: Api, repository: str, source_commit: str) -> None:
    prefix = root(repository)
    commit_sha(source_commit)
    metadata = object_value(api.request("GET", prefix), "repository")
    owner = object_value(metadata.get("owner"), "repository.owner")
    if metadata.get("full_name") != repository or owner.get("type") != "User":
        raise ContractError("Target must be the exact, personally owned demo repository")
    if metadata.get("archived") is not False or metadata.get("disabled") is not False:
        raise ContractError("Repository is archived, disabled, or has incomplete metadata")
    if metadata.get("default_branch") != "main":
        raise ContractError("This proof requires the main default branch")
    check_head(api, repository, source_commit)
    tree = object_value(api.request("GET", f"{prefix}/git/trees/{source_commit}?recursive=1"), "tree")
    if tree.get("truncated") is not False:
        raise ContractError("Repository tree is truncated or its completeness is unknown")
    entries = [object_value(item, "tree entry") for item in array_value(tree.get("tree"), "tree.tree")]
    paths = [string_value(item.get("path"), "tree.path") for item in entries]
    pipelines = [path for path in paths if path.rsplit("/", 1)[-1] == "Jenkinsfile" or path.endswith(".Jenkinsfile")]
    if pipelines != ["Jenkinsfile"]:
        raise ContractError("Exactly one root Jenkinsfile is required; ambiguous sources need manual review")
    workflows = {path for path in paths if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))}
    if workflows != HARNESS_WORKFLOWS:
        raise ContractError("Only the three explicit demo-harness workflows are permitted")
    if any(path.startswith("drafts/") and path.endswith((".draft", "review.md")) for path in paths):
        raise ContractError("A migration proposal already exists on main; do not start duplicate conversion")
    source_entry = next(item for item in entries if item["path"] == "Jenkinsfile")
    if source_entry.get("type") != "blob" or source_entry.get("mode") != "100644":
        raise ContractError("Jenkinsfile must be a regular, non-executable Git blob")
    content = object_value(api.request("GET", f"{prefix}/contents/Jenkinsfile?ref={source_commit}"), "Jenkinsfile")
    if content.get("type") != "file" or content.get("encoding") != "base64":
        raise ContractError("Jenkinsfile is not an inline base64 file response")
    size = positive_integer(content.get("size"), "Jenkinsfile.size")
    if size > 4096:
        raise ContractError("Jenkinsfile exceeds 4 KiB")
    encoded = string_value(content.get("content"), "Jenkinsfile.content")
    try:
        raw = base64.b64decode(encoded.replace("\n", ""), validate=True)
    except (ValueError, binascii.Error):
        raise ContractError("Jenkinsfile response has invalid base64 content") from None
    if len(raw) != size:
        raise ContractError("Jenkinsfile content size is inconsistent")
    check_source(raw)


def check_head(api: Api, repository: str, source_commit: str) -> None:
    ref = object_value(api.request("GET", f"{root(repository)}/git/ref/heads/main"), "main ref")
    identity = object_value(ref.get("object"), "main ref.object")
    if identity.get("type") != "commit" or identity.get("sha") != source_commit:
        raise ContractError("Source revision is stale: main no longer equals the requested commit")


def matching_requests(api: Api, repository: str, source_commit: str) -> list[dict[str, Json]]:
    matches = []
    for item in paginated(api, f"{root(repository)}/issues?state=all"):
        issue = object_value(item, "issue ledger entry")
        if "pull_request" in issue or issue.get("title") != TITLE:
            continue
        author = object_value(issue.get("user"), "ledger issue.user")
        if author.get("login") != repository.split("/")[0]:
            continue
        body = string_value(issue.get("body"), "ledger issue.body")
        if parse_body(body) == source_commit:
            matches.append(issue)
    return matches


def submit_request(api: Api, repository: str, source_commit: str, evidence: Evidence) -> None:
    actor = object_value(api.request("GET", "/user"), "authenticated user")
    if actor.get("login") != repository.split("/")[0]:
        raise ContractError("Sign in as the owner of this personal demo repository before raising a request")
    enabled = object_value(api.request(
        "GET", f"{root(repository)}/actions/variables/ISSUE_AGENT_ENABLED",
    ), "enable variable")
    if enabled.get("value") != "true":
        raise ContractError("Configure the user-token secret and enable ISSUE_AGENT_ENABLED before live intake")
    source_preflight(api, repository, source_commit)
    matches = matching_requests(api, repository, source_commit)
    if matches:
        issue = min(matches, key=lambda item: positive_integer(item.get("number"), "issue.number"))
        evidence.state = "existing-request"
    else:
        evidence.state = "issue-creation-uncertain"
        issue = object_value(api.request(
            "POST", f"{root(repository)}/issues", issue_payload(source_commit),
        ), "created issue")
        evidence.mutations.append("issue-created-unassigned")
        evidence.state = "issue-created"
    evidence.source_commit = source_commit
    evidence.issue_number = positive_integer(issue.get("number"), "issue.number")
    evidence.issue_url = f"https://github.com/{repository}/issues/{evidence.issue_number}"
    evidence.assignment_verified = assigned_to_copilot(issue)


def confirm_available(api: Api, repository: str) -> None:
    owner, name = repository.split("/")
    result = object_value(api.request("POST", "/graphql", {
        "query": (
            "query($owner:String!,$name:String!){repository(owner:$owner,name:$name)"
            "{suggestedActors(capabilities:[CAN_BE_ASSIGNED],first:100)"
            "{nodes{login} pageInfo{hasNextPage}}}}"
        ),
        "variables": {"owner": owner, "name": name},
    }), "Copilot availability")
    if result.get("errors"):
        raise ApiError("Copilot availability query failed; verify user-token permissions and repository access")
    data = object_value(result.get("data"), "availability.data")
    target = object_value(data.get("repository"), "availability.repository")
    actors = object_value(target.get("suggestedActors"), "suggestedActors")
    nodes = array_value(actors.get("nodes"), "suggestedActors.nodes")
    if not any(object_value(node, "actor").get("login") in BOT_LOGINS for node in nodes):
        raise ContractError("Copilot is not an available assignee for this user/repository; check plan and policy")


def start_from_event(
    event: dict[str, Json],
    repository: str,
    control: Api,
    user: Api,
    evidence: Evidence,
    *,
    enabled: bool,
    event_name: str,
    workflow_ref: str,
    workflow_commit: str,
) -> None:
    if not enabled:
        raise ContractError("ISSUE_AGENT_ENABLED must be true; live assignment is disabled")
    if event_name != "issues" or event.get("action") != "opened":
        raise ContractError("Only the original issues:opened event can start work")
    if workflow_ref != "refs/heads/main":
        raise ContractError("The issue trigger must execute trusted main-branch code")
    event_repo = object_value(event.get("repository"), "event.repository")
    if event_repo.get("full_name") != repository:
        raise ContractError("Event repository does not match GITHUB_REPOSITORY")
    original = object_value(event.get("issue"), "event.issue")
    number = positive_integer(original.get("number"), "event.issue.number")
    source_commit = validate_issue(original, repository)
    if commit_sha(workflow_commit) != source_commit:
        raise ContractError("Requested source must match the trusted issue-event workflow commit")
    evidence.controller_commit = workflow_commit
    evidence.issue_number = number
    evidence.issue_url = f"https://github.com/{repository}/issues/{number}"
    evidence.source_commit = source_commit
    issue = read_issue(control, repository, number)
    if validate_issue(issue, repository) != source_commit:
        raise ContractError("Issue source commit changed after creation")
    if issue.get("title") != original.get("title") or normalize_body(
        string_value(issue.get("body"), "issue.body")
    ) != normalize_body(string_value(original.get("body"), "event.issue.body")):
        raise ContractError("Issue title/body was edited after creation")
    if assigned_to_copilot(issue):
        evidence.state = "already-assigned"
        evidence.assignment_verified = True
        return
    if START_LABEL in labels(issue) or ASSIGNED_LABEL in labels(issue):
        raise ContractError("A durable start marker exists; reconcile the previous attempt instead of retrying")
    if issue.get("comments") != 0:
        raise ContractError("Unexpected issue comments exist before assignment; inspect before starting an agent")
    if array_value(issue.get("assignees"), "issue.assignees"):
        raise ContractError("Issue has another assignee; manual review required")
    source_preflight(control, repository, source_commit)
    matching = matching_requests(control, repository, source_commit)
    numbers = [positive_integer(item.get("number"), "ledger issue number") for item in matching]
    if number not in numbers or min(numbers) != number:
        raise ContractError("Another request already owns this source revision; reuse the earliest issue")
    for candidate in matching:
        if candidate.get("number") != number and (
            START_LABEL in labels(candidate) or assigned_to_copilot(candidate)
        ):
            raise ContractError("Another issue already started work for this source revision")
    confirm_available(user, repository)
    latest = read_issue(control, repository, number)
    if latest != issue:
        raise ContractError("Issue changed during preflight; inspect and rerun only if still authorized")
    check_head(control, repository, source_commit)
    evidence.state = "recording-start-intent"
    control.request("POST", f"{root(repository)}/issues/{number}/labels", {"labels": [START_LABEL]})
    evidence.mutations.append("durable-start-marker")
    evidence.state = "assignment-uncertain"
    evidence.assignment_attempted = True
    result = object_value(user.request(
        "POST", f"{root(repository)}/issues/{number}/assignees",
        assignment_payload(repository, source_commit),
    ), "assignment response")
    if result.get("number") != number or not assigned_to_copilot(result):
        raise ApiError("Assignment response did not confirm Copilot. Keep the start marker and inspect the task.")
    evidence.assignment_verified = True
    evidence.mutations.append("copilot-assignment")
    evidence.state = "assignment-verified"
    control.request("POST", f"{root(repository)}/issues/{number}/labels", {"labels": [ASSIGNED_LABEL]})
    evidence.mutations.append("assigned-label")


def safe_run_url(repository: str, run_id: str) -> str:
    if not re.fullmatch(r"[1-9][0-9]*", run_id):
        raise ContractError("GITHUB_RUN_ID must be a positive numeric identifier")
    return f"https://github.com/{repository_name(repository)}/actions/runs/{run_id}"
