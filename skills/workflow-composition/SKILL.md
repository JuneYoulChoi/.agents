---
name: workflow-composition
description: Compose a bounded delivery path after baseline and impact analysis, including task dependencies, persona responsibilities, skill and tool needs, and conditional parallel work. Use for project workflows and documentation; keep small work single-agent and never treat a work plan as execution permission.
---

# Workflow Composition

This is the final G3 assembly step, after applicable Greenfield/Brownfield and
document-purpose outputs. It does not replace G4–G7 or create another router.
Require the classified intent, baseline, acceptance criteria and current
authority/capability evidence. If these change, return to their owning gate.

## Compose the smallest sufficient path

Use `work_type` to describe the outcome: standard, bugfix, feature, refactor,
research, document, or infrastructure. Harness maintenance stays with
`harness-upgrade-analysis`. Apply the route's `work_plan` as a proposed work
outline, not a bypass for any G0–G7 check. See the canonical
[workflow contract](../../plan/08-layered-workflow.md) for inputs and mapping.

- A bugfix needs reproduction or equivalent observed evidence and regression
  proof; it does not automatically need a new architecture design.
- A feature needs confirmed contracts and a smallest useful integrated slice.
- Refactoring needs behavioral invariants and evidenced structural friction.
- Research and documents need sources and claim checks; do not create code tasks.
- Infrastructure needs configuration, rollback and existing action authority.

Record included work, omitted optional procedure with reasons, verification and
document effects. Reuse current baseline and test evidence only for matching
artifact revisions, conditions and scope. A small task may use one compact
record. Reducing documents never weakens quality, SOLID/GRASP where applicable,
security, architecture applicability or the acceptance contract.

## Choose roles only after dependencies

Default to one agent. For independent work, define bounded units with goal,
input revision, dependencies, read/write paths, shared resources, evidence,
allowed tools, output and acceptance. Personas are responsibilities:
analyst, designer, implementer, reviewer, verifier, documenter. A single agent
may perform several roles sequentially. A simplicity reviewer checks justified
complexity; it must preserve required ownership, error and lifecycle boundaries.

Request parallel execution only when evidence supports a net time benefit,
native capability is available, delegation is authorized and a bounded worker
limit/timeout exists. Never derive a team size from depth or field count alone.
Serialize shared files, databases, hardware and other shared resources; split
contracts first when implementation depends on them. Use isolated worktrees or
verified exclusive path ownership for writers. Recheck realpath/symlink scope
and tool permissions at dispatch; the planner's lexical checks are insufficient.

Use fresh focused context, not the entire conversation. Preserve requirements,
constraints, assumptions, uncertainty and evidence in concise reports. A role
name cannot create a missing tool or permission. No recursive delegation unless
the coordinator's explicit scope/budget permits it. The reference Runner stays
serial; native adapters may execute approved units within a current skill and
must join them before submitting one skill result. No adapter capability means
sequential work, not an invented multi-agent success.

## Join and hand off

Require every required result to match its input snapshot, scope and acceptance.
Reject stale or out-of-scope output. On timeout, retain valid results, cancel
dependent work, and retry only within budget or continue serially. Do not accept
partial work as full completion. Integrate once and verify the integrated
revision. Resolve disagreements by evidence; retain user-owned decisions.

Return a `WORK-*` artifact containing the chosen path, unit plan, activation
rationale, omissions, capability/authority checks, join/timeout/fallback rules
and tool requirements. G4/G5 resolve the approved specialist skills; G6 binds
available tools and executes. This skill never loads `incoming` or executes
downloaded scripts. Stop optional expansion once acceptance evidence is complete.

When baseline/impact evidence refines provisional intake units, submit
`workflow_update: {"work_units": [...]}` with the completed result and its
artifact/evidence IDs. The Runner recomputes the plan without changing existing
authority or capabilities. A change to intent, work type or authority goes back
through the responsible routing gate instead.

```yaml
transition:
  next_stage: assembly | clarification | backward_feedback
  next_skill: ''
  entry_conditions: [bounded_work_plan_recorded]
```
