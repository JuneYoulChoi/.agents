---
name: architecture-baseline-and-design
description: Inspect, create, review, or synchronize project architecture documentation before software design or material changes. Use for PRD, SRS, external entities/interfaces, use cases, functional architecture (FA), quality attributes (QA), HLD, LLD, ADRs, layer/infrastructure/architectural/module/C&C views, class/sequence/data/deployment diagrams, missing architecture docs, and code-to-architecture drift.
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

## 1. Locate and assess architecture artifacts

Look for an index and the following logical artifacts (filenames may vary):

```text
PRD, SRS, external entities/interfaces, UC, configuration model,
FA, QA/QAS, HLD, LLD, ADR,
layer, infrastructure, architectural, module, C&C, data, runtime views,
class, sequence, context, deployment diagrams
```

Record path, revision/date, owner, authority, freshness, and source links. A
document is not confirmed merely because it exists. Compare its claims with
approved requirements, tests, code, runtime configuration, and observed
behavior.

## 2. Use the architecture trace

Use the following relation, allowing one-to-many and many-to-one links:

```text
PRD / SRS
  -> External Entity / External Interface
  -> UC
  -> FR / FA
  -> QA / QAS
  -> HLD
  -> ADR
  -> LLD / Module / Configuration Contract
  -> Views / Diagrams
  -> TASK / CODE / TEST / OPERATIONS
```

Treat `FA` as Functional Architecture and `QA` as Quality Attribute. Keep
quality assurance/testing activities labelled `QA testing` to avoid ambiguity.
Do not claim that every UC automatically produces one FA or QA; derive them
from UC, interfaces, constraints, and quality goals and record the evidence.

## 3. Handle a missing or stale baseline

If architecture documents are absent or stale, inspect code, tests, API
contracts, schemas, deployment configuration, and operational evidence. Produce
a draft baseline with `observed`, `inferred`, and `assumed` claims. At minimum
identify:

- external entities and interfaces;
- UC candidates and their actors/boundaries;
- FA candidates and responsibilities;
- QA/QAS candidates and measurable scenarios;
- HLD boundaries and dependencies;
- LLD/module candidates and ownership;
- relevant layer, infrastructure, C&C, runtime, class, and sequence views;
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

## 4. Greenfield and Brownfield modes

For Greenfield, create or update the minimum PRD/SRS/UC/FA/QA/HLD/ADR/LLD
artifacts needed for the requested depth before implementation planning.

For Brownfield/Hybrid, establish the current baseline first, map code and
tests to the existing architecture, and identify impacted UC, FA, QA, modules,
views, ADRs, and documents. Let `$brownfield-impact-analysis` decide
`extend`, `new`, or `mixed` after this evidence is available.

## 5. Produce the architecture record and transition

```yaml
architecture:
  status: confirmed | draft | missing | stale | conflicted
  root: docs/architecture/
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
  evidence: []
  user_confirmations_needed: []
  open_issues: []
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

## Exit gate

Do not allow the next material stage when a required architecture artifact is
`conflicted`, a material UC/module boundary is unconfirmed, or a changed
architecture decision lacks an ADR/owner. A draft may support investigation,
but implementation requires the required baseline status and transition
conditions to be explicit.
