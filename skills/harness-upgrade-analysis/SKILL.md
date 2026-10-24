---
name: harness-upgrade-analysis
description: Analyze and plan changes to the shared engineering harness before modifying its plan, active skills, registry, routing, gates, sequences, contracts, or adapters. Use for requests to upgrade, extend, replace, deprecate, reorganize, or synchronize the harness, including changes prompted by a new requirement or a missing skill.
---

# Harness Upgrade Analysis

Create a read-only, evidence-based change plan for the harness itself. Preserve
the existing concept, direction, sequence, and contracts by default; prefer a
small extension or wrapper over a broad rewrite. Do not edit files in this
skill.

## Entry gate

Require an intake record from `$intake-and-route`. If it is absent, stop and
return only:

```yaml
upgrade:
  status: not_started
transition:
  next_stage: intake
  next_skill: intake-and-route
  entry_conditions: [intake_record_required]
```

For a request that changes the harness rather than a project, the harness plan
is the architecture baseline. Do not invoke `incoming/`; it is quarantined
input, not an approved source. Do not use network resources unless a separately
approved research task explicitly requires them.

## 1. Establish the authoritative baseline

Read in this order, progressively:

1. `plan/README.md`, then every `plan/*.md` file. Treat this set as the
   normative statement of requirements, concept, direction, sequence, gates,
   contracts, and implementation phases.
2. `registry/active-skills.json`, its referenced
   `registry/routing-gates.json`, `registry/adapter-manifest.json`, and any
   referenced registry/taxonomy files.
3. Active skill metadata (`SKILL.md` frontmatter and `agents/openai.yaml`) for
   all entries; read full bodies only for skills affected by the request and
   their immediate route neighbors.
4. Platform adapter, fixture, validator, and task-state files when present.

When the request concerns startup or cross-session enforcement, also inspect
the platform bootstrap files (`AGENTS.md`, `CLAUDE.md`), adapter templates,
and the target `harness.json` configuration if present. Distinguish the
instruction-discovery root from the project target root and from the shared
harness source root.

Record the observed revision/date and paths read. Label every conclusion as
`observed`, `inferred`, or `assumed`. If `plan/` is missing, contradictory, or
not readable, do not invent a baseline: report `blocked` or ask the user which
source should govern the upgrade.

## 2. Compare the request with the baseline

Decompose the request into atomic changes. For each change, identify:

- the preserved concept or contract;
- affected sequence stages, gates, transitions, skills, registry entries,
  adapters, fixtures, and user-facing instructions;
- affected forward edges, activation/suppression behavior, feedback targets,
  invalidation boundaries, and retry/escalation behavior;
- compatibility and regression risks;
- unresolved user decisions and a reversible safe default, if one exists.

Assign exactly one change class to every relevant path:

`unchanged | patch | extend | wrapper | replace | deprecate | new`.

Use `wrapper` when a new gate can delegate to an existing workflow without
changing its contract. Use `extend` for additive behavior with backward
compatibility. Use `replace` only when the current contract cannot satisfy the
approved requirement; explain migration and rollback. A path that is merely
reviewed remains `unchanged`.

## Bootstrap and adapter placement contract

Use one authoritative template per platform:

```text
.agents/adapters/codex/AGENTS.md.tmpl
.agents/adapters/claude/CLAUDE.md.tmpl
```

Render thin wrappers into each target project's root:

```text
<target-root>/AGENTS.md
<target-root>/CLAUDE.md
<target-root>/.agents/harness.json
```

The shared template is the source; rendered files are project-local managed
artifacts. Keep wrappers small and refer to the pinned harness source through
`harness.json`; do not copy the full plan into the prompt. The optional global
Codex file (`~/.codex/AGENTS.md`) is for personal defaults only and must not
contain project paths, task state, credentials, or product decisions.
The shared repository's root `AGENTS.md`/`CLAUDE.md` are a separately marked
self-hosted source-entrypoint exception; they are not target wrappers and must
not be treated as a second rendered template.

Resolve the target in this order: explicit `target_root`, then one unambiguous
nearest Git root, then the current directory only when no Git root exists. A
symlink is canonicalized before resolution. An explicit target must exist and
contain the current directory. A nested repository is valid when it is the
unique nearest root; stop only for conflicting explicit/discovered roots,
multiple equally-near roots, Git command errors, an outside current directory,
or a source/target collision. Git-root presence is only a path heuristic; it
does not classify Greenfield or Brownfield state. Never select the shared
harness repository as a target by accident.

