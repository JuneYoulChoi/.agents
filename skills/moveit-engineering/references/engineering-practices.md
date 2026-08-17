# MoveIt engineering practices

## Models and planning scene

- Version URDF/xacro, SRDF, joint/link limits, collision geometry/matrices,
  kinematics, controllers, calibration, and tooling-generated configuration as
  one compatibility set. Document generated vs owned portions.
- Define planning groups/end effectors/passive or mimic joints and frames from
  actual robot capabilities. Validate self-collision exclusions rather than
  accepting generated output blindly.
- Own PlanningScene/scene-monitor inputs, attached objects, transforms, sensor
  updates, freshness, synchronization, and world-reset behavior.

## Planning and execution

- Select planner/pipeline/request adapters from constraints, completeness,
  timing, path quality, and environment dynamics; record alternatives and
  parameters. One successful plan is not a performance baseline.
- Define start-state validation, goal/path constraints, collision margins,
  planning attempts/timeouts, replanning, cancellation, path simplification,
  time parameterization, velocity/acceleration/jerk limits, and result errors.
- Separate planning from trajectory validation/execution and independent robot
  safety. Own controller mapping, feedback, tolerance, preemption, stop/recovery,
  and scene/model version at execution time.
- Use Task Constructor or hybrid planning only when compositional or reactive
  planning requirements justify their additional state/failure complexity.

## Verification and anti-patterns

- Verify model/config loading, FK/IK and singular/unreachable cases, collision
  and attached objects, constraints, planner failure/timeout distributions,
  trajectory limits/time parameterization, scene update races, cancellation,
  controller simulation, representative scenarios, and guarded hardware tests.
- Reject stale planning scenes, frame/unit ambiguity, disabled collision without
  evidence, planner tuning from a single path, direct execution of unvalidated
  trajectories, and treating simulation success as hardware safety approval.

Primary sources: version-matched MoveIt 2 concepts/how-to/API documentation,
ROS 2/control documentation, robot/controller specifications, and project
safety policy.
