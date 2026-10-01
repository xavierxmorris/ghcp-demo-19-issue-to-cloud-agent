# Enterprise design rehearsal

**Synthetic metadata, local SQLite reservations, no platform execution.**

Status: completed-locally

Runner groups, network isolation, identities and approvals below are fixture assertions,
not verified GitHub or bank configuration. No agent, build or release job ran.

New local work items: 1; queue depth: 1.
Requests: 9; pipeline definitions: 8.
Accepted migrations: 0. Submission limits count local work items, not money or AI credits.

| Request | Decision | Why | Route |
| --- | --- | --- | --- |
| shared-candidate | admitted | Eligible under the synthetic policy; reserved locally, not dispatched. | shared-workflow-candidate |
| duplicate-same-source | duplicate | Reuse the original reservation without consuming another queue slot. | shared-workflow-candidate |
| near-match | manual-review | A near match needs a workflow owner's decision before admission. | manual-review |
| import-not-ready | blocked | Repository arrival is not proof that the approved import handoff is complete. | none |
| unsafe-auto-ci | blocked | Automatic CI was requested without a complete low-privilege boundary. | none |
| runner-escape | blocked | The request tries to move agent work outside the centrally selected sandbox. | none |
| direct-candidate | deferred | This invocation reached its local admission allowance. | direct-conversion-candidate |
| queue-limit | deferred | This invocation reached its local admission allowance. | shared-workflow-candidate |
| opaque-pipeline | manual-review | Opaque pipeline behavior needs an engineer, not an assumed conversion. | manual-review |

## Planned execution lanes

### shared-candidate

- agent: demo-agent-sandbox / fixture-agent-zone; gate: validated-intent-and-supported-task-start-identity; **not run**.
- pr-validation: demo-pr-untrusted / fixture-pr-zone; gate: human-workflow-approval; **not run**.
- trusted-build: demo-trusted-build / fixture-build-zone; gate: independent-review-and-protected-source; **not run**.
- release-nonprod: demo-release-nonprod / fixture-nonprod-zone; gate: identified-artifact-and-nonprod-authorization; **not run**.
- release-prod: demo-release-prod / fixture-prod-zone; gate: independent-production-approval-and-scoped-identity; **not run**.

The ledger is mutable local state outside this immutable bundle. Reuse it explicitly
to demonstrate duplicate protection; use a new output directory for every observation.
