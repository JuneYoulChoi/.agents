# Implementation guide for the universal harness

This document is written for the first implementer. It assumes ordinary
software development experience and limited agent-harness experience. The
implementer must not need to infer missing behavior from the industry links.
Read in this order:

1. [00-operating-model.md](00-operating-model.md) for purpose and principles.
2. [03-contracts-and-fixtures.md](03-contracts-and-fixtures.md) for exact data,
   state, and tests.
3. This guide for the build order and algorithms.
4. [04-user-guide.md](04-user-guide.md) to verify that the result is usable by
   an ordinary developer.

## Normative language

- **MUST**: implement and validate; a violation blocks promotion.
- **SHOULD**: implement unless a documented platform limitation applies.
- **MAY**: optional improvement; it must not be required by the MVP.

## What is being built

The harness has eight layers. Each layer may depend only on layers below it.

```text
L0 Safety and authority guards
L1 Portable contracts (JSON state, events, manifests, traceability)
L2 Router and state machine
L3 Workflow recipes (general intake, Greenfield, Brownfield, documents)
L4 Specialist skills (progressively loaded and wrapped)
L5 Optional delegates and evaluator (Deep mode)
L6 Codex and Claude platform adapters
L7 Fixtures, observability, governance, and release tooling
```

The first release implements L0–L3 with one Router. L4 is added only after the
basic workflows pass. L5 is optional and never a prerequisite for a safe,
single-agent task.

Harness maintenance is a control-plane workflow rather than a replacement for
L3/L4 project workflows. Intake routes a harness change to
`harness-upgrade-analysis`, which reads `plan/` and emits a read-only impact and
approval plan. Only after approval may the implementation owner change active
skills, registry, contracts, or adapters. `harness-overview-html` then publishes
the derived HTML guide and `$verify-and-handoff` verifies the pinned source
revision. A normal project task never needs this path merely because it uses a
skill.

## Reference implementation and dependency boundary

The reference implementation is a local, file-based harness using Python 3.11+
standard-library scripts only. It does not require a server, database, network,
third-party package, cloud account, or MCP server. JSON is the canonical machine
format; NDJSON is the append-only event format. Markdown is the human-facing
format. YAML examples in other plan files are explanatory only.

If a platform can perform the Router and persistence itself, its adapter may
replace the Python scripts, but it MUST produce the same JSON state, event, and
fixture results. If Python is unavailable, a manual adapter may follow the same
contracts, but it is not considered an automated implementation.

## Directory contract

The library repository (this repository) contains reusable source:

```text
.agents/
  plan/                 design and implementation specification
  skills/               approved active skills only
  incoming/             quarantined source candidates; never resolvable
  registry/             provenance, manifest index, and promotion records
  adapters/             Codex and Claude entrypoints
  templates/            copyable state, decision, action, and handoff files
  scripts/              standard-library validators and fixture runner
```

When the library is used by a target project, project state is kept in the
target project and not mixed into the library repository:

```text
target-project/
  .agents/
    state/TASK-<id>/
      state.json
      events.ndjson
      handoff.md
      artifacts.json
    overrides/           optional project taxonomy/source-of-truth rules
```

The adapter MAY symlink or copy approved `skills/`, but it MUST NOT expose
`incoming/`. State files containing sensitive evidence stay outside Git or are
redacted according to the project policy. The default state directory is
`<target-project>/.agents/state/`; a user-level directory is the fallback for
tasks that cannot be stored in the repository.

## Stage contracts

Every stage has one input snapshot, one output record, a completion guard, and a
fallback. The Router writes the output before transitioning.

| Stage | Input | Output | Completion guard | Fallback |
| --- | --- | --- | --- | --- |
| `intake` | user request and available project context | `classification.json`, `intent.json` | scope, field, action, risk, and depth have values plus confidence/evidence | `Unknown` + discovery-only or user question |
| `clarification` | open decision points | `question.json` or recorded answer | every material question is answered, accepted as assumption, or assigned to user | `waiting_user` |
| `discovery` | project path and classification | `baseline.json`, evidence entries | relevant source-of-truth, current behavior, and run/test instructions recorded | `blocked` with missing-access reason |
| `architecture` | intake plus project baseline | architecture status and artifact record | `docs/architecture/` assessed; required UC/FA/QA/module decisions confirmed or explicitly draft | user question, code-derived draft, or architecture block |
| `impact` | baseline and intended change | `impact.json`, document-gap list | affected requirements, contracts, modules, tests, docs, and risks recorded | ask user if scope cannot be bounded |
| `assembly` | classification and impact | selected skill IDs, depth, delegate plan | minimal compatible skills and fallback are selected | core procedure without specialist skill |
| `deliberation` | bounded questions and evidence snapshot | issue ledger and recommendation | every material issue has an allowed terminal status | user decision after budget |
| `design` | intent, impact, recommendations | ADRs, tasks, acceptance contract, trace links | implementation slice and verification are explicit | return to clarification |
| `execution` | accepted slice contract | code/docs/config changes and command log | requested changes are applied within scope | rollback, block, or return to impact |
| `verification` | pinned artifact revision and acceptance contract | validation records and residual-risk record | all required checks pass or have authorized waivers | failed/blocked; never silently complete |
| `handoff` | final state and artifacts | `handoff.md`, final state, next action | no material open issue and durable evidence exists | remain active or blocked |

