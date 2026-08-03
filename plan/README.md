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
