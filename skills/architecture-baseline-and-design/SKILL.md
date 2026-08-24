---
name: architecture-baseline-and-design
description: Inspect, create, review, or synchronize project architecture documentation and international-standard applicability before software design or material changes. Use for PRD, SRS, external entities/interfaces, use cases, functional architecture (FA), quality attributes (QA), HLD, LLD, ADRs, stakeholders/concerns/viewpoints/model kinds, layer/infrastructure/architectural/module/C&C views, class/sequence/data/deployment diagrams, standards alignment or conformance evidence, missing architecture docs, and code-to-architecture drift.
---

# Architecture Baseline and Design

Use this skill as the architecture gate for every `software_engineering` or
`software_related` task before design, implementation, or material review. It
does not replace the existing Greenfield/Brownfield/document workflows; it
returns a transition to them.

## Entry gate

Require an intake record. If it is absent, stop immediately and return only:

```yaml
architecture:
  status: not_started
transition:
  next_stage: intake
  next_skill: intake-and-route
  entry_conditions: [intake_record_required]
```

Do not inspect or infer architecture before the intake record exists. Inspect
`docs/architecture/` before using code as the design authority. Never
invoke `incoming/` skills. Do not make material code changes in this skill.

For a non-software scope, return `not_applicable` and the original workflow.
For software scope, classify the architecture baseline as:

```text
confirmed | draft | missing | stale | conflicted
```

Treat legacy input status `accepted` as `confirmed`, but emit only the canonical
values above.

## 1. Locate and assess architecture artifacts

Look for an index and the following logical artifacts (filenames may vary):

```text
PRD, SRS, external entities/interfaces, UC, configuration model,
FA, QA/QAS, HLD, LLD, ADR, technology and integration model,
layer, infrastructure, architectural, module, C&C, data, runtime views,
class, sequence, context, deployment diagrams
```

Record path, revision/date, owner, authority, freshness, and source links. A
document is not confirmed merely because it exists. Compare its claims with
approved requirements, tests, code, runtime configuration, and observed
behavior.

## 2. Determine international-standard applicability

For every material architecture task, record whether an international standard
profile is applicable even when the user did not name one. Read
[the standards catalog](references/standards/catalog.md), then only the profile
selected by the request, project policy, contract, regulated context, or
architecture evidence:

- architecture descriptions and viewpoints: [ISO/IEC/IEEE 42010](references/standards/iso-42010.md);
- requirements engineering: [ISO/IEC/IEEE 29148](references/standards/iso-29148.md);
- product and quality-in-use models: [ISO/IEC 25010 and 25019](references/standards/iso-25010-25019.md);
- lifecycle processes: [ISO/IEC/IEEE 12207 and 15288](references/standards/iso-12207-15288.md);
- lifecycle information items: [ISO/IEC/IEEE 15289](references/standards/iso-15289.md).

Record `guidance`, `alignment`, or `conformance` as the intent. Never claim
formal conformance from a public abstract, memory, or this skill. A conformance
claim requires the authorized standard edition, identified scope/entity,
applicable criteria, evidence, deviations/waivers, and an accountable owner.
If those inputs are unavailable, downgrade the wording to guidance/alignment or
block the claim; do not block ordinary architecture work that makes no formal
conformance claim.

## 3. Use the architecture trace

Use the following relation, allowing one-to-many and many-to-one links:

```text
PRD / SRS
  -> External Entity / External Interface
  -> UC
  -> FR / FA
  -> QA / QAS
  -> HLD
  -> ADR
  -> TECH / LLD / Module / Configuration Contract
  -> Views / Diagrams
  -> TASK / CODE / TEST / OPERATIONS
```

Treat `FA` as Functional Architecture and `QA` as Quality Attribute. Keep
quality assurance/testing activities labelled `QA testing` to avoid ambiguity.
Do not claim that every UC automatically produces one FA or QA; derive them
from UC, interfaces, constraints, and quality goals and record the evidence.

## 4. Handle a missing or stale baseline

If architecture documents are absent or stale, inspect code, tests, API
contracts, schemas, deployment configuration, and operational evidence. Produce
a draft baseline with `observed`, `inferred`, and `assumed` claims. At minimum
identify:

