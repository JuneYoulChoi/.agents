---
name: document-purpose
description: Classify a documentation request by purpose, audience, authority, lifetime, detail, and source evidence before creating or updating it. Use for reports, seminar materials, manuals, guides, history/change records, references, decisions, specifications, API documentation, and cases where required documentation is missing or stale.
---

# Document Purpose

Use this skill before drafting or changing material documentation. A document is
not complete merely because it is well written; it must fit its audience and be
grounded in the right evidence.

## Entry gate

Require an intake record. If the request is software-related, inspect
`docs/architecture/` and route architecture documents through
`$architecture-baseline-and-design`; use this skill for the document's purpose,
audience, authority, and format. Do not let a generic document classification
silently bypass an architecture baseline for a software design or change.

## 1. Classify the document

Record a brief before writing:

```yaml
type: report | seminar | manual | guide | history | reference | decision | spec | architecture_baseline | architecture_view | architecture_decision | architecture_sync
purpose: inform | decide | operate | teach | record | comply
audience: ''
authority: draft | team_approved | externally_approved
lifetime: temporary | versioned | living | archival
detail: summary | standard | deep
owner: ''
location: ''
review_trigger: ''
sensitivity: public | internal | restricted
```

Ask the user when purpose, audience, authority, or location is material and
unknown. Do not turn a proposal or historical inference into an approved fact.

## 2. Gather evidence and decide whether documentation is needed

Inspect existing documents, code/contracts, tests, approved decisions, and
subject-matter sources. Mark facts as observed, inferred, or assumed. When a
needed document is absent or stale, create or update the smallest
fit-for-purpose artifact only if type, purpose, audience, location, and owner
are known. Otherwise record the gap and ask.

Treat policy, compliance, externally published, legally significant, or
owner-controlled documents as protected; request the required approval before
changing them.

## 3. Use the right structure

| Type | Minimum structure |
| --- | --- |
| report | purpose, findings, evidence, recommendation, risks |
| seminar | audience, narrative, key messages, visuals/diagrams, references |
| manual | prerequisites, steps, expected results, failure recovery |
| guide | goal, concepts, recommended path, examples, boundaries |
| history | dated events, decision/change, evidence, consequence |
| decision | context, options, decision, rationale, consequences |
| spec | scope, requirements, contracts, acceptance criteria, exclusions |
| architecture_baseline | current evidence, status, boundaries, gaps, confirmations |
| architecture_view | stakeholder concerns, viewpoint, model kinds, scope, elements, relationships, correspondence/consistency rules, notation, evidence |
| architecture_decision | context, options, decision, rationale, consequences, owner |
| architecture_sync | expected architecture, observed implementation, drift, action |

## 4. Finish with a document record

For a project document workflow, pass purpose, sources and output boundaries to
`$workflow-composition`. Document-only work uses source/link/claim verification
and does not activate authored-code quality or every detected language. Preserve
decision rationale and uncertainty when shortening text. Format-specific
candidate packages are not active until separately reviewed and registered.

Return the classification, evidence sources, changed or proposed document,
review status, and this transition. Update trace links when a requirement, API,
decision, or operational process changed.

```yaml
transition:
  next_stage: clarification | execution | verification | handoff
  next_skill: ''
  entry_conditions: []
```

Route implementation-related work to `$verify-and-handoff` only after
documentation matches the verified artifact.
