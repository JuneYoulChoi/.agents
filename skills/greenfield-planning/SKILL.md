---
name: greenfield-planning
description: Convert a new software idea, product capability, service, API, UI, or system into a traceable and testable delivery plan. Use after intake identifies Greenfield work or a new capability whose goal, users, scope, and constraints need requirements, quality scenarios, architecture decisions, tasks, tests, and documentation planning before implementation.
---

# Greenfield Planning

Use this skill after `$intake-and-route`. Do not use it to skip impact analysis
for an existing system; route Hybrid work through Brownfield impact first.

## Entry gate

Require an intake record and an architecture record from
`$architecture-baseline-and-design`. If the architecture baseline is missing,
stale, conflicted, or has unconfirmed material UC/FA/QA/module boundaries,
return to that skill or `$intake-and-route`; do not silently design around the
gap.

## 1. Confirm the product boundary

Record goal, target users, success criteria, constraints, excluded scope, and
the desired outcome. Ask the user when concept, priority, audience, acceptance
trade-off, or authority is material and unresolved. Label proposals as
proposals, not confirmed requirements.

## 2. Define the smallest useful requirements set

Create stable IDs and a concise trace:

```text
GOAL -> REQ/FR -> NFR/QAS -> STD -> ADR/PATTERN -> TECH -> IMPL -> CONFIG -> TASK -> TEST -> DOC
```

Write functional requirements as observable outcomes. For important quality
attributes, use a scenario with context, stimulus, expected response, and a
measurable response measure. Do not create an ADR for a trivial, reversible
choice; create one for material architecture, data, integration, security, or
public-contract decisions.

## 3. Design before implementation

Choose the minimum architecture that satisfies the requirements. State system
boundaries, major components, data/API contracts, failure behavior, security
and privacy constraints, operational needs, and alternatives considered.

Carry forward applicable `STD-*` profiles from the architecture record and
their guidance/alignment/conformance intent. Use
`$architecture-and-design-patterns` to evaluate architecture and design scopes
from UC/FA/QAS drivers before implementation; an explicit `not_applicable`
result is valid and safer than forcing a pattern. A material architecture
pattern decision requires a `PATTERN-*` artifact and ADR.

Derive technology capabilities before choosing a product. Route material
runtime, library, framework, protocol, platform, simulator, middleware, build,
or orchestration choices through `$technology-selection-and-integration`.
After an ecosystem is selected, route every implementation-producing module
through the matching ecosystem skill and `$language-engineering`; do not choose
a language or adjacent platform only because an example uses it.

When deploy-time or runtime values may vary, define a configuration contract
before implementation: classify code/build/deploy/runtime/secret values, name
supported sources and precedence, require typed validation, and document safe
defaults and secret handling. Route the design slice through
`$configuration-and-environment-management`; do not make every constant
configurable.

When a decision needs independent expertise, request focused review rather
than a generic debate. Preserve dissent and escalate unresolved material
product choices to the user.

## 4. Build an executable delivery plan

Split work into coherent slices. Every slice needs a goal, acceptance criteria,
implementation boundary, verification command or method, and documentation
effect. Prefer end-to-end vertical slices over technology-layer-only tasks.

Use this minimum output:

```yaml
goal: GOAL-001
requirements: [REQ-001]
quality_scenarios: [QAS-001]
decisions: [ADR-001]
standards: [STD-001]
patterns: [PATTERN-001]
technologies: [TECH-001]
implementation_profiles: [IMPL-001]
tasks:
  - id: TASK-001
    outcome: ''
    acceptance: []
    verifies: []
    document_effect: create | update | none
open_points: []
transition:
  next_stage: execution | clarification
  next_skill: ''
```

Record this result as one `G3` workflow branch. It may join document,
technology, configuration, testing, or other concern branches emitted for the
same request; it does not preload or execute those skills itself.

## 5. Guard implementation

Do not begin material implementation until the current slice has acceptance
criteria and a verification plan. If new evidence changes scope, return to
requirements or design. For a document-only outcome, route to
`$document-purpose`; for completion, route to `$verify-and-handoff`.
