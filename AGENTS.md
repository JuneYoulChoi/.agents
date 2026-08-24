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
