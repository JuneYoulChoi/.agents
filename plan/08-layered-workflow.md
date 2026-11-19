# Five-layer workflow and selective delegation

Approved direction: 2026-10-24. This is the canonical responsibility view for
the harness. The five layers below are not five new gates or five always-on
agents. G0–G7 remains the only routing graph; the durable lifecycle remains
unchanged. Authority, skill trust, evidence, quality and state span all layers.

| View | Inputs and responsibility | Output / owner |
| --- | --- | --- |
| 1. Request and context | Goal, acceptance, fields, project state, risk, changed boundaries; inspect baseline | Classified intent and baseline; G1–G2 |
| 2. Work composition | Baseline, impact, requirements, task kind, dependencies, uncertainty | Smallest useful path and work units; G3 |
| 3. Routing and gates | Evidence, conditions, authority, branch dependencies | Activated/suppressed branches and transitions; G0–G7 |
| 4. Execution | Accepted path, concerns, ecosystems, authored languages, skills, native tools | Bounded changes and unit results; G4–G6 plus adapters |
| 5. Verification and feedback | Pinned outputs, acceptance, tests and documents | Verified handoff or bounded feedback; G7 |

Routing is a control responsibility used throughout the lifecycle, not a stage
that must wait for all execution planning to finish. Fields choose expertise;
work type chooses a delivery outline; risk and uncertainty determine rigor.
Neither a folder category nor an upstream bundle grants activation authority.

## Work profiles and minimum quality

`work_type` is optional and defaults to `standard`. Natural-language adapters
infer it from observed intent or use an explicitly requested supported type.
The deterministic provider does not interpret user prose. `harness` always
uses maintenance; document actions/overviews use document; investigate/review
with no explicit type use research. These are outlines inside existing gates,
not additional workflow engines or permission settings.

| Type | Expected outline | Optional work that can be omitted |
| --- | --- | --- |
| standard | baseline, impact/requirements, implement, verify, handoff | irrelevant specialist detail |
| bugfix | baseline, reproduce, impact, fix, regression, handoff | new design if no structure/contract change |
| feature | baseline, requirements, contracts, vertical slice, integration, handoff | speculative modes and future extension points |
| refactor | baseline, behavioral contract, impact, refactor, regression, handoff | product discovery when behavior is unchanged |
| research | question, evidence, synthesis, claim checks, handoff | implementation and deployment |
| document | purpose, source evidence, draft, link/claim checks, handoff | authored-language and code-quality work |
| infrastructure | baseline, configuration, rollback, authorized change, verification | UI/domain modeling outside scope |
| maintenance | harness baseline, approved change, fixtures, document sync, handoff | target-project workflow when none is changed |

High-risk bugfixes still require appropriate security, contract and rollback
checks. `light` means compact artifacts, not weaker acceptance. Keep all G0–G7
checks; inapplicable branches produce a bounded reason without loading their
skill bodies. A confirmed baseline may receive a delta check. Existing
acceptance evidence is reusable only if revision, environment and scope match.
SOLID/GRASP and established design patterns remain applicable diagnostic lenses;
no profile authorizes speculative abstraction or omission of required design.

## Runtime input and output

Optional intake fields: `work_type`, `work_units`, `delegation`.

Each unit requires `id`, `goal`, `role`, `mutation`, `input_revision`,
`evidence_ids`, `allowed_tools`, `expected_output`, `acceptance`. Optional arrays
are `depends_on`, `read_paths`, `write_paths`, `shared_resources`. String lists
contain nonempty unique values. Paths are canonical project-relative literal
paths; no glob, absolute path, backslash, drive prefix or traversal is allowed.
`mutation` is `none` or `workspace`. Workspace units require write paths;
read-only units cannot claim write paths. Unknown/self/cyclic dependencies fail
validation. See [the executable example](../templates/workflow-intake.json.example).

Personas are bounded responsibilities, not claims of human credentials:

