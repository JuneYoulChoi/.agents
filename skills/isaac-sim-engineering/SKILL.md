---
name: isaac-sim-engineering
description: Design, implement, review, debug, optimize, integrate, or verify NVIDIA Isaac Sim robotics simulations. Use for USD stages/assets/prims, extensions or standalone applications, physics and articulation setup, sensors and rendering, simulation time, headless execution, asset pipelines, ROS 2 bridge, synthetic data, performance, GPU/driver compatibility, or simulation architecture and validation.
---

# Isaac Sim Engineering

Treat simulation assets, physics, sensors, time, and extensions as versioned
architecture. Visual plausibility alone is not physical or behavioral validity.

## Entry gate

Require intake, architecture/simulation QAS, and the Isaac Sim `TECH-*` record.
Record release/install mode, Kit/Python/extension API, GPU/driver/OS, assets,
stage units/axes, physics/render settings, headless/GUI profile, and integrations.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Define stage/USD ownership, asset composition, extension vs standalone
   boundary, physics/control/sensor timing, frames/units, and artifact outputs.
3. Invoke `$language-engineering` for Python/C++ authored extensions or apps;
   do not hand-edit generated/cache artifacts.
4. Invoke `$ros2-engineering` only when ROS interfaces/bridge behavior is in
   scope and `$isaac-lab-engineering` only for learning-task behavior.
5. Route assets/paths, renderer, device, rates, seeds, bridge/domain, streaming,
   and headless/runtime profiles through configuration.
6. Verify compatibility, stage/assets, physics/sensor invariants, deterministic
   scenario setup, headless/GUI behavior, integration clocks/frames/QoS,
   performance/memory, and documented fidelity limitations.

## Result and exit

Return compatibility, stage/asset and application/extension ownership,
physics/sensor/time contracts, integrations, configuration, fidelity QAS,
verification, docs, and open points. Block material work or fidelity claims
when units/frames, asset provenance, timing, compatibility, or validation
criteria are absent.
