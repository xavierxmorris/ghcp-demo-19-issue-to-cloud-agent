# Workshop: prove an issue-to-cloud-agent path

**45-60 minutes after setup; cloud latency additional.**
Use a personal disposable clone/fork and only the synthetic fixture.

## What participants learn

Explain why issue creation, request approval, user-authorized assignment,
cloud execution, a proposed PR and migration acceptance are separate.
Reproduce a deterministic refusal and show why retrying a paid mutation is not
ordinary retry logic.

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
