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

The registry includes `active-skills.json` and the adapter/template provenance
record `adapter-manifest.json`. Their source/tree pins are placeholders until
the bootstrap implementation computes deterministic manifests; placeholders
are not eligible for automatic routing.

Bootstrap source is kept in one place per platform so a rendered project
wrapper never becomes a second policy authority:

```text
.agents/
  adapters/
    codex/AGENTS.md.tmpl
    claude/CLAUDE.md.tmpl
  templates/
    harness.json.example
    harness.schema.json
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
    harness.json        pinned source, adapter, registry, and enforcement
    overrides/           optional, reviewed rules (not loaded by bootstrap MVP)
  AGENTS.md              rendered Codex wrapper (managed, thin)
  CLAUDE.md              rendered Claude wrapper (managed, thin)
```

The installer first accepts an explicit `target_root`; it may use the nearest
Git root only when it is the unique nearest root and no explicit root conflicts;
otherwise it asks. An explicit target must already be an existing directory,
and the current directory must be inside it. Git command errors are not treated
as “no Git”; they block resolution. It canonicalizes symlinks and rejects a
target outside the selected root, an accidental selection of the shared
harness root (identified by its pinned source fingerprint/marker), or a
source/target collision. Git-root discovery is only a path heuristic and never
decides Greenfield/Brownfield.

Installation is a copy by default. A same-hash managed file is idempotent; an
unknown or edited root instruction/config file is preserved and produces a
conflict that requires an explicit upgrade. Wrapper, config, and managed hashes
are written as one atomic transaction with a lock and rollback record. The
installer never truncates a file: rendered UTF-8 content is normalized to LF,
checked against the 32 KiB per-file limit, and rejected if placeholders remain.
Symlinks are allowed only when explicitly approved, contained, and hash-pinned.

The adapter MUST NOT expose `incoming/`. The default state directory is
target-local. A user-level fallback is disabled for the bootstrap MVP; a future
fallback must be an explicit, approved mode with a recorded alternate-root
fingerprint and redaction policy. State files containing sensitive
evidence stay outside Git or are redacted according to project policy. The
default state directory is `<target-project>/.agents/state/`. A `hook`,
`manual`, or `unsupported` enforcement capability is recorded in `harness.json`;
`manual` permits task-state writes and limited reversible workspace edits only
with a valid manual guard, while `unsupported` is ephemeral/read-only and does
not claim cross-session persistence. External, destructive, high-risk,
approval-bypassing, and unsafe state operations remain blocked.

Project `overrides/` are not implicitly trusted or loaded in the bootstrap MVP.
A later release may add a relative, realpath-contained, schema-versioned,
hash-pinned override manifest; until then, an override is ignored or blocks
routing rather than weakening core rules.

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
1. Resolve target_root and load only the pinned bootstrap/config, registry
   metadata, and existing task state.
2. Probe adapter enforcement. If `manual` has no valid manual guard, or the
   capability is `unsupported`, create only an ephemeral run/intake summary;
   do not write task state/events and keep the route read-only until a safe
   guard is recorded. A valid `hook` or `manual_guard` permits the durable
   state contract.
3. Create task_id/run_id and append `intake_started` only when the state-write
   condition from step 2 passes.
4. Classify session_scope, project_state, fields, action, risk, depth.
5. If a material decision is missing, write question.json and enter waiting_user.
6. If software-related, run discovery and the architecture baseline gate before
   impact, design, or mutation.
7. Choose the smallest depth and smallest compatible skill set. When the
   baseline exposes configuration candidates, select the common configuration
   skill and only the detected language reference.
8. If a skill is unavailable, use the core fallback or ask the user.
9. Run the current stage; validate its output contract.
10. Append an event and evaluate the transition guard.
11. Repeat until handoff, blocked, failed, cancelled, or waiting_user.
```

For a harness-maintenance request, keep steps 1–5 (including clarification),
then use this branch:

```text
6. Run `harness-upgrade-analysis` against all `plan/` files, the active
   registry, adapters, templates, and bootstrap configuration; stop before
   mutation at approval or clarification.
7. After approval, apply the bounded change, run its fixtures, refresh the
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
[ ] configuration keys, sources, precedence, hardcoding, secrets, compatibility, and rollback
[ ] extend/new/mixed decision with evidence
```

No material file mutation occurs until the impact record is written.

## Configuration assembly rule

Configuration does not add a state-machine stage. During assembly/design, use
`configuration-and-environment-management` when code or requirements contain
build-, deployment-, runtime-, environment-, or secret-dependent values. The
skill first separates code constants from build/deploy/runtime/secret values,
then defines a typed configuration contract and loads only the applicable
C++, Rust, Java, Python, or common fallback reference.

For Greenfield work, establish sources, precedence, safe defaults, ownership,
validation, secret handling, documentation, and tests before implementing the
affected slice. For Brownfield/Hybrid work, first record current keys,
precedence, behavior, consumers, and migration compatibility. Do not introduce
a new parser/framework without the normal dependency, license, security, and
approval review.

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
