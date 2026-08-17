# Technology taxonomy

Use independent axes so multi-role technologies remain classifiable without
inventing a single overloaded `framework` label.

## Primary kinds

| Kind | Meaning | Examples |
| --- | --- | --- |
| `runtime` | Executes application code | Node.js |
| `library` | Imported capability within an application | React |
| `framework` | Prescribes extension points and application flow | gRPC, Isaac Lab |
| `protocol` | Defines interoperable messages and behavior | Modbus |
| `platform` | Hosts or coordinates a wider solution ecosystem | ROS 2, Isaac Sim, Kubernetes, Docker |
| `tool` | Performs build, test, generation, packaging, or analysis | colcon |

Assign exactly one primary kind for deterministic routing. Use
`secondary_roles` for `middleware`, `ui_framework`, `rpc_stack`, `codegen`,
`simulator`, `robot_learning`, `motion_planning`, `container_runtime`,
`orchestrator`, `build_orchestrator`, or another reviewed role.

## Domain and lifecycle axes

Domains include `frontend`, `backend`, `api`, `robotics`, `simulation`,
`ai_ml`, `industrial_integration`, `devops_release`, and `operations`.
Lifecycle scope includes `design`, `build`, `test`, `generate`, `package`,
`deploy`, `runtime`, `integration`, `simulation`, `training`, and `operate`.

## Initial catalog

| Technology | Primary kind | Secondary roles |
| --- | --- | --- |
| ROS 2 | `platform` | middleware, framework, robotics ecosystem |
| Node.js | `runtime` | application/tooling runtime |
| React | `library` | UI framework |
| gRPC | `framework` | RPC stack, protocol integration, code generation |
| Isaac Lab | `framework` | robot learning, simulation training |
| Docker | `platform` | container toolchain, runtime |
| Isaac Sim | `platform` | robotics simulator, extension host |
| MoveIt 2 | `platform` | motion-planning framework, ROS 2 integration |
| Kubernetes | `platform` | workload orchestration, declarative control plane |
| Modbus | `protocol` | industrial application messaging |
| colcon | `tool` | multi-package build/test orchestration |

## Selection status

- `required_by_user`: mandated by an authorized requirement.
- `detected_existing`: observed in project artifacts or runtime evidence.
- `candidate`: being evaluated; no adoption authority.
- `selected`: accepted with evidence and required decision record.
- `rejected`: evaluated and not chosen, with rationale.
- `not_applicable`: unrelated to the current capability or module.
- `prohibited`: disallowed by policy, compatibility, license, or safety.

Keep version/distribution in a separate field. Never encode a mutable version
assumption in the technology ID.
