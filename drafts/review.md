## Source

Source commit: cc2ce2f21397f45c4b38fad704378152408521a8

- Source file: `Jenkinsfile`
- Source SHA-256: `dba88eedd823cf62db9136941f91fb37bddd40898e7c1baeef8eb66c5d43a54f`
- Requesting issue: https://github.com/xavierxmorris/ghcp-demo-19-issue-to-cloud-agent/issues/2

The source was read as data at the pinned issue commit. Jenkins and source shell
commands were not executed.

## Behavior mapping

| Source behavior | Draft treatment |
| --- | --- |
| `agent any` | Preserved as a hosted `ubuntu-24.04` runner choice for this draft. |
| `stage('Greeting')` | Preserved as the single `hello` job and `Greeting` step. |
| `echo 'Hello from the issue-driven demo'` | Preserved exactly as the step command. |
| No source-defined triggers | Deliberately represented by manual `workflow_dispatch` only. |

The source defines one agent, one stage, and one greeting. It contains no
parameters, credentials, artifacts, tests, publishing, deployment, or other
pipeline behavior to map.

## Deliberate changes

- The proposed workflow is inactive because it remains under `drafts/` with a
  `.draft` suffix; it is not an active workflow.
- `ubuntu-24.04` is an intentional hosted-runner choice, not inferred parity
  with Jenkins.
- A two-minute timeout is an intentional bound for this synthetic greeting,
  not a source setting.
- Manual dispatch is an intentional safety boundary because the source defines
  no trigger.
- The draft has no `uses` references, credentials, secrets, reusable workflows,
  publishing, deployment, or automatic activation.

## Unknowns

The Jenkinsfile does not identify the external Jenkins job name or settings,
executor configuration, queue behavior, scheduling, workspace policy,
environment variables, installed image/tooling, plugins, shared libraries,
retention, notifications, or access controls. These remain unknown and were
not invented. Runtime behavior, hosted-runner parity, and scheduling behavior
are not established by this draft.

## Validation

Checks actually run:

- `python -m unittest discover -s tests -v` — passed.
- `python scripts\check_repo.py --require-draft` — passed.

The root `Jenkinsfile` and the proposed workflow were **not executed**. These
static checks confirm the narrow proposal grammar and repository contracts;
they do not establish runtime equivalence.

## Human decision

This is an inactive proposal only. An independent human reviewer must inspect
the source, requesting issue, source identity and hash, agent/session evidence,
PR revision, behavior mapping, validation results, and unknowns before any
acceptance decision. The agent must not approve or merge this PR, activate the
draft, deploy it, retire Jenkins, or claim behavioral equivalence.
