# Claude adapter: native work dispatch, reasoning mapping and hook

This is the Claude-specific half of the
[native-work contract](../../skills/workflow-composition/references/native-work.md).
The Runner still never starts a worker; this file says how Claude does it.

## Role agents

Installation copies `adapters/claude/agents/harness-*.md` to the target's
`.claude/agents/`. There is one agent per unit role (analyst, designer,
implementer, reviewer, verifier, documenter). Read-only roles have no edit tool.
A unit's role must be allowed at the current gate's portable role:

| Gate role | Unit roles that may run there |
| --- | --- |
| architect (G2) | analyst, designer, reviewer, documenter |
| analyst (G3) | analyst, reviewer |
| planner (G4) | analyst, designer, reviewer |
| specialist (G5) | analyst, designer, implementer, reviewer |
| implementer (G6) | analyst, implementer, reviewer, documenter |
| verifier (G7) | verifier, reviewer, documenter |

Guard (G0) and classifier (G1) work is never dispatched. `prepare-work` rejects
a role outside this table.

## Dispatch procedure

For each batch in `next.work_plan.batches`, and only for units bound to the
current skill:

1. Count free worker slots and call `prepare-work` once per unit with
   `mode: native` and that fresh `native_worker_capacity`. Use `mode: serial`
   and do the unit yourself when delegation is not authorized or no slot exists.
2. Start every prepared unit of the batch in one message, one Agent call each,
   with `subagent_type: harness-<unit.role>` and the returned packet JSON as the
   whole prompt, plus the evidence file path the worker must write. Do not add
   conversation history. Units of one batch run concurrently; the next batch
   starts only after this one is recorded.
3. When each agent returns, read its evidence file, check every acceptance
   string yourself, then call `record-work`. A worker that did not return by the
   unit timeout is stopped and recorded `timed_out`.
4. Submit the single joined skill result only after every unit of the skill is
   recorded `completed`.

When the route sets `independent_context` for G7, run verification as a
`harness-verifier` agent on the pinned revision and submit its evidence IDs as
`independent_verification_evidence_ids`.

## Reasoning resolution

Map the portable `execution_profile.reasoning` to the Agent call. These are
defaults for when the session permits a per-agent model; otherwise record
`platform_default`.

| Portable reasoning | Claude agent model | Recorded status |
| --- | --- | --- |
| low | haiku | exact |
| medium | sonnet | exact |
| high | opus | exact |
| any, when the model cannot be chosen | inherited session model | platform_default (or `upgraded`/`degraded` when the inherited level is known) |

Record the actual model ID in `execution_resolution.model`. A `degraded`
resolution needs evidence IDs. Never lower the model for a gate that a
high-risk or repeated-feedback escalation raised to `high`; use the session
model and record what ran.

## Token usage

The Agent result reports the worker's token total when the host exposes it;
record it as `usage.status: reported` with that source, otherwise
`unavailable`. Worker totals are not task totals. To claim a saving, run the
same acceptance scope once serially and once delegated and compare parent plus
worker usage; until then the Runner reports `savings: not_measured`.
