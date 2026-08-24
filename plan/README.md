# Plan reading order

This directory is the source of truth for implementing and using the harness.
Do not start by downloading or activating every skill.

For any request to modify the harness itself, read this directory completely
before changing `skills/`, `registry/`, routing, gates, sequences, contracts,
or adapters. Use `$harness-upgrade-analysis` to produce a per-file impact and
approval plan first. After an approved change, use `$harness-overview-html` to
refresh the self-contained human guide (default: `docs/harness/index.html`).
The plan remains authoritative; the HTML is a derived view and never replaces
the Markdown contracts.

Platform startup is an adapter concern. Canonical templates live under
`adapters/codex/` and `adapters/claude/`; a target project receives thin,
managed root instruction files and `.agents/harness.json`. The target config
pins source/template revisions, registry order, state containment, and
enforcement capability. It is not task state and cannot grant skill trust.

Skill selection uses the deterministic `G0`–`G7` manifest in
`registry/routing-gates.json`: the taxonomy is hierarchical, gates accept and
emit multiple branches, and bounded backward feedback reopens only the nearest
responsible gate. This is an explainable routing graph, not a trained neural
model.

An optional, dependency-free reference Router, fixed-stage Runner, target-local
State store, Validator, conflict-safe Bootstrap installer, and replaceable
fixture driver live in `scripts/`; executable scenarios live in `fixtures/`
and focused runtime checks in `tests/`. Their JSON protocol is portable and
does not make Python a target-project or adapter requirement. The Router also
emits a vendor-neutral `execution_profile`; only the platform adapter maps its
role and `low/medium/high` reasoning recommendation to an available model.
G2 also evaluates international-standard applicability, while G5 performs an
evidence-backed architecture/design-pattern review only when a structural or
interaction signal makes it applicable. G6 applies one common implementation-
quality skill to authored code and progressively loads only evidenced quality
profiles.
When several materially viable alternatives remain in one decision scope, G5
shows their rationale and trade-offs, recommends one, and waits for the user's
selection instead of silently choosing it.

## For an implementer

1. [00-operating-model.md](00-operating-model.md) — purpose, rules, sequence.
2. [05-glossary.md](05-glossary.md) — terms and enums.
3. [03-contracts-and-fixtures.md](03-contracts-and-fixtures.md) — machine
   contracts and pass/fail fixtures.
4. [02-implementation-guide.md](02-implementation-guide.md) — components,
   stage contracts, Router algorithm, and phased build.
5. [06-platform-adapters.md](06-platform-adapters.md) — Codex/Claude mapping.
6. [07-skill-governance.md](07-skill-governance.md) — review and promotion.
7. [01-industry-patterns-to-adopt.md](01-industry-patterns-to-adopt.md) —
   rationale and external design inputs.

## For an ordinary developer

Read [04-user-guide.md](04-user-guide.md). The user should not need to read
the implementation contracts to submit a task, answer a decision, resume a
task, or understand completion.

## Promotion gate

The plan is implementable when a new developer can build the MVP and pass the
required fixtures without inferring a missing path, enum, state transition,
permission rule, artifact location, or completion condition. Optional
delegation and evaluator features remain disabled until their own fixtures pass.
