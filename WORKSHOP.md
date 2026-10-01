# Workshop: prove an issue-to-cloud-agent path

**45-60 minutes for the issue track; add 20-30 minutes for the offline
enterprise-design track. Cloud latency additional.**
Use a personal disposable clone/fork and only the synthetic fixture.

## What participants learn

Explain why issue creation, request approval, user-authorized assignment,
cloud execution, a proposed PR and migration acceptance are separate.
Reproduce a deterministic refusal and show why retrying a paid mutation is not
ordinary retry logic.
The enterprise track adds policy/runner/CI trust separation and a durable local
admission queue without requiring organization access.

## 1. Predict the flow before running

Read README and [Architecture](docs/ARCHITECTURE.md). Draw the owner, workflow,
user-token and cloud-agent boundaries. Predict what happens if an issue is
opened without an assignee, with the wrong owner, or without the enable switch.

```powershell
.\go.ps1 -Check
.\go.ps1 -NoBrowser
```

Inspect the fresh bundle. Identify the all-zero placeholder commit, empty
mutation ledger and zero migrated count. This is not a model transcript.

## 2. Read the code by responsibility

| File | Question |
| --- | --- |
| `issue_agent\contracts.py` | Which exact source/request/output shapes are allowed? |
| `issue_agent\service.py` | Which checks happen before the first mutation? |
| `issue_agent\github_api.py` | Which identity sends the assignment, and how are failures redacted? |
| `issue_agent\evidence.py` | Which facts are persisted and which are not claimed? |
| `.github\workflows\issue-to-agent.yml` | Which event, code revision and secret environment are used? |
| `scripts\check_repo.py` | What can the static gate establish, and what can it not? |

Explain why a general YAML converter, App host or web dashboard is not required
for this first proof.

## 3. Challenge one boundary

Pick an existing negative test: stale revision, multiple Jenkinsfiles,
unsupported source, extra workflow, absent consent, untrusted requester,
pre-assignment comment, truncated tree, or lost assignment response.

Predict the result, run the relevant unittest, and show that no assignment
operation occurred. Test doubles are explicitly offline, not live AI evidence.
Do not loosen a policy or change the expected fixture to turn a refusal green.

## 4. Prove the live path, only if prepared

Complete [Live setup](docs/LIVE-SETUP.md) with one-task authorization.
Use the same source revision and exact issue wording for the baseline.

```powershell
.\go.ps1 -Live -AcceptLiveRun -Repository OWNER/REPO
python -m issue_agent observe --repository OWNER/REPO --issue ISSUE_NUMBER
```

Record who created the issue, who performed assignment, actual workflow/session
identities, source hashes, PR/head commit and all observed failures/wait states.
Do not start another task simply because the first takes longer than the session.

If credentials or entitlement are unavailable, retain the exact blocker and
continue with the offline contract. Do not substitute your broad login token
or pretend a local conversion is the requested cloud execution.

## 5. Review the proposal independently

Read the two files against [Acceptance](docs/ACCEPTANCE.md). Account for the
greeting, runner choice, timeout, manual trigger and unknown Jenkins job setup.
Read actual test output and the complete diff. The agent must not edit its own
validator, source or harness to pass.

Classify the result as useful baseline, rework, or blocked. Keep review and
sandbox execution separate. Do not approve, merge or activate it during the lab.

## 6. Reconcile and stop

Explain the difference between retrying a pre-assignment read failure and
retrying a possibly accepted assignment. Demonstrate this with the offline
timeout test, not by deliberately creating duplicate live tasks.

Disable new starts and remove/revoke only the temporary credential as described
in live setup. Preserve the synthetic issue/PR and a curated evidence record.
No cleanup resets the source repos, deletes a workspace, or changes global
Copilot configuration.

## Completion rubric

The participant can show an independent prediction, one observed happy-path or
honest blocked result, one meaningful refusal, identity separation, exact source
and attempt evidence, a review disposition and an owned next experiment.

No conversion percentage, productivity multiplier, production certification,
general pipeline support, or migration completion is inferred from this lab.

## Enterprise track: implement the architecture as observable decisions

Read [the design and why](docs/ENTERPRISE-CI-DESIGN.md#runnable-integration-in-this-demo).
Do not configure an actual bank organization for this exercise.

### Predict the nine decisions

Read both `fixtures\enterprise` files. Before running, predict which request:
uses the shared-workflow route, duplicates earlier work, needs a human, lacks
import readiness, tries unsafe automatic CI, escapes the agent runner, uses
bounded direct conversion, fills capacity, or has opaque behavior.

```powershell
.\go.ps1 -Enterprise -NoBrowser
```

Open the reported `enterprise-report.md`. Its first fresh run has two local
admissions, one duplicate, two manual cases, three blocked cases and one deferred
case. Explain each result using its readable reason and the source fixture.
Do not treat the eight pipeline definitions as a real estate sample.

### Trace the five trust lanes

Compare the two admitted plans. The shared candidate retains human workflow-run
approval; the direct candidate's fixture asserts a reviewed, low-privilege
automatic validation boundary. Both retain independent review before trusted
build and separate production approval.

Explain why different labels on the same host would not satisfy isolation,
and why a manual approval button does not fix a privileged PR execution design.
Identify which assertions would need evidence from a real bank platform.

### Prove state survives a process

```powershell
python -m issue_agent enterprise --ledger out\workshop-enterprise.sqlite3 --out out\workshop-first
python -m issue_agent enterprise --ledger out\workshop-enterprise.sqlite3 --out out\workshop-replay
```

The replay adds zero reservations and keeps queue depth two. Compare the
snapshots and confirm the first report's bytes remain unchanged. The database
is deliberately a sibling of the reports, not inside a sealed bundle.

Read the tests for changed request IDs, repository renames, overlapping source
revisions, separate pipeline definitions and two concurrent database clients.
The latter tests exercise real SQLite transactions, not an in-memory duplicate
set. They do not prove a distributed production scheduler.

### Challenge stopping and limits

```powershell
.\go.ps1 -Enterprise -MaxNew 1 -NoBrowser
.\go.ps1 -Enterprise -StopNewWork -NoBrowser
```

Predict one and zero new admissions respectively. Explain why the queue count
is not a paid-credit limit, the stop flag is per invocation, and no worker exists
to complete/dequeue these local reservations.

In a dedicated exercise copy, change one fixture to request automatic CI while
exposing a secret, a privileged follow-on, or production connectivity. A new
ledger/report must show an explicit block. Changing `ci_approval` to `required`
should still require manual boundary review, not magically admit unsafe work.

After a policy/evaluator change, the old ledger must refuse the new fingerprint.
Do not rewrite its policy row. Preserve old evidence and use a new, clearly
labeled lab ledger.

### Enterprise completion evidence

Keep the two report bundles, observed decision counts, one negative case,
request/policy identities and a concise account of what is implemented versus
modeled. The mutable database stays in ignored local `out`. No new issue,
model task, runner, secret, build or deployment should exist because of this lab.
