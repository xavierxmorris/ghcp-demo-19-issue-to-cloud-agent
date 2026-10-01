"""New, local, token-free evidence bundles with a final integrity manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .contracts import ContractError, Json, assignment_payload, issue_body
from .service import Evidence


def reserve_output(root: Path, output: Path) -> Path:
    base = root.resolve()
    requested = output if output.is_absolute() else base / output
    allowed = base / "out"
    if requested.is_symlink() or any(parent.is_symlink() for parent in requested.parents if parent != base):
        raise ContractError("Evidence output cannot traverse symbolic links")
    resolved = requested.resolve()
    if resolved == allowed or not resolved.is_relative_to(allowed):
        raise ContractError("Use a new bundle directory beneath this repository's out directory")
    if resolved.exists():
        raise ContractError("Output already exists; use a new bundle directory")
    resolved.mkdir(parents=True, exist_ok=False)
    return resolved


def write_json(path: Path, value: Json) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def write_bundle(directory: Path, evidence: Evidence) -> None:
    data = evidence.json()
    data["schema_version"] = 1
    data["recorded_at"] = datetime.now(timezone.utc).isoformat()
    data["model"] = "platform default; actual model not observed by this controller"
    write_json(directory / "report.json", data)
    lines = [
        "# Synthetic issue-to-agent evidence", "",
        f"- Mode: {evidence.mode}",
        f"- State: {evidence.state}",
        f"- Repository: {evidence.repository}",
        f"- Source commit: {evidence.source_commit or 'not established'}",
        f"- Source SHA-256: {evidence.source_sha256}",
        f"- Source commit is an offline placeholder: {evidence.source_commit_is_fixture}",
        f"- Issue: {evidence.issue_url or 'not created'}",
        f"- Workflow run: {evidence.workflow_run_url or 'not observed'}",
        f"- Assignment attempted: {evidence.assignment_attempted}",
        f"- Assignment verified: {evidence.assignment_verified}",
        f"- Agent execution observed: {evidence.agent_execution_observed}",
        "- Migrated pipeline definitions: 0 / 1 (no acceptance or cutover performed)",
        f"- Mutations: {', '.join(evidence.mutations) or 'none'}",
        "", "Assignment, execution, a pull request, validation, acceptance and cutover",
        "are separate facts. This bundle does not approve any of them.", "",
    ]
    if evidence.error:
        lines.extend(["## Failure", "", evidence.error, ""])
    if evidence.pull_requests:
        lines.extend(["## Linked pull requests", "", json.dumps(evidence.pull_requests, indent=2), ""])
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    if evidence.source_commit:
        (directory / "issue-body.md").write_text(
            issue_body(evidence.source_commit), encoding="utf-8", newline="\n",
        )
        write_json(
            directory / "assignment-request.json",
            assignment_payload(evidence.repository, evidence.source_commit),
        )
    files: dict[str, Json] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir()) if path.is_file()
    }
    write_json(directory / "bundle-manifest.json", {"schema_version": 1, "sha256": files})
