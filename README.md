# Demo 19 - Open an issue, start the Copilot cloud agent

**Public synthetic proof | issue-opened trigger | offline by default | no merge**

Open one structured, **unassigned** GitHub issue. A GitHub Actions workflow
validates the request, assigns it to Copilot using a separate user-authorized
token, and leaves the agent to prepare an inactive Hello World workflow and a
review packet in a pull request.

```text
Owner opens the synthetic request issue
  -> issues: opened runs trusted main-branch code
  -> deterministic identity, consent, source and duplicate checks
  -> ordinary workflow token records start intent
  -> user token assigns copilot-swe-agent[bot]
  -> existing Copilot cloud agent works in this repository
  -> inactive workflow + behavior-gap packet in a PR
  -> independent human review; no automatic merge or cutover
```

**Opening an ordinary issue does not inherently start Copilot.** This demo
supplies the missing issue-event-to-assignment automation. Its runner creates
an issue without an assignee; it does not quietly start a local Copilot session
or call the Agent Tasks endpoint instead.

**Reading paths:** [try it offline](#run-offline-first),
[prepare a live run](#run-the-real-issue-trigger-proof),
[understand the build](#how-this-demo-was-built),
or [check the limits](#honesty-notes).

## Why this demo exists

It is a deliberately small follow-on to
[demo 14](https://github.com/xavierxmorris/ghcp-demo-14-jenkins-to-github-actions-hackathon)
(private, evidence-first pipeline modernization) and
[demo 16](https://github.com/xavierxmorris/ghcp-demo-16-copilot-agent-migration-orchestrator)
(App/user identity separation and idempotent orchestration).

Both complete published READMEs and their linked notes were considered.
[Source-context coverage](docs/SOURCE-CONTEXT.md) accounts for the retained
requirements, deliberate differences, and deferred work. Private notes, their
customer details, and their source snapshots are **not redistributed here**.
Neither source demo is modified.

The purpose is to prove **trigger plumbing**, not demonstrate a clever converter.
The existing cloud agent receives a tiny, explicit output contract. There is
no new migration model, hosted service, MCP server, custom persona, portal,
portfolio scan, or claim that direct translation is the preferred final design.

## Run offline first

Requires Python **3.11+**; PowerShell **7+** for the runner. No packages,
credentials, GitHub connection, Jenkins, Docker, Maven, or model are needed.

```powershell
.\go.ps1 -Check
.\go.ps1 -NoBrowser
```

Portable entry points:

```powershell
python -m unittest discover -s tests -v
python scripts\check_repo.py
python -m issue_agent preview --out out\first-preview
```

Preview uses an explicitly identified all-zero **placeholder commit** and writes
a new bundle: `report.json`, `report.md`, `issue-body.md`,
`assignment-request.json`, and `bundle-manifest.json`. Nothing is submitted.
Existing output directories are refused. A manifest is a local integrity
check, not an authenticated audit record.

## Run the real issue-trigger proof

First complete [Live setup](docs/LIVE-SETUP.md): an eligible Copilot user,
the default `main` branch, labels, a **main-only `issue-agent` environment**,
the scoped `COPILOT_USER_TOKEN` environment secret, and the
`ISSUE_AGENT_ENABLED=true` repository variable.

Then, from a clean, committed clone whose origin matches the explicit target:

```powershell
.\go.ps1 -Live -AcceptLiveRun `
  -Repository xavierxmorris/ghcp-demo-19-issue-to-cloud-agent
```

Or open **Issues -> New issue -> Start the synthetic cloud-agent proof**.
Select the one scenario, paste the exact current `main` commit SHA, check the
authorization box, and **leave Assignees empty**. Only the repository owner's
request is accepted in this personal-repository PoC.

Watch **Actions -> Issue to Copilot cloud agent**. The workflow re-reads the
issue, checks the source, records a durable marker, and performs the documented
Copilot assignment. There is no second issue-approval click. The generated PR
is the human review boundary.

Observe the issue and its linked agent session without creating more work:

```powershell
python -m issue_agent observe `
  --repository xavierxmorris/ghcp-demo-19-issue-to-cloud-agent --issue ISSUE_NUMBER
```

Replace `ISSUE_NUMBER` with the actual integer. Use a fresh output directory
for every observation. [Recorded evidence](iteration/README.md) states what
has actually run; the presence of this code alone is not live proof.

## What the agent may produce

Only:

- `drafts\hello-world.yml.draft`: manual-only, one bounded greeting job,
  no actions or reusable-workflow dependencies, and no secret access.
- `drafts\review.md`: pinned source identity, behavior mapping, intentional
  changes, unknown Jenkins job settings, actual checks, and human decisions.

The [acceptance contract](docs/ACCEPTANCE.md) is intentionally narrow and
deterministically checked. No draft exists in the starter baseline. The agent
must not change the source, tests, controller, policies, instructions, or active
workflows to pass.

## Guardrails and evidence states

| Boundary | Behavior |
| --- | --- |
| Unknown requester, missing consent, edited issue or unexpected comments | Refuse before assignment |
| Wrong repository, stale commit, truncated tree, missing/multiple pipelines | Refuse; never guess a safe route |
| Modified fixture or unrelated active application workflow | Manual review; only the three named harness workflows are exempt |
| Repeated request for the same commit | Reuse the original issue; serialize the controller; do not start twice |
| Assignment response lost or ambiguous | Keep `agent-start-requested`; require reconciliation, not blind retry |
| Assignment already confirmed | No-op on rerun, even if the final status-label write failed |
| Controller success | Assignment confirmed only; not evidence that the model ran or conversion succeeded |
| Agent session / linked PR | Separately observed; migration remains **0 accepted out of 1** |
| Missing user token, entitlement or platform access | Explicit failure with token-free evidence, never a mock success |

Read [Architecture and limits](docs/ARCHITECTURE.md) for races, public-issue
context, token boundaries, and the difference between instructions and platform
enforcement.

## Runner modes

| Command | Contract |
| --- | --- |
| `.\go.ps1` | Fresh offline preview; no browser or network |
| `.\go.ps1 -Check` | Offline tests and repository contracts |
| `.\go.ps1 -Manual` | Print commands only |
| `.\go.ps1 -NoBrowser` | Offline preview; retained for suite familiarity |
| `.\go.ps1 -Live -AcceptLiveRun -Repository OWNER/REPO` | Raise/reuse one real issue; can consume credits and Actions minutes |
| Live command plus `-NoBrowser` | Same real mutation, without opening the issue in a browser |

These flag meanings are specific to this demo. No command starts an all-tools
CLI session or changes personal Copilot configuration.

## Teaching material

| Read | Purpose |
| --- | --- |
| [RUN-SHEET.md](RUN-SHEET.md) | Five-minute presenter track and explicit fallback |
| [WORKSHOP.md](WORKSHOP.md) | Participant exercises, negative cases, recovery, and evidence rubric |
| [PROMPTS.md](PROMPTS.md) | Baseline task, review, and bounded next experiments |
| [Live setup](docs/LIVE-SETUP.md) | Exact identity prerequisites, enable/disable, retry and cleanup |
| [Acceptance](docs/ACCEPTANCE.md) | Separate trigger, agent, proposal, and human acceptance gates |
| [Source coverage](docs/SOURCE-CONTEXT.md) | Complete reading scope and requirement disposition |
| [Sources](docs/SOURCES.md) | Current API documentation, action pins, dates and limitations |

## How this demo was built

This section explains the construction, not just the commands to run the
finished result. It distinguishes implemented behavior from platform setup and
from outcomes that still need a real cloud observation.

### 1. Read the full context before choosing the solution

The starting point was not a generic "AI migration" architecture. The two
published source READMEs were read completely, followed by the linked planning,
policy, implementation, discussion, workshop and evidence notes. The long note
that exceeded the tool's first output was read in bounded ranges through its
end. The retained twelve-file migration guide and six lesson READMEs were also
read rather than inferred from their summaries.

Two consistent requirements shaped the design:

**First, prove the smallest real interaction.** A single synthetic Jenkinsfile
should result in a traceable issue, agent session and reviewable proposal before
building discovery, routers, dashboards or overnight scheduling.

**Second, preserve the authority boundaries.** Source classification is not
approval; a user-authorized assignment is not completed conversion; a PR is not
acceptance; and no part of this proof authorizes merge, execution or cutover.

The [coverage map](docs/SOURCE-CONTEXT.md) records the immutable source revisions
and gives every major context requirement an implementation, constraint or
explicit deferral. Private source text was not copied into the new public repo.
The original repositories, including unpublished local work, remain separate.

### 2. Turn the request into one observable success path

The user selected **automatic assignment after an unassigned issue is opened**.
That is different from the simpler `gh issue create --assignee @copilot`
interaction, so the implementation does not substitute that simpler path and
call it the requested proof.

The chosen sequence has four independently observable outcomes:

| Stage | Evidence needed | What it still does not prove |
| --- | --- | --- |
| Issue accepted | Correct issue and original opened-event workflow | That assignment happened |
| Assignment confirmed | Copilot returned as an assignee, with exact request/run evidence | That the model has executed |
| Agent execution observed | Real cloud session ID/state and linked PR | That its proposal is correct |
| Proposal checked | Bounded diff, inactive draft, behavior mapping and actual checks | Independent acceptance or runtime equivalence |

The synthetic source contains one greeting. It has no private dependencies,
credentials, shared library, artifact publishing or deployment. That keeps a
failure diagnosable: an identity or trigger problem cannot be mistaken for a
complex build-conversion problem.

### 3. Verify the platform behavior instead of assuming it

Current GitHub documentation and installed CLI help were checked before writing
the integration. Three facts matter:

**Issue creation and Copilot assignment are different operations.** An ordinary
issue has no intrinsic cloud-agent trigger. This demo adds the workflow that
connects them.

**The assignment boundary requires a user context.** The documented
`copilot-swe-agent[bot]` assignment uses a supported user-to-server token.
Giving an installation or workflow token broader permissions is not a valid
substitute for that authentication model.

**Workflow-generated issue events can be suppressed.** Creating the initial
issue with an Actions `GITHUB_TOKEN` normally will not start another issue-event
workflow. The primary interaction therefore uses the owner's UI or normal
`gh` login. A future issue-creating service needs its own approved identity.

Native Copilot Automations were also considered. Their currently documented
private/internal-repository requirement makes them unsuitable for this public
demo. These checks and the API-version caveat are retained in
[the source register](docs/SOURCES.md).

### 4. Separate the four parts instead of building a new service

The implementation deliberately has no server, database, SDK dependency or
local model process:

| Part | Main files | Responsibility |
| --- | --- | --- |
| Requester | `go.ps1`, `issue_agent\cli.py`, issue form | Preview, obtain explicit live consent, create/reuse an unassigned issue |
| Deterministic controller | `contracts.py`, `service.py`, `github_api.py`, issue workflow | Validate immutable scope, prevent duplicates and perform the supported assignment |
| Existing cloud agent | `AGENTS.md`, repository instructions, setup workflow | Read the known source and author only the two permitted proposal files |
| Evidence and review | `evidence.py`, `check_repo.py`, tests and acceptance guide | Retain exact facts and check the narrow proposal without claiming approval |

Python's standard library supplies JSON, hashing, HTTP, subprocess handling and
unittest. Offline use therefore does not begin with a package installation or
credential setup. The optional PowerShell runner is a wrapper, not the engine.

### 5. Freeze the source and constrain the work-order

The [issue form](.github/ISSUE_TEMPLATE/hello-world.yml) has only three fields:
the fixed scenario, the full source commit, and the explicit authorization
checkbox. It does not accept arbitrary repository targets, pipeline paths,
commands, model instructions or secret values.

`parse_body` checks the submitted Markdown shape, not just whether a friendly
label exists. `validate_issue` additionally requires the personal repository's
human owner, correct title, open state and queue label. The controller re-reads
the current issue and compares it with the original event snapshot.

The source commit must match both the issue event's controller revision and
current `main`. The tree must be complete and contain exactly one root
Jenkinsfile. The source must be a regular non-executable blob whose bytes match
the synthetic fixture, including the recorded SHA-256.

This is intentionally a closed example, not a detector that calls any file
containing `echo` or `mvn` safe. Adding a second Jenkinsfile, an unrelated active
workflow or an unsupported command produces a refusal.

### 6. Make the harness exception precise

A same-repository issue trigger needs active infrastructure of its own:

```text
.github\workflows\ci.yml
.github\workflows\copilot-setup-steps.yml
.github\workflows\issue-to-agent.yml
```

Those three names are the complete workflow exception. A broad "ignore all
existing workflows" rule would hide prior migration or unrelated application
behavior. Conversely, copying demo 16's generic "no workflows" discovery rule
unchanged would reject this demo's own controller.

The distinction is documented and tested. It is not presented as a new general
migration-eligibility rule.

### 7. Wire the identity boundary visibly

The workflow checks out the trusted event revision, does not persist checkout
credentials, uses pinned actions and a bounded job timeout, and passes issue
data through `GITHUB_EVENT_PATH`. It never pastes issue text into a shell script.

The API operations are deliberately split:

| Operation | Identity |
| --- | --- |
| Open the initial unassigned issue | Owner through the GitHub UI or existing CLI login |
| Read source/issue/ledger and write lifecycle labels | Ordinary repository workflow token |
| Check Copilot availability for the user | Separate approved user token |
| Assign Copilot with `agent_assignment` | That same separate user token |
| Work on the resulting branch/PR | Copilot's own normal cloud runtime |

`RestApi` fixes the destination to the GitHub API, refuses redirects, bounds
response sizes and deadlines, and redacts credentials from diagnostics.
The two clients do not fall back to one another.

The user credential belongs in a main-only environment with no per-issue
reviewer requirement. That enables the selected automatic interaction while
keeping PR review independent. A main-only environment must actually be
configured; merely writing its name into YAML does not protect a secret.

### 8. Design failure recovery before calling the paid boundary

A request can be accepted by GitHub even if the client loses the response.
Repeating the same POST without checking could start duplicate paid work.

The controller therefore records `agent-start-requested` **before** sending the
assignment. After the response, it checks for the actual Copilot assignee rather
than treating any 2xx status as success. Only then does it add `agent-assigned`.

```text
validated issue
    |
    v
persist start marker
    |
    v
send assignment exactly once
    |
    +-- confirmed assignee --> record assignment verified
    |
    +-- lost/failed/ignored --> retain marker; human reconciliation
```

On a rerun, an already assigned issue is a no-op. A marker without confirmed
assignment stops automatic recovery. A failure before that boundary can be
retried after its cause is fixed and the original source/event remains valid.

The local issue helper checks all bounded ledger pages and reuses an existing
request for the same revision, even if it was closed. A repository-wide
concurrency group serializes controller runs, but is not falsely described as
a durable FIFO queue. The issue ledger and explicit recovery instructions are
still necessary.

### 9. Give the cloud agent an explicit, limited job

The fixed assignment payload supplies the repository, source commit, expected
hash and acceptance instructions. It does not send a model override or select
a newly authored custom migration persona. The experiment starts with the
existing cloud agent.

The setup workflow prepares Python 3.11 on an Ubuntu runner. There is no package
restore, Jenkins install or credential-copy step. The exact
`copilot-setup-steps` job name and default-branch requirement were checked
against current documentation.

The agent may add only an inactive `.yml.draft` and a review packet. The workflow
grammar is tiny by design: one manual-only greeting job, no `uses`, no secrets,
and a two-minute timeout. These are explicit target decisions, not claims that
the source's unknown job configuration had the same behavior.

This is a useful **trigger** experiment even though the desired YAML is spelled
out. It is not a benchmark of the agent's ability to translate arbitrary Jenkins.

### 10. Keep the evidence honest and reproducible

Each attempt gets a new directory. The bundle records its mode, exact source
identity, issue/run links, mutation facts, errors, and whether assignment or
agent execution was actually observed. It also retains the issue body and
assignment request. A manifest hashes the finished files and is written last.

`observe` follows the issue's same-repository Copilot PR reference and reads the
actual linked session through `gh agent-task view`. It does not infer a session
from a branch name or invent a task ID when no session is visible.

The controller's observation is narrower than the full agent log. It records
the model as not observed unless separately evidenced. An agent completion or
PR never changes the accepted-migration count: the report remains **0 out of 1**
because this demo does not perform human acceptance or cutover.

### 11. Test the refusals, not just the successful request

The unit suite uses explicit API doubles to assert which identity called which
endpoint and whether an assignment was attempted. It covers missing consent,
wrong identities, edited requests, comments, stale commits, unsupported source,
multiple pipelines, unrelated workflows, incomplete reads, unavailable Copilot,
duplicate requests, failed labels, ignored assignments and lost responses.

Separate tests cover HTTP redaction/redirects/deadlines, evidence integrity,
output-directory containment, the tiny draft grammar and PowerShell run-mode
behavior. The runner explicitly rejects `-AcceptLiveRun:$false`; presence of a
switch name must not be mistaken for consent.

An actual early check caught the Windows-authored Jenkinsfile using CRLF bytes
while the contract expected LF. The source representation was corrected rather
than weakening the byte/hash check. The exact observed failures and subsequent
results belong in [the dated evidence record](iteration/README.md), not in a
claim that the first attempt was perfect.

Workflow syntax/expressions were also checked with a checksum-verified,
versioned actionlint executable after it was found missing locally. It is an
authoring check, not an added offline runtime dependency.

### 12. Publish only the finished synthetic build and verified facts

The detailed README and linked guides are prepared **before the first content
push**. The public repository contains no private reference snapshot, customer
names, raw exports, credentials or fabricated agent output.

The remaining publication/live sequence is explicit:

1. pass the local gate and inspect the staged synthetic files;
2. commit and push the demo, then observe its actual hosted CI;
3. configure and verify the main-only environment and narrow user-token secret;
4. enable the trigger and open one unassigned, owner-authorized issue;
5. observe the real assignment, session and PR, or retain the exact blocker;
6. inspect the proposal without merging or executing it;
7. disable new submissions, remove/revoke the temporary token, and curate the
   real result with its source and PR revisions.

Code being published, CI being green, a secret name existing, an assignment
returning, and a cloud agent finishing are different pieces of evidence.
The dated record is the authority for which stages actually happened.

### 13. Keep broader context visible without quietly implementing it

The full context also describes shared-workflow assessment, build-system
conversion, action mirrors/quarantine, import readiness, read-only job exports,
governed custom properties, inventory reporting, identity brokers, Vault/OIDC,
artifact provenance and bounded waves.

Those topics were considered and mapped, not forgotten. They require their own
source/target contracts, permissions, owners and acceptance tests. Implementing
them before the first issue-trigger proof would obscure the actual requirement
and make failures harder to diagnose. The ordered backlog is preserved in
[Source-context coverage](docs/SOURCE-CONTEXT.md).

## Honesty notes

- All input is newly written synthetic material. This is not a customer sample
  or approval, and no private source repository is sent to the cloud agent.
- Python validates and orchestrates. Copilot, if actually started, authors the
  proposal. Offline tests use explicit API doubles, not model results.
- This is github.com and a personally owned demo repository, not GHES,
  an enterprise implementation, or an organization-owned workload identity.
- The workflow token handles ordinary reads/labels. The current preview
  assignment boundary needs a user-to-server token; installation tokens and
  `GITHUB_TOKEN` are not substituted.
- GitHub's native Copilot Automations currently require private/internal repos;
  this public demo uses an Actions issue event instead.
- Zero generated `uses` references avoids an action-mirror dependency for this
  first experiment. The harness's pinned public actions are **not** proof of
  enterprise approval, internal mirroring, dependency vetting, or egress controls.
- A manual trigger deliberately does not reproduce unknown Jenkins schedules,
  webhooks, plugin behavior, agent images, or hidden job settings.
- A green YAML/static check, agent completion, or PR is not behavioral
  equivalence, independent review, sandbox approval, production readiness,
  signing, migration acceptance, licensing savings, or Jenkins retirement.
- No production merge protection is claimed by a Markdown rule. Configure and
  verify required reviews/rulesets separately before using any real workload.
- No repository discovery, Airflow rehabilitation, custom-property mutation,
  dashboard product, shared-workflow assessor, Gradle conversion, Vault trust,
  action-sync service, or overnight wave is silently included.

Current sources were checked **1 October 2026**. APIs and policy can change;
recheck [the source register](docs/SOURCES.md) before another live setup.
