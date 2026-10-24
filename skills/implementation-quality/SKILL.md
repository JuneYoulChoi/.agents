---
name: implementation-quality
description: Apply language-neutral implementation-quality rules only to authored code that is being created, changed, reviewed, or verified. Use for correctness, simplicity, coupling, state, lifecycle, errors, testability, API/data boundaries, concurrency, distributed behavior, security, performance, or real-time constraints; do not activate for documentation-only, generated-code-only, or unaffected detected-language work.
---

# Implementation Quality

Apply the smallest evidence-backed rule set to the authored code in scope. This
is a G6 implementation check, not a second architecture, ecosystem, or language
review. A long checklist is not evidence that a change is good.

## Entry gate

Require intake, the architecture checkpoint, the applicable Greenfield or
Brownfield result, and at least one authored code boundary in scope. Consume
accepted `PATTERN-*`, `TECH-*`, and `IMPL-*` results when they exist. Return
`not_applicable` for documentation-only, generated-code-only, configuration-
data-only, or unaffected-language work.

Start with an applicability scan. Every activated profile must have:

- an observed requirement, QAS, interface, code shape, or failure signal;
- a bounded authored path or module;
- an expected implementation outcome; and
- a verification method.

If one is missing, keep the profile suppressed with a reason. Do not activate a
profile merely because its principle is generally desirable.

## 1. Load only applicable profiles

Always read [core](references/core.md) for an applicable authored-code task.
Read additional references only for matching evidence:

- [object-oriented](references/object-oriented.md) for changed class,
  interface, polymorphism, or responsibility boundaries;
- [functional](references/functional.md) for functional state/transform
  pipelines or side-effect boundaries;
- [data-oriented](references/data-oriented.md) for layout, locality, batching,
  or throughput-driven data processing;
- [API and data](references/api-and-data.md) for public/internal contracts,
  schemas, persistence, transactions, or migrations;
- [concurrency](references/concurrency.md) for threads, tasks, async work,
  shared state, cancellation, queues, or shutdown;
- [distributed systems](references/distributed-systems.md) for network calls,
  messaging, partial failure, retries, ordering, or delivery semantics;
- [security](references/security.md) for trust boundaries, identity,
  authorization, secrets, sensitive data, or untrusted input;
- [performance](references/performance.md) only for a measured hotspot,
  capacity limit, resource budget, or performance QAS;
- [real-time and embedded](references/realtime-embedded.md) for determinism,
  deadlines, bounded resources, hardware interaction, or safety constraints.

Several profiles may apply to one mixed boundary, but load no adjacent profile
without its own evidence. Use task depth per profile: `light` for a narrow
local check, `standard` for normal behavioral work, and `deep` only for a
material boundary, high risk, or unresolved evidence conflict.

## 2. Preserve responsibility boundaries

Use these owners instead of repeating their work:

```text
architecture-and-design-patterns -> system/module/collaboration structure
ecosystem skill                  -> framework/protocol/platform contracts
language-engineering             -> language idioms, types, ownership, tooling
implementation-quality           -> language-neutral code quality in this slice
verify-and-handoff               -> acceptance and completion evidence
```

Project conventions remain the Brownfield default when maintained and safe.
Do not introduce an abstraction, dependency, configuration surface, or named
pattern without a demonstrated need. Prefer a local, reversible correction
when it meets the same acceptance criteria.

## 3. Produce a focused result

Consume the accepted `WORK-*` plan without repeating G3 planning. Implement one
coherent acceptance slice; a small diff is not sufficient if it hides root cause
or breaks ownership. A simplicity review checks unnecessary modes, dependencies,
configuration and abstraction while preserving applicable SOLID/GRASP, error
handling, concurrency and lifecycle obligations. Execute native parallel units
only after adapter rechecks and only within the current gate's accepted scope.
Integrate and verify their combined revision before proceeding to G7.

```yaml
implementation_quality:
  status: completed | not_applicable | waiting_user | blocked | failed
  authored_boundaries: []
  activated_profiles:
    - id: core
      depth: light | standard | deep
      authored_boundaries: []
      evidence_ids: []
      expected_outcomes: []
      verification_ids: []
  suppressed_profiles:
    - id: ''
      reason: ''
  findings: []
  changes_or_recommendations: []
  residual_risks: []
  open_points: []
transition:
  next_stage: clarification | execution | verification
  next_skill: ''
  entry_conditions: []
```

## Exit gate

Continue when every activated profile has bounded evidence and verification,
and no material correctness, security, concurrency, compatibility, or
real-time issue remains open. A profile that discovers an architecture,
technology, language, or concern mismatch emits bounded feedback to the
nearest responsible G2–G5 gate; an implementation defect remains at G6.