For non-software scope, `intake` and `clarification` still run, but the Router
selects a general-information, decision-support, or creative workflow. It does
not create code, Brownfield analysis, ADRs, or software trace links by default.

## Router algorithm

The first Router may be implemented as a command or as a skill-backed prompt,
but it MUST follow this order:

```text
1. Load only global rules, registry metadata, and existing task state.
2. Create task_id/run_id; append an intake_started event.
3. Classify session_scope, project_state, fields, action, risk, depth.
4. If a material decision is missing, write question.json and enter waiting_user.
5. If software-related, run discovery and the architecture baseline gate before
   impact, design, or mutation.
6. Choose the smallest depth and smallest compatible skill set.
7. If a skill is unavailable, use the core fallback or ask the user.
8. Run the current stage; validate its output contract.
9. Append an event and evaluate the transition guard.
10. Repeat until handoff, blocked, failed, cancelled, or waiting_user.
```

For a harness-maintenance request, replace step 5 with:

```text
5. Run `harness-upgrade-analysis` against all `plan/` files and the active
   registry; stop before mutation at approval or clarification.
6. After approval, apply the bounded change, run its fixtures, refresh the
   optional HTML overview, and continue through verification and handoff.
```

Routing tie-breakers are deterministic: lower risk, fewer skills, no delegate,
and local/read-only tools win when they satisfy the same acceptance criteria.
The Router never resolves a skill from `incoming/`, a deprecated skill, or a
manifest with a failed integrity check.

## Clarification question template

The Router asks no more than three related questions in one turn. Each question
has a stable ID and is stored with the answer, actor, and timestamp.

```text
Decision needed: <one sentence>
Known facts: <observed facts and sources>
Choice A: <meaning and impact>
Choice B: <meaning and impact>
Recommendation: <proposal, clearly labelled>
Safe default if you do not choose: <reversible behavior or stop>
```

Silence is not consent. A missing answer leaves the task in `waiting_user` or
uses only a previously recorded, still-valid approval.

## Depth and artifact defaults

| Depth | Required artifacts | Delegates |
| --- | --- | --- |
| `light` | intent, classification, changed files, validation result, short handoff | none by default |
| `standard` | light artifacts plus impact, task, acceptance tests, trace links, document update decision | one focused reviewer only when useful |
| `deep` | standard artifacts plus alternatives, NFR/QAS, ADR, issue ledger, independent evaluator, rollback/operational plan | selective and isolated |

“Material work” means a change to behavior, public contract, data, security,
operations, user-facing documentation, or a decision that is costly to reverse.
“Reversible” means the prior state can be restored with a recorded action and
without losing data or authority.

## Brownfield minimum checklist

Before changing an existing project, record:

```text
[ ] repository path, branch, and working-tree status
[ ] base commit or immutable version
[ ] build/run/test commands and their initial results
[ ] current user-visible behavior or characterization evidence
[ ] source-of-truth hierarchy and conflicts
[ ] affected UC, REQ/FR, NFR/QAS, API/data contracts
[ ] affected modules, tests, docs, CI, and operational paths
[ ] dependency, schema, migration, security, and performance signals
[ ] extend/new/mixed decision with evidence
```

No material file mutation occurs until the impact record is written.

## Failure and recovery defaults

| Failure | Default |
| --- | --- |
| malformed state or manifest | `failed`, report path and repair command; do not overwrite |
| missing skill/tool | core fallback, then `waiting_user` if acceptance cannot be met |
| timeout | record partial result; retry once if transient and within budget |
| conflicting evidence | preserve both, run targeted discovery, then ask user if unresolved |
| delegate crash | continue without it only if join condition still passes; otherwise block |
| concurrent state write | optimistic revision conflict; reload and merge or stop |
| unauthorized action | refuse, append action event, create approval request |
| verification unavailable | `blocked` or authorized `waived`; never mark `passed` |
| new scope discovered | invalidate affected plan/acceptance and return to impact |

## Definition of implementable

Before promotion, a new implementer must be able to answer from these plan files:

1. Which files are created and where?
2. What enters and leaves each stage?
3. When does the Router ask the user?
4. How is a skill selected, rejected, or replaced?
5. Where do state, events, evidence, and handoff live?
6. What exactly makes a task complete?
7. How are unauthorized actions refused?
8. How are fixtures run and judged?
9. How can an ordinary developer resume or stop a task?

If any answer requires guessing, the relevant contract or guide is incomplete.
