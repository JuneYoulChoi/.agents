# Skill adaptation review — 2026-10-24

The user authorized the five-layer update and review of the complete candidate inventory. All 110 packages / 126 skill entrypoints were metadata-screened. Selected instruction portions informed original core procedures; no downloaded package was promoted or executed. This is not a full security/license audit of 110 packages.

## Decisions

| Source package | Portion integrated | Core owner | Excluded assumptions |
| --- | --- | --- | --- |
| [codebase-design](../../incoming/architecture/mattpocock-skills/codebase-design/SKILL.md) | small meaningful interfaces and localized complexity | core.architecture-and-design-patterns | No mandated vocabulary, exactly-one-interface rule or two-adapter threshold. |
| [domain-modeling](../../incoming/architecture/mattpocock-skills/domain-modeling/SKILL.md) | preserve domain vocabulary and accepted decisions | core.architecture-and-design-patterns | No full domain model for every task. |
| [improve-codebase-architecture](../../incoming/architecture/mattpocock-skills/improve-codebase-architecture/SKILL.md) | evidenced structural friction before refactoring | core.brownfield-impact-analysis | No blanket architecture scan, mandatory subagent, CDN report or browser launch. |
| [cavecrew](../../incoming/context/caveman/cavecrew/SKILL.md) | bounded role outputs with source locations | core.workflow-composition | No cryptic compression of reasoning, risk, uncertainty or authority; presets not installed. |
| [caveman](../../incoming/context/caveman/caveman/SKILL.md) | concise routine reporting | core.workflow-composition | No global language compression or omitted design rationale. |
| [caveman-compress](../../incoming/context/caveman/caveman-compress/SKILL.md) | compact repeated context while preserving evidence | core.workflow-composition | No destructive context replacement or loss of accepted constraints. |
| [verify-and-stop](../../incoming/quality/caveman/verify-and-stop/SKILL.md) | reuse current checks and stop optional expansion | core.verify-and-handoff | Never skip mandatory checks or discard open material failures. |
| [requesting-code-review](../../incoming/quality/superpowers/requesting-code-review/SKILL.md) | read-only scoped review and actionable evidence | core.verify-and-handoff | No automatic scope expansion or redundant review dispatch. |
| [verification-before-completion](../../incoming/quality/superpowers/verification-before-completion/SKILL.md) | verification evidence before completion claims | core.verify-and-handoff | No redundant reruns when current acceptance evidence suffices. |
| [lean-build](../../incoming/workflow/caveman/lean-build/SKILL.md) | small coherent outcome and explicit non-goals | core.implementation-quality | No one-file rule or removal of necessary ownership/design. |
| [grill-with-docs](../../incoming/workflow/mattpocock-skills/grill-with-docs/SKILL.md) | resolve factual questions from current documents before asking | core.intake-and-route | No interrogation loop for already clear reversible tasks. |
| [dispatching-parallel-agents](../../incoming/workflow/superpowers/dispatching-parallel-agents/SKILL.md) | independent tasks, focused context and integrated verification | core.workflow-composition | No automatic spawning or shared-state mutation. |
| [subagent-driven-development](../../incoming/workflow/superpowers/subagent-driven-development/SKILL.md) | separate implementation/review contexts and acceptance checks | core.workflow-composition | No fixed models, compulsory per-task reviewers, self-approved material rulings or parked critical defects. |
| [writing-plans](../../incoming/workflow/superpowers/writing-plans/SKILL.md) | bounded acceptance slices and explicit dependencies | core.workflow-composition | Do not import a mandatory upstream executor or duplicate planner. |
| [team-composition-patterns](../../incoming/workflow/wshobson-agents/team-composition-patterns/SKILL.md) | minimum roles, explicit ownership and capability matching | core.workflow-composition | No Claude-only tool names, tmux configuration or fixed team-size heuristic. |

AI-DLC work outlines and proportional procedure inform `plan/08-layered-workflow.md`; no AI-DLC runtime, weakened guard policy or second router is imported. The official source is linked in `plan/01-industry-patterns-to-adopt.md`.

