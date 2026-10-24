# Five-layer update review — 2026-10-24

## Scope and outcome

User-authorized update of the five-layer responsibility view, existing G0–G7
routing, conditional persona/delegation planning, core procedures, adapters,
contracts and derived overview. Existing project/architecture/user-decision
checks and specialist selectors are preserved. One new core skill,
`workflow-composition`, brings the active total to 25.

## Candidate review

All 110 downloaded packages / 126 SKILL.md entrypoints were metadata-screened.
15 packages supplied selected procedural ideas; 95 remain deferred for scoped
package review. No upstream package was promoted or executed. No existing core
skill was replaced without evidence. See [adoption decisions](skill-adoption.md)
and [complete candidate inventory](../../registry/skill-candidate-review.json).
The inventory records coverage owners and specialist gaps, not equivalence.

## Findings corrected

- Replaced Deep-only delegation wording with evidence, authority and capability
  conditions; preserved single-agent default and shared-resource serialization.
- Distinguished five responsibility layers, L0–L7 implementation components and
  G0–G7 routing so they cannot be mistaken for three sequential pipelines.
- Added composition after impact/requirements, before specialist execution;
  retained existing specialized language, ecosystem and quality routes.
- Added revisioned work-unit refinement to the Runner: G3 results can update
  units but cannot change authority, risk, user intent or capability.
- Updated the exact composite-route expectation for the added G3 skill and
  corrected document-only fixtures to check empty implementation branches.
- Added actual active skill names and local source links to the HTML overview.
- Replaced obsolete incoming locations with the category/source/package layout.
- Excluded interpreter/test caches from source hashing so a local cache cannot
  invalidate an otherwise unchanged portable source snapshot.

## Verification

- Baseline: 17 runtime tests and 31 integration fixtures passed.
- Updated: 36 runtime/documentation tests and 37 integration fixtures passed.
- New skill metadata validation passed; `git diff --check` passed.
- Candidate hashes, active gate placement, Markdown/HTML links, no remote HTML
  resources, required overview sections and 25 active entries were checked.
- Shared source/template/active-registry pins were regenerated and checked after
  source edits. Source revision identifies a working-tree snapshot, not a release.

Tests exercise dependency cycles, unknown dependencies, overlapping writer/reader
paths, shared resources, read-only personas, missing capability/authority,
blocked-route fallback, risk floors, tampered plans, plan propagation and
unit refinement without privilege expansion. The Runner stays serial; native
adapters own actual agent dispatch within the current accepted skill.

## Limits and remaining decisions

No native agent integration benchmark, external tool execution, hardware test,
full candidate-package security/license audit, browser visual inspection or
formal standards conformance assessment was performed. HTML parsing/link and
structural checks are not a full accessibility audit. No speedup or token saving
is claimed. Candidate promotion and target-project upgrades remain separate
scoped tasks; nothing was installed into an external target project.

## Handoff

The authoritative entry is [five-layer workflow](../../plan/08-layered-workflow.md).
The [HTML overview](index.html) is derived. Changes remain in the working tree;
no commit, push or deployment was performed. The baseline backup, approval scope,
per-file change record and complete check logs are retained under
`/tmp/harness-layer-upgrade-20261024/` for this maintenance session. Rollback must
restore only those changed paths while preserving later user edits.
