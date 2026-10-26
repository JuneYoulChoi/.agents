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
integers `max_workers`, `timeout_seconds`, and arrays `benefit_evidence_ids`,
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
