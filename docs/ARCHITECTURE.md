# Architecture: a visible work-order, not a migration factory

## Two execution tracks

The original live track below still operates on one owner-authorized synthetic
issue. The new `enterprise` / `-Enterprise` track runs only local metadata
validation, trust-lane planning and SQLite admission. It never invokes the live
controller, GitHub API, source commands, runners or cloud agent.

`enterprise.py` owns closed contracts and decisions; `enterprise_ledger.py`
owns atomic persistence. Existing evidence helpers write fresh sealed snapshots
while the mutable database stays outside the bundle. The
[implemented enterprise design and rationale](ENTERPRISE-CI-DESIGN.md#runnable-integration-in-this-demo)
explain the concrete route, duplicate, capacity and stop behavior.

Names, source revisions, readiness, reviews and isolation are declared fixture
data, not effective platform facts. No table row naming a production lane gives
this local program production access.

## Four responsibilities

| Component | Owns | Does not own |
| --- | --- | --- |
| Repository owner / `go.ps1 -Live` | Consent and one unassigned issue | Copilot assignment, conversion, merge |
| `issue-to-agent.yml` + `issue_agent` | Intake, source identity, duplicate checks, assignment evidence | AI reasoning, conversion quality, portfolio scheduling |
| Existing Copilot cloud agent | The two-file inactive proposal and explanatory PR | Policy changes, approval, activation, cutover |
| Independent reviewer | Source-to-proposal assessment and next decision | Retroactively turning a mock/offline run into live evidence |

The issue, workflow and target source are in the same personally owned
repository. `agent_assignment.target_repo` is derived from `GITHUB_REPOSITORY`,
never accepted from issue text. The only base branch is `main`.

## Identity and credential boundary

The owner opens an issue in GitHub or through their existing `gh` login.
The local helper uses that login normally; it does not export its token.
Opening the issue with a user credential produces the required `issues: opened`
event. An issue created by a workflow's `GITHUB_TOKEN` generally will not start
another issue-event workflow.

Inside Actions:

| Credential | Allowed uses in this implementation |
| --- | --- |
| `GITHUB_TOKEN` | Re-read repository, ref, tree, source and issues; add the two lifecycle labels |
| `COPILOT_USER_TOKEN` | Check the user's suggested Copilot assignee, then the one assignment API call |
| Copilot's own runtime identity | Its normal repository-scoped cloud task after assignment |

No fallback collapses these clients. The user token lives only in the
main-restricted `issue-agent` environment; ordinary CI and setup steps do not
reference it. There are deliberately no environment reviewers in this automatic
path. Configure required PR reviews separately.

Environment/step wiring reduces exposure but is not step-level process
isolation. Trusted main-branch code can access secrets granted to that job.
An administrator can change policies or workflows. This PoC does not defend
against a malicious repository owner or claim production authorization.

## Deterministic preflight

The job itself excludes non-owner and non-queued requests. Python then:

1. requires the enable switch, original `issues:opened` event, and trusted main ref;
2. verifies the event repository, human owner, open issue, title, label and exact consent form;
3. requires the requested source SHA to equal the controller's event SHA;
4. re-reads the issue and rejects changed input, comments or another assignee;
5. verifies current main, a complete bounded tree, and exactly one root Jenkinsfile;
6. allows only the three named harness workflows and no existing migration proposal;
7. validates a regular, non-executable Git blob and exact synthetic UTF-8/LF source bytes;
8. reads the complete bounded issue ledger and selects the original request;
9. checks the user identity's Copilot availability;
10. re-reads the issue and main ref immediately before recording start intent.

No Jenkins source is interpreted or executed. Unknown/multiple sources,
unrelated workflows, stale input, absent metadata and incomplete pagination
are explicit refusals, not low-confidence candidates.

The three harness-workflow exception is intentional. Demo 16's published
discovery rule rejects a target with existing workflows; applying it literally
here would reject the controller's own CI/setup/issue workflows. This proof
names those three paths exactly rather than ignoring all workflows.

## At-most-once attempt and recovery

```text
unassigned owner issue
  -> validated
  -> agent-start-requested label persisted
  -> assignment POST attempted once
      -> Copilot returned in assignees -> assignment-verified
      -> failed/lost/ignored response -> assignment-uncertain
  -> agent-assigned label (ordinary workflow identity)
```

The start marker is written **before** the non-idempotent assignment boundary.
No automatic HTTP retry repeats that call. A rerun:

- does nothing if Copilot is already assigned;
- refuses if a durable marker exists without confirmed assignment;
- may retry pre-assignment failures after their cause is fixed and the original
  event/source remains valid.

This deliberately favors avoiding duplicate paid work over automatic recovery.
Even a 403 after the marker requires a human to inspect the original request
before resetting it. Labels are an owner-controlled ledger, not tamper-proof
storage. Removing them or unassigning/reassigning Copilot manually bypasses the
demo's own guarantees.

A repository-wide, non-cancelling concurrency group serializes controller runs.
GitHub Actions concurrency is **not** a durable FIFO queue: pending runs can be
replaced. The issues remain the durable work-orders; inspect pending/unattempted
issues and rerun their original runs deliberately. No throughput claim is made.

## Reads and errors

Responses are capped at 2 MiB; the event at 1 MiB; source/request text at 4 KiB.
Issue/timeline reads stop at ten pages of 100 and fail instead of truncating.
The observer also bounds each active/archived task listing to ten pages of 100.
Requests have deadlines. Redirects away from the selected API endpoint are
refused. HTTPS is not disabled and the API host is fixed to `api.github.com`.

Transport and HTTP failures retain method, endpoint, status and request ID where
available. Credential values and recognized token shapes are redacted. API
responses are never wholesale uploaded as success evidence. An HTTP success
without the Copilot assignee is a failure.

## Remaining races and trust limits

There is no server-side transaction spanning issue text, comments, branch
identity, labels and assignment. Re-reading narrows but does not eliminate the
check/use window. GitHub documents that comments from users without repository
write access are not presented to the agent. Input from write-authorized actors
and repository content can still be untrusted or misleading. This PoC's
zero-comment rule is intentionally stricter than that platform filter.
Repository instructions forbid expanding the task from comments, but are not
an authorization sandbox.

Use a private, appropriately governed target for any non-synthetic workload.
Do not generalize this public owner-only proof into an arbitrary contributor
automation or a multi-tenant service. An issue label is not authorization.

The five-minute controller deadline does not terminate a cloud task already
accepted by GitHub. Disabling the variable stops new eligible controller
attempts; review and stop an in-flight session separately through GitHub.

## Evidence and lifecycle

Every attempt writes a fresh token-free bundle; a hash manifest is written last.
The record separates request creation, assignment attempt, assignment
confirmation, observed agent execution, linked PR and human acceptance.
The assignment controller does not select or know the eventual model. The
read-only observer records it only when the actual session API exposes it.
Prompts, usage/billing payloads and other sessions' source content are not
included in the curated observation.

The observer uses the documented repository-scoped Agent Tasks **GET** API.
It binds a task's pull artifact to the PR database ID, verifies the detail
response and session ownership, and records separate task/session identifiers.
Ambiguous tasks or incomplete session evidence fail explicitly while retaining
the already observed PR facts. There is no direct Agent Tasks creation path.

The denominator is one synthetic **pipeline definition**, not an estate or a
repository migration percentage. Assignment or a PR leaves the accepted count
at zero. An independent review and any separately approved execution are later
decisions.

## Explicit extension boundary

No App hosting or refresh broker is necessary for the owner-created issue proof.
A service creating issues later should use its approved installation identity
for ordinary repository/issue work, keep the separate user-to-server assignment
boundary, and add token rotation, webhook verification, durable state, monitoring
and support ownership.

Portfolio/custom-property discovery, import readiness, exact/near/no-match
shared-workflow assessment, Maven-to-Gradle conversion, action quarantine/mirrors,
private registries, OIDC/Vault, artifact provenance and bounded overnight waves
are separate reviewed extensions. See [coverage](SOURCE-CONTEXT.md).
The [enterprise design](ENTERPRISE-CI-DESIGN.md) now has a runnable local
admission/plan demonstration. Its production integrations and compliance
approval remain explicitly unimplemented.
