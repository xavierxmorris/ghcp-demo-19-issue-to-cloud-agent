# Bank-scale CI: central policy, isolated execution, bounded automation

**Runnable synthetic admission rehearsal plus architecture recommendation.
Not deployed bank infrastructure or compliance approval. Sources checked
1 October 2026.**

Assumption: the bank permits GitHub Enterprise Cloud and has approved the source
classification, model processing, residency, retention and contractual terms.
A private runner or Azure VNet does not turn Copilot into a local/offline model
or establish those approvals.

## Runnable integration in this demo

The design is now integrated into the demo's executable entry points:

```powershell
.\go.ps1 -Enterprise -NoBrowser
python -m issue_agent enterprise --ledger out\bank-lab.sqlite3 --out out\bank-first
python -m issue_agent enterprise --ledger out\bank-lab.sqlite3 --out out\bank-replay
```

Use new output names if those directories exist. `-Enterprise` does not share
the live runner's credential path and cannot be combined with `-Live`.

```text
shipped synthetic request records
    -> strict JSON and policy contracts
    -> deterministic readiness / identity / route / CI-boundary decision
    -> real local SQLite transaction
         -> existing work: duplicate, no new reservation
         -> stop / run limit / queue full: deferred
         -> eligible and capacity available: queued locally
    -> fresh immutable report and planned five-lane path
    -> STOP: no GitHub task, workflow or deployment is executed
```

### Implemented, modeled and still a platform responsibility

| Design element | What runs here | What is not established |
| --- | --- | --- |
| Explicit intake | Strict synthetic fields, typed booleans, immutable-looking fixture IDs/revisions | Real owner authentication, source existence or bank AI-processing consent |
| Central runner placement | Requests must select the policy's agent group; overrides/shared lane identifiers are rejected | Effective organization runner setting, VM cleanliness or network separation |
| Shared/direct/manual routing | Exact tiny-source match -> shared candidate; absent match -> direct; near/opaque -> manual; unknown -> blocked | Semantic Jenkins parsing or inspection/approval of a real shared-workflow catalog |
| Selective automatic CI | Incomplete inventory, unreviewed boundary, token writes, secrets, production network or privileged follow-on block automatic CI | A verified account's complete reachable workflow graph or actual branch protections |
| Durable admission | Real SQLite transactions, unique work identity, immutable request hashes and occupied-pipeline checks | Cloud dispatch, distributed delivery, multi-region/high-availability state or worker reconciliation |
| Submission controls | Persistent queue depth, reducible per-run admission count and per-invocation stop switch | Paid-credit budget, elapsed-time controller, cloud concurrency or cancellation |
| Trust lanes | Separate group/isolation/credential/gate values in the plan; every execution is `not-run` | Provisioned runners, OIDC grants, artifacts, deployment approvals or releases |
| Evidence | Actual decision and queue snapshot in a fresh hashed report | Authenticated audit storage or proof that fixture assertions are true |

The shipped policy creates no platform resources. Group/zone names, repository
IDs and source revisions are clearly labeled invented values. The command does
not read pipeline source, consult GitHub or import the private source notes.

### First-run result and reasons

| Fixture | Result | Why |
| --- | --- | --- |
| `shared-candidate` | Admitted locally | Known synthetic source and declared exact shared-contract match |
| `duplicate-same-source` | Duplicate | Same immutable repository/pipeline/source/policy identity |
| `near-match` | Manual review | A close workflow match still needs an owner decision |
| `import-not-ready` | Blocked | Repository arrival is not a completed import handoff |
| `unsafe-auto-ci` | Blocked | Automatic CI cannot expose secrets or a privileged follow-on |
| `runner-escape` | Blocked | The agent cannot select the production release runner |
| `direct-candidate` | Admitted locally | Known tiny source with no declared shared contract; automatic validation is modeled as isolated |
| `queue-limit` | Deferred | Two local work items have filled this fixture's queue |
| `opaque-pipeline` | Manual review | No known behavior contract, even if a familiar tool might be present |

The second process using the same ledger admits nothing, reports three
duplicates and retains queue depth two. This is reproducible persistence,
not a canned report. The report shows nine requests and eight pipeline definitions,
with zero cloud tasks, executed workflows or accepted migrations.

### Design decisions and tradeoffs

