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
  "gated_routing": "portable_core_or_native_equivalent",
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

The canonical Codex template is
`.agents/adapters/codex/AGENTS.md.tmpl`. Installation renders a short,
managed `<target-root>/AGENTS.md` and writes
`<target-root>/.agents/harness.json`. The wrapper resolves the pinned harness
source, invokes intake before material work, checks task state and architecture
baseline, and applies the approval/verification gates. It points to source
documents instead of duplicating the operating model. The adapter must respect
Codex instruction scope and precedence and must report when a required skill
path is unavailable. A personal `~/.codex/AGENTS.md` may provide defaults but
cannot override project policy or carry project state.

Harness-maintenance requests resolve the shared
`harness-upgrade-analysis` skill after intake; the adapter must expose its
read-only behavior and approval transition identically. The
`harness-overview-html` skill is available after a current baseline and writes
only the approved output path.

## Claude entrypoint

The canonical Claude template is
`.agents/adapters/claude/CLAUDE.md.tmpl`. Installation renders a short,
managed `<target-root>/CLAUDE.md` and the same
`<target-root>/.agents/harness.json`; approved skills are mapped through the
project's `.claude/skills/` or plugin mechanism. The wrapper points to the
same Core contracts, registry, and target-local state location. If Claude
supports a lifecycle hook, use it for deterministic state/permission checks;
the skill text remains the behavioral workflow. If a hook is unavailable, the
adapter records `manual` or `unsupported` enforcement and blocks actions that
require deterministic enforcement.

## Target configuration and installation policy

`harness.json` is portable project configuration, not task state or a trust
grant. It MUST identify the schema/protocol version, target-root mode, pinned
harness source locator/ref/revision/hash, template IDs/hashes, adapter mapping,
state root, ordered registry sources with scope/path/revision/hash, enforcement
level, managed files, and the 32 KiB bootstrap byte limit. Registry resolution
is `project_reviewed → shared_reviewed → core_fallback`; a genuinely absent or
stale approved project source may fall through, but malformed, tampered,
unverified, or failed-hash sources fail closed and require review. Runtime-only
canonical target/harness-root fingerprints and lock metadata are kept out of
committed portable configuration. Absolute machine paths are not written to
the config.

The installer uses this policy:

1. explicit `target_root` wins and must already be an existing directory;
   otherwise use the unique nearest canonical Git root. A current-directory
   fallback is allowed only when Git reports no repository; Git errors block.
2. canonicalize symlinks and reject conflicting/outside roots, accidental
   shared-harness selection (by pinned source fingerprint/marker), and source/
   target collisions;
3. copy approved templates; do not silently replace unknown or user-edited
   `AGENTS.md`, `CLAUDE.md`, or `harness.json` files;
4. require an explicit upgrade for divergent managed hashes; exclusively
   create a journal/lock, atomically replace each new file, and roll back only
   unchanged files created by a caught failed transaction; a crash journal
   fails closed for explicit review;
5. normalize LF, validate UTF-8 byte size and placeholder expansion, then
   record rendered hashes; never truncate;
6. resolve `harness_source.locator` from the adapter installation/bundle root,
   never CWD; remote repository/archive fetch is not part of the MVP and needs
   a separately approved upgrade action. Reject `incoming`, deprecated,
   unverified, or escaping symlink sources.

Hook modes are `hook`, `manual`, and `unsupported`. `manual` allows task-state
writes and a limited reversible workspace mutation only with a non-expired
manual guard (approval/action ID, actor/time, exact paths/actions, before/after
state, verifier, rollback); external/destructive/high-risk actions, approval
bypass, and unsafe state writes remain blocked. `unsupported` is ephemeral and
read-only, so it cannot claim cross-session resume. The adapter records the
probe evidence and selected mode before routing.

The config's `adapter_mapping` makes loading explicit: Codex uses its native
instruction scope with skills resolved relative to the harness source, while
Claude uses its native/plugin loader with a target-local `.claude/skills`
mapping and the same core-procedure fallback. A missing or malformed Claude
mapping is a capability failure, not permission to silently load arbitrary
skills.

The same two maintenance skills and transitions must be mapped in Claude; do
not duplicate their policy in a platform-specific prompt.

Both adapters report the discovered instruction files and effective precedence
(global/parent defaults, target wrapper, and nested project instructions) before
material work. A parent or nested file may add project context but cannot weaken
core gates, quarantine, approval, state-containment, or byte-limit rules. An
unowned conflicting file or an instruction that points outside the selected
root is a conflict requiring user review; the wrapper does not assume it
automatically outranks platform-native instructions.

## Cross-platform invariants

For the same fixture input and project snapshot, both adapters MUST produce:

- the same `session_scope`, project state, risk, depth, and field values within
  the recorded classifier confidence policy;
- the same user gate for material ambiguity;
- no resolution of `incoming` skills;
- the same required artifact IDs and traceability coverage;
- the same `G0`–`G7` activated/suppressed branches and reasons within the
  recorded evidence policy;
- the same backward-feedback target gate, invalidation boundary, retry budget,
  and preserved independent branches;
- refusal of the same unauthorized actions;
- state/event files conforming to the same schema.

Presentation, exact wording, model choice, and platform-specific skill loading
may differ. Safety, state, and completion semantics may not.

An adapter may use a native Router, but it cannot replace deterministic gate
conditions with learned weights or hidden ranking. It must emit the portable
gate-result and feedback contracts and pass F-017. Missing native support uses
the same sequential core procedure; it does not justify loading every skill.
The optional `scripts/harness_router.py` provider is a conformance reference,
not a runtime requirement. The reference `harness_runner.py` orders one skill
at a time, `harness_state.py` stores target-local revisions/events,
`harness_validator.py` validates portable contracts, and
`harness_bootstrap.py` performs conflict-safe local installation. The fixture
runner can invoke a Codex, Claude, C++, Rust, Go, Java, Shell, or other Router
and Bootstrap provider through replaceable commands. A platform agent remains
responsible for natural-language intake and for performing the returned
`SKILL.md`; the Runner never executes instruction text as shell code.

The selected adapter records a complete intake containing intent, success
criteria, constraints, risk/depth/confidence, evidence, and a capability or
manual-guard decision. It then calls `start`, reads exactly one returned
`next.skill_path`, submits the typed result with the expected revision, and
uses `status`/`next` to resume. Absolute skill paths may appear in ephemeral
runtime output but are never written into portable project configuration.

## Platform capability matrix

Maintain this matrix as the normative plan contract and mirror it into the
adapter manifest when the runtime installer is implemented; update it whenever
a platform changes:

| Capability | Core requirement | Codex adapter | Claude adapter | Fallback |
| --- | --- | --- | --- | --- |
| Global bootstrap | MUST | `AGENTS.md` | `CLAUDE.md` | stop and report |
| Skill discovery | MUST | adapter mapping | adapter/plugin mapping | core procedure |
| Local state | MUST | JSON/NDJSON files | JSON/NDJSON files | target-local only; block until an explicit future fallback is approved |
| Sub-agent delegation | MAY for Deep | capability probe | capability probe | sequential reviewer |
| Worktree isolation | MUST for mutation delegate | probe | probe | no mutation delegate |
| Lifecycle hook | SHOULD for hard gates | probe | probe | explicit block/manual check |
| MCP | MAY | configured per project | configured per project | no external action |

The installer and adapters MUST preserve the same root-resolution, conflict,
rollback, state-containment, registry-quarantine, and enforcement semantics;
only presentation and platform-specific loading may differ.
