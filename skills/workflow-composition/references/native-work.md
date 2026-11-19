# Native work: focused packets and checked joins

Use only for declared work units. Keep ordinary tasks on the serial skill path.
The portable Runner records preparation and terminal receipts; the host adapter
starts/stops workers. These checks do not grant tools or implement a sandbox.

## Bind and prepare

Bind each unit's `skill_id` to its responsible activated core skill. Unbound
intake units are provisional. Reject a dependency whose skill owner occurs later in the serial queue.
Before completing composition, bind every pending
unit to a strictly subsequent skill, or remove unnecessary provisional units.
At completed composition, unprepared future units may be refined only while
retaining every prepared definition unchanged and every receipt completed.
Failed/cancelled/timed-out records require responsible-gate recovery; they cannot
be deleted or rewritten by a plan update. Preserve completed evidence and use
the responsible-gate recovery path for failed work; do not retry indefinitely.

For each ready unit call the existing Runner with a JSON request file:

```text
python3 <harness>/scripts/harness_runner.py prepare-work \
  --target-root <project> --task-id TASK-001 \
  --expected-revision <latest> --request prepare.json
```

```json
{
  "unit_id": "a",
  "input_revision": "reviewed-source-snapshot",
  "mode": "native",
  "native_worker_capacity": 3,
  "checks": {
    "authority": true, "capability": true, "revision": true,
    "ownership": true, "tools": true
  },
  "evidence_ids": ["EVD-current-adapter-checks"]
}
```

Recheck these facts against current tools, actual file revisions and ownership;
booleans are attestations, not proof produced by the Runner. Include uncommitted
changes in the snapshot evidence. A plan never authorizes dispatch. Missing
native delegation authority/capability uses `mode: serial` with current local
execution authority. Serial execution still records each declared unit.

Each unit must provide nonempty `context_artifacts`: target-relative path/SHA-256
pairs for the compact current baseline, accepted decisions and necessary prior
skill outputs. Reuse one task-contract file when sufficient; do not copy the
whole conversation. The Runner checks file existence and hashes; the coordinator
still checks semantic sufficiency for this unit. Workers read these files before
work and stop when prerequisite decisions or evidence are missing.

The returned packet includes the current approved skill body, its source path
and hash, application depth, portable execution profile, and the unit's role
responsibility, plus optional reasoning_lens guidance. It also carries the task goal, constraints and one unit's
acceptance, evidence references, paths and allowed tool requirements. Unconditional references declared in approved registry
`required_worker_references` are included automatically, together with the unit's
selected `skill_references`, as path/hash references. Language workers must select
only the languages evidenced in the current intake; paths must be canonical harness-relative files under the current
skill's references directory. Select them from the skill's required branches
and unit evidence. Workers read and hash-check those references before work;
missing required context stops the unit. Do not recursively load other skills.
The adapter resolves the execution profile against actual host capabilities;
the result artifact records actual/degraded model and native reasoning plus
instruction/reference evidence. The coordinator verifies that evidence before
accepting the receipt. A persona name or a hash echo alone is not proof of use. Send only
that packet to a fresh worker context. On Codex use `fork_turns="none"`; on other
hosts disable history inheritance when supported, or use the serial path. No
recursive delegation. The packet is limited to 16,384 UTF-8 JSON bytes; oversize
input fails rather than silently dropping requirements. Reference bounded local
artifacts for details. The cap covers generated input, not later tool output or
the host's automatically supplied context.

At intake, `delegation.native_worker_capacity` records observed worker slots:
exclude the primary and unrelated agents, include this task's running workers.
The plan clamps requested max_workers to that capacity; missing/zero capacity
falls back to serial. Batches contain only units with the same bound skill;
unbound units stay serial until composition binds them. This is a proposal,
not permission to advance past a gate. For each native preparation, report a
fresh `native_worker_capacity` with the adapter evidence. Missing/zero capacity
blocks native preparation; a lower value limits further admission. The Runner
cannot query the provider or prevent races with other sessions; the adapter
must handle spawn failures without claiming execution and terminate/record any
reserved unit. Serial preparation does not require a native capacity field.

Preparation checks current skill, joined dependencies, active worker count,
write/read/resource conflicts and path containment. Symlink aliases must first
be replaced with canonical target-relative paths. The host still needs actual
permission/worktree isolation. Do not run future-skill units early.

On Claude, start each prepared unit as the matching `harness-<role>` agent with
the packet as its whole prompt, one batch per message, following the adapter's
`adapters/claude/native-dispatch.md` in the harness source. The packet's
`gate_role` names the current gate's portable role; a unit role that gate does
not allow is rejected at preparation.

## Stop, verify and record

The adapter supervises the deadline. On timeout/failure, stop the worker and
confirm termination before releasing ownership; an interrupt request alone is
not confirmation. If termination cannot be confirmed, retain the running record
and do not advance the skill or launch conflicting work. The Runner does not
kill processes. Late success is recorded as timed_out, never completed.

