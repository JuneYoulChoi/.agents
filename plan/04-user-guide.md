# Ordinary developer guide

This guide is for a software developer who does not need to know the internals
of the harness. The harness should feel like a careful teammate: it asks only
for decisions that the developer owns, records what it found, and explains what
it verified.

## What to include in a request

Use this short form when possible:

```text
Goal: what should change or be understood?
Context: new project or existing project? Relevant path or feature?
Success: how will we know it works?
Constraints: compatibility, deadline, technology, security, or scope limits?
Output: code, tests, design, document, explanation, or a combination?
```

A one-sentence request is acceptable. The Router fills in what is obvious and
asks about only material uncertainty.

## What happens after a request

The user sees a short intake summary:

```text
Scope: software engineering
Project state: Brownfield (confidence 0.88)
Fields: backend, API, testing
Action: change
Risk/depth: medium / standard
Next: inspect current endpoint and tests
```

For every target-software request, the harness also checks the architecture
baseline in `docs/architecture/` even when the user did not mention it. A
harness-maintenance request uses all of `plan/` as its architecture baseline;
an overview-only request does not invent a target project's architecture gate.
If a target baseline is missing or stale, the harness may produce a code-derived
draft and ask the user to confirm UC, FA, QA, external-interface, or module
boundaries before material implementation.

For material architecture work, G2 also records which international standards
are applicable. It loads only standards requested by you, required by project
policy/contract, or supported by project evidence. `guidance` and `alignment`
are different from formal `conformance`; conformance is blocked unless the
authorized edition, assessment scope, evidence, deviations, and owner exist.

G5 performs a focused architecture/design-pattern review only when the request
explicitly asks for patterns or evidence shows a changed architecture structure
or component/object interaction. A local implementation change does not load
the pattern skill merely because code is changing. Active reviews derive
candidates from UC/FA/QAS, constraints, existing Brownfield structure, and
affected modules. The valid answer can be “no named pattern is applicable.”
Selected patterns include trade-offs, ADR/trace links, migration/rollback, and
verification before ecosystem and language skills implement them.

If several patterns are genuinely viable for the same decision, the harness
does not choose one silently. It shows each candidate's fit, recommendation
reason, benefits, trade-offs, quality effects, migration/rollback cost, and
verification approach. It identifies a recommended option and explains which
changed conditions would favor another option, then asks the user to select.
Patterns at different levels that can coexist are presented as a composition,
not as a false either/or choice. Material implementation waits for the recorded
selection; trivial reversible coding idioms do not create an unnecessary user
gate.

When a request names or touches ROS 2, Node.js, React, gRPC, Isaac Lab, Docker,
Isaac Sim, MoveIt, Kubernetes, Modbus, colcon, or another ecosystem, the harness
does not activate every adjacent technology. It first records whether each one
is mandated, already present, only a candidate, selected, rejected, or not
applicable. It derives required capabilities from UC/FA/QA, checks version and
binding compatibility, records integration relationships and material ADRs,
then loads only the affected professional engineering skill.

Those ecosystem skills contain the widely used architecture, structure,
design rules, anti-patterns, configuration surfaces, testing, debugging,
performance, security, and Brownfield migration practices for that technology.
For actual code, the harness additionally loads only the changed implementation
language profiles: C, C++, C#, Rust, Go, Java, Python, JavaScript, TypeScript,
HTML, CSS, or Shell. Generated interface/client code remains generator-owned.
Examples do not choose a language or platform on the user's behalf.

When authored code is actually in scope, G6 applies one common
`implementation-quality` skill. Its core correctness, simplicity, dependency,
state/lifecycle, error, and testability checks are bounded to the changed
module. Object-oriented/SOLID, functional, data-oriented, API/data,
concurrency, distributed, security, performance, and real-time/embedded
profiles are loaded only when the code or requirements provide matching
evidence and a verification method. A language that is merely detected, a
generated-code-only task, or documentation-only work does not activate these
implementation skills.

