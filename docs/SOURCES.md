# Current sources and observed versions

Retrieved **1 October 2026**. These are rolling pages, not invented release
dates. Preview support and effective account/repository policy must be checked
again before another live demonstration.

## Authoritative procedures

| Source | What was verified |
| --- | --- |
| [Copilot cloud agent API](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api) | User-to-server authentication, suggestedActors availability check, REST issue assignment, target/base/instructions fields and fine-grained token permissions |
| [Issue assignees API](https://docs.github.com/en/rest/issues/assignees#add-assignees-to-an-issue) | Adding an assignee; HTTP success is not enough because unauthorized assignments can be ignored |
| [Triggering a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow) | Issue events from GITHUB_TOKEN generally do not start a second workflow; user/App identities can |
| [Copilot session entry points](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/start-copilot-sessions) | Separate issue, CLI, API and automation entry points |
| [Copilot from GitHub CLI](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-from-cli) | Actual session observation, not local CLI model execution |
| [GitHub CLI v2.93.0 session JSON](https://github.com/cli/cli/blob/v2.93.0/pkg/cmd/agent-task/capi/sessions.go) and [view tests](https://github.com/cli/cli/blob/v2.93.0/pkg/cmd/agent-task/view/view_test.go) | Exact exported field names, single-object view output, and observed state strings used by the read-only observer |
| [Native Copilot Automations](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-automations) | Automations require private/internal repositories; not selected for this public demo |
| [Configure the agent environment](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/customize-the-agent-environment) | Default-branch setup file, exact copilot-setup-steps job name, supported settings and setup-failure caveat |
| [GitHub issue-form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema) | Input/dropdown/checkbox schema; explanatory Markdown is not submitted as issue body |
| [Environment REST API](https://docs.github.com/en/rest/deployments/environments#create-or-update-an-environment) | Main-only environment setup is real configuration, not an implication of its YAML name |
| [Environment branch policy API](https://docs.github.com/en/rest/deployments/branch-policies#create-a-deployment-branch-policy) | Exact main branch policy, distinct from a tag and from a reviewer rule |

Context7's GitHub REST documentation collection was resolved and queried to
cross-check API discovery. The first-party Copilot procedure, not a generic
issues schema alone, documents the preview `agent_assignment` input.

The REST client sends API version **2026-03-10**, as documented by the current
REST pages. The Copilot how-to still shows **2022-11-28** in examples. That
difference is recorded, not silently treated as proof the preview input is a
permanent stable schema. Live results belong in the evidence record.

## Exact action dependencies

Release and tag-to-commit metadata were fetched from the actions' owning
repositories. These pins are for the **public synthetic harness**, not a
customer allow-list or proof of mirrored/vetted dependency content.

| Action | Release date | Full commit |
| --- | --- | --- |
| [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) | 20 July 2026 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| [setup-python v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0) | 20 July 2026 | `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| [upload-artifact v7.0.1](https://github.com/actions/upload-artifact/releases/tag/v7.0.1) | 10 April 2026 | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |

The proposed Hello World workflow has **no action dependencies**. Hosted runner
images and Python servicing releases can still change; the pins do not freeze
the entire environment.

## Authoring and validation tools

Observed locally: GitHub CLI **2.93.0** (its displayed release date is
27 May 2026), Python **3.14.2**, PowerShell **7.6.6**, and
Git **2.55.0.windows.5**. The runtime minimum remains Python 3.11.

Installed `gh` help was read for issue create/edit, agent-task list/view,
repository creation, label creation, variable setting, secret setting/deletion,
and failed-run reruns. In particular, `gh issue create
--assignee @copilot` is supported, but is **not used by the primary demo**:
the user selected the unassigned-issue-opened workflow instead.

[actionlint 1.7.12](https://github.com/rhysd/actionlint/releases/tag/v1.7.12),
released 30 March 2026, was obtained only after the chosen validation command
reported that actionlint was missing. Its Windows AMD64 archive was checked
against the release asset's SHA-256:
`6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9`.
It lives in the authoring session's tools directory, not the repository or
global PATH. The offline runtime has no dependency on it.

The workflow syntax/expression check used `-shellcheck= -pyflakes=` because
those optional integrations were not part of this validation. This is not a
claim that arbitrary shell/Python code was linted by those separate tools.

## Source-reading provenance and limitations

See [Source-context coverage](SOURCE-CONTEXT.md) for the two immutable demo
revisions and complete reading scope. Private notes are not included in this
public repository or the cloud-agent prompt.

One guessed environment-documentation URL returned 404. The documented legacy
URL redirected to the current working procedure linked above, which was read
in full. No source or tool-access failure is converted into a success claim.

No document proves that a particular user has the required entitlement, that a
secret has been installed, that a cloud task ran, or that an enterprise policy
was enforced. Those facts need separate observed evidence.
