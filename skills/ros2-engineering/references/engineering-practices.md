# ROS 2 engineering practices

## Architecture and structure

- Keep packages cohesive and dependency direction explicit. Separate reusable
  interface definitions when multiple packages/teams must share the contract;
  do not create an interface package for a purely private detail.
- Model nodes as independently testable responsibilities. Use composition when
  shared process/zero-copy/deployment needs justify it, not as an automatic
  performance assumption.
- Use managed lifecycle when configure/activate/deactivate/cleanup and ordered
  startup/recovery are operational requirements. Define transition failures.
- Treat launch as deployment composition and parameters as typed runtime
  configuration; keep business decisions out of launch files.

## Communication contracts

- Use topics for continuous/asynchronous streams, services for bounded quick
  request/response, and actions for long-running cancellable operations with
  feedback. Do not use services for operations that block unpredictably.
- Own message/service/action definitions, units, frames, timestamps, bounds,
  defaults, compatibility, and deprecation. Prefer stable semantic messages to
  transport-specific implementation state.
- Select QoS from publisher/subscriber and network requirements. Record
  reliability, durability, history/depth, deadline, lifespan, liveliness, and
  compatibility; do not assume defaults match sensor/control semantics.

## Execution and timing

- Define executors and callback groups from concurrency, blocking, ordering,
  and latency needs. Protect shared state explicitly; avoid callbacks that
  silently block executor progress.
- Give timers, subscriptions, actions, clients, background workers, and loaned
  messages clear ownership and shutdown/cancellation behavior.
- Define ROS time vs system/steady time, simulation clock behavior, timestamp
  source, and time-jump handling. Real-time paths require bounded allocation,
  blocking, logging, lock, and executor analysis.

## Language, build, and integration

- Use `rclcpp` with the C++ profile or `rclpy` with the Python profile. Preserve
  official binding lifecycle and ownership semantics over generic idioms.
- Use colcon/ament only when the project owns a ROS workspace. Record overlay
  order, package dependencies, generated interfaces, and environment sourcing.
- Treat ROS_DOMAIN_ID, RMW implementation, discovery/security, namespace,
  remapping, frame IDs, device addresses, and operational timeouts as reviewed
  configuration candidates, never hardcoded ambient assumptions.

## Verification and anti-patterns

- Verify package dependency declarations, interface generation, unit tests,
  component/node tests, launch tests, QoS interoperability, simulated/hardware
  integration as applicable, bag replay, tracing/latency, and clean shutdown.
- Use CLI introspection, `ros2 doctor`, rosbag2, and tracing as evidence, not as
  substitutes for acceptance tests.
- Reject giant nodes, hidden global executors, unbounded callback work,
  incompatible QoS, frame/unit ambiguity, launch-file business logic, and
  environment sourcing that exists only in a developer shell.

Primary sources: version-matched ROS 2 concepts, design documents, client
library, QoS, executor, lifecycle, launch, testing, and tracing documentation.
