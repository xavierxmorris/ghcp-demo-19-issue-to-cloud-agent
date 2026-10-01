# Repository guidance

Follow AGENTS.md. A cloud-agent migration request permits only the two inactive
files named in docs\ACCEPTANCE.md; the existing harness is not migration output.
Read-only inspection and the documented offline checks are permitted.

Preserve identity separation, exact source identity, strict issue-form parsing,
owner-only intake, bounded reads, explicit failures, durable start markers,
and the distinction between assignment, agent execution, PR creation, validation,
human acceptance, and cutover. A green check is not migration completion.

Do not modify validators or source to accommodate an agent-generated draft.
No private reference material or customer data belongs in this public repo.

The enterprise mode is a separate offline rehearsal using shipped metadata and
a local SQLite admission ledger. It must not call cloud clients, start jobs,
or treat synthetic declarations as verified platform authority. Explain route
and lane decisions, retain deferred/blocked items and leave production
integration behind its own approval and validation boundary.
