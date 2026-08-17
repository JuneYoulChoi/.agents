# C# implementation profile

- Detect target framework, language version, SDK pin, nullable context, project
  layout, analyzers, package lock policy, and deployment model.
- Keep nullable reference types meaningful; do not suppress warnings instead of
  defining the boundary contract.
- Use `async` end-to-end for asynchronous I/O, propagate `CancellationToken`,
  and avoid sync-over-async or unowned background tasks.
- Dispose owned resources deterministically with `using`/`await using`. Make DI
  lifetimes and hosted-service shutdown explicit.
- Prefer immutable request/value models at boundaries and validate untrusted
  input before domain behavior. Separate transport models from core decisions
  when their evolution differs.
- Preserve the project's exception/result, logging, serialization, and options
  conventions. Do not expose secrets or sensitive values in diagnostics.
- Verify nullable/analyzer output, unit/integration tests, cancellation and
  disposal, serialization/API compatibility, trimming/AOT only when relevant,
  and configured performance/security checks.

Primary references: Microsoft .NET/C# documentation, framework compatibility
policy, and project analyzers/coding conventions.