Application depth is recorded per selected skill. For example, a confirmed
architecture baseline can receive a light delta check while a security or gRPC
branch receives standard or deep treatment. The number of active skills alone
does not raise depth.

When software contains IPs, hosts, ports, URLs, paths, timeouts, retries, pool
sizes, feature flags, credentials, profiles, environment variables, or config
files, the harness also checks whether they are code constants, build settings,
deploy/runtime settings, or secrets. It externalizes only justified values,
keeps existing project conventions where safe, and loads the matching C++,
Rust, Java, Python, TypeScript/JavaScript, Go, Shell, HTML, CSS, or common
guidance. HTML and CSS guidance covers only public client bootstrap values and
theme/design-token boundaries; it never treats a browser artifact as a secret
store. Tool popularity is compared only within one ecosystem and function and
does not automatically approve a dependency. The user is asked when a default,
precedence, compatibility window, or secret source is a product/operations
decision.

If a decision is needed, the user receives facts, options, recommendation, and
safe default. Answer with a choice or correct the assumptions. Silence is not
treated as approval for a material decision.

### How a complex request selects several skills

The classification categories form a tree, but routing uses layered gates. One
request can therefore activate several evidence-backed branches without
loading every skill. The user-facing summary shows activated and important
suppressed branches with reasons. For example, a Brownfield ROS 2 C++ request
that adds gRPC, a configurable port, Docker packaging, tests, and documentation
activates those exact concerns; it suppresses MoveIt, Isaac, Kubernetes, or
colcon unless their own project evidence requires them.

The same summary may show an execution role and `low`, `medium`, or `high`
reasoning recommendation for the current gate. These are portable effort hints,
not fixed product names. Codex or Claude maps the hint to what the current
platform actually supports and records whether it matched, upgraded, degraded,
used a platform default, or was unavailable. The portable level stays in the
common three-level scale while the adapter records any native platform label.
A stronger model never grants
permission or resolves a product decision automatically. `light` work is not
raised merely because several skills are active; high risk, architecture
conflict, and repeated evidence-backed failure are the bounded escalation
conditions.

If a later check fails, the Router sends a bounded feedback signal to the
nearest responsible gate and reruns only the affected descendants. A bad port
validation returns to the configuration concern; a changed UC returns to the
architecture baseline; a permission loss returns to the global guard. This is
called backward feedback propagation. It never silently changes the user's
goal, accepted decision, or approval, and three unresolved attempts escalate
instead of looping.

Harness maintainers can check this routing behavior with the fixture runner.
A fixture is a saved example request plus its expected gates and outputs; it
tests the harness, not the application being developed. From the harness root,
`python3 -B scripts/fixture_runner.py` runs the optional reference provider.
Another adapter can be tested through `--adapter-command`, so ordinary target
projects do not need Python.

### Reference runtime for a target project

The optional reference provider installs only thin wrappers and portable
configuration into an existing target that is separate from the shared harness
source:

```sh
python3 -B scripts/harness_bootstrap.py install \
  --target-root /path/to/project --adapter codex
```

Codex or Claude performs the natural-language intake; users do not author the
JSON by hand. The adapter validates that intake and starts a task with
`harness_runner.py`. The Runner returns one reviewed `next` skill, retains the
goal, success criteria, classification, architecture-first order, artifacts,
and evidence in `<project>/.agents/state/<task-id>/`, and advances only after a
matching revisioned result is submitted. `status` or `next` reconstructs the
same step in a later session.

An unreadable or copied task state is preserved and rejected; the runtime does
not guess a repair. This is a small fail-safe for interrupted writes or manual
edits, not an autonomous recovery system. A valid hook or task-scoped manual
guard is required before durable state or material execution.

## Common user commands

These are natural-language intents, not mandatory commands:

```text
Explain the current status of TASK-001.
Show the open decisions.
Continue TASK-001 after my answer.
Pause TASK-001 and write a handoff.
Cancel TASK-001 because <reason>.
Review the proposed design without changing files.
Run the verification again.
Show what evidence supports REQ-001.
```

