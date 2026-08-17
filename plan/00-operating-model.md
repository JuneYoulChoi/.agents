# Universal engineering harness: target operating model

## Purpose

Build a project-independent, shared skill library and lightweight task harness
for Codex and Claude. Every session first classifies its scope and request,
discovers only the skills it needs, retains traceability from intent to
evidence, and stops for user direction when a material decision is not grounded
in the request or project evidence. All sessions receive the intake gate; the
full Greenfield/Brownfield software lifecycle applies only to software-related
scope.

This directory is the design record. `incoming/` is source quarantine; only
reviewed and adapted skills may be promoted to `skills/`.

## Non-negotiable global rules

1. **Intent before execution.** Confirm or reliably derive the goal, success
   criteria, constraints, audience, and concept/direction. Never convert a
   material assumption into a decision. A clear, small, reversible request may
   proceed with its interpretation recorded rather than waiting for ceremony.
2. **Ask on ambiguity or an uncovered domain.** State the known facts, the
   decision needed, options, recommendation, and impact; wait for the user when
   the decision is value-based or materially changes scope.
3. **Classify project state.** Identify Greenfield, Brownfield, Hybrid, or
   Unknown before choosing a workflow.
4. **Evidence before claims.** Mark statements as observed, inferred, or
   assumed. In Brownfield work, inspect the relevant code, tests, contracts,
   and docs before claiming impact is absent.
5. **Protect scope and authority.** Do not mix unrelated changes. Confirm
   external actions, deployment, data mutation, cost, credential access, or
   destructive operations.
6. **Keep traceability.** For material work maintain
   `GOAL -> REQ/FR -> NFR/QAS -> ADR -> CONFIG -> TASK -> TEST -> DOC` as
   applicable.
7. **Detect and repair documentation gaps.** If a required document is absent
   or stale, create/update the smallest fit-for-purpose record when purpose and
   location are clear. Otherwise ask what the document is for before writing it.
8. **No unverified completion.** Report the verification performed, omitted
   checks, and residual risk. Completion means the agreed acceptance criteria
   are evidenced, not merely that files changed.
9. **Least privilege and data care.** Do not expose credentials, secrets, or
   unnecessary sensitive data to skills or delegates. Use only the tools,
   environment, and data tier needed for the assigned task.
10. **Make operational variation explicit.** For software work, detect values
   that may vary by build, deployment, runtime, environment, or secret source.
   Classify them before coding, externalize only justified deploy/runtime
   settings, use typed validation and documented precedence, and never turn
   every code constant into configuration.

Rules have an enforcement class. `MUST` rules are enforced by a file layout,
validator, permission policy, or hook where available; `SHOULD` rules are
Router behavior; `MAY` rules are best-effort suggestions. A skill file alone
cannot guarantee a MUST rule across platforms.

## State machine

```text
Global guard
  -> Intake and classification
  -> Clarification/authority gate ---- unclear or decision needed ---> user
  -> Discovery and baseline
  -> Architecture baseline gate
  -> Impact and documentation-gap analysis
  -> Workflow assembly (skills, depth, roles, delegation)
  -> Deliberation loop
  -> Design, plan, and traceability baseline
  -> Execution loop ------------------ new evidence/change ----------> discovery
  -> Verification and documentation sync
  -> Completion and handoff
```

The durable task status is one of `active`, `waiting_user`, `blocked`,
`failed`, `cancelled`, or `complete`. A transition records its reason, owner,
entry and exit conditions, and attempt number. `waiting_user` resumes only on
a recorded answer/approval; `blocked` and `failed` record a recovery option;
`complete` is invalidated when later evidence changes a relevant requirement,
decision, or verification result. Unknown classification permits discovery but
not material mutation.

The normative stages are `intake`, `clarification`, `discovery`, `architecture`,
`impact`, `assembly`, `deliberation`, `design`, `execution`, `verification`,
and `handoff`. Their inputs, outputs, guards, fallbacks, and examples are defined
in [02-implementation-guide.md](02-implementation-guide.md) and the machine
contracts in [03-contracts-and-fixtures.md](03-contracts-and-fixtures.md).

### 1. Intake and classification

Classify every request across these axes:

