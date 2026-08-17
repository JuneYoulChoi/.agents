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

When configuration is affected, verify safe defaults, supported sources and
precedence, invalid/missing/boundary values, compatibility aliases, secret
redaction, and startup/reload/rollback behavior as applicable. Confirm that
tests and examples contain no real secrets or machine-specific production
values.

## 3. Check traceability and documentation

Confirm that material requirements link to tests or explicit waivers, decisions
link to their rationale, and changed behavior has fit-for-purpose documentation
or a recorded reason not to create it. Do not update protected documents without
approval.

## 4. Decide status honestly

Mark `complete` only when all material acceptance criteria have passed or have
valid waivers, no material issue is `open` or `user_decision`, approvals remain
valid, and a durable handoff exists. Otherwise return `active`, `blocked`,
`failed`, or `waiting_user` with the exact next action.

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
  next_stage: handoff | execution | clarification | blocked | failed
  next_skill: ''
  entry_conditions: []
```