To change the harness itself, say what should be upgraded and why. The harness
first reads all of `plan/`, the active registry, and the affected skills, then
returns a per-file change plan and waits for approval before editing anything:

```text
Upgrade the harness so <new requirement>. Preserve the current sequence and
gates where possible, show affected files and risks, and wait for my approval.
```

To publish or refresh the human-readable overview, use:

```text
Create/update the self-contained harness overview HTML from the current plan
and active registry. Use the default docs/harness/index.html unless it conflicts
with an existing document owner.
```

The overview is a derived guide. The Markdown files in `plan/` and the active
registry remain authoritative.

## First-time project bootstrap

The shared harness keeps its platform templates in
`.agents/adapters/codex/AGENTS.md.tmpl` and
`.agents/adapters/claude/CLAUDE.md.tmpl`. A target project receives thin,
managed root wrappers and `<project>/.agents/harness.json`; task state remains
under `<project>/.agents/state/`. The installer should be given an explicit
target root that already exists. If omitted, it may use the unique nearest
canonical Git root; it may use the current directory only when Git reports no
repository. A Git error, conflicting root, or source/target collision blocks
installation. Git-root detection does not decide whether the project is
Greenfield or Brownfield.

The normal install is a copy. Re-running with the same managed hashes is safe.
An existing unknown or user-edited `AGENTS.md`, `CLAUDE.md`, or
`harness.json` is never silently overwritten; review the reported diff and
request an explicit upgrade. Installation is a recorded, atomic change and
can be rolled back without discarding user edits. The configuration contains
portable source locator/revisions, template and registry hashes, adapter
mappings, state root, registry order, enforcement probe/guard, and a canonical
self-excluded config hash, but no secrets or absolute machine paths.
`harness.json.example` contains `PIN_REQUIRED` sentinels and is not installable
until real revisions and 64-hex hashes are rendered.

When the adapter reports `manual` enforcement, the harness can classify,
persist task state, and perform a limited reversible workspace change only with
an unexpired manual guard and action record. `unsupported` is ephemeral and
read-only: it cannot claim cross-session resume. All modes pause or block
external/destructive/high-risk actions, approval bypasses, and unsafe state
writes. This limitation is shown in the intake summary and handoff rather than
being presented as automatic enforcement.

## Worked example: Brownfield feature

Request:

```text
Add cursor pagination to the existing GET /users endpoint. Keep old clients
working and update tests and API docs.
```

Expected interaction:

1. The Router classifies this as Brownfield, backend/API/testing/documentation,
   standard risk/depth because compatibility is explicit.
2. It records branch, base commit, run/test commands, current endpoint behavior,
   API contract, and existing tests.
3. It writes an impact record covering controller/service/query modules, old
   response shape, database indexes, regression tests, and API docs.
4. If cursor format or compatibility policy is unclear, it asks one bounded
   question before editing.
5. It selects API design and TDD skills if approved and available; otherwise it
   follows the core test-and-contract procedure.
6. It creates a task slice with acceptance criteria:

   ```text
   Given an existing client using the old response
   When it calls GET /users without cursor parameters
   Then the old response remains valid

   Given a client requesting the next page
   When it supplies a valid cursor
   Then the next page and next cursor are returned
   ```

7. It implements, runs the prescribed tests, updates the API guide, and writes
   a handoff containing changed files, validation, and residual risks.

The user does not need to manage sub-agents. Evidence-backed delegation may add focused workers or reviewers, but
the Router owns the final issue ledger and asks the user when a product or
compatibility choice remains.

## Worked example: document-only request

Request:

```text
Document how to run the service locally for new team members.
```

The Router classifies the request as documentation with purpose `operate` or
`teach`, audience `new team members`, and type `guide` or `manual`. It checks
whether a current document exists, records the run commands as evidence, and
creates only the missing sections. It does not create an ADR, code task, or
Brownfield impact record unless the document work discovers a real system
change.

