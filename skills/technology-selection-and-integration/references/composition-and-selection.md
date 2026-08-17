# Composition and selection rules

## Purpose-first sequence

1. Start with UC, external interfaces, FA responsibilities, and measurable QAS.
2. Derive capabilities and operational constraints.
3. Detect existing technologies, versions, bindings, and ownership.
4. Classify named technologies as mandated, existing, or candidate.
5. Build a compatibility and integration graph.
6. Compare functionally equivalent alternatives.
7. Record ADR/approval for material adoption or replacement.
8. Load only the selected ecosystem and implementation-language skills.
9. Verify contracts, operations, configuration, and documentation.

## Relationship record

```yaml
from: TECH-001
to: TECH-002
type: required | recommended | optional | detected | incompatible
condition: ''
rationale: ''
evidence: []
```

The graph must be acyclic for build-time generation dependencies unless the
toolchain explicitly supports a bootstrapping cycle. Runtime communication may
be bidirectional but still records ownership, failure propagation, security,
and compatibility boundaries.

## Common non-implications

- React may use Node.js for build tooling without deploying a Node.js server.
- Docker packages/runs containers; Kubernetes is selected separately for
  orchestration needs.
- ROS 2 may use colcon for a workspace, but a prebuilt consumer need not own a
  colcon workspace.
- MoveIt 2 depends on a compatible ROS 2 ecosystem; ROS 2 does not require
  MoveIt.
- Isaac Lab normally depends on a compatible Isaac Sim/runtime combination;
  ROS 2, Docker, and Kubernetes remain conditional integration choices.
- Modbus is an external protocol boundary, not evidence for a particular
  language library or ROS bridge.
- gRPC code generation selects only the languages of actual producers and
  consumers.

## Compatibility checklist

Check only applicable dimensions, but never omit an applicable one silently:

```text
version/distribution and support window
OS, CPU architecture, libc/runtime, browser, or device
language binding and generated-code/plugin versions
GPU, driver, simulator, middleware, and transport
wire/API/schema compatibility and rollout order
license, security boundary, credentials, and data sensitivity
build, package, deployment, observability, and rollback behavior
```

Brownfield adoption must preserve current behavior or provide a migration,
compatibility window, characterization tests, and rollback. Greenfield
selection must state alternatives and why the smallest selected stack satisfies
the requirements.