| Role | Responsibility | Mutation |
| --- | --- | --- |
| analyst | evidence collection, callers, behavior, alternative hypotheses | none |
| designer | contracts, ownership, coupling, scoped alternatives | none |
| implementer | accepted behavior within owned boundaries | workspace or none |
| reviewer | correctness, simplicity or evidenced specialist concern | none |
| verifier | independent acceptance evidence on a pinned revision | none |
| documenter | source-grounded ordinary documents | workspace or none |

`delegation` has booleans `requested`, `authorized`, `available`, positive
integers `max_workers`, `timeout_seconds`, nonnegative `native_worker_capacity`, and arrays `benefit_evidence_ids`,
`authorization_evidence_ids`, `capability_evidence_ids`. Missing evidence,
missing timeout, a blocked route, insufficient units or unavailable capability
selects serial execution. Authorization may come from an existing applicable
user/project instruction; do not ask repeatedly. Worker capacity is the actual
available native limit, never a fixed team size required by a persona recipe.

The reference Router emits additive `work_plan`: selected type, depth, outline,
mandatory checks, units, dependency batches, actual proposed concurrency,
fallback reasons, timeout and join policy. It always emits
`dispatch_authorized: false` and `adapter_recheck_required: true`: the projection
is a plan, not an action token. The Runner persists it in `state.route` and
exposes it in `next.work_plan`. Old states without it remain readable.

A completed `core.workflow-composition` result may include
`workflow_update: {"work_units": [...]}` with plan artifact/evidence IDs.
The Runner validates and persists the refined units and recomputes batches
before the next skill. This cannot change work type, intent, risk, delegation
authority or capabilities; those require a new validated routing context.
Other skills and non-completed results cannot submit a workflow update.

The planner forms deterministic batches in input order from ready units. It
serializes write/write and write/read path overlaps (including parent paths),
unknown reader scope beside a writer, and any shared resource. Read/read
overlap alone is safe. No child starts before its declared predecessors join.
This is bounded task scheduling, not a general expression language or runtime
plugin executor. `scripts/harness_workflow.py` is the dependency-free reference.

## Native execution and join boundary

The Runner still requests one core skill result at a time. A native adapter
may execute accepted units within that skill; it must not run future G5/G6 work
while G2/G3 decisions are unresolved. Recompute the projection after impact,
contracts or capabilities change; intake batches are provisional.

Before dispatch, validate current authority, actual tool capability, revision,
realpath/symlink containment, exclusive file ownership or isolated worktree,
resource scope, worker limit and timeout. Declared tools are requirements, not
grants. Check time/token cost benefit, and use serial work when coordination
cost dominates. Record actual time, tokens when available, conflicts and rework;
do not claim a speedup from a role name or from estimated parallelism.

Give delegates only their task, evidence, constraints and necessary references.
No conversation-wide context copying by default. No recursive spawning without
coordinator authorization. Keep rationale, uncertainty, negative findings and
failed checks in concise outputs; do not adopt cryptic compression for design
or authority decisions.

Join only current, verified required results. Reject stale/out-of-scope results;
cancel dependent units on failure, preserve unaffected evidence, and use bounded
retry or sequential fallback. A timeout does not satisfy a join. The coordinator
owns integration and final verification; reviewers cannot approve user-owned
trade-offs. Reuse a current completed review rather than stacking equivalent
review skills. Stop optional checks once all required acceptance passes.

## Skills and source decisions

Existing core skills remain the execution authority. `workflow-composition`
adds G3 composition after impact/requirements and before concern/specialist
resolution. It does not replace ecosystem, language, configuration, architecture
or implementation-quality skills. Missing specialist coverage uses a disclosed
core fallback or a scoped selection decision, never a similarly named candidate.

The inventory and per-package dispositions are in
[candidate review](../registry/skill-candidate-review.json). `adapt_principles`
means selected procedural ideas were rewritten into core contracts; it does not
promote the source package, scripts, hooks, tool names or dependencies. Other
packages remain `defer_package_review`, with category-level core coverage and
gaps explicitly recorded. Metadata screening is not a security/license audit.
No source package is replaced just because a more popular one exists.