```yaml
classification:
  session_scope: software_engineering | software_related | general_information | decision_support | creative | non_engineering
  project_state: greenfield | brownfield | hybrid | unknown | not_applicable
  fields: [idea, requirements, architecture, ui_ux, frontend, backend, api, database, data, ai_ml, security, privacy, configuration, implementation, testing, documentation, performance, devops_release, operations, research, compliance]
  field_registry: registry/taxonomy.json
  action: investigate | define | plan | design | implement | change | verify | review | document | approve | handoff
  risk: low | medium | high
  depth: light | standard | deep
```

Hybrid requests are decomposed by dependency, not treated as a single label.
For example, an existing-product feature request normally becomes discovery,
impact analysis, design, implementation, testing, then documentation.

Risk and depth begin conservatively. Public API changes, authentication,
secrets, personal/sensitive data, payments, production configuration,
migrations, dependency/licence changes, destructive commands, regulated
domains, and external publication are at least `medium`; material impact or
irreversibility makes them `high` and normally `deep`. Classification includes
confidence and evidence, and may be revised through a recorded transition. For
non-software scope, `project_state` is `not_applicable` and the Router uses the
general-information or creative path rather than inventing a code workflow.

### 2. Clarification and authority gate

Return to the user before proceeding when there is a material unknown about
product concept, priority, success criteria, constraints, target audience,
acceptable trade-off, authority, or a domain not covered by current skills and
evidence. Suggestions are clearly labelled as proposals, not inferred intent.

Use this decision policy:

| Condition | Default behavior |
| --- | --- |
| Clear, low-risk, reversible, in-scope | Proceed; record interpretation and verification. |
| Bounded, testable working assumption | Proceed only if it can be safely reversed; mark it `assumption`. |
| Product value, concept, priority, or acceptable trade-off | Ask the user before material work. |
| External, costly, destructive, privileged, or sensitive-data action | Fail closed until scoped approval is recorded. |
| Missing/incompatible skill or conflicting evidence | Use a safe fallback, investigate, or ask the user; never invent authority. |

### 3. Discovery and impact analysis

For Brownfield/Hybrid work, identify current behavior and the affected UC,
functional and quality requirements, API/data contracts, modules, tests, docs,
and operational paths. Record the working tree, base revision, run/build/test
commands, initial test status, characterization evidence, dependencies,
schemas/migrations, and source-of-truth conflicts. Decide and justify one of
`extend`, `new`, or `mixed`. The default source-of-truth order is user decision,
approved requirement/ADR/contract, executable tests and observations, code,
ordinary documentation, then inference; a project may override this order.

### 4. Workflow assembly

The Router reads only the skill metadata initially, then opens the selected
skill and its explicitly required resources. It chooses application depth:

| Depth | Default use |
| --- | --- |
| light | narrow, low-risk change with clear evidence |
| standard | normal feature, review, documentation, or refactor |
| deep | architecture, security, data, public API, broad Brownfield impact, or material uncertainty |

Each invoked skill must yield: classification changes, evidence, artifacts,
assumptions/open points, validation requirements, and a `transition` to the
next decision.

The portable core defines a versioned skill manifest: `id`, `version`,
capabilities, inputs, outputs, required resources, dependencies, compatibility,
trust status, and transition contract. Platform adapters translate that core to
Codex or Claude discovery, instruction, tool-permission, and delegation
mechanisms. Resolution is deterministic: project-reviewed skill, then
shared-reviewed skill, then no skill; `incoming/` is never invoked. Missing or
incompatible capabilities fall back to a documented sequential review or a user
decision. Dependency loading is bounded and rejects cycles.

The first implementation is deliberately small: a local file contract, a
single Router, read-only discovery, and validator scripts. Delegation, external
MCP actions, and autonomous mutation are optional later phases rather than
prerequisites for a working harness.

The bootstrap is a thin entrypoint, not the enforcement engine. Shared platform
templates live under `adapters/`; a target project receives managed root
`AGENTS.md`/`CLAUDE.md` wrappers plus `.agents/harness.json`. Automatic MUST
guarantees require the Router, state store, validators, and an adapter
capability probe. When those are unavailable, read-only intake and discovery
may continue, but material mutation and high-risk actions are blocked or
require a recorded manual guard. Git-root discovery is a path heuristic and
never determines Greenfield/Brownfield state.

