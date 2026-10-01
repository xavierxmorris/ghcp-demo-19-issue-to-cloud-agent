"""Offline repository and deliberately narrow proposal contract checks."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from issue_agent.contracts import (  # noqa: E402
    CONSENT, HARNESS_WORKFLOWS, PROPOSAL_FILES, ContractError, check_source,
    commit_sha, validate_draft, validate_review,
)

REQUIRED = (
    "README.md", "AGENTS.md", "RUN-SHEET.md", "WORKSHOP.md", "PROMPTS.md",
    "docs/ACCEPTANCE.md", "docs/ARCHITECTURE.md", "docs/LIVE-SETUP.md",
    "docs/SOURCE-CONTEXT.md", "docs/SOURCES.md", "iteration/README.md",
    ".github/ISSUE_TEMPLATE/hello-world.yml",
)


def validate_proposal(root: Path, required: bool = False) -> None:
    directory = root / "drafts"
    actual = {
        path.relative_to(root).as_posix()
        for path in directory.rglob("*") if path.is_file()
    } if directory.exists() else set()
    if not actual and not required:
        return
    if actual != PROPOSAL_FILES:
        raise ContractError("Proposal must contain exactly drafts/hello-world.yml.draft and drafts/review.md")
    for name in PROPOSAL_FILES:
        path = root / name
        if path.is_symlink() or directory.is_symlink():
            raise ContractError("Proposal files must not be symbolic links")
    validate_draft((root / "drafts" / "hello-world.yml.draft").read_text(encoding="utf-8"))
    validate_review((root / "drafts" / "review.md").read_text(encoding="utf-8"))


def validate_changed_paths(root: Path, base: str) -> None:
    commit_sha(base)
    result = subprocess.run(
        ["git", "-C", str(root), "--no-pager", "diff", "--name-status", "--no-renames", base, "HEAD"],
        capture_output=True, text=True, encoding="utf-8", check=False, timeout=20,
    )
    if result.returncode:
        raise ContractError(f"Cannot establish proposal diff: {result.stderr.strip()}")
    changes = [line.split("\t") for line in result.stdout.splitlines()]
    if {tuple(parts) for parts in changes} != {("A", path) for path in PROPOSAL_FILES}:
        raise ContractError("Cloud-agent PR may add only the two proposal files; harness/source changes are forbidden")
    review = (root / "drafts" / "review.md").read_text(encoding="utf-8")
    if f"Source commit: {base}" not in review.splitlines():
        raise ContractError("Review packet source commit must equal the PR's reviewed base commit")
    source = subprocess.run(
        ["git", "-C", str(root), "show", f"{base}:Jenkinsfile"],
        capture_output=True, check=False, timeout=20,
    )
    if source.returncode:
        raise ContractError("Cannot read the pinned base Jenkinsfile")
    check_source(source.stdout)


def check(root: Path, require_draft: bool = False) -> None:
    for name in REQUIRED:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"Required regular file missing: {name}")
    check_source((root / "Jenkinsfile").read_bytes())
    workflow_dir = root / ".github" / "workflows"
    actual = {path.relative_to(root).as_posix() for path in workflow_dir.iterdir() if path.is_file()}
    if actual != HARNESS_WORKFLOWS:
        raise ContractError("An unexpected active workflow was added or a harness workflow is missing")
    for path in workflow_dir.iterdir():
        text = path.read_text(encoding="utf-8")
        for action in re.findall(r"(?m)^\s*(?:-\s*)?uses:\s*(\S+)", text):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}", action):
                raise ContractError(f"Unpinned action in {path.name}")
        if "persist-credentials: false" not in text or "timeout-minutes:" not in text:
            raise ContractError(f"Missing runner/checkout guard in {path.name}")
        if re.search(r"pull_request_target|write-all|continue-on-error|secrets:\s*inherit", text):
            raise ContractError(f"Unsafe demo workflow contract in {path.name}")
    trigger = (workflow_dir / "issue-to-agent.yml").read_text(encoding="utf-8")
    for expected in (
        "types: [opened]", "environment: issue-agent",
        "github.event.issue.user.login == github.repository_owner",
        "COPILOT_USER_TOKEN: ${{ secrets.COPILOT_USER_TOKEN }}",
        "cancel-in-progress: false",
    ):
        if expected not in trigger:
            raise ContractError(f"Issue trigger is missing its required guard: {expected}")
    if re.search(r"\$\{\{\s*github\.event\.issue\.(body|title)", trigger):
        raise ContractError("Issue text must not be interpolated into workflow commands")
    form = (root / ".github" / "ISSUE_TEMPLATE" / "hello-world.yml").read_text(encoding="utf-8")
    if CONSENT not in form or re.search(r"(?m)^assignees:", form):
        raise ContractError("Issue form must retain consent and must not assign Copilot before validation")
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part in {".git", "out", ".venv", "__pycache__"} for part in relative.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).exists():
                raise ContractError(f"Broken local Markdown target in {relative}: {target}")
    validate_proposal(root, require_draft)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-draft", action="store_true")
    args = parser.parse_args()
    try:
        check(ROOT, args.require_draft)
        base = os.environ.get("PROPOSAL_BASE_SHA")
        if args.require_draft and base:
            validate_changed_paths(ROOT, base)
    except (ContractError, OSError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print("Repository contracts passed. No Jenkins, proposed workflow, model, or live API was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