| Decision | Why this choice | Alternative deliberately not selected |
| --- | --- | --- |
| Keep the live path and enterprise rehearsal separate | Preserve the proven one-task boundary and require no bank credentials | Silently widening the issue form into an organization-wide dispatcher |
| Use existing Python/PowerShell entry points | Participants can run and inspect the design with the current toolchain | A new service, portal, broker deployment or package stack before its platform is chosen |
| Use standard-library SQLite | Demonstrate real cross-process persistence and atomic checks without installation | A process-memory set that loses duplicate protection on restart |
| Include immutable repository ID in work identity | A rename must not create a second reservation for identical work | Deduplication by display name alone |
| Keep request ID -> input hash immutable | A changed request cannot reuse old authorization-shaped evidence | Updating the previous row and hiding the change |
| Preserve the original work intent across duplicate IDs | A new request ID cannot silently change the queued route, reviewer or CI-approval plan | Reporting new authority for an existing reservation |
| Permit one queued revision per pipeline | Avoid two conflicting source-revision migrations in the same local queue | Calling every new commit a safe independent task |
| Bind the ledger to policy and evaluator identity | A rule/code change must not silently reinterpret old decisions | Reusing a mutable version string as sufficient provenance |
| Keep lane groups and isolation boundaries distinct | Different labels on a shared host are not separation | One privileged shared runner fleet |
| Treat manual approval as insufficient for an unsafe CI boundary | An approval button does not sanitize privileges or network exposure | Letting `required` bypass missing CI design |
| Do not convert declared eligibility into job execution | Teaching metadata and local checks cannot authorize real workloads | Automatically invoking live tasks or fake production jobs |
| Keep the database outside the sealed report | Queue state is mutable; evidence snapshots must not change | Hashing a live SQLite file then mutating it inside the bundle |

### Admission identity and transaction

The work key covers **repository ID + pipeline path + source revision +
policy/evaluator fingerprint**. A separate unique pipeline key prevents
overlapping queued revisions. The request table separately detects a changed
payload reusing a request ID. An intent hash excludes only the request ID and
mutable repository name: a duplicate cannot silently change the original route,
reviewer, runner or CI-approval declaration.

The fingerprint binds canonical policy JSON plus the normalized Python source
for the evaluator, ledger and shared contracts. Formatting-only JSON changes
do not invent a new policy; changed behavior requires a fresh ledger. This is
local drift detection, not a digital signature or a policy-approval system.

Each request is handled inside `BEGIN IMMEDIATE`: verify/request-register,
check prior work and capacity, then insert one reservation atomically. A
SQLite error rolls back that request. Earlier committed requests remain durable
if a later operation fails, and the error report directs the operator to inspect
state before replaying. Report creation is not a transaction with the database.

The local store has a demo application ID and schema version. Existing foreign,
uninitialized or incompatible databases are refused instead of overwritten.
Initial creation is exclusive; simultaneous first-time initialization may
return an explicit error to one caller. Once initialized, concurrent connections
are covered by the atomic duplicate/capacity tests.

This queue has **no worker or completion/reset command**. Entries remain
`queued-locally`; the fixture intentionally fills its queue. Use a new ledger
for an independent lab, not as a way to evade live idempotency. A production
control plane must implement governed lifecycle transitions, dispatch/reconcile
logic, migrations, leases, retention and high availability.

### Stop and limit exercises

```powershell
.\go.ps1 -Enterprise -MaxNew 1 -NoBrowser
.\go.ps1 -Enterprise -StopNewWork -NoBrowser
```

On fresh state, the first admits one item; the second admits zero. Duplicates
consume no new slot. A replay with the stop switch still reports existing
reservations instead of pretending they vanished.

`-MaxNew` can only reduce the configured per-run limit. `-StopNewWork` affects
that invocation; it is not a shared service-wide kill switch and does not cancel
anything. Neither is a monetary budget. No real cloud task is needed to
demonstrate these limits.

### How the implementation is checked

The existing `-Check`/unittest/CI path includes expected outcomes for all nine
records, changed request IDs, repository renames, multiple pipeline definitions,
competing source revisions, policy mutation, two-connection duplicate/capacity
races, stop/limit behavior, foreign databases, malformed contracts and path
containment. CLI tests fail immediately if this mode invokes a cloud client,
external command or network connection.