For every software-related task, `architecture-baseline-and-design` is a
mandatory checkpoint. It reads `docs/architecture/`, establishes or drafts the
PRD/SRS/UC/FA/QA/HLD/LLD/view/diagram baseline, and then transitions to the
existing Greenfield, Brownfield, or document workflow. This is an additive gate;
it does not replace those workflows.

Configuration is a conditional cross-cutting concern rather than a new lifecycle
stage. When intake, architecture discovery, or impact analysis finds IPs,
hosts, ports, URLs, paths, timeouts, retries, pool sizes, feature flags,
credentials, profiles, environment variables, configuration files, or other
environment-specific values, workflow assembly selects
`configuration-and-environment-management`. The skill classifies code/build/
deploy/runtime/secret values, preserves language and framework conventions,
and loads only the matching language reference.

### Harness-maintenance path

Requests that change this harness itself use a control-plane path after intake:

```text
intake -> harness-upgrade-analysis (read-only baseline and impact plan)
       -> user approval -> bootstrap/adapter implementation -> verification
       -> harness-overview-html (refresh human-readable overview) -> handoff
```

`harness-upgrade-analysis` reads all of `plan/` first, then the active registry,
adapter/template manifest, and only the relevant skill bodies. It classifies each affected path as
`unchanged`, `patch`, `extend`, `wrapper`, `replace`, `deprecate`, or `new`,
and cannot mutate files. Existing concepts, sequences, gates, and transition
contracts remain preserved unless an approved change record explicitly replaces
one. `harness-overview-html` is the documentation endpoint for this control
plane: it generates a self-contained, no-network HTML guide from the pinned
plan/registry revision and reports provenance, unresolved items, and validation.
These skills are additive wrappers around the existing workflows; ordinary
project requests still use the architecture, Greenfield, Brownfield,
document, and verification paths above.

### 5. Deliberation and selective multi-agent delegation

The Router remains the single accountable coordinator. Delegate only when
independent expertise or parallel evidence collection materially improves the
outcome; do not create agents merely to simulate discussion.

Possible roles: codebase analyst, requirements/domain analyst, architecture
designer, API/compatibility reviewer, test/QA analyst, security reviewer,
UX/accessibility reviewer, performance/operations reviewer, documentation
editor, and neutral synthesizer.

Every delegate receives a bounded question, accessible evidence, allowed tools,
input snapshot, time/budget, mutation permission, expected artifact location,
and this response contract:

```yaml
recommendation: ...
evidence: [...]
alternatives: [...]
risks: [...]
validation: [...]
open_questions: [...]
```

Analysis delegates are read-only by default. Mutation delegates use isolated
workspaces/branches or explicit file ownership; they do not concurrently edit
shared files. The Router defines fan-out join conditions, timeout/cancellation,
and partial-result handling. For material claims, the synthesizer identifies
shared evidence and preserves justified dissent rather than treating correlated
opinions as independent confirmation.

The synthesizer resolves disagreement by evidence and requirements, not vote
count. Classify each issue as `resolved`, `assumption`, `open`,
`user_decision`, or `deferred`.

Default deliberation budget is three rounds: independent analysis, critique and
evidence repair, then neutral synthesis. Escalate earlier for irreversible,
security-sensitive, costly, authority-bound, or value/preference decisions.
After the third unresolved material round, ask the user using a compact
decision record: facts, options, impacts, recommendation, and safe default.
Three rounds are a budget, not a requirement: stop earlier when no new evidence
is produced. A material issue is complete only when it is `resolved`, an
explicitly accepted `assumption`, a recorded `user_decision`, or
`deferred_with_reason`; unresolved `open` issues block completion.

An evaluator receives the pinned acceptance contract and artifact revision,
uses a fresh verification context where feasible, independently reruns the
prescribed checks, and records commands, environment/tool versions, results,
and any unavailable checks. It may reject a slice for unmet acceptance criteria
but cannot redefine user intent. Rework, risk acceptance, or an unavailable
verification exception is a recorded transition with its authorized owner.

### 6. Plan, execution, and verification

