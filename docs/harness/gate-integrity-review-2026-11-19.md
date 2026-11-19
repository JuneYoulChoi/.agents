# Gate integrity and routing review: 2026-11-19

Scope: user-requested review of gating, routing, skill and tool connections,
persona-based parallel work, token reduction and SOLID/GRASP/pattern
application, followed by a user-approved correction.

## Reproduced before the change

- Every activated skill before G7 could be submitted `not_applicable` with no
  artifacts, and the task completed on one trivial evidence file.
- `completed` was accepted with empty artifact/evidence IDs, with a
  `clarification` or `backward_feedback` transition, and with reasoning
  degraded to `low` on a high-risk deep route.
- The pattern and implementation-quality validators were not called by submit.
- A `waiting_user` task could not continue; a linked restart replayed the whole
  queue. Feedback changed events and revision but not the queue.
- Routing: code change under a non-software scope skipped G2/G3; a `candidate`
  technology did not activate selection; `not_applicable` state skipped
  impact/planning; harness and high-risk mutation had no approval gate; manual
  mode blocked only by action name; pattern review stayed suppressed for
  architecture planning and Greenfield design; `security`/`performance` fields
  did not select quality profiles; a one-word change and a read-only question
  ran the full queue.
- SOLID/GRASP appeared only as one-sentence reminders; the intake list omitted
  `object_oriented`; role guidance was one sentence; the Claude adapter had no
  agent definitions, dispatch procedure, model mapping or hook.

## Changed

See [the canonical section](../../plan/08-layered-workflow.md) "Gate integrity,
routing entry and native dispatch (2026-11-19)".

## Verification

`python3 -B -m unittest discover -s tests -p 'test_*.py'` and
`python3 -B scripts/fixture_runner.py`; results are recorded in the handoff for
this change. Two fixtures gained `approval_evidence_ids` and three existing
tests gained the now-required artifacts or typed quality record.

## Not verified / remaining

No live native worker dispatch and no token measurement were run. The hook is
shipped but not enabled. `allowed_tools` are still unvalidated strings, G4
concerns other than security/performance still have no owning skill, and a
token budget still serializes dispatch. The HTML overview was not regenerated.