The configuration is portable and versioned. It records a local/bundled source
locator/ref and revision/hash, template/protocol version, adapter mappings,
project state root, ordered registry sources/revisions/hashes, enforcement probe
and optional manual guard, and managed-file/config hashes. It must not grant
skill trust or bypass the active registry. Store canonical target/harness-root
fingerprints and selected adapter at runtime, not absolute machine paths in
committed config. Missing/stale approved project sources may fall through;
malformed, tampered, unverified, or failed-integrity sources fail closed.

Default installation is a copy, not a symlink. Same managed hashes are
idempotent. Unknown or user-edited `AGENTS.md`, `CLAUDE.md`, or
`.agents/harness.json` files are never overwritten; report a conflict and ask
for an explicit upgrade. Apply wrapper, config, and managed metadata as one
transaction with a lock and rollback record. Preserve user edits during
rollback. Validate rendered UTF-8 bytes after line-ending normalization and
fail if any bootstrap file exceeds 32 KiB; never truncate or leave unresolved
placeholders.

Prompt files alone cannot enforce MUST rules. Record the adapter enforcement
level as `hook`, `manual`, or `unsupported`. `manual` permits durable state and
limited reversible workspace mutation only with a fresh manual guard/action
record; `unsupported` is ephemeral/read-only and cannot claim resume. All modes
block external, destructive, high-risk, approval-bypassing, or unsafe state
actions. Validate source-relative paths, realpath containment, symlink/permission
policy, LF-normalized UTF-8 bytes (32 KiB hard cap), canonical self-excluded
config hash, and reject patch markers or unresolved placeholders.

## 3. Produce the upgrade plan

Return this YAML record before any implementation begins:

```yaml
upgrade:
  request: ''
  status: analyzed | needs_user_decision | blocked
  baseline:
    plan_revision: ''
    registry_revision: ''
    skill_revision: ''
    evidence: []
  bootstrap:
    target_root: ''
    harness_root: ''
    instruction_files: []
    config_path: ''
    template_revision: ''
    enforcement: hook | manual | unsupported | not_applicable
  preserved: []
  affected:
    - path: ''
      change: unchanged | patch | extend | wrapper | replace | deprecate | new
      reason: ''
      risk: low | medium | high
      compatibility: ''
      affected_contracts: []
      affected_fixtures: []
  conflicts: []
  user_decisions_needed: []
  implementation_order: []
  validation_fixtures: []
  rollback_plan: ''
  transition:
    next_stage: clarification | approval | implementation | verification | handoff
    next_skill: ''
    entry_conditions: []
```

`status: needs_user_decision` is mandatory for product direction, policy,
authority, material compatibility, or a change that would alter the existing
sequence. Provide the facts, options, recommendation, impact, and safe default
in the user questions. Do not silently approve the plan.

## 4. Apply the decision gates

- Do not modify `plan/`, active skills, registry, adapters, or fixtures during
  analysis.
- Require explicit user approval of the material upgrade plan before mutation.
- If a core entry gate, transition contract, or registry trust rule changes,
  classify the impact as at least `medium` and include forward-tests for both
  the old and new paths.
- If evidence conflicts, preserve both claims, identify the source-of-truth
  decision, and stop at `clarification` rather than choosing by preference.
- Limit changes to the requested scope. Do not activate quarantined skills or
  download dependencies as part of an upgrade.

## 5. Implementation and validation handoff

After approval, transition to the implementation owner. The owner applies the
plan in the listed order, validates affected fixtures, updates the plan and
registry together, and then invokes `$verify-and-handoff`. If the HTML overview
is stale after the upgrade, transition to `$harness-overview-html` before final
handoff. A completed upgrade must retain the baseline, approved change record,
validation results, residual risks, and rollback plan.

## Example decision

For “add an architecture-document gate to every software request,” the usual
result is a `patch` to intake routing, a `new` architecture skill, and additive
`extend` changes to Greenfield, Brownfield, document, and verification skills.
Do not mark all existing skills `replace` unless the baseline proves their
contracts are incompatible.

## Composition-aware maintenance

Include the five-layer view, `work_plan` contracts, candidate dispositions and
native delegation boundary in impact analysis. Existing explicit approval of
the bounded upgrade satisfies the control-plane gate; do not ask again solely
because a skill says to seek approval. Candidate metadata review does not
promote packages. Keep active core behavior, candidate evidence and generated
HTML synchronized and validate source/registry pins after the final edit.
