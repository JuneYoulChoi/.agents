# Node.js engineering practices

## Structure and runtime

- Pin/support explicit Node versions and preserve the repository's package
  manager and lockfile. Treat Corepack/package-manager changes as toolchain
  changes, not harmless setup.
- Separate domain/application logic from transport/framework/process adapters.
  Keep package exports and public APIs intentional; avoid deep-import contracts.
- Choose ESM/CommonJS from the current ecosystem and consumer contract. Do not
  mix them through ad hoc loaders or duplicate build outputs without evidence.
- Distinguish a browser build runtime from a deployed Node service.

## Async, resources, and operations

- Never block the event loop with uncontrolled CPU or synchronous I/O in a
  latency-sensitive process. Bound worker/thread/process offload and queues.
- Own every Promise rejection, timer, listener, stream, socket, worker, and
  background task. Define timeout, cancellation, backpressure, and cleanup.
- Translate errors once at an owned boundary. Preserve causes and stable public
  error contracts; redact secrets and sensitive data from logs.
- Handle startup validation and graceful shutdown for listeners, in-flight
  work, pools, consumers, telemetry, and forced termination deadlines.
- Expose health/readiness semantics that reflect dependency and drain state,
  not merely that the process exists.

## Security and verification

- Validate untrusted network/config/file inputs. Bound payloads, paths,
  redirects, subprocess arguments, uploads, and deserialization.
- Review dependency provenance, maintenance, license, transitive risk, install
  scripts, and lockfile changes. Do not select a package by downloads alone.
- Verify supported Node versions, deterministic install, lint/type/build,
  unit/integration/contract tests, cancellation/shutdown, stream and event-loop
  behavior, dependency audit, and performance/heap diagnostics when required.

Primary sources: supported Node.js API/diagnostics/security documentation,
package-manager documentation, and version-matched framework guidance.
