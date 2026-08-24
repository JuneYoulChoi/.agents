# Architecture pattern selection

Use only the families relevant to recorded architecture drivers. This is a
selection map, not a catalog to apply wholesale.

| Family | Consider when | Key checks |
| --- | --- | --- |
| Layered | responsibility and dependency direction need a stable separation | forbidden dependencies, bypasses, test seams, deployment implications |
| Modular monolith | one deployment can retain strong module ownership | module contracts, data ownership, compile/runtime coupling, extraction cost |
| Ports and adapters / hexagonal | domain behavior must be isolated from external systems | port ownership, adapter mapping, error translation, test substitution |
| Clean/onion | dependency inversion around domain/application policy is justified | inward dependency rule, mapping cost, framework leakage |
| Service-oriented / microservices | independent ownership/deploy/scale/failure justify distribution | consistency, latency, observability, versioning, operations, team ownership |
| Event-driven | asynchronous decoupling and event semantics are explicit | delivery guarantees, ordering, idempotency, schema evolution, replay, failure |
| Pipes and filters | transformations compose as staged data flow | backpressure, error propagation, ordering, observability, partial restart |
| Broker / message bus | mediation and routing are first-class capabilities | broker dependency, topology, availability, security, operability |
| CQRS / read-write separation | read and write models have materially different needs | consistency, duplication, synchronization, operational complexity |

Evaluate the simplest candidate that satisfies the QAS. Architecture styles
can coexist at different boundaries, but every combination needs an explicit
scope and interaction rule. Record “no named pattern” when direct module
composition is clearer.

Compare only candidates that decide the same boundary. For example, modular
monolith and microservices may be deployment/ownership alternatives, while
ports and adapters may be used inside either and therefore belongs in a
separate decision or a composed option. For every viable alternative show
which drivers it improves, which it worsens, its operational and migration
cost, and the condition under which it becomes preferable. If several remain
materially viable, recommend one but leave selection to the user.
