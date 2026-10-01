# Live setup: one public synthetic issue, one cloud task

**This setup changes GitHub state and can consume Actions minutes and Copilot
credits.** Use only a disposable personal demo repository and its shipped
synthetic fixture. No production source, secrets or customer notes are needed.

## 1. Confirm the target and user

Use your own repository/fork. This PoC intentionally refuses organization-owned
repositories and requests from anyone except the personal repository owner.
That is a scope limit, not advice to move an enterprise workload into a
personal account.

Confirm:

- the complete demo is on the default `main` branch and its ordinary CI passes;
- Actions and Copilot cloud agent are available and allowed for the user/repo;
- the issue form, controller and setup workflow are all present on `main`;
- the owner has authorized one synthetic task and knows how to stop it;
- the target has exactly the synthetic root Jenkinsfile, no proposal on `main`,
  and only the three harness workflows.

The controller checks Copilot through `suggestedActors`, as described in the
[current GitHub API procedure](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api).
Do not add installation-token permissions to try to bypass a user-token boundary.

## 2. Create the labels

In Settings/Issues or with the installed GitHub CLI:

```powershell
$Repository = "YOUR_LOGIN/ghcp-demo-19-issue-to-cloud-agent"
gh label create cloud-agent-request --repo $Repository --color 0969DA `
  --description "Owner-approved synthetic cloud-agent request"
gh label create agent-start-requested --repo $Repository --color D4A72C `
  --description "Durable assignment-attempt marker; reconcile before retry"
gh label create agent-assigned --repo $Repository --color 1A7F37 `
  --description "Copilot assignment confirmed, not migration completion"
```

If a label already exists, inspect it rather than blindly overwriting unrelated
configuration. The queue label must exist before using the issue form.

## 3. Restrict the credential environment to main

In **Settings -> Environments**, create `issue-agent`.
Set deployment branches/tags to **Selected branches and tags**, and add exactly
the **main branch**, not a tag or wildcard.

Do not configure required environment reviewers for this automatic proof.
The owner gives consent by submitting the structured issue; the independent
human approval belongs at the resulting PR.

An environment name in YAML alone does **not** establish a protection rule.
Verify the actual branch restriction before installing a secret. For a new
disposable repository, the documented API equivalent is:

```powershell
@{
  deployment_branch_policy = @{
    protected_branches = $false
    custom_branch_policies = $true
  }
} | ConvertTo-Json -Depth 3 | gh api --method PUT `
  "repos/$Repository/environments/issue-agent" --input -

@{ name = "main"; type = "branch" } | ConvertTo-Json |
  gh api --method POST `
    "repos/$Repository/environments/issue-agent/deployment-branch-policies" --input -
