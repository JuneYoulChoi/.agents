# Native work: focused packets and checked joins

Use only for declared work units. Keep ordinary tasks on the serial skill path.
The portable Runner records preparation and terminal receipts; the host adapter
starts/stops workers. These checks do not grant tools or implement a sandbox.

## Bind and prepare

Bind each unit's `skill_id` to its responsible activated core skill. Unbound
intake units are provisional. Before completing composition, bind every pending
unit to a strictly subsequent skill, or remove unnecessary provisional units.
Already prepared plans cannot be replaced. Preserve completed evidence and use
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

The returned packet contains only the task goal, constraints and one unit's
acceptance, evidence references, paths and allowed tool requirements. Send only
that packet to a fresh worker context. On Codex use `fork_turns="none"`; on other
hosts disable history inheritance when supported, or use the serial path. No
recursive delegation. The packet is limited to 16,384 UTF-8 JSON bytes; oversize
input fails rather than silently dropping requirements. Reference bounded local
artifacts for details. The cap covers generated input, not later tool output or
the host's automatically supplied context.

Preparation checks current skill, joined dependencies, active worker count,
write/read/resource conflicts and path containment. Symlink aliases must first
be replaced with canonical target-relative paths. The host still needs actual
permission/worktree isolation. Do not run future-skill units early.

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
context, tool charges and currency. It is not proof of total savings.

Optional `delegation.worker_token_budget` is a positive integer admission limit
for reported worker input+output tokens. It blocks further dispatch once reached
or while prior usage is pending/unavailable. Consequently budgeted dispatch is
conservative and serial until usage is known. It does not interrupt an in-flight
provider call, predict its cost or enforce a hard billing ceiling. Without an
explicit budget, no invented numeric token target is imposed. Host usage limits
remain separate. Measure parent+workers on comparable tasks before claiming
savings; retain a concise task contract and avoid duplicated reviews.
