# Codex and Claude adapter contract

The portable Core is the source of truth. An adapter translates platform
features into the same state, event, skill, and approval behavior. It must not
silently weaken a MUST rule.

## Adapter responsibilities

Each adapter MUST provide:

```text
bootstrap()          load the short global entry instruction
discover_skills()    return approved metadata only
load_skill(id)       load the selected skill and required resources
delegate(request)    run an isolated delegate or return unavailable
request_approval()   pause and persist an action request
read_state(task_id)  read state/events/handoff
write_event(event)   append with revision/lock validation
run_fixture(id)      expose the same fixture result format
```

The adapter reports capabilities before routing:

```json
{
  "platform": "codex",
  "skills": "lazy_or_platform_defined",
  "subagents": true,
  "worktree_isolation": true,
  "hooks": false,
  "mcp": false,
  "state_write": "local_files",
  "permission_mode": "available"
}
```

If a capability is unavailable, the adapter returns a structured fallback. It
does not pretend that an optional delegate, hook, MCP tool, or preload behavior
exists.

## Codex entrypoint

The Codex adapter consists of a short `AGENTS.md` bootstrap and the shared
`.agents/skills/` discovery path. The bootstrap says to read the Router entry
skill, classify the request, honor the task state, and apply the approval gate.
It points to the repository's source-of-truth documents instead of duplicating
the entire operating model. The adapter must respect Codex instruction scope
and precedence and must report when a required skill path is unavailable.

Harness-maintenance requests resolve the shared
`harness-upgrade-analysis` skill after intake; the adapter must expose its
read-only behavior and approval transition identically. The
`harness-overview-html` skill is available after a current baseline and writes
only the approved output path.

## Claude entrypoint

The Claude adapter consists of a short `CLAUDE.md` bootstrap plus the approved
`.claude/skills/` or plugin mapping. It points to the same Core contracts and
state location. If Claude supports a lifecycle hook, use it for deterministic
state/permission checks; the skill text remains the behavioral workflow. If a
hook is unavailable, the adapter reports the reduced guarantee and blocks
actions that require deterministic enforcement.

The same two maintenance skills and transitions must be mapped in Claude; do
not duplicate their policy in a platform-specific prompt.

## Cross-platform invariants

For the same fixture input and project snapshot, both adapters MUST produce:

- the same `session_scope`, project state, risk, depth, and field values within
  the recorded classifier confidence policy;
- the same user gate for material ambiguity;
- no resolution of `incoming` skills;
- the same required artifact IDs and traceability coverage;
- refusal of the same unauthorized actions;
- state/event files conforming to the same schema.

Presentation, exact wording, model choice, and platform-specific skill loading
may differ. Safety, state, and completion semantics may not.

## Platform capability matrix

Maintain this matrix in the registry and update it when a platform changes:

| Capability | Core requirement | Codex adapter | Claude adapter | Fallback |
| --- | --- | --- | --- | --- |
| Global bootstrap | MUST | `AGENTS.md` | `CLAUDE.md` | stop and report |
| Skill discovery | MUST | adapter mapping | adapter/plugin mapping | core procedure |
| Local state | MUST | JSON/NDJSON files | JSON/NDJSON files | user-level state |
| Sub-agent delegation | MAY for Deep | capability probe | capability probe | sequential reviewer |
| Worktree isolation | MUST for mutation delegate | probe | probe | no mutation delegate |
| Lifecycle hook | SHOULD for hard gates | probe | probe | explicit block/manual check |
| MCP | MAY | configured per project | configured per project | no external action |
