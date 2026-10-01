# Prompts and the actual cloud task

These are task/review contracts, not fabricated transcripts. The exact
assignment request for an attempt is saved as `assignment-request.json` in its
bundle. No credential or private source note belongs in that payload.

## Baseline cloud task

The implementation builds a fixed `custom_instructions` value from
`issue_agent\contracts.py`, using the selected repository, source commit and
fixture hash. It requires the built-in cloud agent to:

1. read README, AGENTS and the acceptance contract;
2. inspect only the known Jenkinsfile as data;
3. add the two inactive proposal files;
4. record source identity, behavior mapping, deliberate changes and unknowns;
5. run the documented offline checks and retain actual results;
6. open a reviewable linked PR without changing policy, activating, merging,
   approving, deploying or retiring Jenkins.

No custom agent or model override is sent. Do not claim a specific model unless
the actual session exposes it.

## Explain the implementation

> Read README's build walkthrough and trace the issue-opened path through
> contracts.py, service.py, github_api.py and the workflow. Identify the first
> durable mutation and the non-idempotent boundary. Explain why assignment,
> execution, a PR, validation and human acceptance are different facts.
> Do not call GitHub or start another task.

## Review the real proposal

> Read the requesting issue, pinned synthetic Jenkinsfile, actual session record,
> complete PR diff and checks. Map every observed source behavior to the draft
> or an explicit gap. Identify deliberate runner/timeout/trigger choices.
> Confirm only the two allowed proposal files were added and the workflow is
> inactive with zero action dependencies. Preserve disagreements and failures.
> Do not execute the source/draft, change the validator, approve or merge.

## Propose the next bounded experiment

> Using this actual baseline and the source-context coverage map, choose one
> added behavior for a separate experiment. State the source/target evidence,
> permissions, deterministic policy, independent oracle, failure case and human
> owner it would need. Prefer approved shared-workflow assessment before scaling
> literal conversion. Do not implement portfolio discovery, production secrets,
> a dashboard application or a wave controller without a separate scope.

## Explain the executable enterprise design

> Read the README enterprise track, the integrated design rationale, both
> enterprise fixtures, enterprise.py and enterprise_ledger.py. Predict all
> nine route decisions before running the offline command. Explain the
> difference between local admission, modeled trust-lane requirements and
> actual platform enforcement. Run the same requests twice with one explicit
> local ledger and new report directories. Show why replay adds zero work.
> Do not call GitHub, execute any planned lane, change live settings or claim
> the fixture's approvals are authenticated.

## Challenge a bank CI boundary without starting a job

> In a disposable exercise copy, add one negative synthetic case for automatic
> PR CI, runner placement, request identity or overlapping pipeline revisions.
> State the expected refusal independently, add the regression test and make
> the smallest change only if the implementation violates its existing
> contract. Preserve the original live proof and sealed evidence. Do not weaken
> a policy to accept a risk or turn a declared group name into a claim that
> bank isolation has been configured.
