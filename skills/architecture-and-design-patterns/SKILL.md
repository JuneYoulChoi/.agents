---
name: architecture-and-design-patterns
description: Evaluate, select, document, or review architecture and software design patterns when an explicit pattern request or evidenced architecture-structure/design-interaction change affects boundaries, coupling, ownership, testability, deployment, or evolution. Do not use for ordinary local code changes without a structural or collaboration decision.
---

# Architecture and Design Patterns

Use patterns as named design decisions, not as mandatory decoration. A standard
may constrain architecture descriptions, requirements, quality, or lifecycle
evidence; it does not automatically select a software pattern.

## Entry gate

Require intake and the G2 architecture record. Greenfield work requires an
accepted planning/design slice; Brownfield/Hybrid work requires the current
pattern/convention evidence and impact record before recommending structural
change. Do not mutate code in this skill. Return to clarification when a choice
depends on product priorities or an unconfirmed UC/FA/QAS/module boundary.

This is a G5 specialist review. Activate it for an explicit pattern scope,
`architecture_structure`, `design_interaction`, or an explicit architecture
design/review request. Action `implement` or `change` alone is insufficient.
Use scope `architecture`, `design`, or both. A pattern failure reopens G5; a requirements
or architecture-driver contradiction reopens G2/G3 instead.

Before loading either reference, require scope overlap, evidence, an expected
decision artifact, and a verification method. If none exists, return
`not_applicable` or keep the branch suppressed without reading the pattern
catalogs.

## 1. Derive drivers before candidates

Record relevant UC, external interfaces, FA responsibilities, QAS and response
measures, constraints, data/consistency needs, deployment/operations, security,
change volatility, team ownership, and existing conventions. In Brownfield
work, name existing patterns and violations as `observed`, `inferred`, or
`assumed`; a recognizable code shape is not proof of original intent.

## 2. Evaluate only the relevant pattern family

For new modules, inspect how much callers must know, where implementation
complexity is contained, and whether tests exercise the actual contract. For
Brownfield work, first establish concrete structural friction; retain existing
seams when they fit. Do not impose an upstream vocabulary, exactly-one-interface
rule, mandatory parallel design contest or fixed number of adapters. Keep
domain language and the project's accepted architecture authoritative.

Read [architecture patterns](references/architecture-patterns.md) only for
system/module/deployment structure. Read [design patterns](references/design-patterns.md)
only for concrete object, component, collaboration, state, integration, or
concurrency responsibilities. Load both only when both scopes are active.

For each plausible candidate record `selected`, `rejected`, `existing`,
`candidate`, or `not_applicable`, plus context, problem, forces, alternatives,
benefits, liabilities, consequences, affected modules/interfaces, QAS impact,
migration/rollback, and verification. Prefer no named pattern when ordinary
composition is clearer. Do not stack patterns to appear comprehensive.

Separate alternatives from composition before comparing them. Candidates are
alternatives only when they address the same decision scope and responsibility
boundary. Patterns at different levels may be compatible parts of one option;
do not present them as a false either/or choice. Keep the shortlist to the
smallest decision-complete set and include direct composition or no named
pattern when it is genuinely viable.

## 3. Recommend without taking the user's decision

For every materially viable candidate provide its fit, recommendation reason,
benefits, liabilities/trade-offs, positive and negative QAS effects, affected
boundaries, migration/rollback cost, and verification approach. Identify one
recommended candidate when evidence supports it, explain why it is preferred,
and state the conditions that would make another candidate preferable. Do not
use popularity, pattern count, or false numeric precision as a selection rule.

When two or more candidates remain materially viable and differ in a user-owned
quality priority, system boundary, ownership model, operational cost, migration
risk, or other consequential trade-off:

1. set `decision.status` to `user_decision_required`;
2. keep every viable option as `candidate` and do not mark one `selected`;
3. present a compact comparison and the evidence-backed recommendation;
4. create a material open issue owned by the user; and
5. transition to `clarification` before material design or execution.

After the user's answer, record the selected candidate, decision evidence, and
any rejected or retained alternatives. An existing accepted ADR or explicit
user requirement may satisfy the decision only while its scope and assumptions
remain valid. A single viable option may be recorded as `single_viable`; an
explicit no-pattern result is `not_applicable`. Do not open a decision gate for
cosmetic alternatives or local, easily reversible idioms with no meaningful
driver or consequence difference.

Use this question shape:

```text
Pattern decision needed: <decision scope>
Drivers and constraints: <UC/FA/QAS and hard constraints>
Options: <candidate, fit, benefits, trade-offs, and change conditions>
Recommendation: <candidate and evidence-backed reason>
Decision requested: <the exact option or composition the user must choose>
Safe default: keep the current/draft structure and do not begin material execution
```

## 4. Reconcile with ecosystem and language rules

Use this precedence:

```text
user-approved requirements and architecture decisions
> external-interface and quality contracts
> maintained Brownfield structure and project conventions
> official ecosystem lifecycle/binding rules
> selected pattern rationale
> language idioms and general recommendations
```

The pattern record constrains later ecosystem and `$language-engineering`
implementation. It never overrides generated-code ownership, framework
lifecycle, protocol compatibility, or language safety. If a material
architecture pattern changes a system boundary, record an ADR.

## 5. Produce the pattern decision

Produce one `PATTERN-*` record per material decision scope. A decision may
cross architecture and design scopes, but unrelated decisions use separate
records so their candidates and user selections cannot be conflated.

```yaml
pattern_review:
  id: PATTERN-001
  scopes: [architecture, design]
  drivers: []
  existing_patterns: []
  candidates:
    - candidate_id: PATTERN-OPTION-001
      name: ''
      status: candidate | selected | rejected | existing | not_applicable
      decision_scope: ''
      fit: ''
      recommendation_reason: ''
      benefits: []
      liabilities: []
      quality_attribute_effects: []
      affected_artifact_ids: []
      migration_and_rollback: []
      verification_ids: []
  decision:
    status: not_applicable | single_viable | user_decision_required | user_selected | existing_decision
    decision_scope: ''
    recommended_candidate_id: null
    recommendation_reason: ''
    conditions_that_change_recommendation: []
    selected_candidate_id: null
    decision_evidence_ids: []
  selected: []
  rejected: []
  affected_modules: []
  quality_attribute_effects: []
  decision_ids: []
  implementation_constraints: []
  migration_and_rollback: []
  verification: []
  open_points: []
transition:
  next_stage: clarification | design | execution | verification
  next_skill: ''
  entry_conditions: []
```

## Exit gate

Material execution may continue when the result is an evidenced selection or
an explicit `not_applicable`; selecting a pattern is not mandatory. Block when
a chosen pattern lacks a driver, contradicts an accepted architecture or
external contract, has no owner/migration path in Brownfield work, or cannot be
verified against its claimed QAS benefit. Also block material execution when
multiple materially viable candidates remain and `decision.status` is
`user_decision_required`, or when a purported user selection lacks decision
evidence.
