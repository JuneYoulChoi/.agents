# gRPC engineering practices

## Contract design and evolution

- Use stable, versioned proto packages and clear service ownership. Choose field
  names/numbers/types, enum zero values, presence, defaults, units, timestamps,
  pagination, and resource identity deliberately.
- Never reuse removed field numbers/names; reserve them. Prefer additive
  evolution and verify wire plus generated-source compatibility for every
  supported consumer language.
- Separate transport messages from internal domain state when release cadence
  or compatibility differs. Avoid exposing storage or framework internals.
- Select streaming only for an actual ordering, incremental delivery,
  bidirectional interaction, or throughput need; define flow control and partial
  failure semantics.

## Runtime behavior

- Require bounded deadlines and cancellation propagation. Define whether an
  operation is idempotent before enabling retry/hedging; bound attempts and
  backoff to avoid retry storms.
- Use canonical status codes consistently and provide safe structured details
  only when consumers can act on them. Do not leak sensitive internals.
- Define message/metadata limits, compression, keepalive, connection lifecycle,
  load balancing, health checking, draining, and rollout compatibility.
- Define TLS and workload/user identity, authorization at the owned boundary,
  audit needs, and observability for method, status, latency, retries, and
  saturation without high-cardinality/sensitive labels.

## Toolchain and verification

- Pin Protobuf/compiler and language plugins. Generate deterministically from
  the authoritative schema. Use Buf or an equivalent established mechanism for
  lint/breaking checks only after project/dependency review.
- Verify schema lint/build, generated-code freshness, breaking change checks,
  cross-language unary/streaming contract tests, deadline/cancellation/retry,
  health/drain/rollout, authentication/authorization, and load/QAS behavior.

Primary sources: Protocol Buffers language/specification guidance,
version-matched gRPC concepts/guides and language bindings, and selected
code-generation tool documentation.
