# React engineering practices

## Component and state design

- Build components around cohesive UI responsibilities and stable composition,
  not arbitrary file-size thresholds. Keep props intentional and avoid boolean
  combinations that create invalid states.
- Keep state at the nearest shared owner. Prefer derived values during render;
  do not mirror props or query data into local state without a lifecycle reason.
- Use reducers/state machines when transitions are complex and invalid states
  need prevention. Keep global state for genuinely cross-cutting ownership.
- Treat effects as synchronization with external systems. Make dependencies,
  cleanup, races, cancellation, and development re-execution safe.

## Rendering, data, and UX

- Detect server/client, hydration, routing, and data-fetching ownership from the
  host framework. Avoid client waterfalls and duplicate caches when the
  framework already owns the boundary.
- Define loading, empty, partial, error, retry, offline, unauthorized, and
  success states. Preserve user input and focus where recovery requires it.
- Use semantic HTML and native controls, labelled forms/errors, predictable
  keyboard/focus behavior, sufficient contrast, reduced motion, and announced
  async status. ARIA does not repair an incorrect interaction model.
- Measure before memoizing. Stabilize identity only when a proven render or
  subscription boundary benefits; avoid cargo-cult memoization.

## Testing and anti-patterns

- Test observable user behavior rather than component internals. Use component
  stories/tests for states, integration tests for data boundaries, and E2E for
  critical user journeys; add accessibility and visual review as required.
- Use React DevTools/profiling as evidence for performance work.
- Reject effect-driven derived state, unowned global stores, index keys for
  mutable identity, state mutation, inaccessible custom controls, client-side
  secrets, and snapshots as the sole behavioral assertion.

Primary sources: version-matched React and host-framework documentation,
Testing Library/Storybook/Playwright documentation when selected, WCAG, and the
project design system.
