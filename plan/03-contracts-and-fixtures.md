# Machine contracts and executable fixtures

This file is the implementation contract. A validator may reject additional
unknown fields for the MVP only when they are not namespaced; adapters may add
`x-<platform>-*` fields. IDs are stable within a task and are never silently
reused.

## State contract

Canonical location:

```text
<project>/.agents/state/<task_id>/state.json
<project>/.agents/state/<task_id>/events.ndjson
<project>/.agents/state/<task_id>/handoff.md
<project>/.agents/state/<task_id>/artifacts.json
```

Minimal `state.json`:

```json
{
  "schema_version": 1,
  "task_id": "TASK-001",
  "run_id": "RUN-001",
  "revision": 3,
  "status": "active",
  "stage": "impact",
  "session_scope": "software_engineering",
  "project_state": "brownfield",
  "classification": {
    "fields": ["backend", "api", "testing"],
    "action": "change",
    "risk": "medium",
    "depth": "standard",
    "confidence": 0.92,
    "evidence_ids": ["EVD-001"]
  },
  "intent": {
    "goal": "Add pagination to the user endpoint",
    "success_criteria": ["Existing clients remain compatible"],
    "constraints": [],
    "confirmed_by_user": true
  },
  "pending_question": null,
  "open_issue_ids": ["ISSUE-001"],
  "required_artifact_ids": ["IMPACT-001", "TESTPLAN-001"],
  "validation_status": "not_run",
  "last_transition": {
    "from": "discovery",
    "to": "impact",
    "reason": "Baseline recorded",
    "actor": "router",
    "at": "2026-08-03T00:00:00Z"
  }
}
```

## State invariants

The validator MUST enforce these invariants:

1. `complete` requires no material `open` or `user_decision` issue and every
   required validation is `passed` or has an authorized, unexpired `waived`
   record.
2. `waiting_user` requires `pending_question.question_id`; no material
   mutation is allowed after the question until an answer event is recorded.
3. `blocked` requires a blocker, owner, and recovery/next action.
4. `failed` requires an error record, `retryable`, and `retry_count`.
5. `cancelled` requires actor, reason, and timestamp. A terminal task cannot be
   mutated; reopening creates a new run or an explicit `reopened` event.
6. `unknown` project state permits read-only discovery only.
7. `incoming` or `deprecated` skills cannot be returned by skill resolution.
8. External or mutating tool calls require an approved `action_id`.
9. Every material claim links to at least one evidence ID; every requirement has
   a verification link or an authorized waiver.
10. Every state write appends an event and increments `revision` using an
    atomic write or optimistic-lock check.

## Event contract

Every line of `events.ndjson` is one JSON object:

```json
{
  "event_id": "EVT-004",
  "schema_version": 1,
  "task_id": "TASK-001",
  "run_id": "RUN-001",
  "revision": 4,
  "type": "state_transition",
  "from": "impact",
  "to": "assembly",
  "actor": "router",
  "reason": "Impact record passed validation",
  "artifact_ids": ["IMPACT-001"],
  "at": "2026-08-03T00:01:00Z"
}
```

Supported event types are `task_created`, `classification_recorded`,
`question_asked`, `question_answered`, `evidence_added`, `artifact_written`,
`skill_selected`, `delegate_started`, `delegate_finished`, `action_requested`,
`action_approved`, `action_executed`, `validation_recorded`,
`state_transition`, `handoff_written`, `task_cancelled`, and `error_recorded`.

## Skill manifest contract

The registry index is machine-readable. One reviewed entry looks like this:

```json
{
  "id": "testing.tdd",
  "version": "1.0.0",
  "entry": "skills/tdd/SKILL.md",
  "source": {
    "repository": "https://github.com/mattpocock/skills",
    "ref": "main",
    "commit": "PIN_REQUIRED_BEFORE_PROMOTION",
    "license": "MIT",
    "downloaded_at": "2026-08-03"
  },
  "integrity": {"sha256": "PIN_REQUIRED_BEFORE_PROMOTION"},
  "capabilities": ["test_design", "red_green_refactor"],
  "inputs": ["intent", "impact", "code_context"],
  "outputs": ["test_plan", "test_artifacts", "transition"],
  "required_tools": ["read", "write", "test_runner"],
  "network_access": "none",
  "data_access": "workspace",
  "mutation": "workspace",
  "dependencies": [],
  "platforms": {"codex": "adapter_required", "claude": "adapter_required"},
  "trust": "approved",
  "transition_contract": "skill-result-v1"
}
```

An `incoming` entry may have a source URL and description but MUST NOT have
`trust: approved` and MUST NOT be resolvable. Promotion requires commit, hash,
license, complete skill reading, dependency review, and a reviewer record.

## Skill result contract

```json
{
  "skill_id": "testing.tdd",
  "status": "completed",
  "classification_updates": [],
  "evidence_ids": ["EVD-010"],
  "artifact_ids": ["TESTPLAN-001"],
  "assumptions": [],
  "open_issue_ids": [],
  "validation": ["VAL-003"],
  "transition": {"next_stage": "execution", "entry_conditions": []},
  "error": null
}
```

`status` is one of `completed`, `not_applicable`, `blocked`, or `failed`.
Failed or blocked results must include an error and recovery action. A skill
cannot mark the whole task complete.

## Issue ledger and deliberation contract

```json
{
  "issue_id": "ISSUE-001",
  "question": "Should pagination be cursor or offset based?",
  "material": true,
  "evidence_ids": ["EVD-020", "EVD-021"],
  "positions": [
    {"agent": "api-reviewer", "position": "cursor", "reason": "..."},
    {"agent": "compatibility-reviewer", "position": "offset", "reason": "..."}
  ],
  "round": 2,
  "shared_evidence": ["EVD-020"],
  "dissent": ["compatibility risk for old clients"],
  "status": "user_decision",
  "owner": "user",
  "next_action": "Choose compatibility priority"
}
```

