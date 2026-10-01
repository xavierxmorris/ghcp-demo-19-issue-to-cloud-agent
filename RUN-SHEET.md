# Five-minute presenter track

**Synthetic only.** Cloud queue time is additional; five minutes is a presenter
plan, not a measured generation-speed claim.

Before presenting, read [live setup](docs/LIVE-SETUP.md), run `.\go.ps1 -Check`,
and prepare either the authorized live path or clearly labeled recorded evidence.

| Beat | Show | Explain |
| --- | --- | --- |
| 0:00 - the work-order | Root Jenkinsfile and issue form | One invented greeting, immutable source, explicit owner consent; no customer source |
| 0:45 - the opening event | Create the issue with Assignees empty | The issue-event workflow supplies the automation; ordinary issue creation alone is not Copilot assignment |
| 1:30 - the identity boundary | Trigger workflow and attempt artifact | Workflow token validates/labels; a separate user-authorized token performs the Copilot call |
| 2:15 - the actual cloud task | Issue assignee and real session/PR if available | Assignment, observed execution and a PR are separate facts; do not claim the queue has finished |
| 3:15 - the proposed change | Two inactive draft files and mapping packet | No active workflow, external action, publishing or merge; unknown job behavior remains unknown |
| 4:15 - the refusal/recovery | Duplicate and lost-response tests | Durable start intent prevents an automatic second paid assignment |
| 4:45 - the decision | Source-context map and next experiment | Prove a small path first; shared workflows, mirrors, imports and scale are separate steps |

## Enterprise design track: five more minutes, entirely offline

This is now a runnable second track, not only an architecture slide.

| Beat | Show | Explain |
| --- | --- | --- |
| 0:00 - the policy | `fixtures\enterprise\policy.json` | Five distinct execution groups/zones and bounded local capacity; these are synthetic declarations |
| 0:45 - admission | `.\go.ps1 -Enterprise -NoBrowser` and the new report | Nine requests: 2 admitted locally, 1 duplicate, 2 manual, 3 blocked, 1 deferred |
| 1:45 - the design and why | Planned lane/gate list | Automatic low-privilege checks do not remove independent review or production approval |
| 2:45 - replay | Two commands below using the same ledger | The second process adds zero work; duplicate protection survives process exit |
| 3:45 - stop and capacity | `-MaxNew 1`, then `-StopNewWork` on fresh default state | Counts limit local admissions, not money; a stop does not erase previous work |
| 4:30 - honest boundary | `platform_controls_verified: false` and `not-run` lanes | Local SQLite behavior is real; bank runner/network/identity enforcement is not configured |

```powershell
python -m issue_agent enterprise --ledger out\presenter-enterprise.sqlite3 --out out\presenter-first
python -m issue_agent enterprise --ledger out\presenter-enterprise.sqlite3 --out out\presenter-replay
```

Use new output names on another presentation. Use a new ledger for an independent
exercise, or deliberately reuse the previous one to teach persistence.

## Presenter commands

```powershell
.\go.ps1 -Check
.\go.ps1 -NoBrowser
.\go.ps1 -Manual
```

Only after live setup and permission:

```powershell
.\go.ps1 -Live -AcceptLiveRun -Repository OWNER/REPO
python -m issue_agent observe --repository OWNER/REPO --issue ISSUE_NUMBER
```

Use actual values. Repeating the live helper for the same commit reuses the
issue; it does not intentionally launch another task.

## Difficult questions

| Question | Accurate answer |
| --- | --- |
| Does the Python code migrate Jenkins? | No. It validates a fixed synthetic task and asks the existing cloud agent to author the proposal |
| Why is there a user token? | The current preview assignment API needs user-to-server authentication; an installation/workflow token is not substituted |
| Is this a new MCP server or custom agent? | No. The point is to establish the built-in cloud-agent baseline first |
| Are Marketplace actions approved for the enterprise? | No claim is made. Generated output uses none; the public harness pins are not an internal approval catalog |
| Does a completed agent mean a completed migration? | No. The accepted count stays zero; reviewers must inspect behavior, checks and unresolved decisions |
| Why not use native Copilot Automations? | Current documented availability excludes public repositories |
| Why not show a complex build? | That would mix trigger debugging with hidden job, dependency, identity and runner questions |
| Does enterprise mode configure those five runner pools? | No. It evaluates synthetic requests and emits a plan; every lane is not run |
| Is the queue just a mock? | Reservations and atomic duplicate/capacity checks use real local SQLite; its inputs and future jobs are synthetic |
| Does an exact catalog match prove shared-workflow compatibility? | No. It is a fixture assertion used to exercise routing, not a semantic catalog lookup |
| Did we remove CI approval to show higher automation? | No. A safe automatic lane is modeled, while the real GitHub policy remains unchanged |

## Honest fallback

If the user token, policy or cloud service is unavailable, show the offline
request and real failure, or a dated record from [iteration](iteration/README.md).
Say **not run**, **blocked**, **queued**, or **recorded**, whichever is true.
Never manually create an agent-looking PR, relax the source contract, publish
private notes, or run the Jenkinsfile to rescue a demonstration.