```

These are setup writes, not ordinary CI steps. Do not apply them to an existing
production environment or remove its reviewers.

## 4. Supply a separate, narrow user token

For this one-off proof, create an approved, short-lived **fine-grained personal
access token** under the demo owner. Select **only this repository**.

Open your GitHub **Settings -> Developer settings -> Personal access tokens ->
Fine-grained tokens -> Generate new token**. Do not choose Tokens (classic).

For the author's repository, this
[pre-filled one-day token form](https://github.com/settings/personal-access-tokens/new?name=ghcp-demo-19-live-proof&target_name=xavierxmorris&expires_in=1&actions=write&contents=write&issues=write&pull_requests=write&metadata=read)
sets the name, resource owner, expiration and permission suggestions. A fork
owner must use their own resource owner. **The link does not select a repository.**

| Creation field | Value |
| --- | --- |
| Token name | `ghcp-demo-19-live-proof` |
| Expiration | 1 day |
| Resource owner | The personal account that owns the demo |
| Repository access | Only select repositories |
| Selected repository | Only your demo repository, not all repositories |

GitHub's documented issue-assignment permissions are:

| Repository permission | Access |
| --- | --- |
| Metadata | Read |
| Actions | Read and write |
| Contents | Read and write |
| Issues | Read and write |
| Pull requests | Read and write |

Leave unrelated administration, organization and account permissions unset.
Click **Generate token**, copy its value, then store it as described below.
The token-creation procedure and URL pre-fill fields are documented in
[GitHub's PAT guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

Use the shortest practical expiry and revoke after the exercise. A supported
GitHub App **user access token** is another user-to-server option, but
registration, consent, refresh and secret rotation are deliberately not
implemented here. An installation token is a different identity and is not a
substitute.

Add the token as the **Actions environment secret** `COPILOT_USER_TOKEN` in
`issue-agent`, not an Agents/Codespaces secret, repository variable or issue
body. Use the GitHub UI or a separate interactive terminal:

```powershell
gh secret set COPILOT_USER_TOKEN --repo $Repository --env issue-agent
```

Paste only into that secure prompt. **Never paste the token into chat, a command
argument, a source file, a transcript or a report.** Do not export a broad
existing CLI login (especially an administrator credential) to make the demo
convenient.

This is a short-lived hack identity, not the proposed production service
identity. Production needs a governed owner, entitlement, minimum access,
rotation, revocation, attribution and support model.

## 5. Enable and open the unassigned issue

Set the repository variable only when the prerequisites are ready:

```powershell
gh variable set ISSUE_AGENT_ENABLED --repo $Repository --body true
.\go.ps1 -Live -AcceptLiveRun -Repository $Repository
```

The runner uses normal `gh` authentication to **create an unassigned issue**.
It requires a clean checkout, matching origin and the current main commit.
It reuses an existing owner request for that commit, including a closed one,
instead of creating another task.

For the UI path, open the issue form, use the exact current main commit, check
consent, leave Assignees empty, and create the issue. Do not add extra text or
comments before assignment.

An issue created by `GITHUB_TOKEN` usually does not cause another issue-event
workflow to run. A future automation creating these work-orders must use a
supported App installation or user credential for issue creation. This is
separate from the user token needed for Copilot assignment.

## 6. Observe the exact run

Look for **Issue to Copilot cloud agent** in Actions. Inspect its actual status
and artifact rather than treating an issue label as proof that the model ran.
Then:

```powershell
python -m issue_agent observe --repository $Repository --issue ISSUE_NUMBER
gh agent-task view SESSION_ID --repo $Repository --json id,state,pullRequestUrl,createdAt,completedAt
```

Substitute the actual issue integer and **session ID**, not the task ID or PR
number. The observer discovers the task/session relationship using documented
repository-scoped GET endpoints. It uses your existing local `gh` login, not
the Actions assignment secret. If that local login uses a fine-grained PAT,
the observation endpoints separately require **Agent tasks: read** permission;
do not broaden the stored assignment token just to perform local observation.

GitHub CLI 2.93.0 rejects PR selectors without an interactive terminal with
`session ID is required when not running interactively`. Supplying a verified
session UUID works; pretending a task UUID is a session UUID does not.

Retain the issue, workflow run, source identity, session, PR/head commit, actual
checks, warnings, failures and manual corrections. If GitHub requires approval
to run checks on an agent PR, inspect its complete diff first and approve only
the intended trusted check run. That is not PR approval or permission to merge.

The standard fork workflow-run approval REST endpoint did **not** approve this
demo's Copilot PR run: it returned HTTP 403, stating the run was not from a fork
or queued by the Actions bot. Use the documented PR UI, not repeated API calls,
broader tokens, a privileged trigger, or a manual-dispatch workaround.

GitHub separately documents an administrator opt-in under **Settings -> Copilot
-> Cloud agent -> Actions workflow approval -> Require approval for workflow
runs**. Disabling it can expose unreviewed code to workflow write permissions or
secrets. This proof leaves that policy unchanged. See the
[enterprise design](ENTERPRISE-CI-DESIGN.md) before considering automatic CI.

Inspect the exact [acceptance contract](ACCEPTANCE.md). Do not merge, activate
the draft, run Jenkins, execute the draft, publish or deploy.

## 7. Recover without starting duplicate work

| Observation | Safe response |
| --- | --- |
| Missing token / unavailable assignee, no start marker | Fix the prerequisite; rerun the original failed Actions run if source is unchanged |
| Edited request, stale source, extra workflow or unsupported pipeline | Stop and inspect. Do not weaken validation or silently change the original issue |
| `agent-start-requested`, no confirmed assignee | Inspect the original run and GitHub agent sessions. A task might already exist |
| Copilot assigned, final label/artifact step failed | Rerun is a no-op for assignment; retain the original failure evidence |
| Issue creation timed out | List existing issues and rerun the helper only after reconciliation; it checks the ledger before creating |
| Task failed or waits for input | Preserve its state and respond through the PR/session. Do not start a replacement automatically |

Rerun the original workflow from its Actions page or with
`gh run rerun RUN_ID --failed`. The original opened-event snapshot is retained;
there is no edited/labeled/reopened auto-start and no alternate assignment
dispatch endpoint.

If the marker is present, reset it only after an accountable owner confirms no
task was accepted. Removing a marker or reassigning Copilot is a deliberate
exception with duplicate-cost risk, not an automated recovery feature.

## 8. Stop and clean up

```powershell
gh variable set ISSUE_AGENT_ENABLED --repo $Repository --body false
gh secret delete COPILOT_USER_TOKEN --repo $Repository --env issue-agent
```

Disabling new submissions does not cancel an accepted cloud task. Stop an
in-flight session separately through GitHub if necessary. Revoke the temporary
token in the issuing user's settings; deleting a stored secret alone does not
revoke that token.

Keep the synthetic issue/PR as labeled evidence or close them after review.
Never merge simply to tidy the demo. Workflow artifacts retain for seven days;
curate a token-free record deliberately if longer retention is required.
