# Compact task contract

Use for material multi-step work or uncertain requirements, after the existing
baseline and impact gates. Reuse the current acceptance/WORK record; do not
create a second plan, mandatory folder hierarchy or new Runner fields.

Record only decisions that another capable model cannot safely infer:

| Item | Required information |
| --- | --- |
| Goal | Observable change and who depends on it |
| Exclusions | Work explicitly outside this slice |
| Preserved behavior | Existing contracts and invariants that must remain |
| Design basis | Relevant architecture/ADR and a representative implementation |
| Acceptance | Normal, error and boundary cases relevant to the change |
| Proof | Command or observation, expected result and artifact being checked |

An existing confirmed record satisfies these items; link it instead of copying
it. Small reversible tasks can express them in a few lines. Ask only about a
material gap; do not manufacture questions, alternatives or approval rounds.
Distinguish user decisions from proposals and evidence-backed working assumptions.

Split implementation into independently meaningful outcomes. Each slice names
owned paths, consumed/produced contracts where dependencies exist, its check,
and document effects. Keep interface names and exact accepted values consistent
across slices. Include only code examples needed to disambiguate a contract;
do not write the implementation twice in the plan and code.

Check coverage once against the accepted requirements. A proposed test must
catch a relevant failure; do not force a fixed number of edge cases. Update only
affected parts after new evidence. This record gives models the same inputs
and stopping conditions; it does not promise identical output or lower tokens.

Adapted from reviewed portions of `obra/superpowers` brainstorming and
writing-plans, commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` (MIT).
No upstream executor, mandatory reviewer, automatic commit, visual server or
new approval gate is imported. Provenance and license are recorded in the
[adoption review](../../../docs/harness/popular-skills-2026-10-25.md).
