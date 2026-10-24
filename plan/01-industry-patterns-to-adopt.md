# Industry patterns assessed for this harness

Checked on 2026-08-03; configuration-management and technology-ecosystem inputs
were reviewed on 2026-08-17. These are design inputs, not runtime dependencies.

| Pattern | Evidence | Apply here |
| --- | --- | --- |
| Short universal instructions; detailed skills loaded only when relevant | [GitHub's skills vs. custom-instructions guidance](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) and [customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet) | Keep the global entry rule short; place workflows, templates, and specialist detail in skills. |
| Router/supervisor for ambiguous or complex work; direct routing for simple work | [Amazon Bedrock collaboration modes](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-announces-general-availability-of-multi-agent-collaboration/) | Use one Router. Delegate only when complexity or uncertainty justifies it. |
| Bounded specialist agents with isolated context and scoped tools | [GitHub custom-agent orchestration](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/custom-agents) | Give each delegate a narrow question, evidence set, tool scope, and response schema. Do not preload every skill into every agent. |
| Planner–generator–evaluator separation and an agreed, testable work contract | [Anthropic harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) | For deep work, establish a slice-level acceptance contract before implementation; an evaluator verifies independently. |
| Incremental features plus durable handoff artifacts across sessions | [Anthropic effective long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Maintain task state, progress/handoff record, feature/acceptance list, and runnable verification instructions. |
| DAG/workflow rather than unrestricted agent chatter | [AWS multi-agent workflow and graph patterns](https://aws.amazon.com/blogs/machine-learning/multi-agent-collaboration-patterns-with-strands-agents-and-amazon-nova/) | Model stages and transition conditions explicitly; parallelize only independent branches and converge through a synthesizer. |
| Observability, governance, and human-in-the-loop for consequential actions | [AWS enterprise agentic AI guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/govern-architect-agentic-ai/enterprise-architecture.html) | Record decisions, evidence, tool/action scope, verification, and user approvals; gate destructive/external activity. |
| Externalized, environment-independent application configuration | [The Twelve-Factor App: Config](https://12factor.net/config) and the reviewed [configuration-management skill](https://www.skills.sh/aj-geddes/useful-ai-prompts/configuration-management) | Add a language-neutral configuration contract with typed validation, explicit precedence, secret separation, and progressively loaded C++/Rust/Java/Python/TypeScript/JavaScript/Go/Shell references plus HTML/CSS public-artifact boundaries. |
| Capability-first technology selection and version-matched ecosystem guidance | Official documentation for [ROS 2](https://docs.ros.org/en/ros2_documentation/rolling/Concepts.html), [Node.js](https://nodejs.org/docs/latest/api/), [React](https://react.dev/), [gRPC](https://grpc.io/docs/), [Isaac Lab](https://isaac-sim.github.io/IsaacLab/), [Docker](https://docs.docker.com/), [Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/), [MoveIt 2](https://moveit.picknik.ai/), [Kubernetes](https://kubernetes.io/docs/concepts/), [Modbus](https://www.modbus.org/modbus-specifications), and [colcon](https://colcon.readthedocs.io/) | Add a product-neutral `TECH-*` decision layer, then progressively load one approved ecosystem engineering skill and only the changed implementation-language profiles. Treat official/versioned contracts as authority and popularity as advisory. |
| Standards applicability before conformance language | Official records for [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html), [29148:2018](https://www.iso.org/standard/72089.html), [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), [25019:2023](https://www.iso.org/standard/78177.html), [ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html), [15288:2023](https://www.iso.org/standard/81702.html), and [15289:2019](https://www.iso.org/standard/74909.html), reviewed 2026-08-24 | Add progressive `STD-*` profiles at G2. Keep guidance/alignment distinct from formal conformance, which requires authorized normative text, scope, evidence, deviations, and owner. |
| Driver-led architecture and design pattern selection | Widely established pattern literature and project/ecosystem conventions, applied through evidence rather than a copied universal catalog | Add one language-neutral G5 skill. Evaluate only relevant architecture/design families from UC/FA/QAS and constraints, distinguish alternatives from composable patterns, and record fit and trade-offs as `PATTERN-*`. If several material alternatives remain, recommend one but require the user to select before ecosystem and language skills implement it. |
| Evaluation-driven reasoning effort instead of maximum effort everywhere | [Official OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model), reviewed 2026-08-17 | Use a balanced portable baseline, raise it only for explicit risk/conflict/feedback signals, and compare actual adapter choices on representative tasks. Keep vendor-specific levels in adapter evidence rather than Core policy. |

## Deliberate adaptations

- **No always-on swarm.** AWS documents swarm and graph patterns, but this
  repository will default to a single Router because agent overhead, duplicated
  reasoning, and conflicting drafts are costs. Parallel experts require separable work, benefit evidence, authority, native
  capability, bounded ownership and a convergence budget; depth alone neither
  enables nor prohibits them.
- **No automatic user-intent invention.** The planner may propose a product
  direction, but ambiguity in concept, priority, audience, or acceptance must
  produce a user decision gate.
- **No vendor lock-in.** AWS and GitHub patterns are architectural references;
  the active skill format and the task-state schema remain portable across
  Codex and Claude.
- **Evaluator is independent, not ceremonial.** It checks agreed acceptance
  evidence and may reject a slice. It does not silently redefine the product.
- **Evidence is not consensus.** Parallel opinions based on the same code,
  document, or failed assumption are correlated. Material conclusions require
  independent verification where practical, and unresolved dissent is retained.
- **Portable core, explicit adapters.** A shared state/skill contract is
  normative; Codex and Claude entrypoints are adapters and must negotiate their
  actual available capabilities rather than pretending feature parity.
- **Portable execution profiles, not fixed models.** The Router recommends a
  role and `low`/`medium`/`high` reasoning level per gate. Each adapter maps that
  recommendation to an available platform model, records the actual resolution,
  and reports degradation instead of encoding vendor model names, prices, or
  token limits in the core policy.

## Applicability and evidence discipline

The linked practices are not copied as universal law. Each adopted pattern must
be recorded with source URL, access/review date, claim, applicability rationale,
owner, and revisit trigger. Apply a pattern only when its benefits exceed its
added context, latency, cost, and operational complexity.

For implementation, every adopted pattern receives a stable `PATTERN-*` ID,
source revision or commit where available, an internal requirement ID, and at
least one fixture/test ID. Vendor guidance is an input to design, not a runtime
dependency. A changed or unavailable source triggers review; it does not change
the running harness automatically.

| Pattern | Adopt when | Do not use / fallback |
| --- | --- | --- |
| Parallel specialists | Work has separable evidence or genuinely conflicting expert concerns | A clear, low-risk task; use the Router or one focused reviewer |
| Planner–generator–evaluator | Deep work has an agreed, testable slice and an executable verification environment | Acceptance is subjective/unapproved or verification cannot run; ask the user or record an exception |
| Durable state and handoff | Work spans sessions, agents, or material decisions | Tiny, reversible work; keep only the minimal task note |
| Human approval gate | Action is external, privileged, costly, destructive, irreversible, or sensitive | Reversible in-scope investigation or workspace change under existing authority |

## Future broad-activation quality goals

These remain useful manual quality goals for a future autonomous/broad
activation, but they are not separate executable fixture families in the
current bounded reference suite:

1. A small, clear, reversible fixture completes without delegation or an
   unnecessary clarification turn, while preserving its interpretation and
   verification evidence.
2. An ambiguous fixture enters `waiting_user` before material work and asks a
   bounded decision question with facts, options, impacts, and recommendation.
3. A Brownfield feature fixture produces an evidence-linked impact record and
   regression scope before edits.
4. A Deep disagreement fixture converges with cited evidence or escalates after
   the defined three-round budget, preserving dissent.
5. A fresh session reconstructs goal, decision, next action, artifact revision,
   and validation status from the durable task record alone.
6. A document-only fixture records purpose, audience, owner, and review status,
   then creates only fit-for-purpose documentation.
7. An unauthorized deploy, secret access, destructive command, or external
   publication fixture is refused, logged, and converted to an approval request.

The selected executable fixture definitions and pass/fail assertions are in
[03-contracts-and-fixtures.md](03-contracts-and-fixtures.md). The ordinary
developer interaction model is in [04-user-guide.md](04-user-guide.md).

## 2026-10-24 workflow adaptation

AI-DLC's [workflow profiles](https://awslabs.github.io/aidlc-workflows/guide/workflow-profiles/)
inform explicit work outlines and proportional procedure. Our adaptation keeps
mandatory gates and quality floors; it does not import Guard Policy off modes,
the complete AI-DLC runtime or a second router. Superpowers' independent task
partitioning and review, wshobson's role composition, and selected Caveman
reporting/stopping ideas inform the native adapter contract. The source snapshot,
accepted portions, rejected assumptions and responsible core destinations are
recorded in [adoption notes](../docs/harness/skill-adoption.md). Owner: harness
maintainer; revisit when source, authority, adapter capability or fixtures change.
