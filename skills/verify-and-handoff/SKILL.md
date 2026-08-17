---
name: verify-and-handoff
description: Verify that a software, design, documentation, or operational task meets its agreed acceptance criteria, record missing checks and residual risk, synchronize traceability and documents, and prepare a durable handoff. Use before claiming completion, after implementation or review, when resuming a task, or when handing work to another session or agent.
---

# Verify and Handoff

Use this skill before declaring a task complete. Verification is evidence, not a
summary of intent.

## Entry gate

Require the intake record, task acceptance contract, and applicable architecture
record. For software work, inspect `docs/architecture/` and check that changed
UC, FA, QA/QAS, HLD, LLD, ADR, views, and diagrams are synchronized or have an
explicit documented waiver. If the architecture baseline is conflicted or a
material boundary is still unconfirmed, do not mark the task complete.

## 1. Pin the target and acceptance contract

Record the artifact revision, requirements, acceptance criteria, expected
checks, environment, and any authorized waivers. Re-open planning or impact
analysis if the implemented result differs materially from the approved intent.

## 2. Run and record checks

For every required check, record command or method, expected result, actual
result, environment/tool version, artifact revision, verifier, and one status:

```text
passed | failed | not_run | not_applicable | blocked | waived
```

`not_run` never means `passed`. A waiver requires an authorized owner, reason,
expiry, and residual risk. For Brownfield work, include relevant regression
checks. For API, data, security, migration, or operational changes, include the
applicable contract, rollback, or post-change checks.

When a technology ecosystem or implementation language is affected, verify the
selected `TECH-*` and `IMPL-*` artifacts: purpose and version/binding evidence,
integration/compatibility edges, required specialist skill result, generated
vs authored ownership, ecosystem-specific checks, language build/lint/test
profile, configuration contracts, and architecture/document synchronization.
Confirm that unrelated ecosystem/language skills were not treated as required
and that popularity did not grant adoption authority.

When configuration is affected, verify safe defaults, supported sources and
precedence, invalid/missing/boundary values, compatibility aliases, secret
redaction, and startup/reload/rollback behavior as applicable. Confirm that
tests and examples contain no real secrets or machine-specific production
values. When a configuration tool or dependency changed, verify the recorded
functional category, popularity-evidence source/window, maintenance, license,
security, compatibility, migration, and approval decision; popularity alone is
not a passing result.

## 3. Check traceability and documentation

Confirm that material requirements link to tests or explicit waivers, decisions
link to their rationale, and changed behavior has fit-for-purpose documentation
or a recorded reason not to create it. Do not update protected documents without
approval.

Use `REQ/QAS -> ADR -> TECH -> IMPL -> CONFIG -> TASK -> TEST -> DOC` for
material technology work, omitting only non-applicable entities with an
explicit compact trace or waiver appropriate to depth.

## 4. Decide status honestly

Mark `complete` only when all material acceptance criteria have passed or have
valid waivers, no material issue is `open` or `user_decision`, approvals remain
valid, and a durable handoff exists. Otherwise return `active`, `blocked`,
`failed`, or `waiting_user` with the exact next action.

When a check fails or new evidence invalidates an earlier output, act as gate
`G7` and emit one bounded backward feedback record. Target the nearest
responsible gate: guard/capability `G0`, intent `G1`, baseline/architecture
`G2`, workflow/impact `G3`, cross-cutting concern `G4`, ecosystem/language
`G5`, or implementation/assembly `G6`. Include expected/actual evidence,
invalidated and preserved artifact IDs, and attempt count. Never broadcast to
every gate, mutate an immutable prior result, or change user-owned intent or an
accepted decision. Escalate after three unresolved material attempts.

## 5. Write the handoff

```markdown
# Task handoff

## Goal and current status
## Changed artifacts
## Evidence and validation results
## Trace links and document status
## Assumptions, waivers, and residual risks
## Open decisions or blockers
## Next action and how to resume
```

Return a concise completion report that distinguishes completed work, checks
not run, waivers, and residual risk. Never conceal an unavailable verification
behind a success statement.

## Exit transition

Always return an explicit transition:

```yaml
transition:
  next_stage: handoff | execution | clarification | backward_feedback | blocked | failed
  next_skill: ''
  entry_conditions: []
```
