---
name: harness-overview-html
description: Create or update a self-contained, human-readable HTML overview of the engineering harness, including its concept, requirements, architecture trace, sequence, gates, Greenfield/Brownfield routing, active skills, registry, and upgrade process. Use when people need a visual guide, reference, onboarding page, or current-state summary of plan/ and .agents/.
---

# Harness Overview HTML

Publish the current harness as a narrative HTML guide that a developer with
limited agent experience can follow. Make the source evidence and document
status visible; never turn missing or conflicting plan content into invented
facts.

## Entry gate

Require an intake record. Require a current harness baseline or an approved
`harness-upgrade-analysis` record before generating an overview. If the request
describes a software project as well as the harness, require the project
architecture baseline from `$architecture-baseline-and-design` too. If a gate
is missing, stop and return:

```yaml
overview:
  status: not_started
transition:
  next_stage: intake | discovery | clarification
  next_skill: intake-and-route | harness-upgrade-analysis | architecture-baseline-and-design
  entry_conditions: []
```

Classify the document with `$document-purpose` before writing: normally
`guide` for onboarding or `reference` for a durable current-state page. Record
audience, purpose, authority, lifetime, detail level, and output location.

## 1. Read the source of truth

Read all of the following before drafting:

1. `plan/README.md`, then all `plan/*.md` files;
2. `registry/active-skills.json` and every active skill entry's metadata;
3. full `SKILL.md` bodies for the active skills (the overview must explain
   their responsibilities and routes);
4. adapters, validators, fixtures, task-state, and existing overview files if
   they exist.

Record paths, revision/date, and whether each statement is `observed`,
`inferred`, or `assumed`. Mark missing, stale, and conflicting sources
explicitly and link them in the unresolved section.

## 2. Tell the complete story

Use this order so the page has a clear beginning, middle, and end:

1. **Why** — problem, audience, goals, and non-goals.
2. **Concept and direction** — project-independent, dependency-light, Codex /
   Claude-compatible, progressive skill loading, and evidence-first behavior.
3. **Architecture** — the harness layers (global guard, intake/router,
   baseline, workflow skills, verification/handoff, registry/adapters) and
   their responsibilities.
4. **Traceability** —
   `PRD/SRS -> external entity/interface -> UC -> FA -> QA/QAS -> HLD -> ADR -> LLD -> views/diagrams -> code/tests/operations`.
   Explain that FA means Functional Architecture and QA means Quality
   Attribute, and link to the project architecture documents when present.
5. **Sequence** — intake, clarification, discovery, architecture, impact,
   assembly, deliberation, design, execution, verification, and handoff; show
   Greenfield, Brownfield, Hybrid, and unknown branches.
6. **Gates** — intent, ambiguity/authority, architecture, impact,
   documentation gap, mutation, verification, and handoff conditions.
7. **Skills and registry** — active skill name, purpose, entry condition, next
   transition, mutation/network policy, and platform coverage.
8. **Upgrade path** — baseline read, impact plan, user approval, implementation,
   validation, registry/plan synchronization, and overview refresh.
9. **How to use and resume** — what a user submits, how to answer decisions,
   where artifacts live, and how status/transition records resume a session.
10. **Sources and unresolved items** — provenance, generated timestamp,
    stale/missing documents, assumptions, and decisions still required.

## 3. Generate a safe, portable artifact

Default to `docs/harness/index.html` when no location is specified; record the
default in the document-purpose record and ask only if that location conflicts
with an existing owner-controlled document. Create one self-contained HTML file
for the MVP:

- inline CSS and minimal inline JavaScript only;
- no external fonts, CDNs, images, analytics, network calls, or runtime build
  dependency;
- responsive and printable layout with semantic headings, keyboard-visible
  focus, sufficient contrast, and text alternatives for diagrams;
- use inline SVG for a simple sequence/architecture map, or a labelled textual
  diagram when SVG would obscure the meaning;
- link to local source files with relative links that resolve from the output;
- show `generated_at`, source revision, document purpose/status, and evidence
  labels on the page.

Do not rewrite the plan or active skills while generating the overview. If the
overview reveals a stale or missing source, record it and transition to the
appropriate upgrade, architecture, document, or user-decision stage.

## 4. Validate before handoff

Check the generated artifact and report each result:

- required sections and headings are present;
- HTML parses with an available standard-library or local validator;
- no `http://`, `https://`, remote `<script>`, remote stylesheet, or CDN
  reference exists;
- every relative source link resolves;
- diagrams have labels or text alternatives;
- plan and registry provenance is visible;
- unresolved, inferred, and assumed statements are not presented as facts.

Return this record and then transition to verification:

```yaml
overview:
  status: draft | published | needs_user_decision | blocked
  purpose: guide | reference
  audience: ''
  output_path: docs/harness/index.html
  source_revision: ''
  sections: []
  unresolved: []
  validation:
    required_sections: pass | fail
    parses: pass | fail | unavailable
    no_network_references: pass | fail
    links_resolve: pass | fail | unavailable
    accessibility_review: pass | fail | partial
transition:
  next_stage: verification | clarification | handoff
  next_skill: verify-and-handoff | intake-and-route | harness-upgrade-analysis
  entry_conditions: []
```

Use `$verify-and-handoff` to confirm the page is synchronized with the pinned
plan and registry revision. Regenerate it after an approved harness upgrade.