Before material implementation, create the minimum appropriate requirements,
quality scenarios, ADRs, tasks, and acceptance/verification plan. Execute in
small coherent slices; renewed evidence or scope changes return the task to
discovery or impact analysis.

Synchronize code, tests, and fit-for-purpose documentation. Retain a handoff
record so a later session can resume without relying on conversational memory.

Documentation updates require an identified purpose, audience, location, and
owner. Automatically update only ordinary, change-coupled project documents.
Protected, policy, compliance, externally published, or owner-controlled
documents require the appropriate approval; records include review status and
supersession/retention information.

## Authority and action record

The Router may investigate and make reversible, in-scope workspace changes.
The user or delegated repository/system owner decides product direction,
priority, acceptance trade-offs, and residual-risk acceptance. External
communications, merge/publish/release, production actions, sensitive-data
access, credential use, dependency/licence changes, cost-incurring actions,
and destructive changes require explicit scope-bound approval.

Every consequential action uses an action record:

```yaml
action_id: ACT-...
request: ...
target_and_environment: ...
risk: low | medium | high
dry_run: true | false | unavailable
approval: { approver: '', scope: '', granted_at: '', expires_at: '' }
result: proposed | approved | executed | failed | cancelled
evidence: []
```

The complete action contract also records `requested_by`, `executed_by`,
`tool`, `approval_id`, `approval_status`, `before_state`, `after_state`, and a
rollback plan. MCP calls are actions: read-only tools may be allowed by policy,
while mutating tools require an approved action.

Absent or expired approval means the action is not executed. Tool failures are
classified as transient or permanent, retried only within the task budget, then
recorded as a fallback, `blocked`, or a user decision.

## Shared task state

```yaml
schema_version: 1
task_id: TASK-...
run_id: RUN-...
status: active | waiting_user | blocked | failed | cancelled | complete
intent: { goal: '', success_criteria: [], constraints: [], confirmed_by_user: false }
classification: { value: {}, confidence: '', evidence: [], reviewed_at: '' }
evidence: [{ id: EVD-..., kind: observation | inference | assumption, source: '', rationale: '', artifact: '' }]
impact: { uc: [], requirements: [], contracts: [], modules: [], risks: [] }
decisions: [{ id: ADR-..., status: proposed | accepted | superseded | waived, owner: '', rationale: '', evidence: [] }]
traceability: [{ from: REQ-..., relation: implements | verifies | supersedes | waived_by, to: TEST-... }]
open_points: [{ id: OPEN-..., status: assumption | open | user_decision | deferred, owner: '', next_action: '' }]
transition: { from: '', to: '', reason: '', owner: '', attempt: 1, entry_conditions: [], exit_conditions: [] }
handoff: { updated_at: '', writer: '', next_action: '', artifacts: [], validation_status: '' }
```

The YAML above is a human-readable example. The reference implementation uses
dependency-free JSON for machine state and NDJSON for events; YAML is accepted
only when a platform adapter provides a parser. State is stored as one durable,
versioned record per task with an append-only
decision/action event log. References point to artifacts rather than embedding
secrets or large outputs. The implementation must define its project-local
location, redaction/retention policy, atomic-write and merge/ownership protocol
before multi-agent mutation is enabled.

## Initial implementation order

0. Read the glossary, contracts, and implementation guide; decide the
   portability baseline and canonical state location.
1. Implement JSON/NDJSON schemas, validators, the state store, and the
   deterministic safety invariants.
2. Implement the single Router and intake/clarification UX; test clear,
   ambiguous, and non-software requests.
3. Implement one Greenfield, one Brownfield, and one document-purpose workflow;
   verify light/standard/deep artifact requirements.
4. Add the reviewed skill registry, progressive loading, and Codex/Claude
   adapters. `incoming/` remains unreachable by resolution.
5. Add traceability, verification, handoff, and conditional release/rollback
   handling.
6. Add isolated delegates and the independent evaluator only for Deep mode;
   test timeouts, partial results, dissent, and escalation.
7. Run all fixtures and cross-platform invariants. Promote only after the
   measurable exit criteria in [03-contracts-and-fixtures.md](03-contracts-and-fixtures.md)
   pass; keep a rollback path to the single-Router MVP.
