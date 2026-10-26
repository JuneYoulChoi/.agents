# Bounded evidence-driven diagnosis

Use for a reported bug, failing test or measured performance regression. This
is a reference inside the existing G3 impact branch, not another skill chain.

1. Capture expected and actual behavior for the user's exact symptom. Prefer
   an existing focused test or local command; pin inputs, versions and timing
   conditions that affect the result. Read relevant code as needed to construct
   the reproduction. Do not create a test that only proves the process starts.
2. Reduce the reproduction enough to distinguish plausible causes. Keep a
   link to the original scenario. Stop minimization when another reduction
   costs more than it improves diagnosis.
3. State a falsifiable cause and the observation that would distinguish it
   from credible alternatives. Do not invent three hypotheses for an obvious
   defect. Test one variable at a time; record disconfirming evidence too.
4. Fix through the responsible code boundary. At authorized execution, turn
   the reproduction into a useful regression check when feasible, then verify
   both the reduced and original symptom plus affected existing behavior.
5. Remove only task-owned temporary instrumentation, preserve useful evidence,
   and hand off the cause, fix and actual checks to G7.

For performance, measure against a comparable baseline before changing code.
For intermittent failures, record trial conditions and observed rates; one
green run is not proof of absence. Bound stress/retry costs to the task. Do not
run upstream helper scripts, change production or access sensitive data merely
because the source suggests a diagnostic technique.

When reproduction is unavailable, label code-derived explanations as hypotheses
and report the exact missing evidence. Read-only analysis may continue; do not
claim a fix is confirmed. Use the existing bounded feedback/escalation contract
instead of an indefinite search or automatic architecture redesign.

Adapted from `mattpocock/skills` diagnosing-bugs, commit
`5beb35b040e3de97e54fa9e386d7e42d15c295c2` (MIT); its required helper scripts,
fixed hypothesis counts, mandatory stress loops and prohibition on reading
code before a runnable reproduction are not imported. See
[source selection](../../../docs/harness/popular-skills-2026-10-25.md).
