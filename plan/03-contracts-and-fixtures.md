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
  "target_root_fingerprint": "sha256:...",
  "harness_root_fingerprint": "sha256:...",
  "harness_source_revision": "PINNED_REVISION",
  "selected_adapter": "codex",
  "status": "active",
  "stage": "impact",
  "session_scope": "software_engineering",
  "project_state": "brownfield",
  "classification": {
    "fields": ["backend", "api", "testing"],
    "action": "change",
    "risk": "medium",
    "depth": "standard",
    "confidence": "high",
    "evidence_ids": ["EVD-001"]
  },
  "intent": {
    "goal": "Add pagination to the user endpoint",
    "success_criteria": ["Existing clients remain compatible"],
    "constraints": [],
    "confirmed_by_user": true
  },
  "gate_network": {
    "model": "layered_gated_skill_graph",
    "forward_revision": 1,
    "evaluated_gate_ids": ["G0", "G1", "G2", "G3"],
    "active_skill_ids": ["core.brownfield-impact-analysis"],
    "pending_feedback_ids": []
  },
  "route": {
    "execution_profile": {
      "policy_id": "adaptive_v1",
      "specific_model": null,
      "depth": "standard",
      "risk": "medium",
      "adapter_resolution_required": true,
      "escalation_triggers": [],
      "gate_profiles": [
        {"gate_id": "G0", "role": "guard", "reasoning": "low", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G1", "role": "classifier", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G2", "role": "architect", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G3", "role": "analyst", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G4", "role": "planner", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G5", "role": "specialist", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G6", "role": "implementer", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]},
        {"gate_id": "G7", "role": "verifier", "reasoning": "medium", "independent_context": false, "reasons": ["depth_standard"]}
      ]
    }
  },
  "execution": {
    "queue": ["core.brownfield-impact-analysis", "core.verify-and-handoff"],
    "cursor": 0,
    "skill_stages": {
      "core.brownfield-impact-analysis": "impact",
      "core.verify-and-handoff": "verification"
    },
    "skill_gates": {
      "core.brownfield-impact-analysis": "G3",
      "core.verify-and-handoff": "G7"
    },
    "results": [],
    "artifact_ids": [],
    "evidence_ids": []
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
11. A state read requires matching target-root and harness-root fingerprints,
    source revision, and selected adapter. A mismatch is `blocked` or `failed`
    and is never merged into the current task.
12. A gate result references one immutable input revision and records a reason
    and evidence for every activated, candidate, suppressed, or blocked branch.
13. Forward gate edges are acyclic. A backward feedback signal creates a new
    forward revision; it never mutates a prior gate result in place.
14. Reopening a gate marks only transitively dependent artifacts stale and
    preserves independent valid branches. An accepted requirement, ADR,
    approval, or user decision changes only through its own authorized event.
15. Three unresolved feedback attempts for one material issue require
    `waiting_user`, `blocked`, or an authorized defer/waiver; the Router cannot
    loop indefinitely.
16. Every routed task records exactly one G0–G7 execution profile. Every skill
    result records the adapter's actual model/reasoning resolution. An
    unavailable resolution cannot complete, and no execution profile may weaken
    authority, safety, architecture, verification, or completion gates.
17. Architecture status is canonically `confirmed`, `draft`, `missing`,
    `stale`, `conflicted`, or `not_applicable`; legacy Router input `accepted`
    is normalized to `confirmed` and never emitted.
18. A formal standards-conformance claim requires authorized normative-source
    evidence, selected edition/profile, declared scope/entity, deviations, and
    owner. Missing evidence blocks only the claim, not ordinary guidance work.
19. An explicit pattern scope, architecture-structure change, or design-
    interaction change reaches a G5 pattern review whose result is selected,
    rejected, existing, candidate, or `not_applicable`. A material action alone
    does not satisfy applicability; a plausible local change records pattern
    suppression instead.
20. When two or more materially viable pattern candidates address the same
    decision scope, the review records one recommendation, its rationale and
    change conditions, keeps all candidates unselected, and enters
    `user_decision_required`. Material execution resumes only after a selected
    candidate links to recorded user or still-valid existing-decision evidence.
21. `language-engineering` and `implementation-quality` activate only for an
    authored language boundary in scope. Detected-only, generated-only, and
    documentation-only work cannot activate them. Every applicable authored
    code route includes implementation-quality `core`; additional profiles
    require their matching change characteristic.
22. Every activated skill has exactly one `light`, `standard`, or `deep`
    `application_depth`. Branch depth reduces irrelevant procedure but cannot
    weaken risk, authority, architecture, or verification gates.

## Event contract

Every line of `events.ndjson` is one JSON object:

```json
{
  "event_id": "EVT-004",
  "schema_version": 1,
  "task_id": "TASK-001",
  "run_id": "RUN-001",
  "revision": 4,
  "target_root_fingerprint": "sha256:...",
  "harness_root_fingerprint": "sha256:...",
  "harness_source_revision": "PINNED_REVISION",
  "selected_adapter": "codex",
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
`skill_selected`, `gate_evaluated`, `feedback_emitted`,
`artifact_invalidated`, `gate_reopened`, `delegate_started`,
`delegate_finished`, `action_requested`, `action_approved`, `action_executed`,
`skill_result_recorded`, `validation_recorded`, `state_transition`, `handoff_written`,
`task_cancelled`, and `error_recorded`.

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
  "schema_version": 1,
  "skill_id": "testing.tdd",
  "status": "completed",
  "classification_updates": [],
  "evidence_ids": ["EVD-010"],
  "artifact_ids": ["TESTPLAN-001"],
  "assumptions": [],
  "open_issue_ids": [],
  "validation": ["VAL-003"],
  "transition": {"next_stage": "execution", "entry_conditions": []},
  "execution_resolution": {
    "adapter": "codex",
    "model": "platform-default",
    "reasoning": "medium",
    "native_reasoning": "medium",
    "status": "exact",
    "evidence_ids": ["EVD-EXEC-001"]
  },
  "error": null
}
```

`status` is one of `completed`, `not_applicable`, `waiting_user`, `blocked`, or `failed`.
Failed or blocked results must include an error and recovery action. A skill
cannot mark the whole task complete. `execution_resolution` records what the
adapter actually used. `reasoning` is the portable normalized level;
`native_reasoning` preserves the adapter's platform label without adding it to
Core's enum. `exact` equals the recommendation, `upgraded` is higher,
`degraded` is lower, `platform_default` means the platform did not expose a
reliable control, and `unavailable` requires a blocked or failed result. The
portable policy never supplies a specific model name.

## Execution profile contract

`execution_profile.policy_id` is `adaptive_v1`; reasoning is `low`, `medium`,
or `high`. It contains exactly one ordered profile for G0–G7 with a portable
role, reasoning recommendation, independent-context flag, and reasons. The
only current escalation triggers are `high_risk`, `architecture_conflict`, and
`repeated_feedback:<gate>`. Branch count, technology count, or model popularity
cannot raise the profile. The adapter owns actual model mapping, but it must
record a resolution and cannot use model capability to weaken a safety gate.

## Gate result contract

Every `G0`–`G7` evaluation produces one immutable result. The taxonomy may be a
tree, but one result can activate several branches:

```json
{
  "gate_result_id": "GATE-005",
  "schema_version": 1,
  "gate_id": "G5",
  "forward_revision": 2,
  "input_state_revision": 11,
  "input_artifact_ids": ["TECH-001", "IMPACT-001"],
  "activated": ["core.architecture-and-design-patterns", "core.ros2-engineering", "core.grpc-engineering", "core.language-engineering"],
  "candidates": [],
  "suppressed": [
    {"skill_id": "core.moveit-engineering", "reason": "motion_planning_not_in_scope", "evidence_ids": ["EVD-040"]}
  ],
  "blocked": [],
  "questions": [],
  "output_artifact_ids": ["IMPL-001"],
  "evidence_ids": ["EVD-040", "EVD-041"],
  "application_depths": {
    "core.architecture-and-design-patterns": "standard",
    "core.ros2-engineering": "standard",
    "core.grpc-engineering": "standard",
    "core.language-engineering": "standard"
  },
  "status": "passed"
}
```

`status` is `passed`, `waiting_user`, `blocked`, or `failed`. Every branch must
appear in at most one activation state. `activated` entries must resolve through
the approved registry and satisfy predecessor gates; `incoming`, deprecated,
failed-integrity, adjacent-but-unevidenced, or cyclic dependencies are rejected.
The Router loads only activated skill bodies. Numeric confidence may describe
classification evidence but never acts as an undocumented learned weight.

### Reference Router transport

The executable reference provider accepts a JSON object using
`schema_version`, `request_id`, `target`, `scope`, `project_state`, `action`,
`enforcement_mode`, architecture status, fields, `change_characteristics`,
languages, `language_scope`, technologies,
configuration candidates, requested standards, conformance intent/scope/owner/evidence,
pattern scopes, evidence, artifacts, and optional feedback. It emits
one JSON object with status, forward revision, `G0`–`G7` evaluation results,
activated and suppressed skills, feedback results, and event projections.
This projection is not a replacement for the durable task-state/event store;
an adapter enriches accepted projections with the IDs, input revisions, locks,
and timestamps required by the persistent contracts above.

The file transport is deliberately small: a conforming adapter accepts
`--input <path> --output <path>`. The reference fixture runner injects any such
command with `--adapter-command`, so the Core does not depend on Python or a
specific executable layout.

## Backward feedback contract

Verification, a user correction, new evidence, or capability loss may emit a
bounded signal to the nearest responsible gate:

```json
{
  "feedback_id": "FDB-001",
  "schema_version": 1,
  "source_gate": "G7",
  "target_gate": "G4",
  "kind": "technology_configuration_or_cross_cutting_gap",
  "issue_id": "ISSUE-020",
  "expected": "Configured port is validated before startup",
  "actual": "Invalid port reached the runtime binder",
  "evidence_ids": ["EVD-090"],
  "invalidated_artifact_ids": ["CONFIG-001", "IMPL-001", "TEST-020"],
  "preserved_artifact_ids": ["INTENT-001", "ARCH-001", "IMPACT-001"],
  "attempt": 1,
  "requires_user": false,
  "next_forward_revision": 3
}
```

Allowed targets and signal kinds are defined in
`registry/routing-gates.json`. A signal invalidates descendants through typed
trace links, not file-name guessing. It cannot alter user intent, an accepted
decision, approval, or unrelated branch. If the nearest cause is uncertain,
the Router records candidates and returns to discovery or asks the user rather
than broadcasting feedback to every gate.

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

Use typed IDs: `GOAL-*`, `REQ-*`, `FR-*`, `NFR-*`, `QAS-*`, `STD-*`, `ADR-*`, `PATTERN-*`, `TECH-*`,
`IMPL-*`, `TASK-*`, `CONFIG-*`, `CODE-*`, `TEST-*`, `DOC-*`, and `EVD-*`.
Relations are:

```text
defines, refines, constrains, decides, implements, verifies, documents,
supersedes, derived_from, waived_by
```

The validator reports orphan requirements, dangling links, requirements with
no verification, and documents that claim a changed API without an API
artifact. Light work may use a compact `TASK -> TEST` link; standard and deep
work require all applicable links and an explicit waiver for omitted entities.

## International-standard applicability contract

Use `STD-*` for each selected or explicitly assessed international standard:

```json
{
  "standard_id": "STD-001",
  "canonical_id": "iso_iec_ieee_42010_2022",
  "edition": "2022",
  "intent": "alignment",
  "scope_or_entity": "payment-service architecture description",
  "applicability": "applicable",
  "rationale": "architecture views must address stakeholder concerns",
  "authorized_source_evidence_ids": [],
  "criteria_evidence": [],
  "deviations": [],
  "owner": "architecture_owner",
  "affected_artifact_ids": ["ARCH-001", "DOC-ARCH-001"],
  "review_trigger": "architecture scope or standard edition change"
}
```

Allowed intent values are `guidance`, `alignment`, and `conformance`;
applicability is `applicable`, `not_applicable`, or `undetermined`. Guidance or
alignment may use public identity/scope evidence. `conformance` requires a
non-empty authorized-source evidence list plus a project-defined criteria and
assessment record. Profiles are progressively loaded from the G2 selector;
unknown IDs block until reviewed instead of silently mapping to a similar
standard.

## Architecture/design pattern contract

Use one `PATTERN-*` record per material decision scope, including when no
pattern is selected. A decision may span both architecture and design scopes,
but independent decisions use independent records:

```json
{
  "schema_version": 1,
  "pattern_id": "PATTERN-001",
  "scopes": ["architecture", "design"],
  "drivers": ["QAS-001", "FR-010"],
  "existing_patterns": [],
  "candidates": [
    {
      "candidate_id": "PATTERN-OPTION-001",
      "name": "ports_and_adapters",
      "status": "selected",
      "decision_scope": "payment provider boundary",
      "context": "external payment provider varies",
      "forces": ["testability", "provider isolation"],
      "fit": "isolates the required external-provider variation",
      "recommendation_reason": "best satisfies QAS-001 without changing deployment boundaries",
      "benefits": ["replaceable provider adapter"],
      "liabilities": ["mapping and indirection"],
      "quality_attribute_effects": ["improves testability", "adds mapping overhead"],
      "affected_artifact_ids": ["ADR-010", "IMPL-001"],
      "migration_and_rollback": ["migrate one provider at a time", "retain the old integration until verification passes"],
      "verification_ids": ["TEST-010"]
    }
  ],
  "decision": {
    "status": "single_viable",
    "decision_scope": "payment provider boundary",
    "recommended_candidate_id": "PATTERN-OPTION-001",
    "recommendation_reason": "other reviewed options fail the provider-isolation driver",
    "conditions_that_change_recommendation": ["provider replacement is no longer required"],
    "selected_candidate_id": "PATTERN-OPTION-001",
    "decision_evidence_ids": ["EVD-ARCH-010"]
  },
  "migration_and_rollback": [],
  "open_issue_ids": []
}
```

Candidate status is `existing`, `candidate`, `selected`, `rejected`, or
`not_applicable`. A selected material architecture pattern requires a linked
ADR. Brownfield migration requires compatibility and rollback. A named pattern
without drivers/trade-offs, or a QAS benefit without a verification link,
fails validation/review.

Decision status is `not_applicable`, `single_viable`,
`user_decision_required`, `user_selected`, or `existing_decision`. Candidates
are compared only inside one decision scope; compatible patterns at different
levels are represented as one composed option or separate decisions. If two or
more candidates remain materially viable, `user_decision_required` requires a
recommended candidate, recommendation reason, change conditions, no selected
candidate, and at least one open issue. `user_selected` requires exactly one
selected candidate plus decision evidence. `existing_decision` requires
evidence for the still-valid ADR/requirement. A recommendation is not a
selection.

## Technology artifact contract

Use a `TECH-*` artifact when a material task selects, mandates, detects,
replaces, upgrades, rejects, prohibits, or integrates a technology ecosystem:

```json
{
  "technology_id": "TECH-001",
  "name": "ros2",
  "primary_kind": "platform",
  "secondary_roles": ["middleware", "framework"],
  "domains": ["robotics"],
  "lifecycle_scope": ["build", "runtime", "integration", "operate"],
  "selection_status": "selected",
  "purpose": "robot component communication",
  "required_capabilities": ["publish_subscribe", "request_response", "long_running_action"],
  "project_evidence": ["EVD-TECH-001"],
  "version_policy": "project pinned distribution and support window",
  "compatibility": {"os": [], "architecture": [], "language": [], "runtime": [], "gpu_driver": [], "middleware_protocol": []},
  "relationships": [{"to": "TECH-002", "type": "optional", "condition": "motion planning in scope", "rationale": "REQ-010", "evidence_ids": ["EVD-TECH-002"]}],
  "ecosystem_skills": ["ros2-engineering"],
  "language_bindings": ["rclcpp"],
  "configuration_surfaces": ["ROS_DOMAIN_ID", "RMW_IMPLEMENTATION"],
  "alternatives": [],
  "decision_id": "ADR-010",
  "verification_profiles": ["TEST-TECH-001"],
  "documentation_effects": ["DOC-ARCH-001"],
  "open_issue_ids": []
}
```

Allowed primary kinds are `runtime`, `library`, `framework`, `protocol`,
`platform`, and `tool`. Allowed selection statuses are `required_by_user`,
`detected_existing`, `candidate`, `selected`, `rejected`, `not_applicable`, and
`prohibited`. Allowed relationship types are `required`, `recommended`,
`optional`, `detected`, and `incompatible`. A selected material technology
requires purpose, evidence, version/binding compatibility, verification, and an
ADR/approval when adoption or replacement changes architecture/dependencies.

## Implementation-language artifact contract

Use an `IMPL-*` artifact for every materially changed authored implementation
boundary governed by an ecosystem skill:

```json
{
  "implementation_id": "IMPL-001",
  "module": "robot_controller",
  "ecosystem_skills": ["ros2-engineering"],
  "language": "cpp",
  "language_version": "project detected",
  "binding": "rclcpp",
  "profile_loaded": "language-engineering/references/cpp.md",
  "authored_paths": ["src/controller"],
  "generated_paths": ["build/generated_interfaces"],
  "build_toolchain": ["cmake", "colcon"],
  "conventions": ["project formatter and warning policy"],
  "error_model": "project result/exception policy",
  "ownership_and_lifecycle": "node and executor owned",
  "concurrency_model": "callback groups recorded",
  "configuration_ids": ["CONFIG-001"],
  "verification_ids": ["TEST-IMPL-001"],
  "document_ids": ["DOC-LLD-001"],
  "open_issue_ids": []
}
```

The validator requires exactly the profiles for changed authored boundaries,
rejects hand-edited generated paths, and reports an ecosystem/binding/language
combination unsupported by the selected version. Project conventions remain
the Brownfield default unless a reviewed migration is approved.

## Implementation-quality artifact contract

An applicable authored-code boundary produces a focused G6 result. It does not
repeat the `PATTERN-*`, `TECH-*`, or `IMPL-*` decision:

```json
{
  "schema_version": 1,
  "status": "completed",
  "authored_boundaries": ["src/controller"],
  "activated_profiles": [
    {
      "id": "core",
      "depth": "standard",
      "authored_boundaries": ["src/controller"],
      "evidence_ids": ["EVD-CODE-001"],
      "expected_outcomes": ["explicit error and lifecycle behavior"],
      "verification_ids": ["TEST-IMPL-001"]
    },
    {
      "id": "concurrency",
      "depth": "standard",
      "authored_boundaries": ["src/controller"],
      "evidence_ids": ["EVD-CALLBACK-001"],
      "expected_outcomes": ["bounded cancellation and shutdown"],
      "verification_ids": ["TEST-CONCURRENCY-001"]
    }
  ],
  "suppressed_profiles": [
    {"id": "performance", "reason": "no performance QAS or observed hotspot"}
  ],
  "findings": [],
  "residual_risks": [],
  "open_points": []
}
```

Allowed profiles are `core`, `object_oriented`, `functional`, `data_oriented`,
`api_data`, `concurrency`, `distributed`, `security`, `performance`, and
`realtime_embedded`. `core` is required whenever the skill is applicable. Each
additional profile requires a matching change characteristic, its own bounded
authored paths within the top-level boundary, evidence, expected outcomes, and
verification. A detected-only,
generated-only, or documentation-only route returns `not_applicable` without
loading the profile references.

## Configuration artifact contract

Use a `CONFIG-*` artifact when a task externalizes, changes, migrates, or
materially relies on application configuration:

```json
{
  "configuration_id": "CONFIG-001",
  "status": "confirmed",
  "language": "rust",
  "boundary_contexts": [],
  "references_loaded": ["references/rust.md"],
  "tool_selection_evidence": [],
  "candidates": [
    {"name": "listener_port", "kind": "runtime", "evidence_ids": ["EVD-030"]}
  ],
  "retained_constants": [],
  "settings": [
    {
      "key": "APP_LISTENER_PORT",
      "kind": "runtime",
      "type": "tcp_port",
      "required": false,
      "safe_default": 8080,
      "sources": ["environment", "toml", "code_default"],
      "precedence": ["environment", "toml", "code_default"],
      "validation": ["1..65535"],
      "secret": false,
      "owner": "service_owner",
      "reload": "startup",
      "compatibility": "existing default preserved",
      "test_ids": ["TEST-CONFIG-001"],
      "document_ids": ["DOC-CONFIG-001"]
    }
  ],
  "secret_strategy": "references_only",
  "rollback": "restore previous key aliases and loader",
  "open_issue_ids": []
}
```

Allowed `kind` values are `code_constant`, `build_time`, `deploy_time`,
`runtime`, and `secret`. A material setting requires evidence, type, owner,
source/precedence, validation, tests, and documentation. Secret entries never
contain the value. Brownfield key removal requires a compatibility/deprecation
record and rollback. `language` is the primary implementation context;
`boundary_contexts` lists only directly affected HTML/CSS public artifacts.
`references_loaded` and any `tool_selection_evidence` make progressive loading
and dependency rationale auditable.

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
`reference`, `decision`, `spec`, `architecture_baseline`, `architecture_view`,
`architecture_decision`, and `architecture_sync`. Missing documentation is created only when
the type, purpose, audience, location, and owner are known; otherwise the
Router asks the user and records the gap.

## Project bootstrap configuration contract

The target project's `.agents/harness.json` pins the source and runtime
boundary. It is portable configuration and MUST NOT contain secrets, absolute
machine paths, task state, or a trust grant:

```json
{
  "schema_version": 1,
  "protocol_version": 1,
  "target_root_mode": "explicit",
  "harness_root_mode": "separate",
  "harness_source": {
    "kind": "local_or_bundled",
    "locator": "shared-harness",
    "ref": "shared-harness",
    "revision": "PIN_REQUIRED",
    "sha256": "PIN_REQUIRED"
  },
  "templates": [
    {"id": "codex.bootstrap", "path": "adapters/codex/AGENTS.md.tmpl", "sha256": "PIN_REQUIRED"},
    {"id": "claude.bootstrap", "path": "adapters/claude/CLAUDE.md.tmpl", "sha256": "PIN_REQUIRED"}
  ],
  "adapters": ["codex", "claude"],
  "state_root": ".agents/state",
  "registry": {
    "resolution_order": ["project_reviewed", "shared_reviewed", "core_fallback"],
    "sources": [
      {"scope": "project_reviewed", "path": ".agents/registry/project-skills.json", "revision": "PIN_REQUIRED", "sha256": "PIN_REQUIRED"},
      {"scope": "shared_reviewed", "path": "registry/active-skills.json", "revision": "PIN_REQUIRED", "sha256": "PIN_REQUIRED"}
    ]
  },
  "adapter_mapping": {
    "codex": {"loader": "native_instruction_scope", "scope": "harness_source", "skill_root": "skills", "fallback": "core_procedure"},
    "claude": {"loader": "native_or_plugin", "scope": "target_project", "skill_root": ".claude/skills", "fallback": "core_procedure"}
  },
  "enforcement": {
    "mode": "manual",
    "capability_probe": {"status": "recorded", "evidence_id": "EVD-BOOTSTRAP-PROBE", "at": "2026-08-03T00:00:00Z"},
    "manual_guard": null
  },
  "bootstrap": {
    "managed_files": ["AGENTS.md", "CLAUDE.md"],
    "line_endings": "LF",
    "max_bytes": 32768,
    "file_hashes": {"AGENTS.md": "PIN_REQUIRED", "CLAUDE.md": "PIN_REQUIRED"},
    "config_hash": "PIN_REQUIRED"
  }
}
```

The adapter resolves `harness_source.locator` from its installation/bundle
root, never from the current working directory, and records that canonical
`harness_root` fingerprint in task evidence. A source directory hash is a
deterministic manifest of sorted relative file paths and normalized file
SHA-256 values; it is not a hash of an ambient path. Registry sources are
resolved relative to their declared scope, and missing/stale project sources
fall through to the shared source without changing the trust order. A malformed,
tampered, unverified, or failed-hash source fails closed and requires explicit
review; it is never silently treated as absent. The
`core_fallback` is built into the Router and has no filesystem path.

At runtime the adapter records the canonical target-root fingerprint, selected
adapter, lock/transaction ID, source status, and capability-probe evidence in
task state; these values are not machine paths in committed config. The
validator rejects missing real pins (`PIN_REQUIRED` is not installable), unknown
top-level fields, duplicate IDs, absolute/drive/UNC/backslash/`..` paths,
unresolved placeholders, non-LF rendered content, over-limit bootstrap files,
and state/source paths that escape their declared root. Realpath containment,
symlink checks, and TOCTOU rechecks remain runtime checks.

`bootstrap.file_hashes` covers only the rendered instruction files. The
config's `config_hash` is the SHA-256 of canonical JSON with `config_hash`
omitted, avoiding a self-hash cycle. All managed/config files are UTF-8 LF,
non-executable by default, and preserve safe permissions on upgrade.

Bootstrap installation is an authorized mutation. Before `.agents/` exists,
the explicit user bootstrap request or a user-level transaction journal is the
approval evidence. The installer exclusively creates a journal that acts as a
lock and atomically replaces each new wrapper/config file; a multi-file rename
is not claimed. A caught failure removes only unchanged files created by that
transaction. A crash leaves the journal and any partial files in place so the
next run fails closed for explicit review. Same-hash managed files are
idempotent. Unknown or edited files are preserved and cause an explicit
conflict/upgrade request; rollback never discards those edits. Copy is the
default; a symlink is accepted only if explicitly approved,
contained, and hash-pinned.

`hook` means deterministic capability checks are available. `manual` means
read-only work is always available; task-state writes and a limited reversible
workspace mutation are allowed only with a non-expired `manual_guard` containing
approval/action ID, actor/time, exact paths/actions, pre/post state, verifier,
and rollback. External, destructive, high-risk, approval-bypassing, and unsafe
state changes remain blocked. `unsupported` permits read-only diagnostics only;
it cannot claim cross-session persistence or write task state.

The JSON Schema provides structural validation; the dependency-free runtime
validator adds these deterministic invariants: `harness_source.locator` is a
safe installation identifier (not a path escape), templates contain exactly
one Codex and one Claude ID, registry sources contain at most one entry per
scope and the resolution order is exactly
`project_reviewed → shared_reviewed → core_fallback`, managed-file hashes match
the two wrapper names, and `manual_guard` is null for `hook`/`unsupported` and
freshly evidenced when `manual` performs a durable write. It also verifies
source/target realpath containment, symlink and permission policy, source-tree
manifest scope (excluding `.git`, `incoming`, state, Python/test caches, and generated metadata),
and the canonical self-excluded config hash. The source-tree manifest excludes
the optional ROS MCP `.runtime/`, upstream `build/`, `ros_mcp.egg-info/` and
`.venv/` under `tools/ros-mcp-server`; these are local dependencies/build output,
not approved source. The tool's entrypoint, vendored source and lockfile remain
covered. It also excludes
its own `registry/adapter-manifest.json` and the mutable
`registry/active-skills.json`; those two manifests are pinned separately to
avoid a recursive hash cycle. The adapter manifest hash excludes its own
source/template hash fields, and the active registry hash excludes only its
own `integrity_policy.manifest_sha256` sentinel. Schema URI metadata is never
resolved over the network.

## Executable fixture suite

The fixture runner creates isolated input/output files, runs the Router adapter
in a controlled mode, and checks state projections, events, artifacts, and
forbidden actions. A fixture passes only when every assertion passes. The
current reference invocation is:

```sh
python3 -B scripts/fixture_runner.py
```

This command is an optional provider invocation, not a Core dependency. Use
`--adapter-command '<native-router>'` to test another implementation. The
runner prints durable temporary result paths unless an explicit
`--artifact-dir` is supplied.

| Family | Executable cases | Required result |
| --- | ---: | --- |
| `F-017` routing | 4 | composite MIMO selection, architecture conflict, unknown feedback, and third-attempt escalation agree with the gate/feedback contract |
| `B-CONFLICT` bootstrap | 4 | fresh install, idempotent reinstall, user/edited wrapper preservation, and symlink refusal are deterministic |
| `C-CONFIG` configuration | 5 | compiled/runtime/Shell/public-web/secret candidates activate the common configuration concern and only affected language/ecosystem branches; invalid secret and port contracts are rejected by unit validation |
| `T-TECH` technology composition | 6 | all 11 mappings resolve, meaningful robotics/simulation/web/platform/gRPC compositions activate, and unevidenced adjacent technologies remain suppressed |
| `E-PROFILE` execution profiles | 3 | light work remains bounded, high risk raises G2–G7, and repeated feedback raises only the responsible gate plus G7 without a model binding |
| `A-STD-PATTERN` standards and patterns | 6 | named standard profiles normalize at G2, compliance/quality branches remain visible, evidenced pattern scopes activate at G5, legacy status is canonicalized, missing/unknown conformance inputs fail closed, and a fully scoped evidenced route may proceed |
| `S-MIN` selective routing | 3 | local authored code suppresses pattern review, structural code selects scoped patterns and quality profiles, and detected-only documentation avoids implementation skills |
| `W-FLOW` workflow composition | 6 | work types, conditional parallel planning, ownership conflicts, capability fallback, document-only routing and risk floors |
| runtime and documentation checks | discovered by unittest | ordered architecture-first execution, profile resolution validation, verified completion/handoff, revision conflict preservation, unreadable-state preservation, secret redaction, port-bound rules, selective pattern and implementation-quality routing and artifact validation, pattern recommendation/user-decision validation, conformance blocking, and legacy-status canonicalization hold |

The intentionally bounded suite is the promotion gate for this reference
runtime. It avoids the Cartesian product of every language, configuration
kind, and technology. Coverage is divided by semantic class: one all-mapping
technology case, representative integration edges, explicit negative adjacency
cases, and representative configuration boundaries. Add a case only when a new
rule or regression cannot be represented by an existing class.

The fixture runner must print fixture ID, pass/fail, expected state, actual
state, and artifact path. Passing `F-017` permits the current deterministic
Router/backward-invalidation claim. Passing `B-CONFLICT` permits only the
documented local/separate-root installer behavior; it does not claim lifecycle
hook enforcement or every platform-native instruction-precedence case.
`C-CONFIG` and `T-TECH` validate routing and portable contract boundaries, not
the availability of an external tool, robot, cluster, simulator, or production
environment.
`A-STD-PATTERN` validates applicability/routing semantics only; it does not
certify a project against any international standard or prove that a selected
software pattern achieves its claimed quality outcome.

Unreadable or mismatched task state is handled as a small safety invariant, not
a separate recovery subsystem or broad fixture family. The state store uses
atomic replacement, rejects another target-root fingerprint or revision,
preserves unreadable originals, and reports a blocked recovery action. It does
not guess or silently repair user-owned task history.

## Additive work-plan contract

The canonical input/output and native delegation contract is
[08-layered-workflow.md](08-layered-workflow.md). Intake accepts optional
`work_type`, `work_units`, `delegation`; the Router emits `work_plan`, and the
Runner preserves it in `state.route` and `next.work_plan`. `WORK-*` artifacts
record accepted plans. New output fields do not change G0–G7 semantics or grant
execution authority. Older states without work plans remain readable.

W-FLOW fixtures and `tests/test_workflow.py` cover profile selection, serial
fallback, dependency/ownership isolation, invalid inputs and Runner propagation.
Counts are reported by the executed suite rather than treated as fixed policy.
`tests/test_documentation.py` checks candidate coverage, active placement,
source links and documentation synchronization. These tests do not claim native
agent speedup or integration with external tools.

## Native-work receipt extension

Declared work uses Runner `prepare-work` and `record-work`, both guarded by
expected_revision and the existing state lock. Unit skill_id binds execution to
a pending skill; missing owner bindings must be resolved at composition. See
[native work packets, receipts and usage](../skills/workflow-composition/references/native-work.md).
The extension preserves the serial skill queue and adds no process executor.
Existing no-unit workflows retain their result contract. Existing plans with
units must produce receipts rather than completing by skill status alone.