The existing live controller, workflow allow-list, root source and original
cloud-proof bundles remain unchanged. These new tests are not evidence that
bank runner groups or review rules are configured.

[The integration observation](../iteration/2026-10-01-enterprise-integration.md)
contains the real local results and four complete report/manifest snapshots.

## Recommendation

Build a centrally governed CI platform with separate execution and identity
boundaries. Automate routine preparation and evidence collection; do not give
the agent the authority to approve its own changes, control the release pipeline
or reach production.

```text
approved request / completed import
    -> deterministic admission and durable work queue
    -> one issue per approved pipeline/source revision
    -> cloud agent on an isolated agent runner
    -> proposed PR
    -> isolated, unprivileged validation
    -> independent required review and merge controls
    -> trusted build of the accepted revision
    -> immutable artifact + SBOM/provenance
    -> separately authorized non-production/production promotion
```

One logical platform does not mean one shared runner fleet, one organization-wide
administrator token, one unrestricted network, or one unbounded agent conversation.

## Three controls that must not be confused

| Control | Question answered | Recommended bank default |
| --- | --- | --- |
| Organization Copilot runner policy | Where does the agent execute? | Dedicated approved group/label; repository runner overrides disabled |
| Copilot Actions workflow approval | Can unreviewed Copilot PR changes start workflows automatically? | Keep approval required until the entire reachable workflow surface meets an explicitly reviewed low-privilege contract |
| Required PR reviews and deployment authority | Who may accept code and release it? | Independently enforced reviews, protected branches/environments, scoped release identity and audit |

The [organization-runner page](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/administer-copilot/manage-for-organization/configure-runner-for-coding-agent)
allows an organization owner to select **Standard GitHub runner** or a
**Labeled runner** with a group name and/or label. It also allows disabling
**Allow repositories to customize the runner type**. With that setting disabled,
repositories use the organization's selected runner type instead of overriding
it through `copilot-setup-steps.yml`.

For a bank, use an explicit approved group and compatible image/label, with
platform-owned exceptions rather than arbitrary repository choices. This setting
does not establish network policy, trusted CI, secret permissions, model/data
approval, automatic CI approval, or a production deployment boundary.

## Separate execution pools by trust and access

The names below are illustrative, not existing bank resources.

| Pool | Runs | Permitted access | Must not have |
| --- | --- | --- | --- |
| `agent-sandbox` | Copilot analysis, edits and safe local checks | Approved repository scope and necessary read-only dependency services | Production routes, deployment identity, broad secrets or shared mutable host state |
| `pr-untrusted` | Tests/static analysis of proposed code | Minimal read token, controlled dependency acquisition, synthetic test data | Release credentials, privileged caches, production network or arbitrary reusable deployment authority |
| `trusted-build` | Reviewed accepted source through an approved build contract | Required build dependencies and narrowly scoped artifact publication | An arbitrary-command interface or inherited production secrets |
| `release-nonprod` | Promotion of identified artifacts to approved test targets | Short-lived target-specific identity | Ability to select unrelated artifacts, execute PR scripts or reach production |
| `release-prod` | Independently authorized production promotion | Exact artifact digest, approved environment and constrained workload identity | Agent access, unreviewed source execution or an organization-wide deployment credential |

Use separate networks, credentials, caches and access policies, not only
different labels on the same persistent machine. Platform-owned deployment
repositories can be the only repositories granted access to release runner
groups; ordinary application PRs should not be able to schedule work there.
Where supported, additional workflow restrictions complement repository
restrictions; neither replaces credential and network controls.

Treat code from internal contributors and agents as untrusted until the relevant
review boundary. Private/internal visibility alone does not make a runner safe.

## Runner hosting choice

**Preferred when the bank approves managed execution:** GitHub-hosted larger
runners with Azure private networking, separated into approved runner groups
and subnets by trust/access tier. This reduces responsibility for maintaining
the runner compute while preserving network controls.

**Use self-hosted when there is a real requirement:** for example, a mandated
image, hardware, location, connectivity or control that the managed offering
cannot satisfy. Use supported ephemeral/JIT registration plus a genuinely clean
single-use execution environment. Re-registering a runner does not sanitize
reused disks, host processes, container privileges or network access.

Avoid shared, long-lived self-hosted runners as the default agent platform.
For Copilot, confirm the currently supported OS/architecture. The documented
agent environment supports Ubuntu x64 and Windows 64-bit, not every runner type
available to ordinary Actions.