Core integrations: bounded planning and dependency isolation in G3; design
seams and structural friction in existing G2/G5; minimal coherent implementation
in G6; independent evidence, reusable checks and stopping rules in G7. The
adoption record identifies the specific sources, exclusions and destinations.

## Popular source skills without an installed workflow

The [2026-10-25 source review](../docs/harness/popular-skills-2026-10-25.md)
records role-matched skills.sh install displays, immutable downloads and selected
procedure mappings. Popularity informs source selection, never gate activation
or trust. Originals remain in incoming; approved skills load only their scoped,
reviewed references. No CLI, hooks, new active skill or second router is added.

G3 reuses one compact acceptance/design/proof contract; bug work adds bounded
reproduction and cause evidence. G5 adds module-interface reasoning only for
an already activated structural review. G6 uses independent test oracles when
behavior warrants tests. G7 separates request coverage from project standards
and ties completion claims to matching execution evidence. Each reference stays
with its existing owner, default single-agent execution and stopping rules.

## Verification boundary

W-FLOW fixtures cover normal profiles, conditional parallel planning and serial
fallback. Runtime tests cover invalid dependencies, path conflicts, role limits,
capability/authority loss and Runner propagation. Documentation checks verify
active skill placement, candidate coverage, source links and inventory hashes.
Passing these proves planning and contract behavior, not native parallel agent
execution, hardware safety, product correctness or token savings.

## Checked native-work receipts (2026-10-30)

The Runner now offers prepare-work/record-work as a small adapter boundary;
it still never spawns workers. Units may be unbound at intake, but composition
must bind pending units to reachable later skills before completion. Preparation
is restricted to the current owner and joined dependencies. Active records
reserve ownership/capacity. Terminal receipts require adapter-confirmed worker
termination; late success becomes timed_out. Running work blocks any skill
transition, and missing/failed/timed-out work blocks its owner's completion and G7.
Composition may refine unprepared future units after all prepared work completed.
Prepared definitions and receipts remain unchanged; removing or changing them,
or carrying failed/cancelled/timed-out work through refinement, is rejected.
Recovery goes through the owning gate rather than silently deleting required work.

Use focused packets (16 KiB) and concise receipts (8 KiB), with detailed evidence
referenced locally; never truncate acceptance or uncertainty to fit. Token usage
is provider-reported per worker or unavailable. Optional worker_token_budget
limits new dispatch based on known worker totals, not provider in-flight billing
or total parent+worker cost. No budget is inferred from skill depth.
See the [native-work contract and commands](../skills/workflow-composition/references/native-work.md).
Adapter attestations still require trustworthy host enforcement; result IDs and
hash echoes are not independent proof of provider behavior or artifact validity.

## Minimal intake and delegation checks

`open_decisions` optionally lists material unresolved questions for the current
slice. G1 waits when the list is nonempty, independently of material_ambiguity.
Adapters check relevant identity/data ownership, persistence, external integration,
date/time semantics and acceptance, reusing confirmed evidence and labeling
proposals/assumptions. This is a structured handoff, not automatic prose parsing.
Clear local changes and excluded/later decisions do not require new questions.
Small coherent slices default to existing single-agent execution. Only bounded
independent work or a specifically needed review/test justifies delegation,
with the existing authority/capability/benefit evidence. No new scheduling policy,
team-size calculation or estimated token-savings claim is introduced.


## Focused skill delivery and executable capacity (2026-11-01)

Preparation now embeds the current approved SKILL.md, its hash, application
depth, execution profile and one bounded role instruction. Units may name only
needed `skill_references` beneath that skill's references directory; workers
verify/read the supplied paths and report instruction evidence and actual
model/reasoning resolution. Scope and authority remain those of the unit.

