# Harness glossary

Use these meanings consistently. If a project uses a different local meaning,
record an override in `.agents/overrides/` before routing work.

| Term | Meaning |
| --- | --- |
| session | One user interaction context; it may contain multiple tasks |
| task | One goal with its own state, evidence, decisions, and completion criteria |
| run | One attempt to progress a task; a resumed task may have multiple runs |
| stage | One named state-machine step such as `impact` or `verification` |
| Router | The accountable coordinator that classifies, selects, transitions, and reports |
| skill | A progressively loaded procedure with instructions/resources and a result contract |
| agent/delegate | A bounded worker invoked for independent analysis or mutation |
| evaluator | A reviewer that checks a pinned acceptance contract independently |
| Greenfield | No relevant existing implementation or contract is being changed |
| Brownfield | A relevant existing implementation, contract, data, or operational behavior is being changed |
| Hybrid | New work crosses an existing system boundary or extends an existing product while adding new structure |
| Unknown | Evidence is insufficient to classify; discovery-only, no material mutation |
| session scope | Whether the request is software, general information, decision support, creative, or non-engineering |
| field | The problem domain, such as API, database, UI/UX, security, or documentation |
| action | What the user wants done: investigate, define, plan, design, implement, verify, review, document, approve, or handoff |
| material | Likely to change behavior, public contract, data, security, operations, cost, user-facing meaning, or a hard-to-reverse decision |
| reversible | Prior state can be restored with a recorded operation without data loss or expanded authority |
| assumption | A temporary interpretation that is bounded, recorded, testable, and safe to reverse |
| evidence | An observation, artifact, command result, user answer, or approved source supporting a claim |
| observed | Directly inspected or executed; include source and timestamp |
| inferred | Derived from evidence; include the reasoning link |
| assumed | Not yet established; include validation or expiry condition |
| open issue | A material question without a terminal decision; blocks completion |
| deferred issue | Explicitly excluded with owner, reason, and follow-up condition |
| waiver | Authorized acceptance of a known unmet validation or traceability requirement |
| depth | Light, standard, or deep procedure intensity |
| NFR | Non-functional requirement, such as latency, availability, privacy, or security |
| configuration candidate | A value examined for classification as a code constant, build-time, deploy-time, runtime, or secret setting; it is not automatically externalized |
| configuration contract | The typed keys, sources, precedence, validation, ownership, compatibility, redaction, tests, and documentation governing application settings |
| QAS | Quality-attribute scenario: stimulus, context, response, and measurable response measure |
| QA | Quality assurance/testing activity; do not use it as a quality-attribute abbreviation |
| source of truth | The artifact that wins when project evidence conflicts; default hierarchy is in the implementation guide |
| ordinary document | A change-coupled project document that the task owner allows the Router to update |
| protected document | Policy, compliance, externally published, owner-controlled, or legally significant content |
| fresh context | A verifier or resumed run that does not rely only on the producer's conversational memory |
| safe fallback | The least-privileged procedure that can still produce an honest result, or a user question/block |
| owner | The person/team authorized to decide or accept risk for the artifact or action |
| residual risk | Risk remaining after the proposed change and verification |
| approval | Explicit, scope-bound authorization with actor, time, expiry, and target |
| artifact revision | Immutable or hashable version of the code/document/configuration being evaluated |