Copilot's integrated firewall is not compatible with self-hosted runners or
Windows agent environments. If those are chosen, approved external network
controls must exist before disabling the integrated firewall. Do not treat
disabling it as an onboarding shortcut.

### Azure networking details that matter

GitHub's [private-networking documentation](https://docs.github.com/en/enterprise-cloud@latest/admin/configuring-settings/configuring-private-networking-for-hosted-compute-products/about-azure-private-networking-for-github-hosted-runners-in-your-enterprise)
states that this integration is for supported **larger** Ubuntu/Windows runners,
not standard hosted runners. Verify the precise size, architecture and region
combination rather than assuming every Actions runner is eligible for Copilot.

Use dedicated subnets and explicit inbound/egress policy. GitHub recommends
blocking inbound connections to runner machines; the service does not require
inbound access. Azure's default NSG rules permit VNet traffic and outbound
internet access, so "inside a VNet" is not a deny-by-default security policy.

Separate dependency access from production connectivity. Use approved network
enforcement for necessary GitHub/Copilot endpoints and package/action services;
do not assume allowing a GitHub domain prevents exfiltration to writable GitHub
endpoints. Network controls, data approval and credential scope work together.

Use current network telemetry and off-runner audit retention. Microsoft Learn
states that new NSG flow logs can no longer be created and existing NSG flow logs
retire on 30 September 2027; new designs should use the supported virtual-network
flow-log approach.

Verify residency and recovery requirements separately. GitHub's documented
VNet failover is currently public preview and **manually switched**. Region
availability differs for GitHub.com and GHE.com. Do not silently fail over to
an unapproved public runner or promise automatic regional recovery.

## Higher-level automation belongs in a deterministic control plane

Keep GitHub Issues as the visible work-order, but do not use a runner process or
GitHub concurrency group as a durable portfolio queue.

The controller should own:

- approved repository/pipeline inventory and import-readiness checks;
- immutable source and policy revisions, accountable requesters and AI-processing eligibility;
- routing to an approved shared-workflow contract, a bounded conversion, manual review or blocked state;
- atomic work reservations and durable idempotency keyed by repository ID, pipeline, source and policy;
- bounded task concurrency, submission/time/rate/error/budget limits and an operator stop switch;
- reconciliation of real task/session/PR/check states, uncertain submissions and expired authorization;
- complete reporting of attempted, queued, blocked, failed and untouched work;
- audit records and support ownership without retaining unnecessary source or secrets.

Repository creation, a custom property, a discovered Jenkinsfile and owner
authorization are different facts. A newly imported repository may not yet have
its source, branch, metadata or approvals. Wait for an approved handoff before
submitting work.

Use one task per well-defined pipeline change. Several pipelines in one
repository need separate accounting. "PR opened" is not "pipeline migrated",
and a completed task is not a completed repository migration.

## Service identity, not a fleet of employee PATs

The PoC's short-lived, one-repository PAT is a temporary proof mechanism.
It is not the bank's steady-state credential architecture.

Use an approved organization-owned GitHub App installation identity for
ordinary discovery, work-order creation and metadata operations. The currently
documented Copilot task-start/assignment boundary still requires a
user-to-server token. If the bank approves an App user-token/service-user model,
put consent, entitlement, refresh rotation, secret storage, revocation and audit
ownership in a controlled broker.

Do not pretend an installation token becomes a supported task-start identity
by granting it more permissions. A dedicated machine user remains a user and
needs identity/licensing/security approval. If that model is not acceptable,
keep task initiation human-authorized rather than inventing a workload-identity
bypass.

For build/release cloud access, prefer short-lived OIDC federation with narrowly
scoped permissions. Bind trust to the approved repository/workflow/ref/environment
using claims and subject templates the target actually supports. A loose
organization wildcard or caller-provided input is not equivalent to trusted
workload identity.

## Reusable workflow contracts, not thousands of translated copies

Have platform owners maintain a small versioned catalog of approved build and
release contracts. Applications should supply typed, bounded inputs rather than
arbitrary command strings.

Prefer an exact behavior match to an approved shared workflow over literal
syntax translation. A near match needs an owner decision; a missing contract
does not justify inventing a workflow, silently changing a build goal, or
changing the application's build system.

