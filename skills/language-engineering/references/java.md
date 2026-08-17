# Java implementation profile

- Detect Java release/toolchain, module/package layout, Maven/Gradle policy,
  framework version, nullness/static analysis, test stack, and runtime target.
- Keep package boundaries cohesive and public APIs minimal. Prefer immutable
  value objects for messages and configuration unless mutation is required.
- Define checked/unchecked exception policy from the project; preserve causes
  and translate exceptions once at owned boundaries.
- Close resources deterministically. Give executors, futures, virtual/platform
  threads, transactions, and shutdown hooks explicit lifecycle ownership.
- Treat reflection, serialization, annotations, proxies, and generated code as
  framework contracts; do not refactor them as ordinary local details.
- Pin dependencies through the established build mechanism and review runtime,
  security, licensing, and migration effects.
- Verify compile/static-analysis output, unit/integration/contract tests,
  resource shutdown, concurrency/cancellation, serialization/API compatibility,
  and relevant JVM performance/operational checks.

Primary references: Java Language/VM specifications, JDK API documentation,
build-tool documentation, and the selected framework binding contract.
