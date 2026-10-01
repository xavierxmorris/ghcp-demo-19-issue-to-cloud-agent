"""Execute an offline, synthetic rehearsal of enterprise admission and trust lanes."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import MappingProxyType

from .contracts import (
    ContractError, Json, array_value, commit_sha, object_value, positive_integer,
    repository_name, string_value,
)
from .enterprise_ledger import open_queue
from .evidence import owned_output_path, reserve_output, seal_bundle, write_json

LANE_IDS = ("agent", "pr-validation", "trusted-build", "release-nonprod", "release-prod")
LANE_CREDENTIALS = {
    "agent": "copilot-repository-branch",
    "pr-validation": "contents-read",
    "trusted-build": "artifact-publish",
    "release-nonprod": "target-scoped-oidc",
    "release-prod": "target-scoped-oidc",
}
REQUEST_KEYS = {
    "request_id", "repository", "repository_id", "pipeline_path", "source_revision",
    "requester", "owner", "reviewer", "authorized", "import_ready", "ai_processing_allowed",
    "pipeline_shape", "catalog_match", "agent_runner_group", "ci_approval", "pr_workflows",
}
REASON_DETAILS = {
    "LOCAL_RESERVATION_CREATED": "Eligible under the synthetic policy; reserved locally, not dispatched.",
    "WORK_ALREADY_RESERVED": "Reuse the original reservation without consuming another queue slot.",
    "WORK_INTENT_CHANGED": "The same source now has different routing or authority input; reconcile its original reservation.",
    "REQUEST_ID_CHANGED": "The same request ID now has different input; do not overwrite its recorded intent.",
    "PIPELINE_ALREADY_QUEUED": "Another source revision of this pipeline is queued; reconcile it first.",
    "STOP_SWITCH": "The operator stopped new admissions; existing work remains intact.",
    "RUN_SUBMISSION_LIMIT": "This invocation reached its local admission allowance.",
    "QUEUE_CAPACITY": "The local queue is full; defer rather than overrun its configured capacity.",
    "REQUEST_NOT_AUTHORIZED": "The fixture does not assert owner authorization; discovery is not consent.",
    "OWNERSHIP_UNRESOLVED": "An accountable owner and independent reviewer must be identified.",
    "INDEPENDENT_REVIEW_REQUIRED": "The requester cannot stand in for the independent reviewer.",
    "IMPORT_NOT_READY": "Repository arrival is not proof that the approved import handoff is complete.",
    "AI_PROCESSING_NOT_APPROVED": "The fixture does not permit AI processing of this input.",
    "AGENT_RUNNER_OVERRIDE": "The request tries to move agent work outside the centrally selected sandbox.",
    "PR_RUNNER_OUTSIDE_VALIDATION_LANE": "Untrusted PR work must not select a build or release runner group.",
    "AUTO_CI_BOUNDARY_UNPROVEN": "Automatic CI was requested without a complete low-privilege boundary.",
    "CI_BOUNDARY_REVIEW_REQUIRED": "Keeping an approval button does not make an unsafe CI boundary acceptable.",
    "CATALOG_EVIDENCE_MISSING": "The target workflow contract is unknown; do not invent an approved mapping.",
    "PIPELINE_BEHAVIOR_UNRESOLVED": "Opaque pipeline behavior needs an engineer, not an assumed conversion.",
    "CATALOG_NEAR_MATCH": "A near match needs a workflow owner's decision before admission.",
    "SYNTHETIC_CONTRACT_MATCH": "The fixture declares an exact shared-contract match; prefer reuse.",
    "BOUNDED_DIRECT_CASE": "The tiny known source has no declared shared-contract match; plan direct conversion.",
}


def exact_keys(data: dict[str, Json], expected: set[str], context: str) -> None:
    if set(data) != expected:
        raise ContractError(
            f"{context}: missing {sorted(expected - set(data))}; unknown {sorted(set(data) - expected)}",
        )


def boolean(value: Json, context: str) -> bool:
    if type(value) is not bool:
        raise ContractError(f"{context} must be a boolean")
    return value


def identifier(value: Json, context: str, *, empty: bool = False) -> str:
    result = string_value(value, context)
    if result == "" and empty:
        return result
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", result):
        raise ContractError(f"{context} must be a bounded synthetic identifier")
    return result


def choice(value: Json, choices: set[str], context: str) -> str:
    result = string_value(value, context)
    if result not in choices:
        raise ContractError(f"{context} must be one of {sorted(choices)}")
    return result


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
    ).hexdigest()


def read_fixture(path: Path) -> dict[str, Json]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 128 * 1024:
        raise ContractError("Enterprise fixture must be a regular JSON file no larger than 128 KiB")

    def unique_pairs(pairs: list[tuple[str, Json]]) -> dict[str, Json]:
        result: dict[str, Json] = {}
        for key, value in pairs:
            if key in result:
                raise ContractError("Duplicate JSON keys are not permitted in enterprise fixtures")
            result[key] = value
        return result

    def invalid_number(value: str) -> Json:
        raise ContractError("Non-finite JSON numbers are not permitted in enterprise fixtures")

    try:
        return object_value(
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs, parse_constant=invalid_number),
            "enterprise fixture",
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ContractError("Enterprise fixture is not valid UTF-8 JSON") from None


@dataclass(frozen=True)
class Lane:
    runner_group: str
    isolation_boundary: str
    credential: str


@dataclass(frozen=True)
class Policy:
    name: str
    lanes: Mapping[str, Lane]
    max_queued: int
    max_new_per_run: int
    fingerprint: str


def parse_policy(data: dict[str, Json]) -> Policy:
    exact_keys(data, {
        "schema_version", "data_classification", "policy_id",
        "repository_runner_overrides", "runner_lifetime", "lanes", "limits",
    }, "policy")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ContractError("Unsupported enterprise policy version")
    if data["data_classification"] != "synthetic":
        raise ContractError("Enterprise mode accepts synthetic fixtures only, not customer policy")
    if boolean(data["repository_runner_overrides"], "runner overrides"):
        raise ContractError("The closed demo policy requires centrally fixed agent runner placement")
    if data["runner_lifetime"] != "clean-ephemeral":
        raise ContractError("The demo profile requires clean, single-use execution environments")
    name = identifier(data["policy_id"], "policy_id")
    values = object_value(data["lanes"], "lanes")
    exact_keys(values, set(LANE_IDS), "lanes")
    lanes: dict[str, Lane] = {}
    for lane_id in LANE_IDS:
        lane = object_value(values[lane_id], lane_id)
        exact_keys(lane, {"runner_group", "isolation_boundary", "credential"}, lane_id)
        group = identifier(lane["runner_group"], "runner_group")
        boundary = identifier(lane["isolation_boundary"], "isolation_boundary")
        if lane["credential"] != LANE_CREDENTIALS[lane_id]:
            raise ContractError(f"{lane_id} has an incompatible credential boundary")
        lanes[lane_id] = Lane(group, boundary, LANE_CREDENTIALS[lane_id])
    if len({lane.runner_group for lane in lanes.values()}) != len(LANE_IDS) or len({
        lane.isolation_boundary for lane in lanes.values()
    }) != len(LANE_IDS):
        raise ContractError("Trust lanes must not share a runner group or isolation boundary")
    limits = object_value(data["limits"], "limits")
    exact_keys(limits, {"max_queued", "max_new_per_run"}, "limits")
    queued = positive_integer(limits["max_queued"], "max_queued")
    new = positive_integer(limits["max_new_per_run"], "max_new_per_run")
    if max(queued, new) > 50:
        raise ContractError("Synthetic queue limits must not exceed 50 work items")
    package = Path(__file__).resolve().parent
    engine: dict[str, Json] = {
        filename: (package / filename).read_text(encoding="utf-8")
        for filename in ("enterprise.py", "enterprise_ledger.py", "contracts.py")
    }
    fingerprint = canonical_hash({"policy": data, "engine": engine})
    return Policy(name, MappingProxyType(lanes), queued, new, fingerprint)


def parse_requests(data: dict[str, Json]) -> list[dict[str, Json]]:
    exact_keys(data, {"schema_version", "data_classification", "identifiers_are_fixtures", "requests"}, "requests")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ContractError("Unsupported enterprise request version")
    if data["data_classification"] != "synthetic" or data["identifiers_are_fixtures"] is not True:
        raise ContractError("Enterprise requests must explicitly identify their synthetic data and identifiers")
    records = array_value(data["requests"], "requests")
    if not 1 <= len(records) <= 100:
        raise ContractError("An enterprise rehearsal requires 1-100 requests")
    result = []
    for value in records:
        request = object_value(value, "request")
        exact_keys(request, REQUEST_KEYS, "request")
        for field in ("request_id", "requester", "agent_runner_group"):
            identifier(request[field], field)
        for field in ("owner", "reviewer"):
            identifier(request[field], field, empty=True)
        repository_name(string_value(request["repository"], "repository"))
        positive_integer(request["repository_id"], "repository_id")
        commit_sha(string_value(request["source_revision"], "source_revision"))
        path = string_value(request["pipeline_path"], "pipeline_path")
        if len(path) > 200 or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", path) or any(
            part in {".", ".."} for part in path.split("/")
        ) or PurePosixPath(path).is_absolute():
            raise ContractError("Pipeline path must be a bounded repository-relative path")
        for field in ("authorized", "import_ready", "ai_processing_allowed"):
            boolean(request[field], field)
        choice(request["pipeline_shape"], {"hello-world", "opaque"}, "pipeline_shape")
        choice(request["catalog_match"], {"exact", "near", "none", "unknown"}, "catalog_match")
        choice(request["ci_approval"], {"required", "automatic"}, "ci_approval")
        surface = object_value(request["pr_workflows"], "pr_workflows")
        exact_keys(surface, {
            "runner_group", "inventory_complete", "boundary_reviewed", "read_token_only",
            "secrets_available", "production_network", "privileged_follow_on",
        }, "pr_workflows")
        identifier(surface["runner_group"], "PR runner group")
        for field in set(surface) - {"runner_group"}:
            boolean(surface[field], f"pr_workflows.{field}")
        result.append(request)
    return result


def policy_decision(request: dict[str, Json], policy: Policy) -> tuple[str, str, str]:
    if request["authorized"] is not True:
        return "blocked", "REQUEST_NOT_AUTHORIZED", "none"
    if not request["owner"] or not request["reviewer"]:
        return "blocked", "OWNERSHIP_UNRESOLVED", "none"
    if request["requester"] == request["reviewer"]:
        return "blocked", "INDEPENDENT_REVIEW_REQUIRED", "none"
    if request["import_ready"] is not True:
        return "blocked", "IMPORT_NOT_READY", "none"
    if request["ai_processing_allowed"] is not True:
        return "blocked", "AI_PROCESSING_NOT_APPROVED", "none"
    if request["agent_runner_group"] != policy.lanes["agent"].runner_group:
        return "blocked", "AGENT_RUNNER_OVERRIDE", "none"
    surface = object_value(request["pr_workflows"], "pr_workflows")
    if surface["runner_group"] != policy.lanes["pr-validation"].runner_group:
        return "blocked", "PR_RUNNER_OUTSIDE_VALIDATION_LANE", "none"
    boundary_unproven = (
        not surface["inventory_complete"] or not surface["boundary_reviewed"] or
        not surface["read_token_only"] or surface["secrets_available"] or
        surface["production_network"] or surface["privileged_follow_on"]
    )
    if boundary_unproven:
        if request["ci_approval"] == "automatic":
            return "blocked", "AUTO_CI_BOUNDARY_UNPROVEN", "none"
        return "manual-review", "CI_BOUNDARY_REVIEW_REQUIRED", "manual-review"
    if request["catalog_match"] == "unknown":
        return "blocked", "CATALOG_EVIDENCE_MISSING", "none"
    if request["pipeline_shape"] != "hello-world":
        return "manual-review", "PIPELINE_BEHAVIOR_UNRESOLVED", "manual-review"
    if request["catalog_match"] == "near":
        return "manual-review", "CATALOG_NEAR_MATCH", "manual-review"
    if request["catalog_match"] == "exact":
        return "candidate", "SYNTHETIC_CONTRACT_MATCH", "shared-workflow-candidate"
    return "candidate", "BOUNDED_DIRECT_CASE", "direct-conversion-candidate"


def planned_lanes(policy: Policy, ci_approval: str) -> list[dict[str, Json]]:
    gates = {
        "agent": "validated-intent-and-supported-task-start-identity",
        "pr-validation": "human-workflow-approval" if ci_approval == "required" else "reviewed-unprivileged-CI-boundary",
        "trusted-build": "independent-review-and-protected-source",
        "release-nonprod": "identified-artifact-and-nonprod-authorization",
        "release-prod": "independent-production-approval-and-scoped-identity",
    }
    return [
        {
            "lane": name, "runner_group": policy.lanes[name].runner_group,
            "isolation_boundary": policy.lanes[name].isolation_boundary,
            "credential": policy.lanes[name].credential,
            "required_gate": gates[name], "execution": "not-run",
        }
        for name in LANE_IDS
    ]


def rehearse(
    policy: Policy, requests: list[dict[str, Json]], ledger: Path,
    *, stop_new_work: bool = False, max_new: int | None = None,
) -> dict[str, Json]:
    allowance = policy.max_new_per_run if max_new is None else positive_integer(max_new, "max_new")
    if allowance > policy.max_new_per_run:
        raise ContractError("The command may reduce but not raise the policy's per-run submission limit")
    decisions: list[Json] = []
    counts: dict[str, Json] = {name: 0 for name in ("admitted", "duplicate", "manual-review", "blocked", "deferred")}
    admitted = 0
    with open_queue(ledger, policy.fingerprint) as queue:
        for request in requests:
            status, reason, route = policy_decision(request, policy)
            key = canonical_hash({
                "repository_id": request["repository_id"], "pipeline_path": request["pipeline_path"],
                "source_revision": request["source_revision"], "policy": policy.fingerprint,
            })
            reservation = queue.decide(
                request_id=string_value(request["request_id"], "request_id"),
                input_hash=canonical_hash(request), work_key=key, route=route,
                intent_hash=canonical_hash({
                    name: value for name, value in request.items() if name not in {"request_id", "repository"}
                }),
                pipeline_key=canonical_hash({
                    "repository_id": request["repository_id"], "pipeline_path": request["pipeline_path"],
                }),
                policy_status=status, policy_reason=reason, max_queued=policy.max_queued,
                remaining_admissions=allowance - admitted, stop_new_work=stop_new_work,
            )
            if reservation.status == "admitted":
                admitted += 1
            count = counts[reservation.status]
            if type(count) is not int:
                raise ContractError("Invalid internal decision counter")
            counts[reservation.status] = count + 1
            decisions.append({
                "request_id": request["request_id"], "repository": request["repository"],
                "pipeline_path": request["pipeline_path"], "source_revision": request["source_revision"],
                "status": reservation.status, "reason": reservation.reason, "route": route,
                "why": REASON_DETAILS[reservation.reason],
                "policy_reason": reason, "policy_why": REASON_DETAILS[reason],
                "canonical_request_id": reservation.canonical_request_id, "work_key": key,
                "planned_lanes": planned_lanes(policy, string_value(request["ci_approval"], "ci_approval"))
                if reservation.status in {"admitted", "duplicate"} else [],
            })
        snapshot = queue.snapshot()
    return {
        "schema_version": 1, "mode": "synthetic-enterprise-rehearsal", "status": "completed-locally",
        "policy_id": policy.name, "policy_engine_fingerprint": policy.fingerprint,
        "requests_fingerprint": canonical_hash(requests),
        "identifiers_are_fixtures": True, "platform_controls_verified": False,
        "live_api_calls": 0, "cloud_tasks_started": 0, "workflows_executed": 0,
        "accepted_migrations": 0, "request_count": len(requests),
        "pipeline_definition_count": len({(item["repository_id"], item["pipeline_path"]) for item in requests}),
        "stop_new_work": stop_new_work, "max_new_this_run": allowance, "max_queued": policy.max_queued,
        "new_local_work_items": admitted, "queue_depth": len(snapshot),
        "decision_counts": counts, "decisions": decisions, "queue_snapshot": snapshot,
    }


def write_report(bundle: Path, report: dict[str, Json]) -> None:
    write_json(bundle / "enterprise-report.json", report)
    lines = [
        "# Enterprise design rehearsal", "",
        "**Synthetic metadata, local SQLite reservations, no platform execution.**", "",
        f"Status: {report['status']}", "",
        "Runner groups, network isolation, identities and approvals below are fixture assertions,",
        "not verified GitHub or bank configuration. No agent, build or release job ran.", "",
    ]
    if "error" in report:
        lines.extend(["## Error", "", string_value(report["error"], "error"), ""])
    else:
        lines.extend([
            f"New local work items: {report['new_local_work_items']}; queue depth: {report['queue_depth']}.",
            f"Requests: {report['request_count']}; pipeline definitions: {report['pipeline_definition_count']}.",
            "Accepted migrations: 0. Submission limits count local work items, not money or AI credits.", "",
            "| Request | Decision | Why | Route |",
            "| --- | --- | --- | --- |",
        ])
        for item in array_value(report["decisions"], "decisions"):
            decision = object_value(item, "decision")
            lines.append(
                f"| {decision['request_id']} | {decision['status']} | {decision['why']} | {decision['route']} |",
            )
        lines.extend(["", "## Planned execution lanes", ""])
        for item in array_value(report["decisions"], "decisions"):
            decision = object_value(item, "decision")
            if decision["status"] != "admitted":
                continue
            lines.extend([f"### {decision['request_id']}", ""])
            for value in array_value(decision["planned_lanes"], "planned_lanes"):
                lane = object_value(value, "lane")
                lines.append(
                    f"- {lane['lane']}: {lane['runner_group']} / {lane['isolation_boundary']}; "
                    f"gate: {lane['required_gate']}; **not run**."
                )
            lines.append("")
        lines.extend([
            "The ledger is mutable local state outside this immutable bundle. Reuse it explicitly",
            "to demonstrate duplicate protection; use a new output directory for every observation.", "",
        ])
    (bundle / "enterprise-report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    seal_bundle(bundle)


def run_enterprise(
    root: Path, output: Path, ledger: Path | None = None,
    *, stop_new_work: bool = False, max_new: int | None = None,
) -> int:
    bundle: Path | None = None
    state: Path | None = None
    try:
        bundle = reserve_output(root, output)
        state = owned_output_path(
            root, ledger if ledger is not None else bundle.parent / (bundle.name + ".sqlite3"),
        )
        if state == bundle or state.is_relative_to(bundle):
            raise ContractError("Keep mutable ledger state outside the immutable evidence bundle")
        if ledger is None and state.exists():
            raise ContractError("Default ledger already exists; pass --ledger explicitly to reuse it")
        policy = parse_policy(read_fixture(root / "fixtures" / "enterprise" / "policy.json"))
        requests = parse_requests(read_fixture(root / "fixtures" / "enterprise" / "requests.json"))
        report = rehearse(policy, requests, state, stop_new_work=stop_new_work, max_new=max_new)
        report["ledger"] = str(state.relative_to(root.resolve()))
        report["recorded_at"] = datetime.now(timezone.utc).isoformat()
        write_report(bundle, report)
        print(json.dumps({
            "state": report["status"], "mode": report["mode"], "evidence": str(bundle),
            "ledger": str(state), "decision_counts": report["decision_counts"],
            "new_local_work_items": report["new_local_work_items"], "live_api_calls": 0,
        }))
        return 0
    except (ContractError, OSError, sqlite3.Error) as error:
        message = str(error) or f"{type(error).__name__} did not provide a diagnostic message"
        if bundle is not None and not (bundle / "enterprise-report.json").exists():
            write_report(bundle, {
                "schema_version": 1, "mode": "synthetic-enterprise-rehearsal", "status": "failed",
                "error": message, "live_api_calls": 0,
                "ledger": str(state) if state is not None else None,
                "local_state": "not inferred after failure; inspect the ledger before replay",
            })
        print(f"ERROR: {message}", file=sys.stderr)
        return 2
