# Isaac Sim engineering practices

## Stage, assets, and application structure

- Pin Isaac Sim/Kit/extension API, install/container, Python, GPU driver, OS,
  and integration versions. Use documentation matching that release.
- Compose USD assets through intentional references/payloads/layers/variants;
  define source, units, up axis, scale, frame, material, collision, articulation,
  and writable session/override ownership. Do not flatten provenance casually.
- Separate reusable extension logic, standalone application/entrypoint,
  stage/scenario construction, configuration, assets, generated data, tests,
  caches, and outputs.

## Physics, sensors, and time

- Define physics timestep/substeps, control rate, render/sensor rate, real-time
  factor, reset order, and clock source. Use consistent units and coordinate
  frames across assets, controllers, sensors, and bridges.
- Validate mass/inertia, joints/limits/drives, collision shapes/filtering,
  contacts, gravity, materials, solver settings, and initial conditions against
  the fidelity needed by the UC/QAS.
- Define sensor model, rate, latency, noise, calibration, frame, timestamp,
  occlusion/range, and output contract. Photorealism is not sensor validation.

## Integration and verification

- For ROS 2, own bridge version, graph/interface, QoS, namespaces, simulation
  clock, frame tree, reset/time-jump behavior, and command/feedback safety.
- Separate GUI development, headless tests/training, streaming, container, and
  deployment profiles. Record GPU/memory/cache/artifact and license/EULA needs.
- Verify stage open/reference resolution, asset provenance, physics and sensor
  invariants, deterministic scenario/reset seeds within documented limits,
  integration contract, representative headless run, performance/memory, and
  golden/metric evidence appropriate to the fidelity claim.
- Reject hidden absolute asset paths, mixed units/axes, unversioned extensions,
  frame/time ambiguity, GUI-only automation, and validation by screenshots only.

Primary sources: the exact Isaac Sim release documentation, USD/PhysX/Kit
documentation applicable to that release, and official integration guides.
