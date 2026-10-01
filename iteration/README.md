# Recorded evidence, not a replay disguised as live execution

This directory contains only deliberately curated, synthetic observations.
It never contains tokens, private source notes, raw customer exports or an
invented model transcript.

The repository's implementation is not itself proof that a cloud task ran.
Local/hosted validation and live issue/session/PR observations are recorded
separately, with exact revisions and links when available.

The [authoring observation](2026-10-01-authoring.md) records the actual local
checks, first-run failures and fixes, fresh preview, and initial disabled setup.

The [live proof](2026-10-01-live-proof.md) records the real unassigned issue,
successful assignment, completed task/session, inactive draft PR, no-op rerun,
observer failure and fix, hosted CI approval boundary, and credential cleanup.
Five complete token-free bundles preserve both failed and successful evidence.
No migration acceptance, merge, activation or cutover is claimed.

The [enterprise integration observation](2026-10-01-enterprise-integration.md)
records the executable offline design: actual local admission, durable replay,
reduced limits and stop behavior. Four complete sealed snapshots show what
ran locally; mutable queue databases stay outside Git. Planned bank execution
lanes and platform controls were not executed or verified.

Fresh attempt bundles go under ignored `out`, with a final integrity manifest.
Copy only reviewed, token-free facts here. `check_repo.py` verifies retained
bundle hashes and exact artifact sets. The cloud workflow's artifact
retention is seven days; an issue or label is not a permanent audit archive.
