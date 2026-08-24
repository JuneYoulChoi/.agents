# Software design pattern selection

Choose a design pattern only at a concrete responsibility or collaboration
boundary. First identify the changing concern and the simpler direct design.

| Family | Typical pressure | Review focus |
| --- | --- | --- |
| Creational | construction varies or lifecycle must be controlled | ownership, invalid states, dependency visibility, testability |
| Structural | interfaces or compositions must vary independently | indirection cost, identity/lifetime, error and performance behavior |
| Behavioral | algorithms, state transitions, or collaborations vary | invariants, ordering, cancellation, concurrency, observability |
| Domain | domain rules and language require explicit modeling | aggregate/module boundary, consistency, persistence leakage |
| Integration | systems exchange commands, events, or translated models | contract ownership, idempotency, compatibility, failure recovery |
| Concurrency | shared state, scheduling, or async work needs coordination | race/deadlock safety, backpressure, cancellation, shutdown, testing |

Examples such as Factory, Adapter, Strategy, State, Observer, Repository,
Unit of Work, anti-corruption layer, circuit breaker, actor, or reactor are
candidates only when their stated pressure exists. Prefer language/framework
idioms when they express the same responsibility without custom machinery.
Record consequences and a test that would fail if the claimed benefit is lost.

Compare patterns only when they solve the same concrete responsibility. A
Factory and Strategy usually address different decisions and may compose; a
Strategy and a direct conditional implementation may be real alternatives for
one variation point. Keep direct implementation in the comparison when it is
viable. Explain the indirection, lifecycle, performance, testing, and change
cost of every viable option. If those trade-offs represent a material user-
owned choice, recommend one and wait for the user's selection.