```text
python3 <harness>/scripts/harness_runner.py record-work \
  --target-root <project> --task-id TASK-001 \
  --expected-revision <latest> --request receipt.json
```

```json
{
  "unit_id": "a",
  "input_revision": "reviewed-source-snapshot",
  "packet_hash": "hash-returned-by-prepare-work",
  "status": "completed",
  "worker_stopped": true,
  "acceptance_verified": true,
  "artifact_ids": ["ART-current-output"],
  "evidence_ids": ["EVD-coordinator-checked-acceptance"],
  "usage": {"status": "unavailable"}
}
```

Use completed, failed, cancelled or timed_out. The coordinator checks output
scope, current revision and acceptance before marking acceptance_verified.
Artifact IDs refer to actual local evidence, not invented labels. Receipts are
limited to 8,192 UTF-8 JSON bytes; retain detailed findings in artifacts, including
uncertainty and failure evidence. A stale hash/revision or duplicate receipt is
rejected. Missing, failed or timed-out units block owning-skill completion and G7.
Running units block every skill transition until termination is recorded.

## Usage and limits

When provider counters exist, report per-unit incremental input/output counts:

```json
{"status":"reported","input_tokens":1200,"output_tokens":300,"source":"provider usage receipt ART-usage-001"}
```

Count cached input once according to the provider's input total. Never substitute
character-count estimates or cumulative session usage. If counters are absent,
use unavailable without numbers. Runner worker_usage sums reported worker counts
and exposes unavailable_or_pending; it excludes parent context, hidden host
context, tool charges and currency. The summary explicitly reports parent_usage as unavailable and total_task_tokens
as null. It is not proof of total savings. Keep small CRUD/local changes and
short documents single-agent; no benchmark or extra reviewer runs by default.
A savings claim requires a separately observed comparable single-agent baseline
and total parent+worker usage for the same acceptance scope; include repeated
context and integration effort. Without those counters, report not_measured.

Optional `delegation.worker_token_budget` is a positive integer admission limit
for reported worker input+output tokens. It blocks further dispatch once reached
or while prior usage is pending/unavailable. Consequently budgeted dispatch is
conservative and serial until usage is known. It does not interrupt an in-flight
provider call, predict its cost or enforce a hard billing ceiling. Without an
explicit budget, no invented numeric token target is imposed. Host usage limits
remain separate. Measure parent+workers on comparable tasks before claiming
savings; retain a concise task contract and avoid duplicated reviews.


## Concrete completion evidence

A completed worker receipt additionally requires `verification`,
`instruction_evidence` and `execution_resolution`. Verification uses the unit's
exact acceptance strings. The same shape is required by a completed G7 skill
result, using the task's exact success_criteria:

```json
{
  "verification": [{
    "criterion": "Exact criterion from the accepted task or unit",
    "status": "passed",
    "evidence": [{"path": "checks/result.txt", "sha256": "actual SHA-256 of file bytes"}]
  }],
  "instruction_evidence": {
    "instruction_hash": "packet.skill_context.sha256",
    "reference_hashes": ["each packet reference SHA-256 in packet order"]
  },
  "execution_resolution": {
    "adapter": "codex", "model": "platform-default", "reasoning": "unknown",
    "native_reasoning": "unavailable", "status": "platform_default", "evidence_ids": []
  }
}
```

Evidence paths are canonical target-relative nonempty files, checked against
actual bytes. One concise report may cover several criteria. Blank, missing,
stale, duplicate, uncovered or not_run criteria cannot complete. Context files
are checked again when recording a worker completion. IDs remain trace labels,
not substitutes for evidence. Hashes establish identity, not truth: the coordinator
must read the report and verify the claimed behavior and instruction application.
Unmet or waived criteria do not pass this runtime contract; resolve them or make
an explicitly authorized acceptance change through a new linked intake.

## Interrupted work and source changes

Runner start/submit/work-event verify existing registry/source pins. A stale
source requires an approved source update and repin; do not manufacture approval
by changing hashes. The stored source revision comes from the verified manifest.

An active task can be continued through status/next. For waiting_user, blocked
or failed tasks, preserve the old task and use ordinary start with a new task ID
and revised intake containing `supersedes_task_id: "TASK-old"`. Recheck intent,
authority and inputs; no old result or approval is automatically copied. The
Runner records the prior ID/revision/status. Old active/complete tasks cannot be
superseded through this path, and all old workers must first terminate and be
recorded. This deliberately adds no resume/retry state machine.

Unknown project state permits read-only investigation/review. Material requests
are blocked until reclassified. G2 discovery must return waiting_user or blocked,
then use the linked intake with confirmed Greenfield/Brownfield/Hybrid state;
do not use completed to advance an unknown baseline into implementation. A
factual reclassification may use inspected repository evidence; it does not
require asking the user to choose a fact already established locally.

Optional reasoning_lens values and the expertise assessment are defined in
[workflow-composition](../SKILL.md#actively-assess-expertise-then-choose-bounded-roles).
Budgeted work plans expose serial admission rather than proposing unavailable
parallelism. All actual usage and completion checks remain unchanged.
