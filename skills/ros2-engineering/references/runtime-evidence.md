# ROS 2 runtime evidence

Selected procedural ideas adapted from `dbwls99706/ros2-engineering-skills`
at `f0de84dfedd67b067ccc6d2851e681529606930c` (Apache-2.0). This is a bounded
core adaptation; upstream scripts, hooks and reference corpus are not active.

- Determine the affected workspace's distribution and binding from current
  evidence; `/opt/ros` inventory is not the running process's environment.
  Keep an existing distribution unless migration is part of the task.
- Source YAML and a successful build do not prove deployed or loaded values.
  Distinguish source revision, installed prefix/overlay, process invocation,
  launch overrides and observed parameters. Record which boundary each check
  actually examined; shell package resolution may differ from a running node.
- For missing data, compare names, types, domain/discovery and offered/requested
  endpoint QoS before changing reliability. A best-effort publisher cannot
  satisfy a reliable subscriber; matching QoS still does not prove freshness.
- Separate an asynchronous request that returns from its callback from a
  synchronous wait. Check callback groups, executor worker availability and
  binding semantics. Do not describe `rclpy.Future.result()` as a blocking wait.
- A connected TF chain is not proof of fresh transforms or a unique publisher.
  A graph listing is not an actuator-state measurement. A stop command or local
  API success is not evidence of physical stopping.
- Report static analysis, unit/mock tests, live middleware observations,
  simulation and hardware measurements separately. Missing dependencies,
  cancelled checks and partial output are not passes. Keep failures and
  uncertainty visible; do not relax a requirement just to obtain a green test.

Verify version-sensitive details against the target distribution's official
ROS 2/client-library documentation. These checks are conditional on the claim;
a prose edit does not require a live robot, a full workspace scan or a migration.

Primary API reference: [rclpy Future implementation](https://github.com/ros2/rclpy/blob/rolling/rclpy/rclpy/task.py).
Use the target distribution's branch for implementation decisions.