Proposed concurrency is capped by observed native_worker_capacity (excluding
primary/unrelated agents). Unknown capacity or unbound owners stays serial;
batches never combine different skill owners. Native prepare requires a fresh
capacity observation and caps admission again. Host queries and race handling
remain adapter responsibilities, not an automatic provider integration.

Small coherent work remains single-agent. Worker usage summaries explicitly
leave parent usage unavailable and total task tokens null. Savings require
comparable serial and total parent+worker measurements; no automatic benchmark,
extra reviewer, or numeric savings estimate is added.


## Enforced boundaries after scenario review

Completion requires current nonempty local evidence files for each task/unit
criterion, not only labels. Current registry/source pins are checked at Runner
execution boundaries. Dependency owners must follow the existing serial skill
order. Contradictory authored/only-content classifications fail validation;
unknown discovery cannot advance past G2 until a new linked intake reclassifies
it. Worker packets contain hashed prerequisite context and required registry
references in addition to selected references. Interrupted tasks use an ordinary
new start with supersedes_task_id and fresh gates; no automatic replay or new
orchestration layer is introduced. See the canonical native-work contract above.

## Evidence-driven expert assessment (2026-11-15)

The user-approved refinement actively assesses delegation at intake and each
current skill for independent uncertainty, conflicting evidence, distinct
expertise or shared producer/test assumptions. The detailed policy has one owner:
[workflow-composition](../skills/workflow-composition/SKILL.md#actively-assess-expertise-then-choose-bounded-roles).
Record a bounded question, expected evidence and actual dispatch or specific
fallback in the existing result; clear local work remains serial. G1 assessment
is adapter-owned before structured intake, not a Runner work unit. Native work
from G2 onward retains current-skill preparation and join requirements.

Optional unit `reasoning_lens` is `meticulous` or `minimal_sufficient`; unknown
values fail validation. The packet delivers the corresponding guidance with
its domain role. Lenses do not change model effort, skills, tools or acceptance.
Use distinct questions rather than duplicate committees. Review original-request
coverage, necessary dependencies and excluded/optional work before declaring
no open decisions; G1 still consumes annotations rather than interpreting prose.

Completed composition can refine only unprepared future units. Every prepared
unit must remain identical and completed, with its receipt retained. New pending
owners and dependencies must satisfy existing serial queue order. Authority,
intent, risk and capabilities remain immutable through workflow_update.

A configured worker_token_budget projects single-worker batches with an explicit
reason because admission waits for prior usage. Unavailable usage still blocks
further dispatch; the budget is not an in-flight or total-task billing ceiling.

Use the opt-in [behavior scenarios](../fixtures/behavior/expert-intake.md) to
exercise actual request interpretation separately from structured router tests.
Report essential omissions, unnecessary questions, scope additions and supported
new findings; compare acceptance-matched runs before claiming quality or cost
improvements. Parent plus worker provider usage is needed for token savings;
packet bytes, role names and passing unit tests are not substitutes.

## Gate integrity, routing entry and native dispatch (2026-11-19)

User-approved after a routing/gating review that reproduced gates closing
without work. The graph, skills and serial Runner are unchanged; closure and
entry conditions are tightened and two Runner commands are added.

Closure. A `completed` skill result requires artifact and evidence IDs; a
`not_applicable` result requires a `reason` and evidence, and an activated
architecture-baseline, Brownfield-impact or Greenfield-planning skill cannot be
skipped when the action is `implement` or `change`. A result whose
`transition.next_stage` is `clarification`, `backward_feedback`, `blocked` or
`failed` cannot advance. The pattern and implementation-quality skills submit
their typed records (`pattern_review`, `implementation_quality`), which the
Runner validates; an open `user_decision_required` pattern decision cannot be
`completed`. A `degraded` execution resolution needs evidence IDs. When the
route sets `independent_context`, G7 completion requires
`independent_verification_evidence_ids`.

Continuation. `resume` returns a task that a skill result suspended
(`waiting_user` or `blocked`) to the same skill after recording the answer and
decision evidence; earlier gates are not replayed. A routing-level block still
needs a corrected linked intake. A `failed` result may carry
`feedback: {"kind": <backward_routes signal>}`: the Runner rewinds the cursor
to the first queued skill at or after the target gate, keeps earlier results,
counts attempts per target gate itself and escalates to the user at the third
attempt, for an unrouted signal, for a gate without a queued owner, or when
recorded work units belong to the reopened gates. A `failed` result without
feedback remains terminal.

Routing entry. An authored code change under a non-software scope is rejected;
`not_applicable` project state blocks design or mutation at G2. A material
technology with status `candidate` activates technology selection. High-risk
mutation and harness mutation block at G0 without `approval_evidence_ids`.
Manual and unsupported enforcement block every workspace write, including
`document` actions and workspace-mutating work units. Pattern review is entered
for an `architecture` field with define/plan/design/review and for any
Greenfield design; `security` and `performance` fields select their quality
profiles. Read-only investigation does not activate implementation quality.
A compact route (Brownfield, light depth, low risk, confirmed baseline, only
`authored_code`, no units, technologies, configuration candidates or sensitive
fields) suppresses `workflow-composition` with a reason; baseline, impact,
language, quality and verification gates remain.

Roles and dispatch. Unit roles carry fuller responsibility guidance and are
bound to the current gate's portable role; `prepare-work` rejects a role that
gate does not allow. The Claude adapter supplies one agent definition per role,
a dispatch procedure, a reasoning-to-model mapping and an opt-in edit guard
hook ([Claude dispatch](../adapters/claude/native-dispatch.md)).
SOLID/GRASP now have one checkable
[reference](../skills/architecture-and-design-patterns/references/solid-grasp.md)
used at G2 responsibility assignment, G5 pattern decisions and the G6
object-oriented profile.

Not changed: a configured `worker_token_budget` still admits one worker at a
time; token savings remain `not_measured` until a comparable serial run is
measured; `allowed_tools` remain requirements checked by the adapter; evidence
hashes prove identity, not truth. `tests/test_gate_integrity.py` covers the new
rules.

## Readable, documented code and document sync

User-approved requirement: authored code must follow a recorded readability
standard and be documented in Korean. The implementation-quality `core` profile
now always loads
[readability and documentation](../skills/implementation-quality/references/readability-and-documentation.md):
a Korean file header (`모듈:`, `컴포넌트:`, `역할:`) on every created or modified
code file and a Korean comment (`역할:`, `입력:`, `출력:`, `예외:` when
relevant) on every created or modified named function, public or private.
Module and component names come from the architecture baseline. Generated,
vendored and comment-less files are exempt with a recorded reason. Existing
files are brought into line when they are next modified; untouched functions
are not retrofitted.

A completed implementation-quality record requires `readability_standard` and
`documentation_check` (`files`, optional `base_revision`, `module_map`,
`exempt_paths`). The Runner runs `scripts/harness_code_docs.py` and
`scripts/harness_doc_sync.py` on those files itself and rejects completion on
any violation. Python is parsed with `ast`; other languages use line-based
detection, so the check proves presence and labels, not the accuracy of the
comments. `tests/test_code_docs.py` covers the checker.

Documents and code stay in agreement through the
[doc and code sync](../skills/architecture-baseline-and-design/references/doc-code-sync.md)
rules: documents state structure, each fact has one owner, and a changed fact
is edited in place by keyword rather than appended. The module map
(`docs/architecture/module-map.md`) owns module and component names; a header
that names no row, a file outside its row's path, a map path that no longer
exists and a dangling code path in the documents all fail the sync check, while
a local change inside a component needs no document edit. The harness applies
the same check to itself through [its module map](../docs/harness/module-map.md),
and `scripts/harness_overview.py` fails the tests when the HTML overview has
not been reviewed since `plan/`, routing or the skill list changed.
