# Authoring observation - 1 October 2026

**Scope:** the newly authored public synthetic demo and its generic index entry.
This record was prepared before the first source push. It is not a cloud-agent
transcript, independent approval, or migration-equivalence result.

The date is the session's Australian local date. The fresh offline preview
recorded its actual UTC timestamp as `2026-09-30T23:55:10.006930+00:00`.

## Current local evidence

| Command/check | Observed result |
| --- | --- |
| `python -m unittest discover -s tests -q` | 64 tests passed; includes four real PowerShell runner subprocess checks and explicitly mocked API/session cases |
| `python scripts\check_repo.py` | Passed required files, local documentation targets, workflow/action-pin contracts, exact source and inactive-output rules |
| `python -m compileall -q issue_agent scripts tests` | Exit 0 |
| actionlint 1.7.12 with `-no-color -shellcheck= -pyflakes=` | Exit 0 for all three active harness workflows; optional shellcheck/pyflakes integrations were not run |
| `python -m issue_agent preview --out out\authoring-preview` | `offline-preview-no-mutations`; no issue, assignment, model or PR |
| Fresh bundle verification | Exact artifact set matched its manifest and every SHA-256 matched actual bytes |
| Parent index unittest suite | 13 tests passed, including publisher privacy/error-path contracts |
| Parent `python scripts\check_index.py` | Index and 19 independent demo entries validated; no publication performed by this check |
| Whitespace checks | `git diff --check` passed for the inspected changes |
| Public-boundary content scan | No matches for the private-context names/paths or credential patterns checked; not a formal security certification |

The shipped Jenkinsfile is 174 bytes with LF line endings. Its SHA-256 is:

```text
dba88eedd823cf62db9136941f91fb37bddd40898e7c1baeef8eb66c5d43a54f
```

The preview's all-zero commit is explicitly a placeholder, not an invented
source revision. The artifact contains zero mutations and zero accepted
migrations out of one synthetic pipeline definition.

## Failures kept in the build story

The first unit run reported 55 tests with one error:

```text
test_checked_in_source_is_exact
issue_agent.contracts.ContractError:
Jenkinsfile is not the exact synthetic Hello World fixture; manual review required
```

The authored working file had 184 bytes and ten CRLF sequences; the contract
expected 174 LF bytes. Adding `.gitattributes` and asking Git to refresh the
index checkout did not initially change those working bytes, so a later
56-test run still failed the same exact check.

The known authored fixture was then formatted to LF. The checker was **not**
changed to normalize arbitrary input. Git reported `i/lf w/lf`, the byte check
passed, and later 60-test then 64-test gates passed.

The initial actionlint command failed because the executable was not installed.
A session-local 1.7.12 archive was downloaded from its official release, verified
against the published SHA-256 and used without modifying global PATH.

An API error test also exposed an unclosed HTTPError response resource; the
client now closes that response while retaining the redacted diagnostic.
Inspection identified that an explicitly false PowerShell consent switch must
not become authorization merely because the argument was present; the runner
guard and regression test cover that case.

## GitHub setup observed before publication

The new target was confirmed as public, personally owned, with issues enabled
and `main` as its default branch. The `issue-agent` environment was created and
its only deployment branch policy was verified as **main / branch**.
No required environment reviewer was added.

The three lifecycle labels were created and `ISSUE_AGENT_ENABLED` was observed
as **false**. No existing CLI credential was exported into a workflow secret.
Repository creation and environment setup are not evidence of a cloud task.

The detailed README build section and all linked guides were authored before
the first content push. Neither original source demo was edited or published.

## Not established by this record

Hosted CI, a narrow user-token installation, live issue assignment, cloud-agent
execution, an agent-authored PR, independent proposal acceptance, runtime
equivalence and cutover are **not established here**. Any later live result must
have its own actual run/session/PR identities and observed status.

The exact committed source revision is provided by this record's Git history;
it was not invented before the initial commit existed.
