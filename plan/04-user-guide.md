# Ordinary developer guide

This guide is for a software developer who does not need to know the internals
of the harness. The harness should feel like a careful teammate: it asks only
for decisions that the developer owns, records what it found, and explains what
it verified.

## What to include in a request

Use this short form when possible:

```text
Goal: what should change or be understood?
Context: new project or existing project? Relevant path or feature?
Success: how will we know it works?
Constraints: compatibility, deadline, technology, security, or scope limits?
Output: code, tests, design, document, explanation, or a combination?
```

A one-sentence request is acceptable. The Router fills in what is obvious and
asks about only material uncertainty.

## What happens after a request

The user sees a short intake summary:

```text
Scope: software engineering
Project state: Brownfield (confidence 0.88)
Fields: backend, API, testing
Action: change
Risk/depth: medium / standard
Next: inspect current endpoint and tests
```

For every software-related request, the harness also checks the architecture
baseline in `docs/architecture/` even when the user did not mention it. If the
baseline is missing or stale, the harness may produce a code-derived draft and
ask the user to confirm UC, FA, QA, external-interface, or module boundaries
before material implementation.

If a decision is needed, the user receives facts, options, recommendation, and
safe default. Answer with a choice or correct the assumptions. Silence is not
treated as approval for a material decision.

## Common user commands

These are natural-language intents, not mandatory commands:

```text
Explain the current status of TASK-001.
Show the open decisions.
Continue TASK-001 after my answer.
Pause TASK-001 and write a handoff.
Cancel TASK-001 because <reason>.
Review the proposed design without changing files.
Run the verification again.
Show what evidence supports REQ-001.
```

To change the harness itself, say what should be upgraded and why. The harness
first reads all of `plan/`, the active registry, and the affected skills, then
returns a per-file change plan and waits for approval before editing anything:

```text
Upgrade the harness so <new requirement>. Preserve the current sequence and
gates where possible, show affected files and risks, and wait for my approval.
```

To publish or refresh the human-readable overview, use:

```text
Create/update the self-contained harness overview HTML from the current plan
and active registry. Use the default docs/harness/index.html unless it conflicts
with an existing document owner.
```

The overview is a derived guide. The Markdown files in `plan/` and the active
registry remain authoritative.

## Worked example: Brownfield feature

Request:

```text
Add cursor pagination to the existing GET /users endpoint. Keep old clients
working and update tests and API docs.
```

Expected interaction:

1. The Router classifies this as Brownfield, backend/API/testing/documentation,
   standard risk/depth because compatibility is explicit.
2. It records branch, base commit, run/test commands, current endpoint behavior,
   API contract, and existing tests.
3. It writes an impact record covering controller/service/query modules, old
   response shape, database indexes, regression tests, and API docs.
4. If cursor format or compatibility policy is unclear, it asks one bounded
   question before editing.
5. It selects API design and TDD skills if approved and available; otherwise it
   follows the core test-and-contract procedure.
6. It creates a task slice with acceptance criteria:

   ```text
   Given an existing client using the old response
   When it calls GET /users without cursor parameters
   Then the old response remains valid

   Given a client requesting the next page
   When it supplies a valid cursor
   Then the next page and next cursor are returned
   ```

7. It implements, runs the prescribed tests, updates the API guide, and writes
   a handoff containing changed files, validation, and residual risks.

The user does not need to manage sub-agents. Deep mode may add reviewers, but
the Router owns the final issue ledger and asks the user when a product or
compatibility choice remains.

## Worked example: document-only request

Request:

```text
Document how to run the service locally for new team members.
```

The Router classifies the request as documentation with purpose `operate` or
`teach`, audience `new team members`, and type `guide` or `manual`. It checks
whether a current document exists, records the run commands as evidence, and
creates only the missing sections. It does not create an ADR, code task, or
Brownfield impact record unless the document work discovers a real system
change.

## Status meanings

| Status | Meaning | User action |
| --- | --- | --- |
| `active` | work is progressing | none unless asked |
| `waiting_user` | a decision or approval is required | answer the pending question |
| `blocked` | progress requires access, tool, or recovery | provide access/choice or stop |
| `failed` | an operation failed | inspect error and retry/repair |
| `cancelled` | user or policy stopped the task | start a new run if needed |
| `complete` | acceptance and verification are evidenced | review handoff |

## When a task is complete

The final response must state:

- what changed or was produced;
- which requirements and acceptance criteria were addressed;
- tests/checks run and their results;
- documents updated or intentionally not created;
- assumptions, waivers, and residual risks;
- the next action, if any.

“Files changed” alone is not completion.

## Recovery

If a session ends unexpectedly, start a new session in the same project and say
`Continue TASK-<id>`. The Router reads `state.json`, `events.ndjson`, and
`handoff.md`. If state is corrupt, it preserves the original, reports the
repair path, and does not guess a new state. If you want to abandon the task,
say `Cancel TASK-<id> because <reason>`.

## Safe answers to common questions

- If asked to choose between product priorities, choose or state that the user
  owns the decision.
- If a tool is missing, allow the core fallback or provide the tool explicitly;
  do not claim the check ran.
- If an external or destructive action is proposed, confirm its exact target,
  environment, scope, and rollback before approving.
- If the Router misunderstood the project state, correct it; the correction is
  recorded and the affected plan is re-evaluated.
