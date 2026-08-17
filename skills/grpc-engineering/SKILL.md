---
name: grpc-engineering
description: Design, implement, review, evolve, debug, migrate, or verify gRPC and Protocol Buffers APIs. Use for proto packages/services/messages, unary or streaming RPCs, generated clients/servers, schema compatibility, deadlines, cancellation, retries, idempotency, metadata, status/errors, health checking, reflection, load balancing, security, observability, or multi-language gRPC integration.
---

# gRPC Engineering

Treat `.proto` definitions and operational semantics as public contracts. Keep
generated code reproducible and never hand-edit it.

## Entry gate

Require intake, architecture/external-interface evidence, and the gRPC
`TECH-*` record. Brownfield work requires current schema history, producers,
consumers, language plugins, runtime versions, rollout topology, and
compatibility tests.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Model versioned packages, services, messages, ownership, field semantics,
   and evolution before choosing unary/client/server/bidirectional streaming.
3. Define deadlines, cancellation, idempotency, retry/hedging, flow control,
   errors, metadata, authentication/authorization, health, and observability.
4. Invoke `$language-engineering` for each authored producer/consumer binding;
   generated paths remain tool-owned. Record protoc/Buf and plugin pins.
5. Route endpoints, TLS identities, limits, deadlines, keepalive, and policy
   values through `$configuration-and-environment-management`.
6. Verify lint/generation freshness, wire/source compatibility, cross-language
   contract tests, streaming/backpressure, failure/rollout, security, and docs.

## Result and exit

Return schema/package/service ownership, RPC semantics, compatibility policy,
codegen/bindings, resilience/security/operations, configuration, verification,
docs, and open points. Block execution for unowned schema evolution, ambiguous
field semantics, unsafe retry, absent deadline/cancellation, or unpinned codegen.
