# Module responsibility and interface review

Use only within an already activated G5 structure/design-interaction review.
This supports new modules and evidenced improvements to existing ones; it does
not activate pattern review for every bugfix.

- Identify callers, owned invariants, failure modes and lifecycle. An interface
  includes ordering, errors and resource obligations, not only type signatures.
- Keep callers from repeating knowledge that one cohesive owner can maintain.
  Compare using the existing module, a local change, and a new boundary only
  when each is viable. Prefer the smallest clear solution that meets acceptance.
- Ask what happens if a proposed abstraction is removed: does necessary
  complexity spread into callers, or does only forwarding disappear? Treat this
  as evidence, not a rule to delete adapters, security checks or lifecycle owners.
- Test at the boundary that exposes the relevant behavior. Inject dependencies
  where control of effects is needed; do not demand an interface for every class
  or a second implementation before any dependency boundary is legitimate.
- Preserve applicable SOLID/GRASP, idiomatic language rules and accepted ADRs.
  A small public surface does not justify a giant implementation with unrelated
  responsibilities or hidden errors.

For existing structure, stay within the requested module or observed change
friction. Cite callers, coupled edits or test obstacles before proposing a
refactor. Use the normal G5 alternative/decision contract; do not scan the whole
repository, generate a report or dispatch a design contest by default.

Return these findings inside the existing PATTERN record with verification and
rollback implications. No extra design artifact is required when that record
already explains the decision.

Adapted from `mattpocock/skills` codebase-design and
improve-codebase-architecture at `5beb35b040e3de97e54fa9e386d7e42d15c295c2`
(MIT). Mandatory vocabulary, sibling skill calls, parallel agents, CDN HTML and
automatic domain-document edits are excluded. See
[source selection](../../../docs/harness/popular-skills-2026-10-25.md).
