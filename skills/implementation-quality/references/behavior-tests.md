# Tests that distinguish correct behavior

Use for authored behavior changes requiring tests, a bug regression, or explicit
test-first work. It is supporting guidance within the existing quality result,
not a new profile enum. Do not apply it to cosmetic/document-only edits or add
tests that merely mirror a reversible low-impact change.

1. Reuse the accepted behavior contract and established test boundary. Ask only
   if a material boundary or expected behavior remains unresolved; existing
   user decisions need no second approval.
2. Choose an assertion with an independent oracle: an accepted example, known
   expected value, protocol rule or invariant. Recomputing the expected result
   using the implementation's algorithm is not useful proof.
3. For new test-first behavior, run one meaningful failing case, implement its
   coherent slice, and rerun. For a regression, demonstrate that the check catches
   the original failure where feasible. Never delete user work to manufacture
   a red result; use an isolated baseline or record the evidence limitation.
4. Exercise the real behavior boundary. Mock external effects when isolation
   requires it, rather than mocking away the defect or coupling every assertion
   to private calls. Internal invariants may need targeted tests; this is not
   an absolute ban on unit tests or internal verification.
5. Keep applicable error/edge cases and existing regression checks. Refactor
   within the accepted scope after the relevant checks pass, preserving
   SOLID/GRASP and language rules. Do not make a second review agent mandatory.

Report actual commands/results and the tested boundary to G7. Test-first is a
method, not evidence by itself. Stop additional tests when acceptance coverage
is sufficient; do not claim coverage of untested inputs.

Adapted from `mattpocock/skills` tdd and its tests/mocking references, commit
`5beb35b040e3de97e54fa9e386d7e42d15c295c2` (MIT). Upstream mandatory seam
approval, sibling skill dispatch and a separate refactoring review stage are
not imported. See [source selection](../../../docs/harness/popular-skills-2026-10-25.md).
