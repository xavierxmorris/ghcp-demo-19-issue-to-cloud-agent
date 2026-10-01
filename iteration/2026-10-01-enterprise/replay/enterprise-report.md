# Enterprise design rehearsal

**Synthetic metadata, local SQLite reservations, no platform execution.**

Status: completed-locally

Runner groups, network isolation, identities and approvals below are fixture assertions,
not verified GitHub or bank configuration. No agent, build or release job ran.

New local work items: 0; queue depth: 2.
Requests: 9; pipeline definitions: 8.
Accepted migrations: 0. Submission limits count local work items, not money or AI credits.

| Request | Decision | Why | Route |
| --- | --- | --- | --- |
| shared-candidate | duplicate | Reuse the original reservation without consuming another queue slot. | shared-workflow-candidate |
| duplicate-same-source | duplicate | Reuse the original reservation without consuming another queue slot. | shared-workflow-candidate |
| near-match | manual-review | A near match needs a workflow owner's decision before admission. | manual-review |
| import-not-ready | blocked | Repository arrival is not proof that the approved import handoff is complete. | none |
| unsafe-auto-ci | blocked | Automatic CI was requested without a complete low-privilege boundary. | none |
| runner-escape | blocked | The request tries to move agent work outside the centrally selected sandbox. | none |
| direct-candidate | duplicate | Reuse the original reservation without consuming another queue slot. | direct-conversion-candidate |
| queue-limit | deferred | The local queue is full; defer rather than overrun its configured capacity. | shared-workflow-candidate |
| opaque-pipeline | manual-review | Opaque pipeline behavior needs an engineer, not an assumed conversion. | manual-review |

## Planned execution lanes

The ledger is mutable local state outside this immutable bundle. Reuse it explicitly
to demonstrate duplicate protection; use a new output directory for every observation.
