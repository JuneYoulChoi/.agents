---
name: ros2-engineering
description: Design, implement, review, debug, migrate, or verify professional ROS 2 systems. Use for ROS 2 distributions, workspaces/packages, nodes/components, topics, services, actions, parameters, launch, lifecycle, QoS, executors, callback groups, DDS/RMW, rclcpp/rclpy bindings, rosbag, tracing, real-time behavior, robot interfaces, or ROS 1-to-ROS 2 and ROS 2 integration work.
---

# ROS 2 Engineering

Apply ROS 2 architecture and runtime rules before language-level implementation.
Do not reduce ROS 2 work to message publishing or CLI commands.

## Entry gate

Require intake, architecture, and a `TECH-*` record from
`$technology-selection-and-integration`. Brownfield work requires the ROS
distribution, RMW/DDS, workspace/overlay, package graph, interfaces, runtime
topology, and current tests/launch behavior. Real-time, safety, hardware, or
external-interface decisions are at least medium risk.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Map UC/FA responsibilities to node/component and package ownership.
3. Choose topic, service, action, or parameter by interaction semantics; record
   interface ownership, versioning, QoS, failure, and observability.
4. Define executor, callback-group, lifecycle, threading, time, shutdown, and
   composition behavior before implementation.
5. Select `$language-engineering` with C++/`rclcpp`, Python/`rclpy`, or each
   genuinely authored binding. Select `$colcon-workspace-engineering` only when
   workspace/build ownership is in scope.
6. Route parameters, domain/RMW selection, endpoints, timeouts, paths, and
   device settings through `$configuration-and-environment-management`.
7. Verify interface/QoS compatibility, unit/component/launch/system behavior,
   shutdown and failure paths, timing/performance QAS, and architecture docs.

For runtime diagnosis, also read
[references/runtime-evidence.md](references/runtime-evidence.md).
For an explicitly selected ROS MCP integration, read
[references/mcp-inspection.md](references/mcp-inspection.md). Do not require
MCP for ordinary ROS 2 development or infer robot access from skill selection.

## Result

```yaml
ros2:
  distribution: ''
  rmw: ''
  packages: []
  nodes_and_components: []
  interfaces: []
  qos_profiles: []
  execution_model: []
  lifecycle_and_shutdown: []
  language_bindings: []
  configuration_contracts: []
  verification: []
  mcp_inspection: null # optional; capability and observed evidence, never presumed
  documentation_effects: []
  open_points: []
transition:
  next_stage: clarification | design | execution | verification
  next_skill: ''
  entry_conditions: []
```

## Exit gate

Block implementation when a material interface, QoS, execution/lifecycle,
clock, safety, or real-time boundary is unowned or when a distribution/binding
combination is unsupported. Never hand-edit generated interface output.
