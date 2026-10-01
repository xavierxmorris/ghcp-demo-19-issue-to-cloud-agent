# Bank-scale CI: central policy, isolated execution, bounded automation

**Architecture recommendation, not deployed bank infrastructure or compliance
approval. Sources checked 1 October 2026.**

Assumption: the bank permits GitHub Enterprise Cloud and has approved the source
classification, model processing, residency, retention and contractual terms.
A private runner or Azure VNet does not turn Copilot into a local/offline model
or establish those approvals.

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
