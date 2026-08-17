# Go implementation profile

- Detect the `go` directive/toolchain, module/workspace layout, generated code,
  build tags, formatter/linter, test, race, and platform requirements.
- Organize packages around cohesive capabilities. Keep package APIs small;
  define interfaces at the consumer boundary rather than pre-abstracting every
  implementation.
- Return and wrap errors with actionable context while preserving comparison
  semantics. Do not log and return the same error without an ownership reason.
- Propagate `context.Context` across cancellable request boundaries; do not
  store it in long-lived structs or use it as an optional bag of parameters.
- Give every goroutine and channel an owner, termination condition, backpressure
  policy, and error path. Avoid copying mutex-bearing values.
- Preserve standard formatting and existing dependency/tool choices. Do not
  edit generated files.
- Verify `gofmt`, `go vet`/project lint, unit/integration tests, `go test -race`
  where supported, cancellation/leak behavior, cross-platform builds, and
  benchmarks when performance is material.

Primary references: Go language specification, Effective Go, Go Code Review
Comments where adopted, and official module/testing documentation.
