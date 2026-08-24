# Distributed-systems profile

Use when a remote call, message, or partial-failure boundary is in scope. Set
timeouts, define cancellation and idempotency, constrain retries with backoff
and jitter, and document delivery, duplication, ordering, replay, and failure
isolation semantics. Add circuit breakers, bulkheads, outbox/inbox, sagas, or
load shedding only when the failure model and QAS justify their operational
cost.
