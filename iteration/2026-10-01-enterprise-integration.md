# Enterprise design integration - 1 October 2026

**Observed local execution, synthetic inputs, no cloud job submission.**

The user selected a runnable enterprise-design rehearsal rather than
documentation-only integration or a real organization configuration. The
implementation adds local policy/routing and durable admission without
changing the previous issue-to-cloud-agent proof.

## What was integrated and why

The new `enterprise` CLI command and `go.ps1 -Enterprise` use the shipped
synthetic policy and nine request records. They evaluate readiness, ownership,
declared shared-workflow matching, central agent-runner selection and
low-privilege PR execution boundaries.

Eligible work is reserved in a real local SQLite database. Transactions and
unique identities protect against duplicate work, altered intent and queue
overrun. Admitted work receives five separate lane/gate plans, all marked
`not-run`. Read [the design and rationale](../docs/ENTERPRISE-CI-DESIGN.md#runnable-integration-in-this-demo).

This provides an executable architecture lesson without giving a metadata
fixture or approval-shaped boolean authority over a bank environment.

## Fresh capture

The final commands were run in separate Python processes. Times below are
actual report timestamps in UTC.

| Capture | Recorded at | New local items | Queue depth | Admitted / duplicate / manual / blocked / deferred |
| --- | --- | --- | --- | --- |
| [First run](2026-10-01-enterprise/first/enterprise-report.json) | `2026-10-01T02:12:10.028909+00:00` | 2 | 2 | 2 / 1 / 2 / 3 / 1 |
| [Same-ledger replay](2026-10-01-enterprise/replay/enterprise-report.json) | `2026-10-01T02:12:10.501246+00:00` | 0 | 2 | 0 / 3 / 2 / 3 / 1 |
| [One-admission cap](2026-10-01-enterprise/capped/enterprise-report.json) | `2026-10-01T02:12:11.123866+00:00` | 1 | 1 | 1 / 1 / 2 / 3 / 2 |
| [Stop switch](2026-10-01-enterprise/stopped/enterprise-report.json) | `2026-10-01T02:12:11.736785+00:00` | 0 | 0 | 0 / 0 / 2 / 3 / 4 |

All four reports record nine requests for eight pipeline definitions,
`platform_controls_verified=false`, and zero API calls, started cloud tasks,
executed workflows and accepted migrations. The cap and stopped captures each
use fresh, independent ledgers.

Policy/evaluator fingerprint:

```text
3fdd6064f3b6bb40329f89d0ed93b79bb7920e99d106de1366d87f1755635830
```

Request-set fingerprint:

```text
1f9b5f750666dc87037b10bc0da04c1dce8e0877661167ad39903e84674379f3
```

Every capture has `enterprise-report.json`, `enterprise-report.md` and the
original final `bundle-manifest.json`. Hashes and exact file sets were verified
before and after copying to this directory. Mutable SQLite databases were
**not** copied into Git.

These fingerprints bind the local normalized evaluator/contracts and fixture
inputs. They are drift checks, not cryptographic attestations of approval.

## Actual validation

| Check | Observed result |
| --- | --- |
| `python -m unittest discover -s tests -q` | 117 tests passed |
| `python scripts\check_repo.py` | Passed source, active-workflow, fixture, documentation-link and retained-evidence checks |
| `python -m compileall -q issue_agent scripts tests` | Exit 0 |
| Real PowerShell `-Enterprise`, `-MaxNew 1` and `-StopNewWork` runs | Correct local outcomes; no live-mode fallback |
| Separate-process ledger replay | Zero new work; original first-run report unchanged |
| Two-connection synchronized concurrency tests | Same work reserves once; distinct work cannot exceed one configured slot |
| Parent index unittest suite | 13 tests passed |
| Parent inventory/documentation validator | Passed the index and 19 independent demo entries |

The new tests cover malformed/unknown fields, non-synthetic envelopes, shared
lane identifiers, runner escape, unproven automatic CI, manual-approval
limitations, missing owners/consent, incomplete import, changed requests,
changed duplicate intent, overlapping revisions, repository renames, foreign
databases, fingerprint/version mismatch, output containment and stop/limit
behavior.

One additional correctness boundary was made explicit during implementation:
a duplicate request with a new ID cannot change the original route, reviewer
or CI-approval plan. Its work-intent hash must match the existing reservation;
otherwise the decision is blocked with `WORK_INTENT_CHANGED`.

## What was preserved

The live controller, assignment client, issue form, three active workflows,
root Jenkinsfile and previously recorded proof bundles were unchanged.
Only the shared CLI/runner/evidence integration and maintenance contract
were extended for the new offline mode.

Read-only GitHub checks confirmed the live enable switch remained **false**,
the temporary assignment secret remained absent, and migration PR #3 remained
**open, draft and unmerged**. No new paid agent task, runner, environment or
deployment was requested.

The recorded real cloud proof remains at its original source and PR revisions.
This enterprise capture is not a second cloud run, a claim of semantic
shared-workflow assessment, a distributed production queue, or verification
of any bank's actual runner, network, identity or approval configuration.
