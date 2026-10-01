# Source-context coverage: what was read and what it changed

**Reading date: 1 October 2026.** This is a requirement-disposition map, not a
copy of either source repository and not evidence of customer authorization.
All private source material stays private.

## Immutable reading baselines

| Source | Published commit | Reading boundary |
| --- | --- | --- |
| [Demo 14](https://github.com/xavierxmorris/ghcp-demo-14-jenkins-to-github-actions-hackathon/tree/508f0e348bba3a28fbf83674388a95f7f958b550) (private) | `508f0e348bba3a28fbf83674388a95f7f958b550` | Complete README, every README-linked note, linked lesson READMEs and the complete retained migration-guide text |
| [Demo 16](https://github.com/xavierxmorris/ghcp-demo-16-copilot-agent-migration-orchestrator/tree/1004181a45c80e931f6b348a53244cbbb161d01c) | `1004181a45c80e931f6b348a53244cbbb161d01c` | Complete README, architecture, live setup, presenter/workshop/prompts, plus the live workflow and API client |

The source-14 README blob was
`3b5aa9b0e0fb9feeeb17ea7c68988e00cc142de0`; source 16's was
`f9479087683aa055e823f63580ddfdbdb4c1a528`.
These identities record what was read, not a promise that newer revisions have
the same behavior.

The source-16 local checkout also contained substantial unpublished changes.
Those were left untouched; this public demo does not represent them as the
published baseline or copy them into a new repository.

## Complete reading inventory

The reading covered **43 files in demo 14** and **8 in demo 16**:

| Source group | Complete material read |
| --- | --- |
| Demo 14 orientation | README, RUN-SHEET, WORKSHOP and PROMPTS |
| Demo 14 planning/governance | Three-day plan, scope, discovery, policy/review, decision pack, architecture, Importer option, sources and source-coverage notes |
| Demo 14 private discussion context | All nine linked brief/follow-up notes, including the full long note rather than its tool preview |
| Demo 14 teaching context | Refactoring-pack README and all six individual lesson READMEs |
| Demo 14 retained guide | The provenance manifest and all twelve retained files: guide README, contribution rules, Cloud/DC/pipeline runbooks, decision guide, references, tool catalog, validation/cutover, stalled-migration guidance, mixed-estate example and discovery questionnaire |
| Demo 14 evidence context | The curated-evidence README and its historical-versus-fresh distinction |
| Demo 16 narrative | README, architecture, live setup, RUN-SHEET, WORKSHOP and PROMPTS |
| Demo 16 implementation prior art | Published assignment API client and manually dispatched orchestration workflow |

The twelve retained guide files total 1,063 lines in their original manifest.
Their source snapshot is **not copied into this public demo**. Reading the
lesson READMEs is not a claim that their entire executable example corpus was
run. Historical evidence was not rerun and was not presented as fresh.
External/internal engagement links were not recursively fetched or redistributed.
Current product procedures actually checked are listed in [Sources](SOURCES.md).

## Decisions taken from every linked note

Private notes are identified below by topic rather than customer names, quoted
text, estate details, internal hosts, or meeting records.

| Context topic | Disposition in this demo |
| --- | --- |
| Initial scope/value brief | Keep this a non-production, synthetic feasibility proof; no estate commitment, savings estimate or implied approval |
| Issue-driven follow-up | GitHub is the interface, the issue is the work-order, assignment starts work, PR is the review boundary |
| End-to-end migration-method note | Keep tools/identity, agent reasoning, deterministic validation and human judgment separate |
| Plumbing-first note | Start with one canonical Hello World case; baseline the existing agent before designing a broad router |
| Action-mirror/trigger note | Prove the trigger independently; generated output has zero action dependencies; do not equate public action pins with enterprise approval |
| Hackathon-focus note, read in full | Preserve opt-in intent, immutable source, exact failure evidence, literal-versus-shared-workflow distinction, data boundaries, progressive examples and honest lifecycle reporting |
| Supply-chain/quarantine note | Acquisition, integrity, vetting, approval and revocation remain distinct; no fixed delay, internal-action exemption, property-clear operation or production credential shortcut is invented |
| Shared-workflow/Gradle note | Direct conversion, consumer-to-shared-workflow adoption, build-system conversion and central-workflow contribution are separate changes; all beyond this one trigger proof |
| Overnight-wave note | Keep durable idempotency, bounded reads, explicit stop/recovery, one repository/task and honest state; portfolio controllers, capacity promises and OIDC/Vault trust are deferred |

## Requirements carried into the runnable path

| Requirement | Concrete implementation/evidence |
| --- | --- |
| Explicit owner intent and AI-processing consent | Exact issue form; owner-only validation; `-AcceptLiveRun` and repository enable switch |
| GitHub issue is the durable work-order | Unassigned issue creation; `issues: opened` controller; no hidden direct Agent Tasks call |
| Immutable source and request | Issue source commit equals controller event commit and current main; exact fixture bytes; re-read issue before mutation |
| Read only the necessary source | Bounded tree plus one root Jenkinsfile; no estate scan, source execution or Groovy interpretation |
| Conservative handling of unknowns | Strict known scenario; multiple pipelines, arbitrary source and unrelated workflows refuse |
| Keep ordinary and user-authorized identities separate | Independent API clients; workflow token for reads/labels, user token for availability/assignment |
| No credential export | Environment secret, fixed API host, no token arguments/serialization, redacted diagnostics |
| Duplicate/lost-response protection | Complete bounded issue ledger, repository concurrency, persisted start marker, no blind mutation retry |
| Distinguish deterministic logic from actual AI | Python only validates/starts; existing cloud agent authors the proposal; preview/API doubles are labeled |
| Inactive reviewable output | Two exact proposal paths; `.yml.draft` outside `.github`; no automatic activation |
| No unresolved action dependency | Tiny output grammar accepts no `uses`, local actions, reusable workflows, dynamic/nested references or secrets |
| Preserve behavior gaps | Required mapping, intentional changes, unknowns, source hash and actual-check record |
| Human/platform authority remains separate | No merge/approval API; documentation distinguishes instructions from required review/ruleset enforcement |
| Reproducible attempt evidence | Fresh JSON/Markdown bundles, exact issue/prompt request, source/run identities, final hash manifest |
| Honest denominator and lifecycle | One synthetic pipeline definition; assignment/PR never increments accepted migrations |
| Safe fallback and blocked evidence | Offline preview, negative tests, explicit errors; missing access never becomes a fabricated live result |

## Every README section has a disposition

| Source section/group | New-demo treatment |
| --- | --- |
| Demo 14 positioning and retained private context | Separate new synthetic repository; bounded goal; immutable provenance without private redistribution |
| Synthetic demonstrator and closed policy | Offline/check/manual modes; one exact synthetic request only; no magic customer-approval switch |
| Produced artifacts | Fresh report/request/manifest bundle; agent output separately lives in inactive PR files |
| Optional real Copilot reading | Changed intentionally to an actual cloud-agent task, not a read-only local advisory; no model run is claimed from preview |
| Facilitation, refactoring lessons and runner semantics | Own run sheet, workshop and prompts; explicit per-demo flag meanings; advanced patterns remain future experiments |
| Honesty and input-storage notes | No equivalence, approval, execution or migration-rate claims; ignored folders are convenience, not DLP |
| Demo 16 identity rationale | User-to-server task-start boundary retained and checked against current sources |
| Safe offline mode | Stdlib-only preview/tests with no credentials, packages or network |
| Live prototype | Intentionally replaces manual discovery dispatch with the user-selected automatic issue-opened flow |
| Routing contract | Known one-file fixture rather than general discovery; exact harness-workflow exception documented; all other ambiguity refuses |
| Repository anatomy and learning material | Small request/controller/agent/reviewer separation with corresponding code, tests and docs |
| Honesty and production gaps | No registered App, service account, token broker, org webhook host or production hosting is falsely implied |
| Source references and rolling-preview warning | Dated current sources, observed versions, exact action pins and live-evidence separation |

## What the six refactoring lessons add to the review discipline

| Lesson topic | Constraint retained; implementation deferred |
| --- | --- |
| Shared Maven contract | Do not silently change `test` to `verify`; behavior, not a tool keyword, selects reuse |
| Parallel/artifact/post behavior | Workspace isolation, dependencies, failure evidence and artifact identity need explicit design |
| Credentials/publishing | A registry or identity change is not cosmetic conversion; job authority and protected review need separate decisions |
| Schedules/parameters | Hashed schedules, time zones, typed inputs and queue semantics are not interchangeable |
| Hidden shared libraries | Read actual resolved implementations; a short caller is not evidence of a simple pipeline |
| Artifact provenance | Archival, digest integrity, signed provenance, trustworthy builder and production approval are different claims |

The Hello World source has none of these behaviors. They are recorded as
expansion stop conditions, not quietly dropped from a supposedly general
converter.

## What the retained migration guide prevents us from claiming

Repository transport/fidelity, Git history, LFS, metadata, permissions, identity,
integrations, pipeline execution, cutover and decommissioning are separate
workstreams. This demo assumes an already available synthetic GitHub repo.
It does not implement GEI, mirror migration, Actions Importer, bulk inventory,
source-platform administration or a cutover runbook.

Discovery requires owners and approved evidence. A representative pilot should
include exceptions, not just easy cases. Preserve exact versions/errors and
escalate access failures instead of expanding credentials or repeatedly
resubmitting. Those principles are retained without copying private field
examples or attempting their external procedures.

## Deliberate differences from demo 16

| Difference | Why it is justified here |
| --- | --- |
| Human creates the issue; no GitHub App registration | The selected interaction is raising an issue, not repository-arrival discovery |
| Automatic opened-event assignment | Explicitly selected for this PoC; direct create-and-assign remains a documented simpler alternative, not the tested path |
| No per-issue environment reviewer | Owner consent starts this synthetic task; independent human review is at the PR |
| Main-only secret environment remains | Restricts where the assignment credential is available without adding a second intake approval |
| Three exact harness workflows are allowed | A same-repo issue controller needs its own CI/setup/trigger files; arbitrary application workflows remain blocked |
| Uncertain assignment is not blindly retried | Avoids duplicate paid work if GitHub accepted the first request but its response was lost |

## Ordered follow-on backlog, not hidden scope

The issue/task/PR baseline below has since been observed in
[the dated live proof](../iteration/2026-10-01-live-proof.md).
The next explicitly requested integration adds an **offline enterprise
admission rehearsal**, described in the
[implemented design and why](ENTERPRISE-CI-DESIGN.md#runnable-integration-in-this-demo).
It exercises synthetic readiness/routing/runner/CI-boundary decisions, real
local SQLite reservations and bounded admission. It does not implement a
production catalog assessor, organization dispatcher, token broker or cloud
worker. The original published reading baselines and private-data boundaries
above remain unchanged.

1. Complete the one live issue/session/PR observation and independent proposal review.
2. Add one controlled pipeline behavior at a time and record baseline gaps.
3. Assess approved shared-workflow exact/near/no-match routing before broad literal conversion.
4. Add a real versioned internal-action catalog, nested dependency checks and approval lifecycle.
5. Add approved repository-arrival manifests, normalized read-only job exports and request IDs.
6. Integrate property lifecycle and a reporting-only inventory refresh without conflating assignment with acceptance.
7. Add a governed App/user token broker, durable queue, bounded wave controls, budget/rate/error stops and operational ownership.
8. Design private runners/registries, OIDC/Vault, artifact provenance, separate sandbox equivalence and cutover only with their accountable owners.

No step implies that another note was ignored or that deferred capabilities are
unnecessary. They require different evidence, authority and acceptance criteria.