Pin approved external actions/reusable workflows to immutable revisions.
Where policy requires internal mirrors, retain the exact source-to-internal
mapping and distinguish synchronization, integrity verification, vetting,
approval and revocation. Review nested and repository-local dependencies too.
A full SHA is an identity, not proof of approval.

Build accepted source once, identify outputs by digest, produce the required
SBOM/provenance, and promote the same approved artifact. Signing, test success,
source review and release authorization are separate assurances. A privileged
follow-on workflow must not execute arbitrary code or scripts taken from a
lower-trust workflow's artifact.

## Can Copilot PR CI be fully automatic?

**GitHub provides a supported opt-in, but it is not automatically a safe bank
default.**

The current [agent settings procedure](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/configuring-agent-settings)
lets a repository administrator disable **Require approval for workflow runs**
under **Settings -> Copilot -> Cloud agent -> Actions workflow approval**.
GitHub explicitly warns that this can let unreviewed Copilot code obtain
workflow write permissions or access Actions secrets.

Treat this as a **repository-level trust decision**, not a per-workflow
allow-list. Evaluate every reachable workflow and privileged follow-on, including
proposed workflow-file edits, token permission changes, caches, artifacts,
runner routing and environment access. A read-only default token is not by
itself proof that no job can request greater authority.

| Repository/workflow condition | Recommended decision |
| --- | --- |
| Isolated synthetic sandbox with an explicitly reviewed low-privilege execution surface | An administrator may approve auto-run as a bounded experiment |
| Bank repository with demonstrably isolated untrusted validation and no route to privileged resources | Consider opt-in only after platform/security approval and negative testing |
| Mixed PR checks and privileged build/deployment workflows, broad secrets, shared persistent runners or unknown dependencies | Keep approval required; separate the trust boundaries first |

Automation of validation never means automatic PR approval, merge or deployment.
Use enforced independent reviews and protection rules. GitHub also documents
that the user who requested a Copilot PR cannot supply its required independent
approval. Agent self-review and another AI review do not replace that separation.

Some native-Automations guidance still describes human workflow approval as
part of its default safeguards. Do not assume every entry point or organization
policy has identical effective behavior; test the chosen supported configuration.

The demo's attempted fork-run approval API returned a run-type-specific 403.
That is not a reason to broaden its PAT, change to a privileged event trigger,
or dispatch around the gate. Use the supported UI or an explicitly authorized
policy change after the execution boundary is suitable.

## Pragmatic rollout

1. Keep the public synthetic issue-to-agent proof as integration evidence only.
2. Pilot one approved private UAT repository on the centrally selected isolated runner.
3. Establish independent validation and one reviewed shared-workflow contract.
4. Prove negative cases: wrong requester/ref, altered workflow, unavailable runner,
   missing mirror, denied credential, stale evidence and duplicate/uncertain submission.
5. Add a small, approved cohort and measure task duration, failures, costs and
   reviewer capacity before raising limits.
6. Automate low-risk work under the established controls; retain explicit human
   release and cutover authority.

The next architecture deliverable should be a tested platform contract and
owned operating model, not a promise of unattended estate-wide migration.

## Sources and evidence boundary

All sources below were retrieved or checked on **1 October 2026**:

- [Organization-level Copilot runner configuration](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/administer-copilot/manage-for-organization/configure-runner-for-coding-agent)
- [Configure the agent environment](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/customize-the-agent-environment)
- [Copilot risks and mitigations](https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations)
- [Review Copilot output and workflow approval](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/review-copilot-output)
- [Copilot agent settings and automatic workflow runs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/configuring-agent-settings)
- [GitHub Actions secure-use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Larger-runner group access](https://docs.github.com/en/actions/how-tos/manage-runners/larger-runners/control-access)
- [Azure private networking for GitHub-hosted runners](https://docs.github.com/en/enterprise-cloud@latest/admin/configuring-settings/configuring-private-networking-for-hosted-compute-products/about-azure-private-networking-for-github-hosted-runners-in-your-enterprise)
- [Azure network security groups overview](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview) (read through Microsoft Learn MCP)
- [Copilot API identity boundary](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api)

The live PoC proves only its [dated issue/task/PR path](../iteration/2026-10-01-live-proof.md).
It does not prove any bank's effective enterprise settings, private networking,
token broker, data-processing approval, review enforcement or production readiness.
