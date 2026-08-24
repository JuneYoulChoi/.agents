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
| layered gated skill graph | The `G0`–`G7` deterministic routing DAG that evaluates tree-classified evidence and may activate several skill branches |
| gate | One routing layer that consumes multiple evidence/artifact inputs and emits activated, candidate, suppressed, or blocked branches plus typed outputs |
| activation | Evidence-backed selection of a branch whose approved skill body may be loaded |
| suppression | An explicit decision not to activate a candidate or adjacent branch, with reason and evidence |
| change characteristic | A small evidence-backed description of the affected slice, such as authored code, architecture structure, design interaction, API/data contract, concurrency, security, or documentation-only work; it selects profiles but is not a learned weight |
| language scope | Whether listed languages are `authored_in_scope`, `detected_only`, `generated_only`, or `none`; only the first may activate language and implementation-quality skills |
| application depth | The light, standard, or deep procedure rigor assigned to one activated skill; it does not weaken task risk, authority, or completion gates |
| implementation-quality profile | A progressively loaded, language-neutral G6 rule set selected for an evidenced authored-code concern; `core` is mandatory only when the skill is applicable |
| forward pass | Ordered evaluation from guard through verification, joining required predecessor outputs |
| backward feedback propagation | Bounded repair that reopens the nearest responsible gate, invalidates only dependent descendants, and starts a new forward revision; it is not learned-weight training |
| forward revision | Immutable version of one gate-network evaluation pass for a task |
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
| execution profile | Vendor-neutral gate role, low/medium/high reasoning recommendation, independent-context flag, and evidence-backed escalation reasons |
| execution resolution | Adapter record of the actual model/reasoning application: exact, upgraded, degraded, platform_default, or unavailable |
| NFR | Non-functional requirement, such as latency, availability, privacy, or security |
| QA | Quality Attribute; use `QA testing` when referring to quality-assurance/testing activity |
| configuration candidate | A value examined for classification as a code constant, build-time, deploy-time, runtime, or secret setting; it is not automatically externalized |
| configuration contract | The typed keys, sources, precedence, validation, ownership, compatibility, redaction, tests, and documentation governing application settings |
| technology ecosystem | A runtime, library, framework, protocol, platform, simulator, middleware, build tool, or orchestration system with its own architecture and engineering rules |
| primary technology kind | Exactly one deterministic classification: runtime, library, framework, protocol, platform, or tool |
| ecosystem engineering skill | An approved skill containing professional architecture, structure, rule, anti-pattern, integration, and verification practices for one technology ecosystem |
| technology status | required_by_user, detected_existing, candidate, selected, rejected, not_applicable, or prohibited |
| technology relationship | A required, recommended, optional, detected, or incompatible integration edge with condition and evidence |
| implementation profile | The `IMPL-*` record connecting a module and ecosystem binding to exactly the changed authored language profiles, toolchain, ownership, and verification |
| generated code | Tool-owned output regenerated from an authoritative schema/model; it is not hand-edited as ordinary source |
| QAS | Quality-attribute scenario: stimulus, context, response, and measurable response measure |
| standard profile | A progressively loaded `STD-*` applicability/alignment/conformance guide for one identified standard edition and scope |
| conformance intent | `guidance`, `alignment`, or `conformance`; only the last requires authorized normative text and criteria-level evidence |
| architecture pattern | A reusable system/module/deployment structure selected from architecture drivers and trade-offs, not prescribed by an international standard |
| design pattern | A reusable object/component/collaboration solution selected at a concrete responsibility boundary |
| pattern decision | A `PATTERN-*` record with scope, drivers, alternatives, status, consequences, trace, migration, and verification |
| materially viable pattern candidate | An option that satisfies hard constraints for the same decision scope and differs in consequential quality, boundary, ownership, operations, cost, or migration trade-offs |
| pattern recommendation | The evidence-backed preferred candidate plus rationale and conditions that could change the preference; it is not a user selection |
| source of truth | The artifact that wins when project evidence conflicts; default hierarchy is in the implementation guide |
| ordinary document | A change-coupled project document that the task owner allows the Router to update |
| protected document | Policy, compliance, externally published, owner-controlled, or legally significant content |
| fresh context | A verifier or resumed run that does not rely only on the producer's conversational memory |
| safe fallback | The least-privileged procedure that can still produce an honest result, or a user question/block |
| owner | The person/team authorized to decide or accept risk for the artifact or action |
| residual risk | Risk remaining after the proposed change and verification |
| approval | Explicit, scope-bound authorization with actor, time, expiry, and target |
| artifact revision | Immutable or hashable version of the code/document/configuration being evaluated |
