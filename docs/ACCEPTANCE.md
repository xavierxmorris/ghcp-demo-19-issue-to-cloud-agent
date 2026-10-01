# Acceptance: four different outcomes

This is a trigger experiment, not a migration-quality benchmark. The output
grammar is deliberately specified so an agent can concentrate on the real
issue-to-cloud-to-PR path. Copying that tiny grammar is not evidence of general
Jenkins conversion capability.

## 1. Trigger accepted

One owner-created, unassigned issue contains the exact synthetic form, current
`main` commit and explicit consent. Its `issues: opened` workflow validates the
request, records start intent, and confirms Copilot in the assignment response.

Evidence: issue URL, controller run URL/revision, source commit/SHA-256, exact
assignment request, and mutation ledger. A successful assignment is not yet
evidence of agent execution.

## 2. Agent execution observed

Observe the linked PR and actual cloud-agent session ID/state. Retain a failure
or waiting state as such. Record the model only if the platform exposes it; this
controller neither selects a model nor infers which default was used.

Evidence: task/session ID, observed state/timestamps, PR URL and head commit.
Do not replace the agent's result with a locally authored PR to make this pass.

## 3. Proposal passes this tiny contract

Read the root `Jenkinsfile` at the issue source commit. Never run it.
Add exactly these two files and no others.

### Inactive workflow

`drafts\hello-world.yml.draft` must use this closed grammar. Blank lines and
standalone comments are allowed; other YAML is rejected:

```yaml
name: Synthetic Hello World
on:
  workflow_dispatch:
permissions: {}
jobs:
  hello:
    runs-on: ubuntu-24.04
    timeout-minutes: 2
    steps:
      - name: Greeting
        run: echo 'Hello from the issue-driven demo'
```

The controller/validator does not generate this file. The test suite contains
an explicitly labeled expected fixture, not a saved agent output.

This is a small exact-shape validator, not a general YAML parser, Groovy parser,
approved enterprise workflow catalog, or arbitrary command sanitizer. Its zero
`uses` policy also rejects local/internal, nested, dynamic, and reusable-workflow
references. A new supported pattern needs new policy and independent tests,
not a broader regex to make a model answer pass.

### Review packet

`drafts\review.md` must have all of these headings:

```text
## Source
## Behavior mapping
## Deliberate changes
## Unknowns
## Validation
## Human decision
```

Under Source, use the exact line `Source commit: <40-character issue commit>`,
record `Jenkinsfile` and its SHA-256, and link the requesting issue.
Under Behavior mapping, account for the source agent, stage, greeting, and
absence of source-defined triggers. Separate preserved intent from redesign.

Explicitly identify the hosted runner, two-minute timeout and manual dispatch
as deliberate choices, not inferred parity. Retain unknown external Jenkins
job settings, image/tooling and scheduling behavior. Do not invent secrets,
libraries, artifacts, or tests in this tiny source.

Run:

```powershell
python -m unittest discover -s tests -v
python scripts\check_repo.py --require-draft
```

Record the actual commands and results. State that Jenkins and the proposed
workflow were **not executed**. Static acceptance does not establish runtime
equivalence. On a Copilot PR, CI also compares changed paths against its base
commit: only the two new proposal files are permitted, and the packet must name
that reviewed source commit.

## 4. Human acceptance remains separate

An independent reviewer reads source, issue, session, exact PR revision, checks,
mapping and gaps. They can reject an otherwise grammar-valid draft.
Required review/branch protection must be configured and verified on GitHub;
instructions alone do not establish it.

No command in this demo accepts or merges the migration. Do not activate the
draft, execute it, approve the PR as the agent, deploy, or retire Jenkins.
The reporting denominator is **one synthetic pipeline definition**, with
**zero accepted migrations** until a separately governed decision occurs.
