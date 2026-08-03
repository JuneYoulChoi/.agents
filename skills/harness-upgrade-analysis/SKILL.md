---
name: harness-upgrade-analysis
description: Analyze and plan changes to the shared engineering harness before modifying its plan, active skills, registry, routing, gates, sequences, contracts, or adapters. Use for requests to upgrade, extend, replace, deprecate, reorganize, or synchronize the harness, including changes prompted by a new requirement or a missing skill.
---

# Harness Upgrade Analysis

Create a read-only, evidence-based change plan for the harness itself. Preserve
the existing concept, direction, sequence, and contracts by default; prefer a
small extension or wrapper over a broad rewrite. Do not edit files in this
skill.

## Entry gate

Require an intake record from `$intake-and-route`. If it is absent, stop and
return only:

```yaml
upgrade:
  status: not_started
transition:
  next_stage: intake
  next_skill: intake-and-route
  entry_conditions: [intake_record_required]
```

For a request that changes the harness rather than a project, the harness plan
is the architecture baseline. Do not invoke `incoming/`; it is quarantined
input, not an approved source. Do not use network resources unless a separately
approved research task explicitly requires them.

## 1. Establish the authoritative baseline

Read in this order, progressively:

1. `plan/README.md`, then every `plan/*.md` file. Treat this set as the
   normative statement of requirements, concept, direction, sequence, gates,
   contracts, and implementation phases.
2. `registry/active-skills.json` and any referenced registry/taxonomy files.
3. Active skill metadata (`SKILL.md` frontmatter and `agents/openai.yaml`) for
   all entries; read full bodies only for skills affected by the request and
   their immediate route neighbors.
4. Platform adapter, fixture, validator, and task-state files when present.

Record the observed revision/date and paths read. Label every conclusion as
`observed`, `inferred`, or `assumed`. If `plan/` is missing, contradictory, or
not readable, do not invent a baseline: report `blocked` or ask the user which
source should govern the upgrade.

## 2. Compare the request with the baseline

Decompose the request into atomic changes. For each change, identify:

- the preserved concept or contract;
- affected sequence stages, gates, transitions, skills, registry entries,
  adapters, fixtures, and user-facing instructions;
- compatibility and regression risks;
- unresolved user decisions and a reversible safe default, if one exists.

Assign exactly one change class to every relevant path:

`unchanged | patch | extend | wrapper | replace | deprecate | new`.

Use `wrapper` when a new gate can delegate to an existing workflow without
changing its contract. Use `extend` for additive behavior with backward
compatibility. Use `replace` only when the current contract cannot satisfy the
approved requirement; explain migration and rollback. A path that is merely
reviewed remains `unchanged`.

## 3. Produce the upgrade plan

Return this YAML record before any implementation begins:

```yaml
upgrade:
  request: ''
  status: analyzed | needs_user_decision | blocked
  baseline:
    plan_revision: ''
    registry_revision: ''
    skill_revision: ''
    evidence: []
  preserved: []
  affected:
    - path: ''
      change: unchanged | patch | extend | wrapper | replace | deprecate | new
      reason: ''
      risk: low | medium | high
      compatibility: ''
      affected_contracts: []
      affected_fixtures: []
  conflicts: []
  user_decisions_needed: []
  implementation_order: []
  validation_fixtures: []
  rollback_plan: ''
  transition:
    next_stage: clarification | approval | implementation | verification | handoff
    next_skill: ''
    entry_conditions: []
```

`status: needs_user_decision` is mandatory for product direction, policy,
authority, material compatibility, or a change that would alter the existing
sequence. Provide the facts, options, recommendation, impact, and safe default
in the user questions. Do not silently approve the plan.

## 4. Apply the decision gates

- Do not modify `plan/`, active skills, registry, adapters, or fixtures during
  analysis.
- Require explicit user approval of the material upgrade plan before mutation.
- If a core entry gate, transition contract, or registry trust rule changes,
  classify the impact as at least `medium` and include forward-tests for both
  the old and new paths.
- If evidence conflicts, preserve both claims, identify the source-of-truth
  decision, and stop at `clarification` rather than choosing by preference.
- Limit changes to the requested scope. Do not activate quarantined skills or
  download dependencies as part of an upgrade.

## 5. Implementation and validation handoff

After approval, transition to the implementation owner. The owner applies the
plan in the listed order, validates affected fixtures, updates the plan and
registry together, and then invokes `$verify-and-handoff`. If the HTML overview
is stale after the upgrade, transition to `$harness-overview-html` before final
handoff. A completed upgrade must retain the baseline, approved change record,
validation results, residual risks, and rollback plan.

## Example decision

For “add an architecture-document gate to every software request,” the usual
result is a `patch` to intake routing, a `new` architecture skill, and additive
`extend` changes to Greenfield, Brownfield, document, and verification skills.
Do not mark all existing skills `replace` unless the baseline proves their
contracts are incompatible.