Allowed terminal statuses are `resolved`, `accepted_assumption`,
`user_decision`, and `deferred_with_reason`. `open` is non-terminal. The Router
stops deliberation when all material issues are terminal, when no new evidence
appears, when the time/token/cost budget is exhausted, or when a high-risk
 decision requires the user. The default maximum is three rounds per issue.

## Delegation contract

```json
{
  "delegate_id": "DELEGATE-001",
  "role": "api_compatibility_reviewer",
  "question": "Assess pagination compatibility",
  "input_revision": 7,
  "evidence_ids": ["EVD-020"],
  "allowed_paths": ["src/api", "tests/api"],
  "allowed_tools": ["read", "search"],
  "data_tier": "workspace",
  "mutation": "none",
  "timeout_seconds": 300,
  "budget": {"tokens": 12000, "cost_limit": "project_policy"},
  "artifact_path": ".agents/state/TASK-001/delegates/DELEGATE-001.json"
}
```

The default delegate is read-only. Mutation requires a separate worktree or
file lease and a join rule. A stale result whose `input_revision` differs from
the current state is re-run or marked stale; it is never silently merged.

## Authority and validation contracts

An action record MUST include:

```json
{
  "action_id": "ACT-001",
  "requested_by": "user",
  "executed_by": "router",
  "tool": "git",
  "target": "repository/path",
  "environment": "local",
  "risk": "medium",
  "approval_id": "APR-001",
  "approval_status": "approved",
  "scope": "create branch and run tests",
  "expires_at": "2026-08-04T00:00:00Z",
  "before_state": "clean",
  "after_state": "tests passed",
  "rollback_plan": "delete local branch",
  "result": "executed"
}
```

Validation records use this status enum:

```json
{
  "validation_id": "VAL-003",
  "kind": "regression_test",
  "command": "pytest tests/api",
  "expected": "exit code 0",
  "actual": "exit code 0",
  "environment": "python 3.11",
  "artifact_revision": 9,
  "status": "passed",
  "verifier": "evaluator",
  "reproducible": true,
  "waiver": null
}
```

Allowed statuses are `passed`, `failed`, `not_run`, `not_applicable`,
`blocked`, and `waived`. A waiver requires owner, reason, expiry, and residual
risk. `not_run` is never equivalent to `passed`.

## Traceability contract

Use typed IDs: `GOAL-*`, `REQ-*`, `FR-*`, `NFR-*`, `QAS-*`, `ADR-*`, `TASK-*`,
`CODE-*`, `TEST-*`, `DOC-*`, and `EVD-*`. Relations are:

```text
defines, refines, constrains, decides, implements, verifies, documents,
supersedes, derived_from, waived_by
```

The validator reports orphan requirements, dangling links, requirements with
no verification, and documents that claim a changed API without an API
artifact. Light work may use a compact `TASK -> TEST` link; standard and deep
work require all applicable links and an explicit waiver for omitted entities.

## Document metadata contract

```json
{
  "document_id": "DOC-001",
  "type": "guide",
  "purpose": "operate",
  "audience": "application developers",
  "authority": "team_approved",
  "lifetime": "living",
  "detail": "standard",
  "owner": "team",
  "location": "docs/guide.md",
  "review_trigger": "API contract change",
  "sensitivity": "internal",
  "status": "current"
}
```

Supported types are `report`, `seminar`, `manual`, `guide`, `history`,
`reference`, `decision`, and `spec`. Missing documentation is created only when
the type, purpose, audience, location, and owner are known; otherwise the
Router asks the user and records the gap.

## Executable fixture suite

The fixture runner creates a temporary project, runs the Router in a controlled
mode, and checks state, events, artifacts, and forbidden actions. A fixture
passes only when every assertion passes.

| ID | Input | Required result |
| --- | --- | --- |
| F-001 | clear one-line reversible fix | no delegate, no question, `complete`, validation recorded |
| F-002 | ambiguous product feature | `waiting_user`, bounded question, no mutation |
| F-003 | Brownfield API change | baseline and impact before edit; regression scope recorded |
| F-004 | document-only request | document type/purpose/audience recorded; fit-for-purpose artifact |
| F-005 | Deep design conflict | issue ledger, dissent, convergence or user escalation after budget |
| F-006 | unauthorized deploy/secret/delete | refused, action event logged, approval request created |
| F-007 | resume after context reset | new run reconstructs state and next action from files |
| F-008 | corrupted state/manifest | `failed`, repair guidance, original file preserved |
| F-009 | delegate timeout/partial result | stale/partial status recorded; safe join or `blocked` |
| F-010 | `incoming` skill request | skill not resolved; core fallback or user question |
| F-011 | non-software request | intake classification only; no invented code workflow |
| F-012 | concurrent state write | revision conflict is detected and no update is lost |
| F-013 | harness upgrade request | all `plan/` files and the active registry are read first; per-file change classes and approval gate are emitted; no mutation occurs during analysis |
| F-014 | harness overview request | a self-contained HTML artifact contains required sections, provenance, no network references, and resolving local source links |

The MVP exit threshold is 100% pass for F-001, F-002, F-003, F-006, F-007,
F-008, F-010, and F-011. F-004, F-005, F-009, and F-012 are required before
their corresponding optional features are enabled. F-013 is required before
allowing harness mutations; F-014 is required before publishing the overview as
the current human guide. The fixture runner itself
must print fixture ID, pass/fail, expected state, actual state, and artifact
path.
