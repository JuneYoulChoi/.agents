# Acceptance and standards evidence

For material code handoff or an explicit code review, reuse existing checks and
review evidence. Review once along two distinct questions:

| Question | Evidence |
| --- | --- |
| Does it implement the request? | Accepted requirements, actual diff, observable behavior and omissions |
| Does it fit the project? | Existing architecture, coding conventions, ownership and applicable quality rules |

Pin the comparison and include work in scope: committed branch changes,
staged/unstaged edits and relevant untracked additions as applicable. A
`base...HEAD` diff alone cannot review work that has not been committed. Do not
ask for an issue tracker when the user request or local task record already
supplies the acceptance contract.

For each material finding, give the requirement/rule, location, failure
condition and consequence. Keep missing features, wrong behavior and scope
creep distinct from optional design preferences. Smells suggest investigation;
they do not mandate a rewrite or override project conventions.

An exit-zero command proves only its checked scope. Lint is not build proof,
passing tests are not proof every requirement is met, and an agent's report is
not integration evidence. Reuse a recorded pass only when revision, environment
and scope still match. Otherwise rerun the affected check, read its result and
report failed, not_run or blocked honestly.

Use one agent by default. Independent review is conditional on request or
material risk/uncertainty, authority, capability and cost benefit; no automatic
two-agent review or separate model call is introduced. When the user defers
model evaluation, report it as not_run. Do not quietly run it or call it passed.
Stop optional review expansion when required acceptance is evidenced; unresolved
material defects still go through bounded feedback.

Adapted from `obra/superpowers` verification-before-completion at
`2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` and `mattpocock/skills` code-review
at `5beb35b040e3de97e54fa9e386d7e42d15c295c2` (both MIT). Mandatory repeated
checks per message, tracker setup, parallel reviewers and blanket smell fixes
are excluded. See [source selection](../../../docs/harness/popular-skills-2026-10-25.md).
