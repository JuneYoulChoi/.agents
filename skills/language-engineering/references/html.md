# HTML implementation profile

- Treat HTML as a public semantic and accessibility contract, not merely a
  rendering target. Use the simplest native element matching the interaction.
- Preserve heading hierarchy, landmarks, labels, names/roles/values, keyboard
  order, focus behavior, form semantics, errors, and status announcements.
- Keep content and essential actions usable under progressive loading/failure
  conditions appropriate to the product. Avoid div/button and clickable-span
  substitutes for native controls.
- Encode and sanitize untrusted content according to its destination context.
  Never place secrets or private configuration in markup or public bootstrap.
- Keep metadata, links, language, viewport, CSP/integrity, and resource loading
  aligned with the host framework and deployment policy.
- Verify document validity where tooling exists, keyboard and screen-reader
  semantics, accessible names, focus/error flows, responsive behavior, and
  automated accessibility checks plus required manual review.

Primary references: WHATWG HTML Living Standard, WAI-ARIA Authoring Practices
for non-native patterns, WCAG policy, and the host framework documentation.
