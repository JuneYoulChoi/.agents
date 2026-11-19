# Universal Engineering Harness — Codex entrypoint

This repository is the shared, dependency-light source for the engineering
harness. Treat `plan/`, `skills/`, `registry/`, and the adapter templates as
the source of truth; do not use the generated HTML overview as authority.

Before material work:

1. Run `skills/intake-and-route/SKILL.md` and record scope, project state,
   fields, action, risk, depth, change characteristics, language scope,
   evidence, and unresolved decisions. Evaluate
   `registry/routing-gates.json` as the deterministic `G0`–`G7` multi-input/
   multi-output skill graph and load only activated branches. Resolve each
   returned portable `execution_profile` through current Codex capabilities;
   never treat a model name as skill policy, and record the actual or degraded
   model/reasoning resolution and native reasoning label in the skill result.
2. If the request changes this harness, run `harness-upgrade-analysis` across
   all `plan/`, the active registry, skills, adapters, templates, and fixtures;
   the harness plan is its architecture baseline. If it also changes a target
   software project, add that project's architecture gate.
3. For other software work, inspect `docs/architecture/` in the target project
   with `architecture-baseline-and-design` before impact, design, or mutation.
   Record international-standard applicability and require authorized evidence
   before any formal conformance claim.
4. For an existing codebase, run `brownfield-impact-analysis` before editing.
   Route through `architecture-and-design-patterns` only for an explicit
   pattern scope or evidenced architecture-structure/design-interaction change;
   suppress it for ordinary local code changes. For authored code in scope,
   route through its changed language profile and G6 `implementation-quality`,
   loading only evidence-backed quality profiles.
   If several materially viable patterns remain for one decision scope, show
   their reasons and trade-offs, recommend one, and wait for the user's choice.
5. For a harness change, obtain approval before mutation; do not bypass the
   control-plane gate.
6. Load only the smallest approved skill set. Never resolve `incoming`,
   deprecated, unverified, or integrity-failed skills.
7. Preserve task state and evidence under the selected target's
   `.agents/state/<task-id>/`; do not invent state after a reset.
8. If the request, skill, or source document is unclear or missing, ask whether
   the user wants exploratory expansion or a specific concept/direction before
   making a material assumption.
9. Finish with `verify-and-handoff`, including tests/checks, traceability,
   documentation status, assumptions, waivers, and residual risk. Route a
   failure through bounded backward feedback to the nearest responsible gate
   while preserving unaffected branches and user-owned decisions.

This is a self-hosted source-repository entrypoint. Target projects use the
canonical templates under `adapters/`; this repository is not a target project
and its own `.agents/state/` is not a task store.

If the plan, registry, bootstrap configuration, or deterministic guard is
missing or stale, read-only diagnosis may continue, but material mutation and
external/destructive actions must stop until the user approves a safe path.

## Work composition

Use the five-layer view in `plan/08-layered-workflow.md` without replacing
G0–G7. For target work, run `workflow-composition` after G3 impact/requirements;
keep work type separate from fields and risk. Consume the route's `work_plan`
(or `next.work_plan`) as a proposal. At intake and each current skill, actively
assess bounded expert delegation using workflow-composition's expertise policy.
For independent uncertainty, conflicting evidence or shared verification
assumptions, dispatch a focused expert with current authority/capability/benefit
evidence or record a concrete fallback. Keep clear local work serial. Pair domain
roles with meticulous or minimal_sufficient reasoning lenses when useful; retain
all acceptance criteria and avoid duplicate reviews. Check original-request
coverage and separate requested work, necessary dependencies and optional extras;
ask only unresolved user-owned choices necessary to complete the current scope.
Recheck owned paths, shared resources, tools and revisions before execution.
The Runner stays serial; native adapters join approved units within the current
skill. Preserve required quality and user decisions, then verify integration.

For declared units, use the Runner's prepare-work/record-work boundary and the
native-work reference under workflow-composition. Send only focused packets to
fresh worker contexts. Confirm termination and verified joins before advancing;
report token counters as unavailable when the provider does not expose them.

## Application depth and gate closure

`next.application_depth` bounds every skill the same way: `light` checks only
the changed boundary and records a compact result with reasons for omitted
optional steps; `standard` runs the skill's normal procedure; `deep` also
examines alternatives, boundary failures and independent evidence. Depth never
removes acceptance criteria, required checks or approvals.

A gate closes only on evidence. `completed` needs artifact and evidence IDs
(plus the typed `pattern_review` / `implementation_quality` record for those
skills); `not_applicable` needs a reason and evidence and cannot skip an
activated baseline or impact skill for a mutation. Return `waiting_user`,
`blocked` or `failed` when that is the real state, continue a suspended skill
with Runner `resume`, and report a routed verification failure as `failed`
with `feedback.kind` so only the responsible gate reopens. High-risk and
harness mutations need `approval_evidence_ids` at intake.

## Readable, documented code

Every authored code file created or modified starts with a Korean header
comment with `모듈:`, `컴포넌트:` and `역할:` taken from the architecture
baseline, and every created or modified function carries a Korean comment with
`역할:`, plus `입력:` and `출력:` when it has parameters or a result. Record the
readability standard first (project formatter/linter, else the language guide
plus the harness defaults). Run `scripts/harness_code_docs.py` before
completing G6; the Runner re-runs it. See
`skills/implementation-quality/references/readability-and-documentation.md`.
