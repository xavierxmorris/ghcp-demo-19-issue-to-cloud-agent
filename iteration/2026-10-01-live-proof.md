# Live proof - 1 October 2026

**Observed:** one unassigned issue started the issue-opened workflow, which
assigned Copilot; one real cloud task completed and produced an inactive,
two-file draft PR. A second controller run made no mutations and started no
additional task.

**Not claimed:** independent migration acceptance, hosted PR CI approval,
runtime equivalence, activation, merge, deployment or Jenkins cutover.

## Exact identities

| Evidence | Observed identity |
| --- | --- |
| Source/controller commit | `cc2ce2f21397f45c4b38fad704378152408521a8` |
| Root Jenkinsfile SHA-256 | `dba88eedd823cf62db9136941f91fb37bddd40898e7c1baeef8eb66c5d43a54f` |
| Owner-created unassigned issue | [Issue #2](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/issues/2) |
| Assignment workflow, attempts 1 and 2 | [Run 36795695019](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/actions/runs/36795695019) |
| Task | [`b1c9479e-4453-4470-9159-3dee193652d2`](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/tasks/b1c9479e-4453-4470-9159-3dee193652d2) |
| Session | [`5e93d7ff-98b5-4545-a53f-e64822d376b1`](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/pull/3/agent-sessions/5e93d7ff-98b5-4545-a53f-e64822d376b1) |
| Model reported by the session API | `sweagent-capi:gpt-5.6-luna` |
| Model selection | Platform default; no explicit override was sent |
| Agent-authored proposal | [Draft PR #3](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/pull/3) |
| Validated PR head | `b836ca99d9b3464c2a7eb6bd9158f3ba8ce819a1` |
| Original PR base | `cc2ce2f21397f45c4b38fad704378152408521a8` |
| Hosted PR CI at observation | [Run 36795870721](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/actions/runs/36795870721): `action_required` |

The task ID and session ID are different. The observed model string is the
API's reported value, not a recommendation for an explicit model parameter.
No usage/billing payload or raw session transcript is published here.

## Timeline

These timestamps are observed API/report values in **UTC**, not a productivity
benchmark or an estimate of human review time.

| Time on 1 October 2026 | Observation |
| --- | --- |
| `00:20:32Z` | Issue #2 created |
| `00:20:33.988278Z` | Local intake recorded `issue-created` and `issue-created-unassigned`; assignment not yet observed |
| `00:20:49.626586Z` | Controller recorded `assignment-verified` |
| `00:20:53.306338165Z` | GitHub task created |
| `00:20:57.108259235Z` | Cloud session created |
| `00:22:51.092404Z` | Initial local observer failed at non-interactive CLI session selection |
| `00:23:02.903659816Z` | Cloud session completed |
| `00:33:10.209710Z` | Corrected read-only observer recorded actual completed task/session and PR |

The source was never replaced with a harder pipeline, the task was not restarted
to hide a failure, and the agent's proposal was not manually rewritten.

## What the issue-trigger workflow actually did

Attempt 1 completed successfully. Its mutation ledger contains exactly:

1. `durable-start-marker`
2. `copilot-assignment`
3. `assigned-label`

The record has `assignment_attempted=true`, `assignment_verified=true`,
and `agent_execution_observed=false`. That final value is intentional: the
controller only proves the assignment; it does not pretend to watch the model.

The workflow used its ordinary token for reads/labels and the configured user
secret for availability/assignment. The assistant verified only secret metadata
locally; it never retrieved or displayed the secret value. Effective token
expiry and its complete grants were not independently inspected from that
opaque secret.

## Live duplicate protection

The same original issue-event workflow was rerun once after assignment.
Attempt 2 also completed successfully, reporting:

```text
state: already-assigned
assignment_attempted: false
assignment_verified: true
mutations: []
```

A subsequent repository task listing still contained the same single completed
task with **one session**. Two controller attempts are not two model tasks.
No replacement issue, reassignment or second cloud session was used.

## Agent output and independent checks

The complete PR diff adds exactly:

- `drafts/hello-world.yml.draft` - the eleven-line inactive, manual-only greeting workflow;
- `drafts/review.md` - a 64-line source/mapping/change/unknowns/validation/review packet.

No source, test, policy, instruction or active workflow file changed in the PR.
It remains **open, draft and unmerged** at the recorded head.

The actual cloud session log records:

```text
python scripts/check_repo.py --require-draft
Repository contracts passed.

python -m unittest discover -s tests -v
Ran 64 tests
OK
```

The generated packet uses Windows path spelling for the checker; the actual
Linux session command above used forward slashes. Both the source and proposed
workflow were treated as data, not executed.

The exact PR head was also fetched into a separate detached local worktree.
With `PROPOSAL_BASE_SHA` set to the original base, its 64 tests and
`check_repo.py --require-draft` passed. No file in that worktree or PR was edited.
The current controller/observer maintenance gate subsequently passed **77 tests**,
including the new REST observation and retained-bundle integrity cases.

These checks establish this narrow contract, not complete migration quality.
One wording point remains for human review: the packet initially calls the
`agent any` to Ubuntu mapping "preserved", while its later deliberate-changes
section correctly says that Ubuntu is a chosen target, not inferred parity.
The agent's original wording is retained rather than polished into artificial
evidence of a perfect first result.

## Observer failure, diagnosis and root-cause correction

The initial observer used the installed CLI's documented PR-selector shape:

```text
gh agent-task view --repo OWNER/REPO PR_NUMBER --json ...
```

The real result was:

```text
GitHub CLI failed (1): session ID is required when not running interactively
```

GitHub CLI 2.93.0's `NewCmdView` implementation checks for an actual session
identifier before allowing a non-interactive call, even though help also lists
PR selectors. This was an observation-client problem, not a failed assignment
or failed agent task.

The correction uses the documented repository-scoped Agent Tasks GET APIs:
find the PR artifact by its database ID, obtain that task, verify its sessions
and select the newest timezone-qualified session. Active and archived listings
are bounded, mismatches and ambiguity fail explicitly, and partial PR facts are
retained on an observation failure.

The API client refuses non-GET operations on Agent Tasks endpoints. The primary
trigger remains issue assignment. Once the actual session ID was known,
`gh agent-task view SESSION_ID --log` also retrieved the original execution log.

The original failed observation remains in the retained evidence; it was not
overwritten with the later successful result.

## Hosted CI and the approval boundary

The repository's initial four-way CI and setup workflow passed at the original
source revision:

- [Main CI](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/actions/runs/36794256070)
- [Copilot Setup Steps](https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/actions/runs/36794256069)

The PR's separate CI run was held by GitHub for human approval. After inspecting
the complete two-file diff, an attempt to approve **only that CI run** through
the standard fork-run approval endpoint returned:

```json
{
  "message": "This run is not from a fork pull request or queued by the Actions bot",
  "documentation_url": "https://docs.github.com/rest/actions/workflow-runs#approve-a-workflow-run-for-a-fork-pull-request",
  "status": "403"
}
```

The gate was not bypassed, no permission was broadened, and no PR approval or
merge was submitted. The supported human UI is **Approve and run workflows**.
The separate repository administrator auto-run policy was researched for the
[bank-scale design](../docs/ENTERPRISE-CI-DESIGN.md), not changed to manufacture
a green demonstration.

This record binds checks to the listed source/base/head revisions. Later
maintenance or evidence commits on main are not retroactive validation or
approval of a newer merge candidate.

## Retained complete bundles

Each linked folder contains the original five files, including its own final
SHA-256 manifest. Copies were verified before and after retention, and the
repository gate checks the retained manifests. Hashes detect drift; they do not
make the record an independently authenticated audit system.

| Stage | Original bundle copy |
| --- | --- |
| Unassigned issue creation | [intake](2026-10-01-live/intake/report.json) |
| Successful assignment | [assignment](2026-10-01-live/assignment/report.json) |
| Zero-mutation controller rerun | [rerun](2026-10-01-live/rerun/report.json) |
| Original observation failure | [observer-failure](2026-10-01-live/observer-failure/report.json) |
| Actual task/session/PR observation | [observation](2026-10-01-live/observation/report.json) |

`assignment-request.json` records the bounded request/template; its presence in
a preview or observation bundle does not mean that bundle sent a POST. Use the
mode and mutation facts, not a filename, to determine what actually happened.

## Cleanup and remaining human decisions

After the proof:

- `ISSUE_AGENT_ENABLED` was verified as **false**;
- `COPILOT_USER_TOKEN` was deleted from the `issue-agent` environment and its
  absence was verified;
- the repository still showed one completed task and one session;
- PR #3 remained draft/open/unmerged;
- hosted PR CI still reported `action_required`.

Deleting the environment copy does **not** revoke the underlying PAT. Its owner
must revoke it in GitHub token settings, or let the chosen expiry take effect.
No account-token revocation is claimed here.

Independent human review, any later approved sandbox execution and a separate
cutover decision remain outstanding. The accepted migration count is still
**zero out of one synthetic pipeline definition**.
