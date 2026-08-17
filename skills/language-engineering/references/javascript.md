# JavaScript implementation profile

- Detect Node/browser/runtime versions, ESM/CommonJS policy, package manager and
  lockfile, bundler/framework, lint/format/test configuration, and deployment.
- Preserve module boundaries and avoid ambient globals. Validate all network,
  storage, DOM, environment, and serialized inputs at runtime.
- Use Promises and `async`/`await` consistently; own rejection handling,
  cancellation/timeout, resource cleanup, and process/browser lifecycle.
- Distinguish `null`, `undefined`, absent fields, and falsy values at public
  contracts. Avoid implicit coercion where it obscures invariants.
- Keep event listeners, timers, streams, workers, and subscriptions paired with
  cleanup and backpressure/error behavior.
- Preserve the existing package manager and build/test stack; dependency or
  module-system changes require Brownfield impact review.
- Verify lint/format policy, unit/integration/E2E tests as applicable,
  unhandled rejection/error paths, bundle/runtime compatibility, accessibility
  for UI boundaries, and performance/security QAS.

Primary references: ECMAScript/runtime documentation and the selected
framework's official versioned guidance.
