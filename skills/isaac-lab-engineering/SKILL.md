---
name: isaac-lab-engineering
description: Design, implement, review, debug, optimize, reproduce, or verify robot-learning systems built with NVIDIA Isaac Lab. Use for Isaac Lab projects, environments, tasks, manager-based or direct workflows, observations/actions/rewards/terminations, domain randomization, curricula, reinforcement or imitation learning, training/evaluation, checkpoints, vectorized simulation, sim-to-real, GPU/headless execution, or Isaac Lab and Isaac Sim compatibility.
---

# Isaac Lab Engineering

Treat a learning environment as a measurable experiment and software contract,
not merely a training script. Pin the Isaac Lab/Isaac Sim/hardware stack before
interpreting results.

## Entry gate

Require intake, architecture, measurable learning/simulation QAS, and the Isaac
Lab `TECH-*` record. Record Isaac Lab/Sim versions, install mode, Python/ML
stack, GPU/driver, assets, selected workflow, training library, and baseline
metrics. Costly cloud/GPU actions require explicit approval.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Define task MDP/behavior contract: observations, actions, rewards,
   terminations, resets, events/randomization, curriculum, timing, and metrics.
3. Choose manager-based or direct workflow from reuse/control needs; keep
   environment, agent configuration, training, evaluation, and assets owned.
4. Invoke `$isaac-sim-engineering` for material simulator/asset/physics/sensor
   decisions and `$language-engineering` for Python implementation.
5. Route seeds, paths, device, environment counts, physics/control rates,
   randomization ranges, checkpoints, logging, and backend values through
   `$configuration-and-environment-management`.
6. Verify deterministic software setup, smoke tests, reset/termination/reward
   invariants, training/evaluation separation, metric distributions,
   checkpoint resume, performance, and sim-to-real assumptions.

## Result and exit

Return compatibility pins, workflow/task contract, experiment configuration,
randomization/curriculum, training/evaluation, reproducibility limits,
verification, docs, and open points. Block implementation or result claims
when compatibility, metric, seed/artifact provenance, or evaluation protocol is
missing.
