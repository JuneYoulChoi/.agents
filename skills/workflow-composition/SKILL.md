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

For material multi-step work, load the
[compact task contract](references/task-contract.md) and reuse the current
requirements/acceptance record. Keep ordinary local work compact; do not add
a second planner, automatic reviewer or upstream execution chain.

## Actively assess expertise, then choose bounded roles

At intake and each current skill, reconsider delegation when evidence exposes
independent unknowns, conflicting explanations, distinct specialist boundaries,
or a verification risk shared by the producer and its tests. Do not wait for
the user to ask for a team. For such a trigger, record the concrete question,
expected additional evidence, and dispatch or a specific fallback reason in
the existing task/skill result. Reuse current authority; a trigger does not
grant it. Small clear work needs no separate assessment artifact.

Use a focused worker when the question is independent and current authority,
capability and expected quality or time benefit justify its context/join cost.
Otherwise perform the bounded check serially and state why for a material
trigger. Field count, depth and persona names alone are not benefit evidence.
G1 assessment is adapter-owned read-only reasoning before the structured intake;
the Runner skips intake and does not execute G1 work units. Never bind units to
that skipped owner. G2 onward uses current-skill preparation and checked joins.

Keep one small coherent slice (including ordinary greeting/calendar CRUD), a
local fix or a text change on one agent; leave `delegation.requested` false.
Several fields or persona labels alone do not justify splitting. Delegate only
bounded independent investigations, work with settled contracts and exclusive
ownership, or an explicitly needed independent review/test. Explain the benefit
against sequential work in the existing benefit evidence; merge duplicate checks.
Do not infer token savings from parallel execution or invent usage counters.

Keep clear local work on one agent. For independent work, define bounded units with goal,
input revision, dependencies, read/write paths, shared resources, evidence,
allowed tools, output and acceptance. Personas are responsibilities:
analyst, designer, implementer, reviewer, verifier, documenter. A single agent
may perform several roles sequentially. A simplicity reviewer checks justified
complexity; it must preserve required ownership, error and lifecycle boundaries.

Pair a domain responsibility with an optional `reasoning_lens` when a distinct
question warrants it; do not create duplicate workers solely to fill both rows:

| Lens | Required contribution |
| --- | --- |
| `meticulous` (꼼꼼한 똑똑함) | Missing requirements, counterexamples and relevant boundary failures, with evidence and unresolved decisions |
| `minimal_sufficient` (게으른 똑똑함) | Least redundant sufficient path, reusable evidence, removable optional work and stopping conditions; all acceptance and required checks preserved |

These lenses complement analyst/designer/reviewer and other roles; they neither
select a model nor change reasoning effort or authority. At join, compare new
supported findings, shared evidence and justified disagreement. Resolve by
evidence, not vote count. Do not repeat equivalent reviews after acceptance.

Request parallel execution only when evidence supports a quality or time benefit
that justifies coordination cost,
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

For declared units, follow [native work receipts](references/native-work.md):
bind owners and only needed skill references, clamp to observed worker capacity,
prepare a focused packet with the current skill instructions and role, and record
verified terminal results. Parallel batches must share the current skill owner.

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
authority or capabilities. Retain every prepared unit unchanged with a completed
receipt; refine only unprepared future units and preserve owner/dependency order.
Failed work needs responsible-gate recovery. A change to intent, work type or authority goes back
through the responsible routing gate instead.

```yaml
transition:
  next_stage: assembly | clarification | backward_feedback
  next_skill: ''
  entry_conditions: [bounded_work_plan_recorded]
```

Check dependency owners against serial skill order before dispatch: a unit cannot
wait for a later skill. Supply compact hashed context_artifacts for prerequisite
decisions and evidence. Mandatory registry references are added automatically;
select only evidenced conditional references. Use concrete acceptance evidence
for completion as specified by the native-work contract.
