---
name: moveit-engineering
description: Design, implement, configure, review, debug, optimize, migrate, or verify MoveIt 2 robotic manipulation systems. Use for robot models and SRDF, planning groups, PlanningScene, move_group, kinematics, collision checking, planners and planning pipelines, request adapters, constraints, trajectory processing/execution, controllers, MoveIt Task Constructor, hybrid planning, or MoveIt and ROS 2 integration.
---

# MoveIt Engineering

Treat motion planning output as a constrained proposal inside a larger robot
safety and execution architecture. MoveIt configuration is not proof that a
trajectory is safe on hardware.

## Entry gate

Require intake, robot/architecture/safety evidence, compatible ROS 2 and MoveIt
`TECH-*` records, and Brownfield baseline when applicable. Record robot model,
SRDF/groups, planning scene sources, kinematics, pipelines, controllers,
frames/limits, execution environment, and current tests.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Define robot/semantic model ownership, planning-scene/world updates, group,
   constraints, collision, kinematics, planner/pipeline, and execution boundary.
3. Define timeouts, replanning, cancellation, trajectory validation,
   controller feedback, failure/recovery, and independent safety controls.
4. Invoke `$ros2-engineering`, then `$language-engineering` for C++/Python
   authored APIs; use `$colcon-workspace-engineering` only for owned workspaces.
5. Route planner IDs/parameters, limits, frames, timeouts, scene sources, and
   controller mappings through configuration with model provenance.
6. Verify models/config, collision/constraints, planning success and failure
   distributions, trajectory processing/execution, scene freshness, simulated
   integration, hardware gates, timing, rollback, and docs.

## Result and exit

Return models/groups, scene and planning pipeline, kinematics/constraints,
execution/safety, language/configuration, verification, docs, and open points.
Block hardware execution when model/limits/frames, scene freshness, controller
mapping, cancellation, or safety authority is unverified.