## Status meanings

| Status | Meaning | User action |
| --- | --- | --- |
| `active` | work is progressing | none unless asked |
| `waiting_user` | a decision or approval is required | answer the pending question |
| `blocked` | progress requires access, tool, or recovery | provide access/choice or stop |
| `failed` | an operation failed | inspect error and retry/repair |
| `cancelled` | user or policy stopped the task | start a new run if needed |
| `complete` | acceptance and verification are evidenced | review handoff |

## When a task is complete

The final response must state:

- what changed or was produced;
- which requirements and acceptance criteria were addressed;
- tests/checks run and their results;
- documents updated or intentionally not created;
- selected/detected technologies, compatibility and integration decisions, and the ecosystem rules applied when changed;
- applicable standard profiles, intent, evidence, and honest conformance status;
- architecture/design pattern decisions, trade-offs, ADRs, and verification or explicit not-applicable result;
- user selection evidence when several materially viable pattern alternatives existed;
- implementation languages/bindings, generated-code ownership, and language checks when code changed;
- implementation-quality profiles applied or suppressed, their bounded authored paths, and verification evidence;
- configuration sources, precedence, validation, and secret handling when changed;
- activated and materially suppressed routing branches, plus any backward feedback and recomputed artifacts;
- recommended execution profiles and any actual model/reasoning degradation or platform-default fallback;
- assumptions, waivers, and residual risks;
- the next action, if any.

“Files changed” alone is not completion.

## Recovery

If a session ends unexpectedly, start a new session in the same project and say
`Continue TASK-<id>`. The Router reads `state.json`, `events.ndjson`, and
`handoff.md`. If state is corrupt, it preserves the original, reports the
repair path, and does not guess a new state. If you want to abandon the task,
say `Cancel TASK-<id> because <reason>`.

Gate results are immutable history. A resumed run continues from the latest
forward revision and pending feedback record rather than relying on the prior
conversation or recomputing unaffected branches.

## Safe answers to common questions

- If asked to choose between product priorities, choose or state that the user
  owns the decision.
- If a tool is missing, allow the core fallback or provide the tool explicitly;
  do not claim the check ran.
- If a skill or source document is missing, the harness asks whether to explore
  alternatives or follow your chosen concept/direction before making a material
  assumption. It may create a missing document only after purpose, audience,
  owner, and location are confirmed.
- If an external or destructive action is proposed, confirm its exact target,
  environment, scope, and rollback before approving.
- If the Router misunderstood the project state, correct it; the correction is
  recorded and the affected plan is re-evaluated.

## Work paths and focused teams

You can say “fix this bug”, “add this feature”, “refactor without changing
behavior”, “research this question”, or “update this document”. The harness
shows the required path and explains optional work it omits. It checks the
baseline and necessary quality requirements even for a quick fix.

The five views are request/context → work composition → routing/gates →
execution → verification/feedback; routing and authority apply throughout.
One agent is the default. Independent evidence collection, implementation with
confirmed contracts and separate ownership, or focused review may be delegated
when capability, authorization and benefit are established. Existing valid
permission is reused. Sequential fallback is normal, not failure.

A persona names a responsibility, not an extra mandatory worker. The coordinator
integrates results and verifies the combined change. Reported token/time savings
require measurement. Downloaded packages remain candidates; source affiliation
and storage category do not make them active. See the
[workflow guide](08-layered-workflow.md) and
[candidate review](../registry/skill-candidate-review.json).

## Native-work receipt extension

Declared work uses Runner `prepare-work` and `record-work`, both guarded by
expected_revision and the existing state lock. Unit skill_id binds execution to
a pending skill; missing owner bindings must be resolved at composition. See
[native work packets, receipts and usage](../skills/workflow-composition/references/native-work.md).
The extension preserves the serial skill queue and adds no process executor.
Existing no-unit workflows retain their result contract. Existing plans with
units must produce receipts rather than completing by skill status alone.
