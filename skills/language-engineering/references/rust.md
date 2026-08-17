# Rust implementation profile

- Detect edition, MSRV/toolchain pin, Cargo workspace/features, target triples,
  async runtime, `unsafe` policy, formatting, lint, and test configuration.
- Model ownership and borrowing directly; use cloning, interior mutability, or
  shared ownership only with a recorded lifecycle/concurrency reason.
- Use `Result` and domain error types at recoverable boundaries. Reserve panic
  for violated invariants; avoid `unwrap`/`expect` in ordinary production paths.
- Keep `unsafe` minimal, documented with safety invariants, and covered by
  focused review/tests. Do not infer `Send`/`Sync` correctness from compilation
  alone when external resources or FFI are involved.
- Give spawned tasks, channels, locks, cancellation, and shutdown explicit
  owners. Avoid holding blocking locks across `await`.
- Keep feature flags additive and test meaningful feature combinations. Do not
  hand-edit generated bindings.
- Verify `cargo fmt`, project lint policy/Clippy, unit/integration/doc tests,
  target builds, feature matrix, unsafe/FFI boundaries, and benchmarks or
  property tests when QAS require them.

Primary references: Rust Reference, Rust API Guidelines where applicable,
Cargo documentation, and the selected ecosystem crate/binding documentation.