- external entities and interfaces;
- UC candidates and their actors/boundaries;
- FA candidates and responsibilities;
- QA/QAS candidates and measurable scenarios;
- HLD boundaries and dependencies;
- technology capabilities, existing/candidate ecosystems, versions/bindings,
  and integration/compatibility boundaries;
- LLD/module candidates and ownership;
- relevant layer, infrastructure, C&C, runtime, class, and sequence views;
- stakeholders, concerns, viewpoints, model kinds, and correspondence rules
  needed to explain why each architecture view exists;
- configuration boundaries, sources, precedence, secret strategy, and their
  deployment/runtime relationships when applicable;
- document gaps, contradictions, and risks.

Never promote code-derived intent to confirmed product requirements. Ask the
user to confirm material UC boundaries, external contract meaning, FA/QA intent,
and module boundaries. Use this question format:

```text
Architecture decision needed: <boundary or interpretation>
Observed facts: <paths, tests, contracts, runtime evidence>
Inferred model: <draft interpretation>
Options: A ... / B ...
Recommendation: ...
Safe default: keep draft and do not start material implementation
```

## 5. Greenfield and Brownfield modes

For Greenfield, create or update the minimum PRD/SRS/UC/FA/QA/HLD/ADR/LLD
artifacts needed for the requested depth before implementation planning.

For Brownfield/Hybrid, establish the current baseline first, map code and
tests to the existing architecture, and identify impacted UC, FA, QA, modules,
views, ADRs, and documents. Let `$brownfield-impact-analysis` decide
`extend`, `new`, or `mixed` after this evidence is available.

## 6. Produce the architecture record and transition

This skill is gate `G2`. Consume all relevant intake branches and project
evidence together. Emit each applicable workflow/concern candidate rather than
forcing one exclusive output, but keep unsupported adjacent technologies or
documents suppressed with evidence. A user correction or later architecture
contradiction may reopen `G2`; preserve the prior result and mark only dependent
downstream artifacts stale.

```yaml
architecture:
  status: not_applicable | confirmed | draft | missing | stale | conflicted
  root: docs/architecture/
  entity_of_interest: ''
  stakeholders: []
  concerns: []
  viewpoints: []
  model_kinds: []
  correspondences: []
  standard_profiles: []
  conformance_intent: guidance | alignment | conformance
  conformance_scope: ''
  conformance_owner: ''
  conformance_evidence: []
  artifacts_read: []
  artifacts_created_or_updated: []
  entities: []
  interfaces: []
  use_cases: []
  fa: []
  qa: []
  hld: []
  lld_modules: []
  views: []
  diagrams: []
  configuration: []
  technologies: []
  integration_relationships: []
  pattern_review_required: false
  evidence: []
  user_confirmations_needed: []
  open_issues: []
gate_result:
  gate_id: G2
  activated_branches: []
  suppressed_branches: []
  output_artifacts: []
transition:
  next_stage: clarification | discovery | impact | design | execution | verification
  next_skill: ''
  entry_conditions: []
```

Use `confirmed` only after the relevant user/owner decisions and evidence are
recorded. Route to `$greenfield-planning` for a new system, to
`$brownfield-impact-analysis` for an existing system, to `$document-purpose`
for a document-only request, and to `$verify-and-handoff` after implementation
or architecture synchronization.

Route a material technology choice or detected specialist ecosystem through
`$technology-selection-and-integration` after the Greenfield/Brownfield
baseline and before implementation. Architecture records required capability
and integration constraints; the technology skill selects products and
specialist procedures.

Route material architecture, design, implementation, and change work through
`$architecture-and-design-patterns` at G5. The architecture baseline supplies
drivers and constraints; the pattern skill evaluates reusable structures and
trade-offs without forcing a pattern or replacing an ADR.

## Exit gate

Do not allow the next material stage when a required architecture artifact is
`conflicted`, a material UC/module boundary is unconfirmed, or a changed
architecture decision lacks an ADR/owner. A draft may support investigation,
but implementation requires the required baseline status and transition
conditions to be explicit.
