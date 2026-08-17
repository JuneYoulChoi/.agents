---
name: brownfield-impact-analysis
description: Establish an evidence-based baseline and change impact before editing an existing codebase, service, API, database, UI, configuration, or operational workflow. Use for Brownfield or Hybrid feature work, bug fixes, refactors, migrations, API changes, dependency changes, performance work, and any request that might affect existing behavior or regression coverage.
---

# Brownfield Impact Analysis

Use this skill before material edits to an existing system. Read and inspect;
do not claim no impact without evidence.

## Entry gate

Require an intake record and an architecture baseline attempt from
`$architecture-baseline-and-design`. Read `docs/architecture/` before code
impact analysis. If its status is `missing`, `stale`, or `conflicted`, use the
code-derived draft and record the gap; do not treat inferred UC, FA, QA, or
module boundaries as approved intent.

## 1. Establish a reproducible baseline

Record the repository path, branch, working-tree status, base commit/version,
build/run/test commands, and initial results. Inspect the current user-visible
behavior, relevant tests, contracts, docs, dependencies, schemas/migrations,
CI, and operational signals.

Detect runtimes, libraries, frameworks, protocols, platforms, simulators,
middleware, build tools, language bindings, generated-code owners, versions,
support windows, and their integration graph. An installed executable or
manifest entry is evidence of presence, not proof that it owns the affected
behavior.

If the system cannot be run, record why. Use code, tests, or observed behavior
as characterization evidence. Do not fabricate a passing baseline.

## 2. Resolve source-of-truth conflicts

Use this default order unless the project defines an override:

```text
user decision
> approved requirement, ADR, or contract
> executable test and observed behavior
> code
> ordinary documentation
> inference
```

Record contradictions as open issues. Ask the user if resolving one requires a
product, compatibility, or authority decision.

## 3. Map impact before choosing a code shape

Identify affected UC, REQ/FR, NFR/QAS, API and data contracts, modules,
dependencies, tests, documents, CI, operational paths, security/privacy risks,
configuration keys/sources/precedence, environment-specific hardcoding,
secret handling, compatibility aliases, and rollback needs. Then decide one of:

- `extend`: an existing boundary remains appropriate;
- `new`: a new boundary is required with limited existing changes;
- `mixed`: both existing and new boundaries must change.

Justify the decision with evidence and alternatives. A request to "just add a
feature" is not evidence that extending the nearest file is correct. If a
baseline cannot be established, set the shape to `undetermined`; do not present
`extend`, `new`, or `mixed` as a final architectural decision.

## 4. Produce an impact record

```yaml
baseline:
  revision: ''
  working_tree: ''
  commands: []
  observed_behavior: []
impact:
  use_cases: []
  requirements: []
  contracts: []
  technologies: []
  language_bindings: []
  configuration: []
  modules: []
  tests: []
  documents: []
  risks: []
decision:
  shape: extend | new | mixed | undetermined
  rationale: ''
  alternatives: []
regression_plan: []
open_points: []
transition:
  next_stage: design | clarification | execution
  next_skill: ''
```

Record this result as one `G3` workflow branch. A Hybrid request may join it
with a bounded Greenfield branch for a genuinely new area. Emit affected
technology, configuration, testing, documentation, security, performance, or
operations concerns as `G4` candidates without loading every concern skill.

## 5. Choose the next action

Route to design when architecture, contract, data, or quality decisions remain.
Route configuration candidates to `$configuration-and-environment-management`
after the current behavior and migration impact are recorded.
Route technology adoption, replacement, upgrade, or specialist integration to
`$technology-selection-and-integration` after the current stack and migration
impact are recorded. Invoke only the affected ecosystem skill, then
`$language-engineering` for changed authored code.
Route to execution only when the change boundary and regression plan are clear.
Route to clarification when impact depends on user intent. Route to
`$verify-and-handoff` after implementation and required documentation updates.