## Whole-inventory coverage

| Category | Packages | Existing core coverage |
| --- | ---: | --- |
| workflow | 13 | core.workflow-composition, core.greenfield-planning, core.brownfield-impact-analysis |
| architecture | 3 | core.architecture-baseline-and-design, core.architecture-and-design-patterns |
| context | 5 | core.workflow-composition |
| documentation | 9 | core.document-purpose, core.harness-overview-html |
| frontend | 6 | core.react-engineering, core.language-engineering |
| backend | 5 | core.technology-selection-and-integration, core.nodejs-engineering, core.grpc-engineering, core.implementation-quality |
| languages | 16 | core.language-engineering |
| quality | 13 | core.implementation-quality, core.verify-and-handoff |
| security | 7 | core.implementation-quality |
| devops | 3 | core.docker-engineering, core.kubernetes-engineering, core.configuration-and-environment-management |
| integrations | 1 | core.technology-selection-and-integration |
| ai | 8 | core.technology-selection-and-integration, core.language-engineering |
| physical-ai | 3 | core.isaac-lab-engineering, core.isaac-sim-engineering |
| simulation | 9 | core.isaac-sim-engineering |
| 3d | 4 | core.technology-selection-and-integration |
| robotics | 6 | core.ros2-engineering, core.moveit-engineering, core.modbus-engineering |

Coverage identifies the routing owner, not equivalence to every candidate. PDF/Office authoring, Blender, CUDA/model training, vendor sensor setup, specialized security scanners and database-specific guidance are still candidate capabilities. A task needing them requires a scoped review/adaptation or an explicit core fallback. No generic robotics skill is represented as a gripper or force-sensor driver.

## Trust and reproducibility

The [machine inventory](../../registry/skill-candidate-review.json) records each package, repository, metadata, snapshot digest and disposition. A changed snapshot triggers review. Active resolution remains exclusively [active-skills.json](../../registry/active-skills.json); incoming files are evidence only. Missing upstream sibling dependencies remain quarantined and do not become core dependencies.

## Replacement decision

Retain all existing core skills: their authority, portability and result contracts remain needed. Add one `workflow-composition` owner rather than installing overlapping orchestration frameworks. Incorporate planning, design, implementation and review improvements in their existing owners. Claims of lower tokens, shorter elapsed time and better output require representative measurements; none are claimed by this review.

## ROS 2 scoped addition — 2026-10-25

The inventory now contains 111 packages / 127 entrypoints. The original
[ROS 2 package](../../incoming/robotics/dbwls99706/ros2-engineering-skills/SKILL.md)
is pinned at `f0de84dfedd67b067ccc6d2851e681529606930c`, Apache-2.0.
Its entrypoint and selected runtime-provenance, callback/QoS and claim-boundary
ideas informed the active `core.ros2-engineering` 0.2.0 references. Original
hooks, validators, install scripts and the full reference corpus remain inert;
this is selective adaptation, not whole-package promotion or audit. There are
now 16 packages with selected procedural adaptations.

The separate [ROS MCP tool](../../tools/ros-mcp-server/README.md) preserves a
pinned original runtime subset and adds an inspected graph-only entrypoint.
It is outside incoming because it is a tool, not a skill. The user approved
download, scoped integration, testing and commit. No other MCP skill was
activated. See [review evidence](ros2-mcp-review-2026-10-25.md).

## Popularity-informed source refresh — 2026-10-25

Eight existing packages were downloaded again from pinned current official
commits; all 26 source files match their previous bytes. The
[source-selection review](popular-skills-2026-10-25.md) records install displays,
same-role alternatives, licenses and exact active-reference mappings.
Brainstorming, diagnosing-bugs, tdd and code-review now have scoped procedural
adaptations, bringing the total to 20 adapted sources; no package is promoted.
The inventory remains 111 packages / 127 entrypoints. The new short references
strengthen existing owners instead of running both upstream frameworks.
